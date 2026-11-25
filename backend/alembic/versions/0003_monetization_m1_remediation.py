"""Monetization M1 Remediation: Add financial precision (Numeric), plan_slug foreign key constraint.

Revision ID: 0003_monetization_remediation
Revises: 0002_monetization_m1
Create Date: 2026-11-18
"""
from alembic import op
import sqlalchemy as sa


revision = "0003_monetization_remediation"
down_revision = "0002_monetization_m1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Update Float columns to Numeric(12, 2)
    with op.batch_alter_table("plan_catalog", schema=None) as batch_op:
        batch_op.alter_column("price_pkr", existing_type=sa.Float(), type_=sa.Numeric(12, 2), existing_nullable=False, server_default="0.0")
        batch_op.alter_column("price_usd", existing_type=sa.Float(), type_=sa.Numeric(12, 2), existing_nullable=False, server_default="0.0")

    with op.batch_alter_table("invoices", schema=None) as batch_op:
        batch_op.alter_column("amount", existing_type=sa.Float(), type_=sa.Numeric(12, 2), existing_nullable=False)
        batch_op.alter_column("tax_amount", existing_type=sa.Float(), type_=sa.Numeric(12, 2), existing_nullable=False, server_default="0.0")
        batch_op.alter_column("fee_amount", existing_type=sa.Float(), type_=sa.Numeric(12, 2), existing_nullable=False, server_default="0.0")

    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.alter_column("amount_pkr", existing_type=sa.Float(), type_=sa.Numeric(12, 2), existing_nullable=False)
        batch_op.alter_column("amount_usd", existing_type=sa.Float(), type_=sa.Numeric(12, 2), existing_nullable=True, server_default="0.0")

    # 2. Add foreign key from subscriptions.plan_slug to plan_catalog.slug
    with op.batch_alter_table("subscriptions", schema=None) as batch_op:
        batch_op.create_foreign_key("fk_subscriptions_plan_slug_plan_catalog", "plan_catalog", ["plan_slug"], ["slug"])


def downgrade() -> None:
    with op.batch_alter_table("subscriptions", schema=None) as batch_op:
        batch_op.drop_constraint("fk_subscriptions_plan_slug_plan_catalog", type_="foreignkey")

    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.alter_column("amount_usd", existing_type=sa.Numeric(12, 2), type_=sa.Float(), existing_nullable=True)
        batch_op.alter_column("amount_pkr", existing_type=sa.Numeric(12, 2), type_=sa.Float(), existing_nullable=False)

    with op.batch_alter_table("invoices", schema=None) as batch_op:
        batch_op.alter_column("fee_amount", existing_type=sa.Numeric(12, 2), type_=sa.Float(), existing_nullable=False)
        batch_op.alter_column("tax_amount", existing_type=sa.Numeric(12, 2), type_=sa.Float(), existing_nullable=False)
        batch_op.alter_column("amount", existing_type=sa.Numeric(12, 2), type_=sa.Float(), existing_nullable=False)

    with op.batch_alter_table("plan_catalog", schema=None) as batch_op:
        batch_op.alter_column("price_usd", existing_type=sa.Numeric(12, 2), type_=sa.Float(), existing_nullable=False)
        batch_op.alter_column("price_pkr", existing_type=sa.Numeric(12, 2), type_=sa.Float(), existing_nullable=False)
