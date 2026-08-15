"""Add email column to orders table

Revision ID: 2026_add_order_email
Revises: 2026_add_product_featured
Create Date: 2026-08-15 21:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_add_order_email'
down_revision = '2026_add_product_featured'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('email', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'email')
