import json

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from app.core.database import Base
from app.constants.order_status import OrderStatus


class Order(Base):
    __tablename__ = "orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    order_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    # CHANGED: ondelete SET NULL, nullable True so order survives user deletion
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # NEW: JSON snapshot of user info at time of order (survives user deletion)
    user_snapshot = Column(Text, nullable=False, server_default="{}")

    full_name = Column(
        String(255),
        nullable=False,
    )

    phone_number = Column(
        String(20),
        nullable=False,
    )

    email = Column(
        String(255),
        nullable=True,
    )

    district = Column(
        String(100),
        nullable=False,
    )

    thana = Column(
        String(100),
        nullable=False,
        server_default="",
    )

    address = Column(
        Text,
        nullable=False,
    )

    note = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(50),
        nullable=False,
        default=OrderStatus.PENDING.value,
        index=True,
    )

    total_price = Column(
        Numeric(10, 2),
        nullable=False,
    )

    total_discount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,
        server_default="0",
    )

    # JSON snapshot of discount breakdown at time of order (survives rule changes)
    discount_snapshot = Column(Text, nullable=False, server_default="{}")

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

    def get_user_snapshot(self) -> dict:
        """Parse user_snapshot JSON and return dict, or {} on failure."""
        try:
            return json.loads(self.user_snapshot) if self.user_snapshot else {}
        except (json.JSONDecodeError, TypeError):
            return {}