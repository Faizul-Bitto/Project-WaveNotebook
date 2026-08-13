from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, Date
from sqlalchemy.sql import func

from app.core.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    expense_type_id = Column(
        Integer,
        ForeignKey("expense_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    payment_by_id = Column(
        Integer,
        ForeignKey("payment_by.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    payment_method_id = Column(
        Integer,
        ForeignKey("payment_methods.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    date = Column(
        Date,
        nullable=False,
        index=True,
    )

    items = Column(
        String(500),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    amount = Column(
        Float,
        nullable=False,
    )

    payment_status = Column(
        String(50),
        nullable=False,
        default="paid",
        index=True,
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
