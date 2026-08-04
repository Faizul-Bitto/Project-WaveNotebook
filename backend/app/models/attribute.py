from sqlalchemy import Column, DateTime, Integer, String, Boolean
from sqlalchemy.sql import func

from app.core.database import Base


class Attribute(Base):
    __tablename__ = "attributes"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    slug = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
