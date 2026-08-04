from datetime import timedelta

from fastapi import APIRouter, HTTPException
from starlette import status

from app.core.config import settings
from app.core.logger import logger
from app.core.security import (
    authenticate_user,
    create_access_token,
)
from app.dependencies.auth import login_token_field_dependency
from app.dependencies.database import db_dependency
from app.schemas.auth import Token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(form_data: login_token_field_dependency, db: db_dependency):
    """
    Authenticate a user and return a JWT access token.

    Raises:
        HTTPException: If the credentials are invalid.
    """

    user = authenticate_user(
        phone_number=form_data.username,
        password=form_data.password,
        db=db,
    )

    if not user:
        logger.warning(f"❌ Login Failed | Phone Number={form_data.username}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password.",
        )

    token = create_access_token(
        user_id=user.id,
        role=user.role,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    logger.info(
        f"🔐 User Logged In | "
        f"ID={user.id} | "
        f"Phone={user.phone_number} | "
        f"Email={user.email} | "
        f"Role={user.role}"
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }
