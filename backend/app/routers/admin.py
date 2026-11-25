from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user_models import User, Transaction
from app.models.monetization_models import PlanCatalog, Subscription, Invoice, CreditLedger, CreditUsage, AdminAuditLog
from app.auth.dependencies import get_current_active_user
from app.services.credit_service import CreditService
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
import uuid
import datetime

router = APIRouter(prefix="/admin", tags=["Admin Console"])


def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Administrator privileges required")
    return current_user


def log_admin_action(admin_user_id: int, action_type: str, target_resource: str, prev_val: str, new_val: str, reason: str, db: Session):
    req_id = f"aud_{uuid.uuid4().hex[:12]}"
    log = AdminAuditLog(
        admin_user_id=admin_user_id,
        action_type=action_type,
        target_resource=target_resource,
        previous_value=prev_val,
        new_value=new_val,
        reason=reason,
        request_id=req_id
    )
    db.add(log)
    db.commit()


class PlanUpdateRequest(BaseModel):
    price_pkr: Optional[Decimal] = None
    price_usd: Optional[Decimal] = None
    credits_monthly: Optional[int] = None
    is_active: Optional[bool] = None


class CreditAdjustmentRequest(BaseModel):
    amount: int = Field(..., description="Positive to grant, negative to deduct")
    reason: str = Field(..., min_length=3)
    reference_id: str = Field(..., min_length=2)


@router.get("/dashboard")
def admin_dashboard(admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    active_subs_count = db.query(Subscription).filter_by(status="active").count()
    sub_status_counts = dict(
        db.query(Subscription.status, func.count(Subscription.id)).group_by(Subscription.status).all()
    )

    # Revenue separated by PKR and USD
    revenue_pkr = db.query(func.sum(Invoice.amount)).filter(Invoice.currency == "pkr", Invoice.status == "paid").scalar() or Decimal("0.00")
    revenue_usd = db.query(func.sum(Invoice.amount)).filter(Invoice.currency == "usd", Invoice.status == "paid").scalar() or Decimal("0.00")

    successful_txns = db.query(Transaction).filter_by(status="completed").count()
    failed_txns = db.query(Transaction).filter_by(status="failed").count()

    provider_stats = dict(
        db.query(Transaction.payment_method, func.count(Transaction.id)).group_by(Transaction.payment_method).all()
    )

    total_credits_allocated = db.query(func.sum(CreditLedger.amount)).filter(CreditLedger.amount > 0).scalar() or 0
    total_credits_consumed = db.query(func.sum(CreditLedger.amount)).filter(CreditLedger.amount < 0).scalar() or 0

    return {
        "metrics": {
            "total_users": total_users,
            "active_subscriptions": active_subs_count,
            "subscription_statuses": sub_status_counts,
            "revenue_pkr": float(revenue_pkr),
            "revenue_usd": float(revenue_usd),
            "successful_transactions": successful_txns,
            "failed_transactions": failed_txns,
            "provider_stats": provider_stats,
            "total_credits_allocated": int(total_credits_allocated),
            "total_credits_consumed": int(total_credits_consumed),
        }
    }


@router.get("/plans")
def admin_list_plans(admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    plans = db.query(PlanCatalog).all()
    return {
        "plans": [{
            "id": p.id,
            "slug": p.slug,
            "name": p.name,
            "is_active": p.is_active,
            "price_pkr": float(p.price_pkr),
            "price_usd": float(p.price_usd),
            "credits_monthly": p.credits_monthly,
            "billing_interval": p.billing_interval
        } for p in plans]
    }


@router.put("/plans/{slug}")
def admin_update_plan(slug: str, req: PlanUpdateRequest, admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    plan = db.query(PlanCatalog).filter_by(slug=slug).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    prev_snapshot = f"PKR:{plan.price_pkr}, USD:{plan.price_usd}, Credits:{plan.credits_monthly}, Active:{plan.is_active}"

    if req.price_pkr is not None:
        if req.price_pkr < 0:
            raise HTTPException(status_code=400, detail="Price PKR cannot be negative")
        plan.price_pkr = req.price_pkr
    if req.price_usd is not None:
        if req.price_usd < 0:
            raise HTTPException(status_code=400, detail="Price USD cannot be negative")
        plan.price_usd = req.price_usd
    if req.credits_monthly is not None:
        if req.credits_monthly < 0:
            raise HTTPException(status_code=400, detail="Credits monthly cannot be negative")
        plan.credits_monthly = req.credits_monthly
    if req.is_active is not None:
        plan.is_active = req.is_active

    db.commit()
    db.refresh(plan)

    new_snapshot = f"PKR:{plan.price_pkr}, USD:{plan.price_usd}, Credits:{plan.credits_monthly}, Active:{plan.is_active}"
    log_admin_action(admin.id, "UPDATE_PLAN", f"plan:{slug}", prev_snapshot, new_snapshot, f"Updated plan catalog {slug}", db)

    return {"success": True, "message": f"Plan '{slug}' updated successfully", "plan": {"slug": plan.slug, "price_pkr": float(plan.price_pkr), "price_usd": float(plan.price_usd), "credits_monthly": plan.credits_monthly, "is_active": plan.is_active}}


@router.get("/users")
def admin_list_users(skip: int = 0, limit: int = 50, search: Optional[str] = None, admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    query = db.query(User)
    if search:
        query = query.filter(User.email.ilike(f"%{search}%") | User.username.ilike(f"%{search}%"))
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "users": [{
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "plan_type": u.plan_type,
            "credits": u.credits,
            "is_admin": u.is_admin,
            "created_at": u.created_at
        } for u in users]
    }


@router.get("/users/{user_id}/credits")
def admin_user_credits_history(user_id: int, admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    ledger_entries = db.query(CreditLedger).filter_by(user_id=user_id).order_by(CreditLedger.created_at.desc()).all()
    usages = db.query(CreditUsage).filter_by(user_id=user_id).order_by(CreditUsage.created_at.desc()).all()
    return {
        "user_id": user.id,
        "email": user.email,
        "credits": user.credits,
        "ledger": [{
            "id": le.id,
            "entry_type": le.entry_type,
            "amount": le.amount,
            "source": le.source,
            "idempotency_ref": le.idempotency_ref,
            "description": le.description,
            "created_at": le.created_at
        } for le in ledger_entries],
        "usages": [{
            "id": u.id,
            "operation_type": u.operation_type,
            "credit_cost": u.credit_cost,
            "status": u.status,
            "created_at": u.created_at
        } for u in usages]
    }


@router.post("/users/{user_id}/adjust-credits")
def admin_adjust_user_credits(user_id: int, req: CreditAdjustmentRequest, admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    target_user = db.query(User).filter_by(id=user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    old_credits = target_user.credits or 0
    ledger_entry = CreditService.admin_adjustment(target_user, admin, req.amount, req.reason, req.reference_id, db)
    new_credits = target_user.credits or 0

    log_admin_action(admin.id, "ADMIN_CREDIT_ADJUSTMENT", f"user:{user_id}", f"credits:{old_credits}", f"credits:{new_credits}", req.reason, db)

    return {
        "success": True,
        "message": f"Successfully adjusted credits by {req.amount}",
        "previous_credits": old_credits,
        "new_credits": new_credits,
        "ledger_entry_id": ledger_entry.id
    }


@router.get("/subscriptions")
def admin_list_subscriptions(status: Optional[str] = None, provider: Optional[str] = None, skip: int = 0, limit: int = 50, admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    query = db.query(Subscription)
    if status:
        query = query.filter_by(status=status)
    if provider:
        query = query.filter_by(provider=provider)
    total = query.count()
    subs = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "subscriptions": [{
            "id": s.id,
            "user_id": s.user_id,
            "plan_slug": s.plan_slug,
            "provider": s.provider,
            "status": s.status,
            "currency": s.currency,
            "current_period_start": s.current_period_start,
            "current_period_end": s.current_period_end,
            "created_at": s.created_at
        } for s in subs]
    }


@router.get("/payments")
def admin_list_payments(provider: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 50, admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    query = db.query(Transaction)
    if provider:
        query = query.filter_by(payment_method=provider)
    if status:
        query = query.filter_by(status=status)
    total = query.count()
    txns = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "payments": [{
            "id": t.id,
            "transaction_id": t.transaction_id,
            "user_id": t.user_id,
            "amount_pkr": float(t.amount_pkr),
            "amount_usd": float(t.amount_usd or 0),
            "credits_purchased": t.credits_purchased,
            "payment_method": t.payment_method,
            "status": t.status,
            "created_at": t.created_at
        } for t in txns]
    }


@router.get("/invoices")
def admin_list_invoices(skip: int = 0, limit: int = 50, admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    query = db.query(Invoice)
    total = query.count()
    invoices = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "invoices": [{
            "id": i.id,
            "invoice_number": i.invoice_number,
            "user_id": i.user_id,
            "amount": float(i.amount),
            "currency": i.currency,
            "status": i.status,
            "paid_at": i.paid_at,
            "created_at": i.created_at
        } for i in invoices]
    }


@router.get("/audit-logs")
def admin_list_audit_logs(skip: int = 0, limit: int = 50, admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    query = db.query(AdminAuditLog)
    total = query.count()
    logs = query.order_by(AdminAuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "audit_logs": [{
            "id": l.id,
            "admin_user_id": l.admin_user_id,
            "action_type": l.action_type,
            "target_resource": l.target_resource,
            "previous_value": l.previous_value,
            "new_value": l.new_value,
            "reason": l.reason,
            "request_id": l.request_id,
            "created_at": l.created_at
        } for l in logs]
    }
