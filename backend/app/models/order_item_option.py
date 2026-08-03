from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class OrderItemOption(Base):
    __tablename__ = "order_item_options"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    order_item_id = Column(
        Integer,
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    attribute_name = Column(
        String(100),
        nullable=False,
    )

    option_value = Column(
        String(100),
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
