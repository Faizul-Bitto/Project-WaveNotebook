import json

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class OrderItem(Base):
    __tablename__ = "order_items"

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

    # CHANGED: nullable True, ondelete SET NULL so order item survives product deletion
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # NEW: JSON snapshot of product name, code, etc. at time of order
    product_snapshot = Column(Text, nullable=False, server_default="{}")

    # NEW: JSON snapshot of variant options and price at time of order
    variant_snapshot = Column(Text, nullable=False, server_default="{}")

    quantity = Column(
        Integer,
        nullable=False,
    )

    unit_price = Column(
        Numeric(10, 2),
        nullable=False,
    )

    price_at_purchase = Column(
        Numeric(10, 2),
        nullable=False,
    )

    discount_amount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,
        server_default="0",
    )

    # BOGO bonus units added for free/discounted (physical units shipped & stock-adjusted)
    bonus_quantity = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    selected_attributes = Column(
        Text,
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

    def get_product_snapshot(self) -> dict:
        """Parse product_snapshot JSON and return dict, or {} on failure."""
        try:
            return json.loads(self.product_snapshot) if self.product_snapshot else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def get_variant_snapshot(self) -> dict:
        """Parse variant_snapshot JSON and return dict, or {} on failure."""
        try:
            return json.loads(self.variant_snapshot) if self.variant_snapshot else {}
        except (json.JSONDecodeError, TypeError):
            return {}