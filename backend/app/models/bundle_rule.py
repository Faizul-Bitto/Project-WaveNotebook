from sqlalchemy import Boolean, Column, ForeignKey, Integer, Text, String

from app.core.database import Base


class BundleRule(Base):
    __tablename__ = "bundle_rules"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    discount_id = Column(
        Integer,
        ForeignKey("discounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    bundle_type = Column(
        String(20),
        nullable=False,
        comment="quantity | combo",
    )

    # JSON string of product IDs (used only for combo bundles)
    # e.g. "[1, 3, 5]"
    required_products = Column(
        Text,
        nullable=True,
    )

    # Whether this bundle rule also grants free shipping (UI label only)
    free_shipping = Column(
        Boolean,
        nullable=False,
        default=False,
    )
