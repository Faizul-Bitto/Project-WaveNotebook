from sqlalchemy import Column, ForeignKey, Integer, String

from app.core.database import Base


class DiscountScope(Base):
    __tablename__ = "discount_scopes"

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

    scope_type = Column(
        String(20),
        nullable=False,
        comment="product | category",
    )

    scope_id = Column(
        Integer,
        nullable=False,
    )
