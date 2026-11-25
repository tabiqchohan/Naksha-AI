"""Monetization M1 Database Foundation: Plan catalog, subscriptions, invoices, credit ledger, credit usages.

Revision ID: 0002_monetization_m1
Revises: 0001_bootstrap
Create Date: 2026-11-18
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_monetization_m1"
down_revision = "0001_bootstrap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. plan_catalog table
    op.create_table(
        "plan_catalog",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("slug", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("price_pkr", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("price_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("billing_interval", sa.String(), server_default="monthly", nullable=False),
        sa.Column("credits_monthly", sa.Integer(), server_default="0", nullable=False),
        sa.Column("features", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True, nullable=False),
        sa.Column("plan_slug", sa.String(), index=True, nullable=False),
        sa.Column("provider", sa.String(), server_default="stripe", nullable=False),
        sa.Column("provider_customer_id", sa.String(), nullable=True),
        sa.Column("provider_subscription_id", sa.String(), unique=True, index=True, nullable=True),
        sa.Column("currency", sa.String(), server_default="pkr", nullable=False),
        sa.Column("billing_interval", sa.String(), server_default="monthly", nullable=False),
        sa.Column("status", sa.String(), server_default="pending", nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 3. invoices table
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True, nullable=False),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), index=True, nullable=True),
        sa.Column("invoice_number", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("provider_invoice_id", sa.String(), unique=True, index=True, nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), server_default="pkr", nullable=False),
        sa.Column("tax_amount", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("fee_amount", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("status", sa.String(), server_default="draft", nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 4. credit_ledger table
    op.create_table(
        "credit_ledger",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True, nullable=False),
        sa.Column("entry_type", sa.String(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("idempotency_ref", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("transactions.id"), nullable=True),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )

    # 5. credit_usages table
    op.create_table(
        "credit_usages",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True, nullable=False),
        sa.Column("operation_type", sa.String(), nullable=False),
        sa.Column("credit_cost", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), server_default="pending", nullable=False),
        sa.Column("idempotency_key", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("model_metadata", sa.String(), nullable=True),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("credit_usages")
    op.drop_table("credit_ledger")
    op.drop_table("invoices")
    op.drop_table("subscriptions")
    op.drop_table("plan_catalog")
