from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Banner(Base):
    __tablename__ = "banners"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    subtitle = Column(
        String(255),
        nullable=True,
    )

    image_url = Column(
        String(500),
        nullable=False,
    )

    link_url = Column(
        String(500),
        nullable=True,
    )

    sort_order = Column(
        Integer,
        nullable=False,
        default=0,
    )

    is_active = Column(
        Integer,
        nullable=False,
        default=1,
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