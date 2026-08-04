from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.sql import func

from app.core.database import Base


class AttributeOption(Base):
    __tablename__ = "attribute_options"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    attribute_id = Column(
        Integer,
        ForeignKey("attributes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    value = Column(
        String(255),
        nullable=False,
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
