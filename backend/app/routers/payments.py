from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.user_models import User, Transaction, plan_value
from app.models.auth_schemas import PurchaseCredits, PaymentResponse
from app.auth.dependencies import get_current_active_user
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
    return {"packs": CREDIT_PACKS, "currency": {"pkr": "PKR", "usd": "USD"}}


@router.post("/purchase", response_model=PaymentResponse)
def purchase_credits(req: PurchaseCredits, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
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
        if stripe_key and not stripe_key.startswith("sk_test_xxx"):
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
    # dev fallback - only useful in controlled environments; keeps existing behavior explicit
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
        if event["type"] == "checkout.session.completed":
            meta = event["data"]["object"].get("metadata", {}) or {}
            txn_id = meta.get("transaction_id")
            if txn_id:
                tx = db.query(Transaction).filter(Transaction.transaction_id == txn_id).first()
                if tx:
                    user = db.query(User).filter(User.id == tx.user_id).first()
                    if user:
                        _apply_credits(user, tx, db)
                        return {"received": True, "processed": True}
        return {"received": True, "processed": False}
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
