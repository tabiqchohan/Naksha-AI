from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.user_models import User, Transaction, plan_value
from app.models.monetization_models import Subscription, Invoice, CreditLedger
from app.models.auth_schemas import PurchaseCredits, PaymentResponse
from app.auth.dependencies import get_current_active_user
from app.services.subscription_service import SubscriptionService
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid
import os
import hmac
import hashlib
import json
from urllib.parse import parse_qs

router = APIRouter(prefix="/payments", tags=["Payments"])

CREDIT_PACKS = {
    10: {"pkr": 500, "usd": 1.8, "name": "10 Credits"},
    25: {"pkr": 1000, "usd": 3.6, "name": "25 Credits"},
    50: {"pkr": 1800, "usd": 6.5, "name": "50 Credits"},
    100: {"pkr": 3000, "usd": 10.8, "name": "100 Credits"},
}


class SubscriptionCheckoutRequest(BaseModel):
    plan_slug: str


def _parse_webhook_payload(raw: bytes) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        form = parse_qs(raw.decode("utf-8", errors="ignore"))
        return {k: v[0] for k, v in form.items() if v}


def _apply_credits(user: User, transaction: Transaction, db: Session):
    if transaction.status == "completed":
        return False
    transaction.status = "completed"
    user.credits = (user.credits or 0) + (transaction.credits_purchased or 0)
    if plan_value(user.plan_type) == "free" and (user.credits or 0) >= 50:
        user.plan_type = "pro"
    db.commit()
    return True


@router.get("/pricing")
def get_pricing():
    return {
        "packs": CREDIT_PACKS,
        "subscriptions": {
            "starter": {"usd": 7, "pkr": 1499, "credits": 80},
            "pro": {"usd": 19, "pkr": 4499, "credits": 300},
            "architect": {"usd": 49, "pkr": 11999, "credits": 1000},
            "studio": {"usd": 129, "pkr": 29999, "credits": 3000},
        },
        "currency": {"pkr": "PKR", "usd": "USD"}
    }


@router.post("/purchase", response_model=PaymentResponse)
def purchase_credits(req: PurchaseCredits, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not settings.SUBSCRIPTIONS_ENABLED:
        raise HTTPException(status_code=403, detail="Subscriptions and credit purchases are temporarily disabled during Google Play Closed Testing.")
    if req.credits not in CREDIT_PACKS:
        raise HTTPException(status_code=400, detail="Invalid credit pack")
    if req.payment_method not in ["jazzcash", "easypaisa", "stripe", "dev"]:
        raise HTTPException(status_code=400, detail="Invalid payment method")

    pack = CREDIT_PACKS[req.credits]
    txn_id = f"NKH-{uuid.uuid4().hex[:12].upper()}"
    transaction = Transaction(
        user_id=current_user.id,
        amount_pkr=pack["pkr"],
        amount_usd=pack["usd"],
        credits_purchased=req.credits,
        payment_method=req.payment_method,
        transaction_id=txn_id,
        status="pending",
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    frontend_base = settings.FRONTEND_URL.rstrip("/")
    if req.payment_method == "jazzcash":
        payment_url = os.getenv("JAZZCASH_CHECKOUT_URL")
        return PaymentResponse(success=True, message="JazzCash payment initiated. Complete payment in JazzCash; use Verify/confirm after gateway callback setup.", transaction_id=txn_id, payment_url=payment_url or f"{frontend_base}/?payment=pending&txn={txn_id}&method=jazzcash")
    if req.payment_method == "easypaisa":
        payment_url = os.getenv("EASYPAISA_CHECKOUT_URL") or os.getenv("EASYPAYSA_CHECKOUT_URL")
        return PaymentResponse(success=True, message="Easypaisa payment initiated. Complete payment in Easypaisa; use Verify/confirm after gateway callback setup.", transaction_id=txn_id, payment_url=payment_url or f"{frontend_base}/?payment=pending&txn={txn_id}&method=easypaisa")
    if req.payment_method == "stripe":
        stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
        if stripe_key and not stripe_key.startswith("sk_test_xxx") and not stripe_key.startswith("sk_live_xxx"):
            try:
                import stripe
                stripe.api_key = stripe_key
                session = stripe.checkout.Session.create(
                    mode="payment",
                    payment_method_types=["card"],
                    line_items=[{"price_data": {"currency": "usd", "product_data": {"name": f"NakshaAI {req.credits} Credits"}, "unit_amount": int(pack["usd"] * 100)}, "quantity": 1}],
                    metadata={"transaction_id": txn_id, "user_id": str(current_user.id)},
                    success_url=f"{frontend_base}/?payment=success&txn={txn_id}",
                    cancel_url=f"{frontend_base}/?payment=cancel&txn={txn_id}",
                )
                transaction.gateway_ref = session.id
                db.commit()
                return PaymentResponse(success=True, message="Redirecting to Stripe checkout.", transaction_id=txn_id, payment_url=session.url)
            except Exception as e:
                return PaymentResponse(success=False, message=f"Stripe setup error: {e}. Configure STRIPE_SECRET_KEY on backend.", transaction_id=txn_id)
        return PaymentResponse(success=True, message="Stripe not fully configured (test placeholder). Use dev mode locally or set STRIPE_SECRET_KEY.", transaction_id=txn_id, payment_url=f"{frontend_base}/?payment=pending&txn={txn_id}&method=stripe")
    return PaymentResponse(success=True, message="Development payment record created. Verify to apply credits (configure real gateways for production).", transaction_id=txn_id)


@router.post("/verify/{transaction_id}")
def verify_payment(transaction_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id, Transaction.user_id == current_user.id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    allow_manual = os.getenv("ALLOW_MANUAL_PAYMENT_VERIFY", "false").lower() == "true" or transaction.payment_method == "dev"
    if not allow_manual and transaction.payment_method in ["jazzcash", "easypaisa", "stripe"]:
        return {"success": False, "message": "Awaiting gateway confirmation/webhook. Manual verify disabled for production gateways.", "status": transaction.status}
    if _apply_credits(current_user, transaction, db):
        db.refresh(current_user)
        return {"success": True, "message": "Payment verified! Credits added.", "credits_added": transaction.credits_purchased, "credits": current_user.credits}
    return {"success": True, "message": "Transaction already processed", "credits": current_user.credits}


@router.post("/subscription/checkout")
def create_subscription_checkout(req: SubscriptionCheckoutRequest, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not settings.SUBSCRIPTIONS_ENABLED:
        raise HTTPException(status_code=403, detail="Subscriptions and credit purchases are temporarily disabled during Google Play Closed Testing.")
    if req.plan_slug not in ["starter", "pro", "architect", "studio"]:
        raise HTTPException(status_code=400, detail="Invalid plan slug for subscription checkout (Free plan does not require checkout)")

    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    if stripe_key.startswith("sk_live_"):
        raise HTTPException(status_code=400, detail="Live Stripe keys are prohibited in M4 Test Mode")

    if not stripe_key or stripe_key.startswith("sk_test_xxx") or not stripe_key.startswith("sk_"):
        frontend_base = settings.FRONTEND_URL.rstrip("/")
        existing_sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
        if not existing_sub:
            sub = Subscription(
                user_id=current_user.id,
                plan_slug=req.plan_slug,
                provider="stripe",
                status="pending",
                currency="usd",
                billing_interval="monthly"
            )
            db.add(sub)
        else:
            existing_sub.plan_slug = req.plan_slug
            existing_sub.provider = "stripe"
            existing_sub.status = "pending"
        db.commit()
        return {"success": True, "message": "Stripe test mode mock checkout created.", "checkout_url": f"{frontend_base}/?subscription=pending&plan={req.plan_slug}"}

    price_id_map = {
        "starter": os.getenv("STRIPE_STARTER_PRICE_ID"),
        "pro": os.getenv("STRIPE_PRO_PRICE_ID"),
        "architect": os.getenv("STRIPE_ARCHITECT_PRICE_ID"),
        "studio": os.getenv("STRIPE_STUDIO_PRICE_ID"),
    }
    price_id = price_id_map.get(req.plan_slug)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Stripe Price ID not configured for plan '{req.plan_slug}'")

    try:
        import stripe
        stripe.api_key = stripe_key

        customer_id = None
        existing_sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
        if existing_sub and existing_sub.provider_customer_id:
            customer_id = existing_sub.provider_customer_id
        else:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.username,
                metadata={"user_id": str(current_user.id)}
            )
            customer_id = customer.id

        frontend_base = settings.FRONTEND_URL.rstrip("/")
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            metadata={"user_id": str(current_user.id), "plan_slug": req.plan_slug},
            success_url=f"{frontend_base}/?subscription=success&plan={req.plan_slug}",
            cancel_url=f"{frontend_base}/?subscription=cancel&plan={req.plan_slug}",
        )

        if not existing_sub:
            sub = Subscription(
                user_id=current_user.id,
                plan_slug=req.plan_slug,
                provider="stripe",
                provider_customer_id=customer_id,
                status="pending",
                currency="usd",
                billing_interval="monthly"
            )
            db.add(sub)
        else:
            existing_sub.provider_customer_id = customer_id
            existing_sub.plan_slug = req.plan_slug
            existing_sub.provider = "stripe"
            existing_sub.status = "pending"
        db.commit()

        return {"success": True, "checkout_url": session.url, "session_id": session.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Stripe Checkout error: {e}")


@router.get("/subscription/status")
def get_subscription_status(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).order_by(Subscription.created_at.desc()).first()
    if not sub:
        return {"status": "none", "plan_slug": current_user.plan_type, "credits": current_user.credits}
    return {
        "id": sub.id,
        "plan_slug": sub.plan_slug,
        "status": sub.status,
        "provider": sub.provider,
        "current_period_start": sub.current_period_start,
        "current_period_end": sub.current_period_end,
        "rollover_balance": sub.rollover_balance,
        "credits": current_user.credits,
    }


SUBSCRIPTION_PLANS = {
    "starter": {"pkr": 1499, "usd": 7, "credits": 80, "name": "Starter Plan"},
    "pro": {"pkr": 4499, "usd": 19, "credits": 300, "name": "Pro Plan"},
    "architect": {"pkr": 11999, "usd": 49, "credits": 1000, "name": "Architect Plan"},
    "studio": {"pkr": 29999, "usd": 129, "credits": 3000, "name": "Studio Plan"},
}


class LocalSubscriptionCheckoutRequest(BaseModel):
    plan_slug: str
    payment_method: str  # "jazzcash" or "easypaisa"


@router.post("/subscription/local-checkout")
def create_local_subscription_checkout(req: LocalSubscriptionCheckoutRequest, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not settings.SUBSCRIPTIONS_ENABLED:
        raise HTTPException(status_code=403, detail="Subscriptions and credit purchases are temporarily disabled during Google Play Closed Testing.")
    if req.plan_slug not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan slug for local subscription checkout")
    if req.payment_method not in ["jazzcash", "easypaisa"]:
        raise HTTPException(status_code=400, detail="Invalid local payment method (must be jazzcash or easypaisa)")

    plan = SUBSCRIPTION_PLANS[req.plan_slug]
    txn_id = f"PKR-{uuid.uuid4().hex[:12].upper()}"
    transaction = Transaction(
        user_id=current_user.id,
        amount_pkr=plan["pkr"],
        amount_usd=plan["usd"],
        credits_purchased=plan["credits"],
        payment_method=req.payment_method,
        transaction_id=txn_id,
        status="pending",
    )
    db.add(transaction)

    existing_sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).order_by(Subscription.created_at.desc()).first()
    if not existing_sub or existing_sub.status == "expired":
        sub = Subscription(
            user_id=current_user.id,
            plan_slug=req.plan_slug,
            provider=req.payment_method,
            status="pending",
            currency="pkr",
            billing_interval="monthly"
        )
        db.add(sub)
    else:
        existing_sub.plan_slug = req.plan_slug
        existing_sub.provider = req.payment_method
        existing_sub.status = "pending"
        existing_sub.currency = "pkr"
    db.commit()
    db.refresh(transaction)

    frontend_base = settings.FRONTEND_URL.rstrip("/")
    checkout_url = f"{frontend_base}/?payment=pending&txn={txn_id}&method={req.payment_method}&plan={req.plan_slug}"
    return {
        "success": True,
        "message": f"{req.payment_method.capitalize()} subscription checkout initiated. Complete payment via sandbox simulator.",
        "transaction_id": txn_id,
        "checkout_url": checkout_url,
        "amount_pkr": plan["pkr"]
    }


@router.post("/subscription/local-renew")
def renew_local_subscription(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not settings.SUBSCRIPTIONS_ENABLED:
        raise HTTPException(status_code=403, detail="Subscriptions and credit purchases are temporarily disabled during Google Play Closed Testing.")
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).order_by(Subscription.created_at.desc()).first()
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found to renew")
    if sub.provider not in ["jazzcash", "easypaisa"]:
        raise HTTPException(status_code=400, detail="Manual local renewal only applies to JazzCash or Easypaisa subscriptions")

    plan = SUBSCRIPTION_PLANS.get(sub.plan_slug, SUBSCRIPTION_PLANS["starter"])
    txn_id = f"PKR-REN-{uuid.uuid4().hex[:12].upper()}"
    transaction = Transaction(
        user_id=current_user.id,
        amount_pkr=plan["pkr"],
        amount_usd=plan["usd"],
        credits_purchased=plan["credits"],
        payment_method=sub.provider,
        transaction_id=txn_id,
        status="pending",
    )
    db.add(transaction)
    sub.status = "pending"
    db.commit()
    db.refresh(transaction)

    frontend_base = settings.FRONTEND_URL.rstrip("/")
    return {
        "success": True,
        "message": f"Manual renewal payment initiated via {sub.provider}. Complete payment to renew subscription cycle.",
        "transaction_id": txn_id,
        "checkout_url": f"{frontend_base}/?payment=pending&txn={txn_id}&method={sub.provider}&plan={sub.plan_slug}&renew=true",
        "amount_pkr": plan["pkr"]
    }


@router.get("/transaction/{transaction_id}")
def get_transaction_status(transaction_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id, Transaction.user_id == current_user.id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {
        "transaction_id": tx.transaction_id,
        "status": tx.status,
        "payment_method": tx.payment_method,
        "amount_pkr": tx.amount_pkr,
        "credits_purchased": tx.credits_purchased,
        "created_at": tx.created_at
    }


@router.post("/subscription/cancel")
def cancel_subscription(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    sub = SubscriptionService.cancel_subscription(current_user, db)
    return {"success": True, "message": "Subscription canceled successfully", "status": sub.status}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key or not secret:
        return {"received": True, "processed": False, "message": "Stripe webhook not configured"}
    try:
        import stripe
        stripe.api_key = stripe_key
        event = stripe.Webhook.construct_event(payload, sig, secret)
        event_id = event.get("id")

        # Idempotency check via ledger reference
        idemp_ref = f"evt_{event_id}"
        existing_ledger = db.query(CreditLedger).filter_by(idempotency_ref=idemp_ref).first()
        if existing_ledger:
            return {"received": True, "processed": True, "duplicate": True}

        event_type = event.get("type")
        obj = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            meta = obj.get("metadata", {}) or {}
            txn_id = meta.get("transaction_id")
            if txn_id:
                tx = db.query(Transaction).filter(Transaction.transaction_id == txn_id).first()
                if tx:
                    user = db.query(User).filter(User.id == tx.user_id).first()
                    if user:
                        _apply_credits(user, tx, db)
            elif obj.get("mode") == "subscription":
                user_id_str = meta.get("user_id")
                plan_slug = meta.get("plan_slug")
                sub_id = obj.get("subscription")
                cust_id = obj.get("customer")
                if user_id_str and plan_slug:
                    user = db.query(User).filter(User.id == int(user_id_str)).first()
                    if user:
                        sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
                        if not sub:
                            sub = Subscription(
                                user_id=user.id,
                                plan_slug=plan_slug,
                                provider="stripe",
                                provider_customer_id=cust_id,
                                provider_subscription_id=sub_id,
                                status="active",
                                currency="usd",
                                billing_interval="monthly"
                            )
                            db.add(sub)
                        else:
                            sub.status = "active"
                            sub.plan_slug = plan_slug
                            sub.provider_subscription_id = sub_id
                            sub.provider_customer_id = cust_id
                        db.commit()
                        db.refresh(sub)
                        SubscriptionService.process_billing_cycle(sub, db)

        elif event_type in ["customer.subscription.created", "customer.subscription.updated"]:
            sub_id = obj.get("id")
            cust_id = obj.get("customer")
            status_val = obj.get("status")
            if sub_id:
                sub = db.query(Subscription).filter(Subscription.provider_subscription_id == sub_id).first()
                if not sub and cust_id:
                    sub = db.query(Subscription).filter(Subscription.provider_customer_id == cust_id).first()
                if sub:
                    sub.status = "active" if status_val == "active" else ("past_due" if status_val == "past_due" else sub.status)
                    if status_val in ["canceled", "unpaid"]:
                        sub.status = "canceled"
                    db.commit()

        elif event_type == "customer.subscription.deleted":
            sub_id = obj.get("id")
            if sub_id:
                sub = db.query(Subscription).filter(Subscription.provider_subscription_id == sub_id).first()
                if sub:
                    sub.status = "expired"
                    db.commit()

        elif event_type == "invoice.paid":
            inv_id = obj.get("id")
            sub_id = obj.get("subscription")
            cust_id = obj.get("customer")
            amount_paid = Decimal(str(obj.get("amount_paid", 0) / 100))
            if inv_id:
                # Record invoice idempotently
                existing_inv = db.query(Invoice).filter_by(provider_invoice_id=inv_id).first()
                if not existing_inv and sub_id:
                    sub = db.query(Subscription).filter(Subscription.provider_subscription_id == sub_id).first()
                    if sub:
                        inv = Invoice(
                            user_id=sub.user_id,
                            subscription_id=sub.id,
                            invoice_number=f"INV-{inv_id[-8:].upper()}",
                            provider_invoice_id=inv_id,
                            amount=amount_paid,
                            currency="usd",
                            status="paid",
                            paid_at=datetime.now(timezone.utc)
                        )
                        db.add(inv)
                        db.commit()
                        SubscriptionService.process_billing_cycle(sub, db)

        elif event_type == "invoice.payment_failed":
            sub_id = obj.get("subscription")
            if sub_id:
                sub = db.query(Subscription).filter(Subscription.provider_subscription_id == sub_id).first()
                if sub:
                    sub.status = "past_due"
                    db.commit()

        return {"received": True, "processed": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")


@router.post("/webhook/jazzcash")
async def jazzcash_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    secret = os.getenv("JAZZCASH_HASH_KEY", "")
    if secret:
        sig = request.headers.get("x-jazzcash-signature", "")
        expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
        if not sig or not hmac.compare_digest(expected, sig.strip()):
            raise HTTPException(status_code=401, detail="Invalid JazzCash signature")
    data = _parse_webhook_payload(raw)
    txn_id = data.get("pp_TxnRefNo") or data.get("transaction_id")
    code = str(data.get("pp_ResponseCode", ""))
    if txn_id and code in ["000", "121"]:
        tx = db.query(Transaction).filter(Transaction.transaction_id == txn_id).first()
        if tx:
            user = db.query(User).filter(User.id == tx.user_id).first()
            if user:
                _apply_credits(user, tx, db)
                sub = db.query(Subscription).filter(Subscription.user_id == user.id, Subscription.provider == "jazzcash").order_by(Subscription.created_at.desc()).first()
                if sub and sub.status in ["pending", "past_due"]:
                    sub.status = "active"
                    db.commit()
                    db.refresh(sub)
                    SubscriptionService.process_billing_cycle(sub, db)
                    inv = Invoice(
                        user_id=user.id,
                        subscription_id=sub.id,
                        invoice_number=f"INV-JC-{txn_id[-8:].upper()}",
                        provider_invoice_id=txn_id,
                        amount=Decimal(str(tx.amount_pkr)),
                        currency="pkr",
                        status="paid",
                        paid_at=datetime.now(timezone.utc)
                    )
                    db.add(inv)
                    db.commit()
                return {"received": True, "processed": True}
    return {"received": True, "processed": False, "message": "JazzCash webhook received but no valid transaction/status processed."}


@router.post("/webhook/easypaisa")
async def easypaisa_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    secret = os.getenv("EASYPAISA_HASH_KEY", "")
    if secret:
        sig = request.headers.get("x-easypaisa-signature", "")
        expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
        if not sig or not hmac.compare_digest(expected, sig.strip()):
            raise HTTPException(status_code=401, detail="Invalid Easypaisa signature")
    data = _parse_webhook_payload(raw)
    txn_id = data.get("orderRefNum") or data.get("transaction_id")
    status_val = str(data.get("transactionStatus", "")).lower()
    if txn_id and status_val in ["paid", "success", "completed"]:
        tx = db.query(Transaction).filter(Transaction.transaction_id == txn_id).first()
        if tx:
            user = db.query(User).filter(User.id == tx.user_id).first()
            if user:
                _apply_credits(user, tx, db)
                sub = db.query(Subscription).filter(Subscription.user_id == user.id, Subscription.provider == "easypaisa").order_by(Subscription.created_at.desc()).first()
                if sub and sub.status in ["pending", "past_due"]:
                    sub.status = "active"
                    db.commit()
                    db.refresh(sub)
                    SubscriptionService.process_billing_cycle(sub, db)
                    inv = Invoice(
                        user_id=user.id,
                        subscription_id=sub.id,
                        invoice_number=f"INV-EP-{txn_id[-8:].upper()}",
                        provider_invoice_id=txn_id,
                        amount=Decimal(str(tx.amount_pkr)),
                        currency="pkr",
                        status="paid",
                        paid_at=datetime.now(timezone.utc)
                    )
                    db.add(inv)
                    db.commit()
                return {"received": True, "processed": True}
    return {"received": True, "processed": False, "message": "Easypaisa webhook received but no valid transaction/status processed."}


@router.get("/history")
def payment_history(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.user_id == current_user.id).order_by(Transaction.created_at.desc()).all()
    return {"transactions": [{
        "id": t.id, "transaction_id": t.transaction_id, "amount_pkr": t.amount_pkr, "amount_usd": t.amount_usd,
        "credits_purchased": t.credits_purchased, "payment_method": t.payment_method, "status": t.status, "created_at": t.created_at
    } for t in transactions]}


@router.get("/suppliers/marketplace")
def get_supplier_marketplace():
    return {
        "suppliers": [
            {"id": "s1", "name": "Best Bricks & Blocks Co.", "item": "A-Grade Bricks", "price_pkr": 14.5, "unit": "per piece", "location": "Lahore / Islamabad"},
            {"id": "s2", "name": "Pak Arab Cement Ltd", "item": "OPC Cement (50kg bag)", "price_pkr": 1450, "unit": "per bag", "location": "Nationwide"},
            {"id": "s3", "name": "Mughal & Amreli Steel", "item": "Grade 60 Deformed Bars", "price_pkr": 265000, "unit": "per ton", "location": "Karachi / Lahore"},
            {"id": "s4", "name": "Chenab Sand & Aggregate", "item": "Chenab Sand", "price_pkr": 45, "unit": "per cft", "location": "Punjab"},
        ]
    }
