"""Add cost_price to order_items

Revision ID: add_cost_price_order_items
Revises: fe17f9484e10
Create Date: 2026-09-05 10:50:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_cost_price_order_items'
down_revision = 'fe17f9484e10'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('order_items', sa.Column('cost_price', sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('order_items', 'cost_price')
