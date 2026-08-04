# app/models/category.py
from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(255),
        nullable=False,
        index=True,
    )

    slug = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    parent_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
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
