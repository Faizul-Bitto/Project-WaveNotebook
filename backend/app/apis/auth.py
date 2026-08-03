from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from starlette import status

from app.core.config import settings
from app.core.logger import logger
from app.core.security import (
    authenticate_user,
    create_access_token,
    generate_otp,
    hash_password,
    verify_password,
)
from app.core.sms import send_sms

from app.dependencies.auth import login_token_field_dependency
from app.dependencies.database import db_dependency

from app.models.otp import OTP
from app.models.user import User

from app.schemas.auth import (
    CreateUserRequest,
    Token,
    ForgotPasswordRequest,
    VerifyOTPRequest,
    ResetPasswordRequest,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# --------------------------
# Register
# --------------------------
@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    db: db_dependency,
    create_user_request: CreateUserRequest,
):
    """
    Register a new user.
    """

    existing_phone = (
        db.query(User)
        .filter(User.phone_number == create_user_request.phone_number)
        .first()
    )

    if existing_phone:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered.",
        )

    if create_user_request.email:

        existing_email = (
            db.query(User).filter(User.email == create_user_request.email).first()
        )

        if existing_email:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered.",
            )

    user = User(
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        phone_number=create_user_request.phone_number,
        email=create_user_request.email,
        password=hash_password(create_user_request.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(
        f"✅ User Registered | " f"User ID={user.id} | " f"Phone={user.phone_number}"
    )

    return {
        "message": "User registered successfully.",
        "user": {
            "id": user.id,
            "phone_number": user.phone_number,
            "role": user.role,
        },
    }


# --------------------------
# Login
# --------------------------
@router.post(
    "/login",
    response_model=Token,
)
async def login(
    form_data: login_token_field_dependency,
    db: db_dependency,
):
    """
    Login using phone number and password.
    """

    user = authenticate_user(
        phone_number=form_data.username,
        password=form_data.password,
        db=db,
    )

    if not user:

        logger.warning(f"❌ Login Failed | " f"Phone={form_data.username}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password.",
        )

    logger.info(
        f"🔑 Login Successful | " f"User ID={user.id} | " f"Phone={user.phone_number}"
    )

    token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


# --------------------------
# Forgot Password
# --------------------------
@router.post(
    "/forgot-password",
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: db_dependency,
):
    """
    Send OTP to user's phone number.
    """

    user = db.query(User).filter(User.phone_number == request.phone_number).first()

    if not user:

        return {"message": "If phone number exists, OTP has been sent."}

    # Disable previous OTP
    db.query(OTP).filter(
        OTP.user_id == user.id,
        OTP.purpose == "password_reset",
        OTP.is_used.is_(False),
    ).update({OTP.is_used: True})

    db.commit()

    otp = generate_otp()

    otp_record = OTP(
        user_id=user.id,
        code=hash_password(otp),
        purpose="password_reset",
        expires_at=(
            datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        ),
    )

    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)

    try:

        send_sms(
            phone_number=user.phone_number,
            message=(
                f"Your password reset OTP is {otp}. "
                f"Expires in {settings.OTP_EXPIRE_MINUTES} minutes."
            ),
        )

        logger.info(
            f"📱 Password Reset OTP Sent | "
            f"User ID={user.id} | "
            f"Phone={user.phone_number}"
        )

    except Exception:

        logger.exception(
            f"❌ Failed To Send Password Reset OTP | "
            f"User ID={user.id} | "
            f"Phone={user.phone_number}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send OTP. Please try again later.",
        )

    return {"message": "If phone number exists, OTP has been sent."}


# --------------------------
# Verify OTP
# --------------------------
@router.post(
    "/verify-otp",
)
async def verify_otp(
    request: VerifyOTPRequest,
    db: db_dependency,
):

    user = db.query(User).filter(User.phone_number == request.phone_number).first()

    if not user:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP.",
        )

    otp_record = (
        db.query(OTP)
        .filter(
            OTP.user_id == user.id,
            OTP.purpose == "password_reset",
            OTP.is_used.is_(False),
        )
        .order_by(OTP.created_at.desc())
        .first()
    )

    if not otp_record:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP.",
        )

    if datetime.now(timezone.utc) > otp_record.expires_at:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired.",
        )

    if not verify_password(
        request.otp,
        otp_record.code,
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP.",
        )

    otp_record.verified = True

    db.commit()

    logger.info(
        f"✅ Password Reset OTP Verified | "
        f"User ID={user.id} | "
        f"Phone={user.phone_number}"
    )

    return {"message": "OTP verified successfully."}


# --------------------------
# Reset Password
# --------------------------
@router.post(
    "/reset-password",
)
async def reset_password(
    request: ResetPasswordRequest,
    db: db_dependency,
):

    user = db.query(User).filter(User.phone_number == request.phone_number).first()

    if not user:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request.",
        )

    otp_record = (
        db.query(OTP)
        .filter(
            OTP.user_id == user.id,
            OTP.purpose == "password_reset",
            OTP.verified.is_(True),
            OTP.is_used.is_(False),
        )
        .order_by(OTP.created_at.desc())
        .first()
    )

    if not otp_record:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP verification required.",
        )

    if datetime.now(timezone.utc) > otp_record.expires_at:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired.",
        )

    user.password = hash_password(request.new_password)

    otp_record.verified = False
    otp_record.is_used = True

    db.commit()
    db.refresh(user)
    db.refresh(otp_record)

    logger.info(
        f"🔐 Password Reset Successful | "
        f"User ID={user.id} | "
        f"Phone={user.phone_number}"
    )

    return {"message": "Password reset successfully."}
