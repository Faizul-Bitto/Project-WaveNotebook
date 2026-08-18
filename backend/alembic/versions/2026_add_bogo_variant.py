"""Add selected_attributes to bogo_rules for variant-specific BOGO rules

Revision ID: 2026_add_bogo_variant
Revises: 2026_add_adjustment_value_type
Create Date: 2026-08-18 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '2026_add_bogo_variant'
down_revision = '2026_add_adjustment_value_type'
branch_labels = None
depends_on = None


def _column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in existing


def upgrade() -> None:
    if not _column_exists("bogo_rules", "selected_attributes"):
        op.add_column(
            "bogo_rules",
            sa.Column("selected_attributes", sa.Text, nullable=True),
        )


def downgrade() -> None:
    if _column_exists("bogo_rules", "selected_attributes"):
        op.drop_column("bogo_rules", "selected_attributes")
