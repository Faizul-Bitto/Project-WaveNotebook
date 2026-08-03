from typing import Annotated

from fastapi import Depends, HTTPException
from starlette import status

from app.dependencies.user import user_dependency
from app.models.user import User


async def get_current_admin(
    user: user_dependency,
) -> User:
    """
    Ensure the authenticated user has administrator privileges.

    Raises:
        HTTPException: If the authenticated user is not an administrator.
    """

    if user.role != "admin":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )

    return user


admin_dependency = Annotated[
    User,
    Depends(get_current_admin),
]
