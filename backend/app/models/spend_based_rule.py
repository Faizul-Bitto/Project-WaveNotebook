from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class SpendBasedRule(Base):
    """
    Spend-based discount rule.

    Applies discount based on cart/order total spend amount.
    Can be storewide or category-specific.
    """
    __tablename__ = "spend_based_rules"

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

    # 'storewide', 'category', or 'product'
    scope_type = Column(
        String(20),
        nullable=False,
        default="storewide",
        server_default="storewide",
    )

    # Category or Product ID when scope_type is 'category' or 'product', NULL for storewide
    scope_id = Column(
        Integer,
        nullable=True,
        index=True,
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

