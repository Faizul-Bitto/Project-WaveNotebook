from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.sql import func

from app.core.database import Base


class ProductAttributeOption(Base):
    __tablename__ = "product_attribute_options"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    attribute_option_id = Column(
        Integer,
        ForeignKey("attribute_options.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    additional_price = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,
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
