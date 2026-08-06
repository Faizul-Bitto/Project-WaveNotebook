from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    cart_session_id = Column(
        String(100),
        nullable=False,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quantity = Column(
        Integer,
        nullable=False,
        default=1,
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