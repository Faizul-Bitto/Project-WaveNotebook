from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.sql import func

from app.core.database import Base


class DiscountUsage(Base):
    __tablename__ = "discount_usage"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    discount_id = Column(
        Integer,
        ForeignKey("discounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    applied_amount = Column(
        Numeric(10, 2),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )