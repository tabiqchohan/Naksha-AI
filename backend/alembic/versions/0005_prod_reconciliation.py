"""Production schema reconciliation: projects parity, orphan checks, financial numeric precision, and robust monetization table inspection.

Revision ID: 0005_prod_reconciliation
Revises: 0004_m3_subscription_rollover
Create Date: 2026-11-26
"""
from alembic import op
import sqlalchemy as sa


revision = "0005_prod_reconciliation"
down_revision = "0004_m3_subscription_rollover"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. Reconcile projects table (add missing ORM fields, preserve plan_data, verify/add user_id FK with orphan check)
    if "projects" in tables:
        proj_cols = {c["name"] for c in inspector.get_columns("projects")}
        with op.batch_alter_table("projects", schema=None) as batch_op:
            if "project_id" not in proj_cols:
                batch_op.add_column(sa.Column("project_id", sa.String(), nullable=True))
                batch_op.create_index("ix_projects_project_id", ["project_id"], unique=True)
            if "prompt" not in proj_cols:
                batch_op.add_column(sa.Column("prompt", sa.Text(), nullable=True))
            if "floor_plan_data" not in proj_cols:
                batch_op.add_column(sa.Column("floor_plan_data", sa.JSON(), nullable=True))
            if "thumbnail" not in proj_cols:
                batch_op.add_column(sa.Column("thumbnail", sa.Text(), nullable=True))
            if "is_favorite" not in proj_cols:
                batch_op.add_column(sa.Column("is_favorite", sa.Boolean(), server_default=sa.false(), nullable=False))

        # Verify existing foreign key on projects.user_id
        fks = inspector.get_foreign_keys("projects")
        user_id_fk_valid = False
        for fk in fks:
            if "user_id" in fk.get("constrained_columns", []):
                if fk.get("referred_table") == "users" and "id" in fk.get("referred_columns", []):
                    user_id_fk_valid = True
                else:
                    raise RuntimeError(
                        f"Incompatible foreign key on projects.user_id referencing '{fk.get('referred_table')}({fk.get('referred_columns')})'. "
                        "Expected reference to users.id. Manual intervention required."
                    )

        if not user_id_fk_valid:
            # Check for orphan records before adding FK constraint
            orphan_count = bind.execute(
                sa.text("SELECT count(*) FROM projects WHERE user_id IS NOT NULL AND user_id NOT IN (SELECT id FROM users);")
            ).scalar()
            if orphan_count > 0:
                raise RuntimeError(
                    f"Cannot add foreign key constraint on projects.user_id: found {orphan_count} orphan project record(s) "
                    "with no matching user in users table. Manual intervention required."
                )
            with op.batch_alter_table("projects", schema=None) as batch_op:
                batch_op.create_foreign_key("fk_projects_user_id", "users", ["user_id"], ["id"])

    # 2. Convert transactions financial columns to Numeric(12, 2) if float/double precision
    if "transactions" in tables:
        txn_cols = {c["name"]: c for c in inspector.get_columns("transactions")}
        with op.batch_alter_table("transactions", schema=None) as batch_op:
            if "amount_pkr" in txn_cols and isinstance(txn_cols["amount_pkr"]["type"], (sa.Float, sa.DOUBLE_PRECISION)):
                batch_op.alter_column("amount_pkr", existing_type=sa.Float(), type_=sa.Numeric(12, 2), existing_nullable=False)
            if "amount_usd" in txn_cols and isinstance(txn_cols["amount_usd"]["type"], (sa.Float, sa.DOUBLE_PRECISION)):
                batch_op.alter_column("amount_usd", existing_type=sa.Float(), type_=sa.Numeric(12, 2), existing_nullable=True, server_default="0.0")

    # 3. Monetization & Audit Tables: Inspection and Safe Reconciliation
    expected_tables = {
        "plan_catalog": [
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("slug", sa.String(), unique=True, index=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column("price_pkr", sa.Numeric(12, 2), nullable=False, server_default="0.0"),
            sa.Column("price_usd", sa.Numeric(12, 2), nullable=False, server_default="0.0"),
            sa.Column("billing_interval", sa.String(), server_default="monthly", nullable=False),
            sa.Column("credits_monthly", sa.Integer(), server_default="0", nullable=False),
            sa.Column("features", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        ],
        "subscriptions": [
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True, nullable=False),
            sa.Column("plan_slug", sa.String(), sa.ForeignKey("plan_catalog.slug"), index=True, nullable=False),
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
            sa.Column("billing_cycle_key", sa.String(), index=True, nullable=True),
            sa.Column("rollover_balance", sa.Integer(), server_default="0", nullable=False),
            sa.Column("rollover_expiry", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_allocated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        ],
        "invoices": [
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True, nullable=False),
            sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), index=True, nullable=True),
            sa.Column("invoice_number", sa.String(), unique=True, index=True, nullable=False),
            sa.Column("provider_invoice_id", sa.String(), unique=True, index=True, nullable=True),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("currency", sa.String(), server_default="pkr", nullable=False),
            sa.Column("tax_amount", sa.Numeric(12, 2), server_default="0.0", nullable=False),
            sa.Column("fee_amount", sa.Numeric(12, 2), server_default="0.0", nullable=False),
            sa.Column("status", sa.String(), server_default="draft", nullable=False),
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        ],
        "credit_ledger": [
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
        ],
        "credit_usages": [
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
        ],
        "admin_audit_logs": [
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("admin_user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True, nullable=False),
            sa.Column("action_type", sa.String(), nullable=False),
            sa.Column("target_resource", sa.String(), nullable=True),
            sa.Column("previous_value", sa.String(), nullable=True),
            sa.Column("new_value", sa.String(), nullable=True),
            sa.Column("reason", sa.String(), nullable=False),
            sa.Column("request_id", sa.String(), unique=True, index=True, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        ],
    }

    for t_name, cols in expected_tables.items():
        if t_name not in tables:
            op.create_table(t_name, *cols)
        else:
            existing_cols = {c["name"]: c for c in inspector.get_columns(t_name)}
            with op.batch_alter_table(t_name, schema=None) as batch_op:
                for col in cols:
                    if col.name not in existing_cols:
                        batch_op.add_column(col)
                    else:
                        ex_type = str(existing_cols[col.name]["type"]).lower()
                        expected_type = str(col.type).lower()
                        if "int" in expected_type and "int" not in ex_type and "numeric" not in ex_type:
                            raise RuntimeError(
                                f"Incompatible existing column type for {t_name}.{col.name}: found {ex_type}, expected {expected_type}. "
                                "Manual intervention required."
                            )


def downgrade() -> None:
    pass
