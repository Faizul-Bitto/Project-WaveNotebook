from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class OrderAdjustment(Base):
    """
    Manual discount/adjustment applied by an admin on an existing order.

    This is a separate ledger from BOGO / product / bundle discounts. It is
    used when an admin manually adjusts an order's total (e.g. loyalty
    discount, complaint resolution, goodwill credit).
    """
    __tablename__ = "order_adjustments"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Which admin made the adjustment (nullable if admin later deleted)
    admin_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # E.g. "manual_discount", "manual_charge", "rounding"
    adjustment_type = Column(
        String(50),
        nullable=False,
        default="manual_discount",
        server_default="manual_discount",
    )

    # How the value was expressed: 'flat' (BDT) or 'percentage' (% of current total)
    value_type = Column(
        String(20),
        nullable=True,
        default="flat",
        server_default="flat",
        comment="flat | percentage",
    )

    # Positive = reduce order total (discount), negative = increase order total (chargeback)
    amount = Column(
        Numeric(10, 2),
        nullable=False,
    )

    reason = Column(
        Text,
        nullable=True,
        comment="Admin-provided reason for the adjustment",
    )

    # JSON snapshot of the order total before / after this adjustment
    before_total = Column(
        Numeric(10, 2),
        nullable=True,
    )

    after_total = Column(
        Numeric(10, 2),
        nullable=True,
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