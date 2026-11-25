from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.user_models import User, plan_value
from app.models.monetization_models import CreditLedger, CreditUsage, PlanCatalog
import json
import hashlib
import uuid


OPERATION_COSTS = {
    "ai_consultation": 2,
    "plan_generation": 8,
    "plan_revision": 3,
    "design_improvement": 2,
    "plan_repair": 4,
    "boq_calculation": 0,
    "pdf_dxf_export": 0,
    "client_3d_view": 0,
    "geometry_validation": 0,
    "project_crud": 0,
    "supplier_browse": 0,
}


class CreditService:
    @staticmethod
    def get_operation_cost(operation_type: str) -> int:
        return OPERATION_COSTS.get(operation_type, 8)  # default to 8 for plan generation

    @staticmethod
    def get_available_credits(user: User, db: Session) -> int:
        return user.credits or 0

    @staticmethod
    def reserve_credits(user: User, operation_type: str, idempotency_key: str, db: Session, project_id: int = None, payload: dict = None) -> CreditUsage:
        cost = CreditService.get_operation_cost(operation_type)

        # Deterministic payload normalization and fingerprinting
        canonical_payload = json.dumps(payload or {}, sort_keys=True)
        payload_signature = hashlib.sha256(f"{user.id}:{operation_type}:{cost}:{canonical_payload}".encode()).hexdigest()

        # Check existing idempotency key in usage records
        existing_usage = db.query(CreditUsage).filter_by(idempotency_key=idempotency_key).first()
        if existing_usage:
            if existing_usage.user_id != user.id:
                raise HTTPException(status_code=400, detail="Idempotency key mismatch for user")
            # Verify payload fingerprint / signature conflict
            if existing_usage.model_metadata and existing_usage.model_metadata != payload_signature:
                raise HTTPException(status_code=400, detail="Idempotency key reuse with conflicting payload or parameters")
            if existing_usage.credit_cost != cost or existing_usage.operation_type != operation_type:
                raise HTTPException(status_code=400, detail="Idempotency key reuse with conflicting operation or cost")
            return existing_usage

        # Row-level locking on user row for PostgreSQL concurrency safety (`with_for_update`)
        locked_user = db.query(User).filter_by(id=user.id).with_for_update().first()
        if not locked_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check available balance
        available = locked_user.credits or 0
        if plan_value(locked_user.plan_type) not in ["pro", "enterprise"] and available < cost:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient credits. Required: {cost}, Available: {available}. Please purchase more credits or upgrade."
            )

        # Create CreditUsage (status='reserved')
        usage = CreditUsage(
            user_id=locked_user.id,
            operation_type=operation_type,
            credit_cost=cost,
            status="reserved",
            idempotency_key=idempotency_key,
            project_id=project_id,
            model_metadata=payload_signature,
        )
        db.add(usage)

        # If cost > 0, deduct via CreditLedger reservation entry
        if cost > 0:
            ledger_ref = f"res_{idempotency_key}"
            existing_ledger = db.query(CreditLedger).filter_by(idempotency_ref=ledger_ref).first()
            if not existing_ledger:
                ledger_entry = CreditLedger(
                    user_id=locked_user.id,
                    entry_type="reservation",
                    amount=-cost,
                    source=operation_type,
                    idempotency_ref=ledger_ref,
                    description=f"Reservation for {operation_type}"
                )
                db.add(ledger_entry)
                locked_user.credits = max(0, (locked_user.credits or 0) - cost)

        try:
            db.commit()
            db.refresh(usage)
            return usage
        except IntegrityError:
            db.rollback()
            existing_usage = db.query(CreditUsage).filter_by(idempotency_key=idempotency_key).first()
            if existing_usage:
                if not existing_usage.model_metadata or existing_usage.model_metadata == payload_signature:
                    return existing_usage
                raise HTTPException(status_code=400, detail="Idempotency key reuse with conflicting payload or parameters")
            raise HTTPException(status_code=400, detail="Concurrent idempotency conflict")

    @staticmethod
    def commit_usage(idempotency_key: str, db: Session):
        usage = db.query(CreditUsage).filter_by(idempotency_key=idempotency_key).first()
        if usage and usage.status == "reserved":
            usage.status = "completed"
            db.commit()

    @staticmethod
    def release_reservation(idempotency_key: str, reason: str, db: Session):
        usage = db.query(CreditUsage).filter_by(idempotency_key=idempotency_key).first()
        if usage and usage.status == "reserved":
            usage.status = "released"
            usage.failure_reason = reason
            cost = usage.credit_cost
            if cost > 0:
                refund_ref = f"rel_{idempotency_key}"
                existing_ledger = db.query(CreditLedger).filter_by(idempotency_ref=refund_ref).first()
                if not existing_ledger:
                    user = db.query(User).filter_by(id=usage.user_id).first()
                    refund_entry = CreditLedger(
                        user_id=usage.user_id,
                        entry_type="refund",
                        amount=cost,
                        source=f"{usage.operation_type}_refund",
                        idempotency_ref=refund_ref,
                        description=f"Refund for failed {usage.operation_type}: {reason}"
                    )
                    db.add(refund_entry)
                    if user:
                        user.credits = (user.credits or 0) + cost
            db.commit()

    @staticmethod
    def grant_purchase(user: User, transaction_id_str: str, credits_amount: int, db: Session):
        ledger_ref = f"txn_{transaction_id_str}"
        existing_ledger = db.query(CreditLedger).filter_by(idempotency_ref=ledger_ref).first()
        if existing_ledger:
            return False  # Already granted (idempotent safeguard)

        ledger_entry = CreditLedger(
            user_id=user.id,
            entry_type="purchase",
            amount=credits_amount,
            source="credit_pack_purchase",
            idempotency_ref=ledger_ref,
            description=f"Purchased {credits_amount} credits via transaction {transaction_id_str}"
        )
        db.add(ledger_entry)
        user.credits = (user.credits or 0) + credits_amount
        db.commit()
        db.refresh(user)
        return True

    @staticmethod
    def allocate_monthly_credits(user: User, plan_slug: str, billing_cycle_key: str, db: Session):
        plan = db.query(PlanCatalog).filter_by(slug=plan_slug).first()
        if not plan or plan.credits_monthly <= 0:
            return False

        ledger_ref = f"alloc_{user.id}_{billing_cycle_key}"
        existing_ledger = db.query(CreditLedger).filter_by(idempotency_ref=ledger_ref).first()
        if existing_ledger:
            return False  # Already allocated for this cycle

        ledger_entry = CreditLedger(
            user_id=user.id,
            entry_type="monthly_allocation",
            amount=plan.credits_monthly,
            source=f"subscription_{plan_slug}",
            idempotency_ref=ledger_ref,
            description=f"Monthly credit allocation for {plan_slug} plan (Cycle: {billing_cycle_key})"
        )
        db.add(ledger_entry)
        user.credits = (user.credits or 0) + plan.credits_monthly
        db.commit()
        db.refresh(user)
        return True

    @staticmethod
    def admin_adjustment(user: User, admin_user: User, amount: int, reason: str, ref_id: str, db: Session):
        ledger_ref = f"admin_adj_{ref_id}"
        existing_ledger = db.query(CreditLedger).filter_by(idempotency_ref=ledger_ref).first()
        if existing_ledger:
            raise HTTPException(status_code=400, detail="Idempotency reference already used for admin adjustment")

        new_balance = (user.credits or 0) + amount
        if new_balance < 0:
            raise HTTPException(status_code=400, detail=f"Adjustment would result in negative balance ({new_balance}).")

        ledger_entry = CreditLedger(
            user_id=user.id,
            entry_type="admin_adjustment",
            amount=amount,
            source=f"admin_{admin_user.id}",
            idempotency_ref=ledger_ref,
            description=f"Admin adjustment by admin #{admin_user.id}: {reason}"
        )
        db.add(ledger_entry)
        user.credits = new_balance
        db.commit()
        db.refresh(user)
        return ledger_entry
