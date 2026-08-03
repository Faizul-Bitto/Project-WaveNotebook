from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class OTP(Base):
    __tablename__ = "otps"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    phone_number = Column(
        String(20),
        nullable=False,
    )

    # Stores the hashed OTP
    code = Column(
        String(255),
        nullable=False,
    )

    # register, login, password_reset,
    # email_verification, phone_verification
    purpose = Column(
        String(50),
        nullable=False,
        index=True,
    )

    is_used = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    expires_at = Column(
        DateTime,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
