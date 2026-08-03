from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


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

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    total_amount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,
    )

    # Customer snapshot
    customer_first_name = Column(
        String(100),
        nullable=False,
    )

    customer_last_name = Column(
        String(100),
        nullable=False,
    )

    customer_phone = Column(
        String(20),
        nullable=False,
    )

    customer_email = Column(
        String(255),
        nullable=True,
    )

    # Delivery info
    district = Column(
        String(100),
        nullable=False,
    )

    delivery_address = Column(
        Text,
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
