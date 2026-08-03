from typing import Annotated

from fastapi import Depends, HTTPException
from jose import JWTError, jwt
from starlette import status

from app.core.config import settings
from app.dependencies.auth import oauth2_bearer_token_dependency
from app.dependencies.database import db_dependency
from app.models.user import User


async def get_current_user(
    token: oauth2_bearer_token_dependency,
    db: db_dependency,
) -> User:
    """
    Validate the JWT access token and return the authenticated user.

    Raises:
        HTTPException: If the access token is invalid, expired,
        or the user no longer exists.
    """

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[
                settings.ALGORITHM,
            ],
        )

        user_id = payload.get("sub")

        if user_id is None:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token.",
            )

        user = (
            db.query(User)
            .filter(
                User.id == int(user_id),
            )
            .first()
        )

        if user is None:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        return user

    except JWTError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        )


user_dependency = Annotated[
    User,
    Depends(get_current_user),
]
