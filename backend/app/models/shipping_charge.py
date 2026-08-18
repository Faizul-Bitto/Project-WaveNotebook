from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class ShippingCharge(Base):
    __tablename__ = "shipping_charges"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    zone_name = Column(
        String(255),
        nullable=False,
        index=True,
    )

    amount = Column(
        Integer,
        nullable=False,
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
