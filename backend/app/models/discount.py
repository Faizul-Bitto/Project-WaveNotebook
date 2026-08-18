from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.core.database import Base


class Discount(Base):
    __tablename__ = "discounts"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(255),
        nullable=False,
    )

    type = Column(
        String(50),
        nullable=False,
        comment="percentage | flat | bundle | bogo | free_shipping",
    )

    # For percentage / flat discounts
    value_type = Column(
        String(20),
        nullable=True,
        comment="percentage | flat  (NULL for bundle, bogo, free_shipping)",
    )

    value = Column(
        Numeric(10, 2),
        nullable=True,
        comment="percentage (0-100) or flat amount",
    )

    max_discount_cap = Column(
        Numeric(10, 2),
        nullable=True,
        comment="Cap total discount for percentage discounts (optional)",
    )

    start_date = Column(
        DateTime,
        nullable=False,
    )

    end_date = Column(
        DateTime,
        nullable=True,
        comment="NULL means unlimited time",
    )

    status = Column(
        String(20),
        nullable=False,
        default="active",
    )

    free_shipping = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="If true, this discount rule includes free shipping",
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
