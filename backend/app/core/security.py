from datetime import datetime, timedelta, timezone
import secrets

from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User

# Password Hashing
bcrypt_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


# OAuth2
oauth2_bearer = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


def hash_password(password: str) -> str:
    """
    Hash a plain text password.
    """

    return bcrypt_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain password against its hashed value.
    """

    return bcrypt_context.verify(
        plain_password,
        hashed_password,
    )


def authenticate_user(
    phone_number: str,
    password: str,
    db: Session,
) -> User | None:
    """
    Authenticate a user using phone number.
    """

    user = db.query(User).filter(User.phone_number == phone_number).first()

    if user is None:
        return None

    if user.password is None:
        return None

    if not verify_password(
        password,
        user.password,
    ):
        return None

    return user


def create_access_token(
    user_id: int,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Generate a JWT access token.
    """

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )