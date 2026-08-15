"""Add is_featured column to products table

Revision ID: 2026_add_product_featured
Revises: 2025_add_order_snapshots
Create Date: 2026-08-15 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_add_product_featured'
down_revision = '2025_add_order_snapshots'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('products', sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('products', 'is_featured')
