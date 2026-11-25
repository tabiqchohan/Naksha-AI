from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user_models import User, plan_value
from app.models.monetization_models import Subscription, PlanCatalog, CreditLedger
from app.services.credit_service import CreditService
from datetime import datetime, timedelta, timezone
import calendar
import uuid


ROLLOVER_CAPS = {
    "free": 0.0,
    "starter": 0.5,
    "pro": 1.0,
    "architect": 1.0,
    "studio": 1.0,
}


def add_months(dt: datetime, months: int) -> datetime:
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


class SubscriptionService:
    @staticmethod
    def get_rollover_cap(plan_slug: str) -> float:
        return ROLLOVER_CAPS.get(plan_slug, 0.0)

    @staticmethod
    def create_subscription(user: User, plan_slug: str, provider: str = "dev", db: Session = Depends(get_db) if False else None) -> Subscription:
        # Check plan catalog
        plan = db.query(PlanCatalog).filter_by(slug=plan_slug).first()
        if not plan:
            raise HTTPException(status_code=400, detail=f"Invalid plan slug: {plan_slug}")

        # Check existing active/pending subscription
        existing = db.query(Subscription).filter_by(user_id=user.id, status="active").first()
        if existing:
            if existing.plan_slug == plan_slug:
                return existing
            # If changing plans, we transition or update
            existing.status = "canceled"
            existing.canceled_at = datetime.now(timezone.utc)

        now = datetime.now(timezone.utc)
        period_end = add_months(now, 1)
        cycle_key = f"{plan_slug}_{now.strftime('%Y-%m')}"

        sub = Subscription(
            user_id=user.id,
            plan_slug=plan_slug,
            provider=provider,
            status="pending",
            currency="pkr",
            billing_interval="monthly",
            current_period_start=now,
            current_period_end=period_end,
            billing_cycle_key=cycle_key,
            rollover_balance=0,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def activate_subscription(subscription_id: int, db: Session) -> Subscription:
        sub = db.query(Subscription).filter_by(id=subscription_id).first()
        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found")
        if sub.status == "active":
            return sub
        if sub.status in ["canceled", "expired"]:
            raise HTTPException(status_code=400, detail=f"Cannot activate subscription in status '{sub.status}'")

        sub.status = "active"
        sub.current_period_start = datetime.now(timezone.utc)
        sub.current_period_end = add_months(sub.current_period_start, 1)
        sub.billing_cycle_key = f"{sub.plan_slug}_{sub.current_period_start.strftime('%Y-%m')}"
        db.commit()
        db.refresh(sub)

        # Trigger initial allocation
        SubscriptionService.process_billing_cycle(sub, db)
        return sub

    @staticmethod
    def process_billing_cycle(subscription: Subscription, db: Session):
        if subscription.status != "active":
            return False

        user = db.query(User).filter_by(id=subscription.user_id).first()
        plan = db.query(PlanCatalog).filter_by(slug=subscription.plan_slug).first()
        if not user or not plan:
            return False

        cycle_key = subscription.billing_cycle_key or f"{subscription.plan_slug}_{datetime.now(timezone.utc).strftime('%Y-%m')}"

        # Check if already allocated for this cycle
        allocated_ref = f"alloc_{user.id}_{cycle_key}"
        existing_alloc = db.query(CreditLedger).filter_by(idempotency_ref=allocated_ref).first()
        if existing_alloc:
            return False  # Already processed for this cycle

        # 1. Handle previous rollover expiry if any
        if subscription.rollover_expiry and datetime.now(timezone.utc) >= subscription.rollover_expiry and subscription.rollover_balance > 0:
            exp_ref = f"exp_roll_{user.id}_{subscription.id}_{cycle_key}"
            existing_exp = db.query(CreditLedger).filter_by(idempotency_ref=exp_ref).first()
            if not existing_exp and subscription.rollover_balance > 0:
                amt_to_expire = subscription.rollover_balance
                exp_entry = CreditLedger(
                    user_id=user.id,
                    entry_type="rollover_expiration",
                    amount=-amt_to_expire,
                    source=f"rollover_expiry_{subscription.plan_slug}",
                    idempotency_ref=exp_ref,
                    subscription_id=subscription.id,
                    description=f"Rollover credits expired for cycle {cycle_key}"
                )
                db.add(exp_entry)
                user.credits = max(0, (user.credits or 0) - amt_to_expire)
                subscription.rollover_balance = 0
                subscription.rollover_expiry = None

        # 2. Calculate rollover from previous cycle if applicable
        # (For simplicity in monthly renewal: if user had credits remaining, calculate rollover cap)
        cap_pct = SubscriptionService.get_rollover_cap(subscription.plan_slug)
        if cap_pct > 0 and plan.credits_monthly > 0:
            # Eligible unused credits estimation or explicit tracking
            current_credits = user.credits or 0
            max_rollover = int(plan.credits_monthly * cap_pct)
            # Suppose we rollover portion of current balance up to cap
            rollover_amt = min(current_credits, max_rollover)
            if rollover_amt > 0:
                roll_ref = f"roll_{user.id}_{cycle_key}"
                existing_roll = db.query(CreditLedger).filter_by(idempotency_ref=roll_ref).first()
                if not existing_roll:
                    roll_entry = CreditLedger(
                        user_id=user.id,
                        entry_type="rollover",
                        amount=rollover_amt,
                        source=f"rollover_{subscription.plan_slug}",
                        idempotency_ref=roll_ref,
                        subscription_id=subscription.id,
                        description=f"Rollover allocation for {subscription.plan_slug}"
                    )
                    db.add(roll_entry)
                    subscription.rollover_balance = rollover_amt
                    subscription.rollover_expiry = add_months(datetime.now(timezone.utc), 1)

        # 3. Allocate current monthly credits
        CreditService.allocate_monthly_credits(user, subscription.plan_slug, cycle_key, db)
        subscription.last_allocated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(subscription)
        return True

    @staticmethod
    def change_plan(user: User, new_plan_slug: str, db: Session) -> Subscription:
        new_plan = db.query(PlanCatalog).filter_by(slug=new_plan_slug).first()
        if not new_plan:
            raise HTTPException(status_code=400, detail=f"Plan {new_plan_slug} not found")

        active_sub = db.query(Subscription).filter_by(user_id=user.id, status="active").first()
        if active_sub:
            if active_sub.plan_slug == new_plan_slug:
                return active_sub
            active_sub.status = "canceled"
            active_sub.canceled_at = datetime.now(timezone.utc)

        now = datetime.now(timezone.utc)
        period_end = add_months(now, 1)
        cycle_key = f"{new_plan_slug}_{now.strftime('%Y-%m')}"

        new_sub = Subscription(
            user_id=user.id,
            plan_slug=new_plan_slug,
            provider="dev",
            status="active",
            currency="pkr",
            billing_interval="monthly",
            current_period_start=now,
            current_period_end=period_end,
            billing_cycle_key=cycle_key,
            rollover_balance=0,
        )
        db.add(new_sub)
        db.commit()
        db.refresh(new_sub)

        # Process immediate cycle allocation for new plan (idempotent)
        SubscriptionService.process_billing_cycle(new_sub, db)
        user.plan_type = new_plan_slug if new_plan_slug in ["free", "pro", "enterprise"] else "pro"
        db.commit()
        return new_sub

    @staticmethod
    def cancel_subscription(user: User, db: Session) -> Subscription:
        sub = db.query(Subscription).filter_by(user_id=user.id, status="active").first()
        if not sub:
            raise HTTPException(status_code=404, detail="No active subscription found")
        sub.status = "canceled"
        sub.canceled_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(sub)
        return sub
