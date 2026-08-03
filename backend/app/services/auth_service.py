from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session


def ensure_timezone_aware(dt):
    """Ensure datetime is timezone-aware"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

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
from app.models.otp import OTP
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyOTPRequest,
)


class AuthService:

    @staticmethod
    def register_user(db: Session, create_user_request) -> dict:
        """
        Register a new user.
        """

        existing_phone = (
            db.query(User)
            .filter(User.phone_number == create_user_request.phone_number)
            .first()
        )

        if existing_phone:

            raise ValueError("Phone number already registered.")

        if create_user_request.email:

            existing_email = (
                db.query(User).filter(User.email == create_user_request.email).first()
            )

            if existing_email:

                raise ValueError("Email already registered.")

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
            f"✅ User Registered | "
            f"User ID={user.id} | "
            f"Phone={user.phone_number}"
        )

        return {
            "message": "User registered successfully.",
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number,
                "email": user.email,
                "role": user.role,
            },
        }

    @staticmethod
    def login_user(db: Session, form_data) -> dict:
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

            raise ValueError("Incorrect phone number or password.")

        logger.info(
            f"🔑 Login Successful | "
            f"User ID={user.id} | "
            f"Phone={user.phone_number}"
        )

        token = create_access_token(
            user_id=user.id,
            role=user.role,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    @staticmethod
    def forgot_password(db: Session, request: ForgotPasswordRequest) -> dict:
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
            phone_number=user.phone_number,
            code=hash_password(otp),
            purpose="password_reset",
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
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

            raise RuntimeError("Unable to send OTP. Please try again later.")

        return {"message": "If phone number exists, OTP has been sent."}

    @staticmethod
    def verify_otp(db: Session, request: VerifyOTPRequest) -> dict:
        """
        Verify OTP for password reset.
        """

        user = db.query(User).filter(User.phone_number == request.phone_number).first()

        if not user:

            raise ValueError("Invalid OTP.")

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

            raise ValueError("Invalid OTP.")

        if datetime.now(timezone.utc) > ensure_timezone_aware(otp_record.expires_at):

            raise ValueError("OTP expired.")

        if not verify_password(
            request.otp,
            otp_record.code,
        ):

            raise ValueError("Invalid OTP.")

        otp_record.verified = True

        db.commit()

        logger.info(
            f"✅ Password Reset OTP Verified | "
            f"User ID={user.id} | "
            f"Phone={user.phone_number}"
        )

        return {"message": "OTP verified successfully."}

    @staticmethod
    def reset_password(db: Session, request: ResetPasswordRequest) -> dict:
        """
        Reset user password.
        """

        user = db.query(User).filter(User.phone_number == request.phone_number).first()

        if not user:

            raise ValueError("Invalid request.")

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

            raise ValueError("OTP verification required.")

        if datetime.now(timezone.utc) > ensure_timezone_aware(otp_record.expires_at):

            raise ValueError("OTP expired.")

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
