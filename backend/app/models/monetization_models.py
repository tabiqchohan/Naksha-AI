from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Index, Numeric, event
from sqlalchemy.orm import relationship, backref as sa_backref
from sqlalchemy.sql import func
from app.database import Base


class PlanCatalog(Base):
    __tablename__ = "plan_catalog"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)  # free, starter, pro, architect, studio
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    price_pkr = Column(Numeric(12, 2), nullable=False, default=0.0)
    price_usd = Column(Numeric(12, 2), nullable=False, default=0.0)
    billing_interval = Column(String, default="monthly")  # monthly, annual
    credits_monthly = Column(Integer, default=0)
    features = Column(String, nullable=True)  # JSON or comma-separated feature flags
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    plan_slug = Column(String, ForeignKey("plan_catalog.slug"), index=True, nullable=False)
    provider = Column(String, default="stripe")  # stripe, jazzcash, easypaisa, dev
    provider_customer_id = Column(String, nullable=True)
    provider_subscription_id = Column(String, unique=True, index=True, nullable=True)
    currency = Column(String, default="pkr")  # pkr, usd
    billing_interval = Column(String, default="monthly")  # monthly, annual
    status = Column(String, default="pending")  # pending, active, past_due, canceled, expired
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    billing_cycle_key = Column(String, index=True, nullable=True)
    rollover_balance = Column(Integer, default=0, nullable=False)
    rollover_expiry = Column(DateTime(timezone=True), nullable=True)
    last_allocated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="subscriptions")
    plan = relationship("PlanCatalog", backref="subscriptions")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), index=True, nullable=True)
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    provider_invoice_id = Column(String, unique=True, index=True, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="pkr")
    tax_amount = Column(Numeric(12, 2), default=0.0, nullable=False)
    fee_amount = Column(Numeric(12, 2), default=0.0, nullable=False)
    status = Column(String, default="draft")  # draft, open, paid, void, uncollectible
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="invoices")
    subscription = relationship("Subscription", backref="invoices")


class CreditLedger(Base):
    __tablename__ = "credit_ledger"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    entry_type = Column(String, nullable=False)  # grant, monthly_allocation, rollover, rollover_expiration, purchase, reservation, consumption, release, refund, admin_adjustment, expiration
    amount = Column(Integer, nullable=False)  # positive for additions/allocations/purchases/refunds, negative for reservations/consumptions/expirations
    source = Column(String, nullable=False)  # ai_generation, monthly_reset, admin, purchase, etc.
    idempotency_ref = Column(String, unique=True, index=True, nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    description = Column(String, nullable=True)
    metadata_json = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="credit_ledger_entries")
    transaction = relationship("Transaction", backref="credit_ledger_entries")
    subscription = relationship("Subscription", backref="credit_ledger_entries")


@event.listens_for(CreditLedger, "before_update")
def prevent_credit_ledger_update(mapper, connection, target):
    raise RuntimeError("CreditLedger entries are strictly immutable. Use compensating entries for corrections.")


@event.listens_for(CreditLedger, "before_delete")
def prevent_credit_ledger_delete(mapper, connection, target):
    raise RuntimeError("CreditLedger entries are strictly immutable and cannot be deleted.")


class CreditUsage(Base):
    __tablename__ = "credit_usages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    operation_type = Column(String, nullable=False)  # ai_consultation, plan_generation, plan_revision, design_improvement, plan_repair
    credit_cost = Column(Integer, nullable=False)
    status = Column(String, default="pending")  # pending, reserved, completed, released, failed
    idempotency_key = Column(String, unique=True, index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    model_metadata = Column(String, nullable=True)
    failure_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="credit_usages")
    project = relationship("Project", backref=sa_backref("credit_usages", lazy="noload"))


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    action_type = Column(String, nullable=False)
    target_resource = Column(String, nullable=True)
    previous_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    reason = Column(String, nullable=False)
    request_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin_user = relationship("User", backref="admin_audit_logs")


@event.listens_for(AdminAuditLog, "before_update")
def prevent_admin_audit_log_update(mapper, connection, target):
    raise RuntimeError("Admin audit logs are strictly immutable.")


@event.listens_for(AdminAuditLog, "before_delete")
def prevent_admin_audit_log_delete(mapper, connection, target):
    raise RuntimeError("Admin audit logs are strictly immutable and cannot be deleted.")
