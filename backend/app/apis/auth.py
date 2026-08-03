from fastapi import APIRouter, HTTPException
from starlette import status

from app.dependencies.auth import login_token_field_dependency
from app.dependencies.database import db_dependency
from app.exceptions.auth_exceptions import (
    BadRequestException,
    ConflictException,
    ExternalServiceException,
    UnauthorizedException,
)
from app.schemas.auth import (
    CreateUserRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    VerifyOTPRequest,
)
from app.services.auth_service import AuthService

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

    try:

        result = AuthService.register_user(db, create_user_request)

        return result

    except ConflictException as e:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


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

    try:

        result = AuthService.login_user(db, form_data)

        return result

    except UnauthorizedException as e:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


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

    try:

        result = AuthService.forgot_password(db, request)

        return result

    except ExternalServiceException as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


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
    """
    Verify OTP for password reset.
    """

    try:

        result = AuthService.verify_otp(db, request)

        return result

    except BadRequestException as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


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
    """
    Reset user password.
    """

    try:

        result = AuthService.reset_password(db, request)

        return result

    except BadRequestException as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )