from sqlalchemy import Column, ForeignKey, Integer, Numeric, String

from app.core.database import Base


class BundleSlab(Base):
    __tablename__ = "bundle_slabs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    bundle_rule_id = Column(
        Integer,
        ForeignKey("bundle_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    min_quantity = Column(
        Integer,
        nullable=False,
    )

    value_type = Column(
        String(20),
        nullable=False,
        comment="percentage | flat",
    )

    value = Column(
        Numeric(10, 2),
        nullable=False,
    )
