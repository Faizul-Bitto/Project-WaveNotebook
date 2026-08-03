from fastapi import APIRouter, HTTPException
from starlette import status

from app.dependencies.database import db_dependency
from app.dependencies.user import user_dependency
from app.schemas.user import UpdateUserRequest, UserUpdatePasswordRequest
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
    Update the authenticated user's profile.
    """

    try:

        result = UserService.update_profile(db, user, update_request)

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