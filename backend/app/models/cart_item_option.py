from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func

from app.core.database import Base


class CartItemOption(Base):
    __tablename__ = "cart_item_options"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    cart_item_id = Column(
        Integer,
        ForeignKey("cart_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_attribute_option_id = Column(
        Integer,
        ForeignKey(
            "product_attribute_options.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
