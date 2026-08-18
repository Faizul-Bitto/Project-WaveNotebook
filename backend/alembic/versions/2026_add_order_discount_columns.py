"""Add discount tracking columns to orders and order_items

Revision ID: 2026_add_order_discount_columns
Revises: 2026_add_discount_system
Create Date: 2026-08-16 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '2026_add_order_discount_columns'
down_revision = '2026_add_discount_system'
branch_labels = None
depends_on = None


def _column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in existing


def _is_nullable(table_name, column_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    for c in inspector.get_columns(table_name):
        if c["name"] == column_name:
            return c["nullable"]
    return None


def upgrade() -> None:
    if not _column_exists("orders", "total_discount"):
        op.add_column(
            "orders",
            sa.Column("total_discount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        )

    if not _column_exists("orders", "discount_snapshot"):
        # MySQL does not allow a DEFAULT on TEXT columns, so add it nullable,
        # backfill existing rows, then enforce NOT NULL
        op.add_column(
            "orders",
            sa.Column("discount_snapshot", sa.Text, nullable=True),
        )
        op.execute("UPDATE orders SET discount_snapshot = '{}' WHERE discount_snapshot IS NULL")
    # Ensure NOT NULL even if a previous partial run left it nullable
    if _is_nullable("orders", "discount_snapshot"):
        op.alter_column("orders", "discount_snapshot", nullable=False, existing_type=sa.Text)

    if not _column_exists("order_items", "discount_amount"):
        op.add_column(
            "order_items",
            sa.Column("discount_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    if _column_exists("order_items", "discount_amount"):
        op.drop_column("order_items", "discount_amount")
    if _column_exists("orders", "discount_snapshot"):
        op.drop_column("orders", "discount_snapshot")
    if _column_exists("orders", "total_discount"):
        op.drop_column("orders", "total_discount")
