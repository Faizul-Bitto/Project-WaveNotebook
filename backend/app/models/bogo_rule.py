from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.sql import func

from app.core.database import Base


class BogoRule(Base):
    __tablename__ = "bogo_rules"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    discount_id = Column(
        Integer,
        ForeignKey("discounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    selected_attributes = Column(
        Text,
        nullable=True,
    )

    buy_quantity = Column(
        Integer,
        nullable=False,
    )

    get_quantity = Column(
        Integer,
        nullable=False,
    )

    get_discount_percent = Column(
        Numeric(10, 2),
        nullable=False,
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