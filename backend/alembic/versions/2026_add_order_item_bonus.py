"""Add bonus_quantity to order_items for BOGO free units

Revision ID: 2026_add_order_item_bonus
Revises: 2026_add_order_discount_columns
Create Date: 2026-08-16 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '2026_add_order_item_bonus'
down_revision = '2026_add_order_discount_columns'
branch_labels = None
depends_on = None


def _column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in existing


def upgrade() -> None:
    if not _column_exists("order_items", "bonus_quantity"):
        op.add_column(
            "order_items",
            sa.Column("bonus_quantity", sa.Integer, nullable=False, server_default="0"),
        )


def downgrade() -> None:
    if _column_exists("order_items", "bonus_quantity"):
        op.drop_column("order_items", "bonus_quantity")
