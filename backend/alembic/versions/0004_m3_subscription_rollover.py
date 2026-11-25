"""M3 Subscription Lifecycle & Rollover Engine additions

Revision ID: 0004_m3_subscription_rollover
Revises: 0003_monetization_remediation
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa


revision = "0004_m3_subscription_rollover"
down_revision = "0003_monetization_remediation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("billing_cycle_key", sa.String(), nullable=True))
    op.add_column("subscriptions", sa.Column("rollover_balance", sa.Integer(), server_default="0", nullable=False))
    op.add_column("subscriptions", sa.Column("rollover_expiry", sa.DateTime(timezone=True), nullable=True))
    op.add_column("subscriptions", sa.Column("last_allocated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_subscriptions_billing_cycle_key"), "subscriptions", ["billing_cycle_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_subscriptions_billing_cycle_key"), table_name="subscriptions")
    op.drop_column("subscriptions", "last_allocated_at")
    op.drop_column("subscriptions", "rollover_expiry")
    op.drop_column("subscriptions", "rollover_balance")
    op.drop_column("subscriptions", "billing_cycle_key")
