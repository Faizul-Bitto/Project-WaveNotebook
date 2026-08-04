from fastapi import APIRouter, HTTPException
from starlette import status

from app.dependencies.database import db_dependency
from app.dependencies.user import user_dependency
from app.schemas.user import (
    UpdatePhoneRequest,
    UpdateUserRequest,
    UserUpdatePasswordRequest,
    VerifyPhoneUpdateRequest,
)
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_profile(user: user_dependency):
    """
    Retrieve the authenticated user's profile.
    """

    try:

        result = UserService.get_user_profile(user)

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/me", status_code=status.HTTP_200_OK)
async def update_profile(
    user: user_dependency,
    db: db_dependency,
    update_request: UpdateUserRequest,
):
    """
    Update the authenticated user's profile (name and email only).
    """

    try:

        result = UserService.update_profile(db, user, update_request)

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/me/phone/request", status_code=status.HTTP_200_OK)
async def request_phone_update(
    user: user_dependency,
    db: db_dependency,
    request: UpdatePhoneRequest,
):
    """
    Request phone number update - sends OTP to new phone number.
    """

    try:

        result = UserService.request_phone_update(db, user, request)

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/me/phone/verify", status_code=status.HTTP_200_OK)
async def verify_phone_update(
    user: user_dependency,
    db: db_dependency,
    request: VerifyPhoneUpdateRequest,
):
    """
    Verify OTP for phone number update.
    """

    try:

        result = UserService.verify_phone_update(db, user, request)

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/me/phone/confirm", status_code=status.HTTP_200_OK)
async def confirm_phone_update(
    user: user_dependency,
    db: db_dependency,
    verified_phone_number: str,
):
    """
    Confirm and update phone number after OTP verification.
    """

    try:

        result = UserService.confirm_phone_update(db, user, verified_phone_number)

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/me/password", status_code=status.HTTP_200_OK)
async def update_password(
    user: user_dependency,
    db: db_dependency,
    update_password_request: UserUpdatePasswordRequest,
):
    """
    Update the authenticated user's password.
    """

    try:

        result = UserService.update_password(user, update_password_request)

        db.commit()
        db.refresh(user)

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )