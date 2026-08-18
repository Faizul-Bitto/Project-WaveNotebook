from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class SpendBasedSlab(Base):
    """
    Slab/tier for spend-based discount.

    Each slab defines a minimum spend amount and the discount to apply.
    Only the highest applicable slab is used (like quantity bundle slabs).
    """
    __tablename__ = "spend_based_slabs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    spend_based_rule_id = Column(
        Integer,
        ForeignKey("spend_based_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    min_spend_amount = Column(
        Numeric(10, 2),
        nullable=False,
        comment="Minimum cart spend to trigger this slab",
    )

    # 'percentage' or 'flat'
    value_type = Column(
        String(20),
        nullable=False,
        comment="percentage | flat",
    )

    value = Column(
        Numeric(10, 2),
        nullable=False,
        comment="Percentage (0-100) or flat amount in BDT",
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
