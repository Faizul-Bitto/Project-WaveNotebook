from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.core.database import Base


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sku = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    # JSON: {"Size": "A4", "Color": "Black", "Quality": "Normal"}
    selected_attributes = Column(Text, nullable=False)

    # Direct selling price (no calculation - set by admin)
    price = Column(Numeric(10, 2), nullable=False)

    # Stock quantity
    stock_quantity = Column(Integer, nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)