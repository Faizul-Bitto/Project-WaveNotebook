"""add spend-based discount tables

Revision ID: 2026_add_spend_based_discount
Revises: 2026_add_order_item_bonus
Create Date: 2026-08-17 02:20:29.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '2026_add_spend_based_discount'
down_revision = '2026_add_order_item_bonus'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'spend_based_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('discount_id', sa.Integer(), nullable=False),
        sa.Column('scope_type', sa.String(20), nullable=False, server_default='storewide'),
        sa.Column('scope_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['discount_id'], ['discounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_spend_based_rules_id', 'spend_based_rules', ['id'], unique=False)
    op.create_index('ix_spend_based_rules_discount_id', 'spend_based_rules', ['discount_id'], unique=False)
    op.create_index('ix_spend_based_rules_scope_id', 'spend_based_rules', ['scope_id'], unique=False)

    op.create_table(
        'spend_based_slabs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('spend_based_rule_id', sa.Integer(), nullable=False),
        sa.Column('min_spend_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('value_type', sa.String(20), nullable=False),
        sa.Column('value', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['spend_based_rule_id'], ['spend_based_rules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_spend_based_slabs_id', 'spend_based_slabs', ['id'], unique=False)
    op.create_index('ix_spend_based_slabs_rule_id', 'spend_based_slabs', ['spend_based_rule_id'], unique=False)


def downgrade():
    op.drop_table('spend_based_slabs')
    op.drop_table('spend_based_rules')
