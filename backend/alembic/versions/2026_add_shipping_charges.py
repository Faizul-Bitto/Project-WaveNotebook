"""add shipping charges table

Revision ID: 2026_add_shipping_charges
Revises: 2026_add_discount_free_shipping
Create Date: 2026-08-17 23:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '2026_add_shipping_charges'
down_revision = '2026_add_discount_free_shipping'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'shipping_charges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('zone_name', sa.String(255), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_shipping_charges_id', 'shipping_charges', ['id'], unique=False)
    op.create_index('ix_shipping_charges_zone_name', 'shipping_charges', ['zone_name'], unique=False)


def downgrade():
    op.drop_index('ix_shipping_charges_zone_name', table_name='shipping_charges')
    op.drop_index('ix_shipping_charges_id', table_name='shipping_charges')
    op.drop_table('shipping_charges')
