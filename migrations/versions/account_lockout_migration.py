"""Add failed_login_attempts and locked_until to users table.

Adds per-account brute-force protection fields without requiring a separate table.
- failed_login_attempts: increments on each bad password attempt; resets on success.
- locked_until: UTC timestamp; login is rejected if this is in the future.
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_account_lockout'
down_revision = 'add_cost_price_order_items'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns as nullable first so existing rows aren't broken
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))

    # Backfill existing rows (they have 0 failed attempts, not locked)
    op.execute("UPDATE users SET failed_login_attempts = 0 WHERE failed_login_attempts IS NULL")


def downgrade():
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
