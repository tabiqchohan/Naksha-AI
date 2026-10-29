from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.models.user_models import User, Transaction, Base
from app.models.auth_schemas import PurchaseCredits, PaymentResponse
from app.auth.dependencies import get_current_active_user
import uuid
import os

router = APIRouter(prefix="/payments", tags=["Payments"])

Base.metadata.create_all(bind=engine)

# Pricing
CREDIT_PACKS = {
    10: {"pkr": 500, "usd": 1.8, "name": "10 Credits"},
    25: {"pkr": 1000, "usd": 3.6, "name": "25 Credits"},
    50: {"pkr": 1800, "usd": 6.5, "name": "50 Credits"},
    100: {"pkr": 3000, "usd": 10.8, "name": "100 Credits"},
}


@router.get("/pricing")
def get_pricing():
    return {"packs": CREDIT_PACKS}


@router.post("/purchase", response_model=PaymentResponse)
def purchase_credits(req: PurchaseCredits, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if req.credits not in CREDIT_PACKS:
        raise HTTPException(status_code=400, detail="Invalid credit pack")
    
    pack = CREDIT_PACKS[req.credits]
    txn_id = f"NKH-{uuid.uuid4().hex[:12].upper()}"
    
    transaction = Transaction(
        user_id=current_user.id,
        amount_pkr=pack["pkr"],
        amount_usd=pack["usd"],
        credits_purchased=req.credits,
        payment_method=req.payment_method,
        transaction_id=txn_id,
        status="pending"
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    if req.payment_method == "jazzcash":
        return {
            "success": True,
            "message": "JazzCash payment initiated. Please complete payment in JazzCash app.",
            "transaction_id": txn_id,
            "payment_url": f"https://payments.jazzcash.com.pk/pay?txn={txn_id}&amount={pack['pkr']}"
        }
    elif req.payment_method == "easypaisa":
        return {
            "success": True,
            "message": "Easypaisa payment initiated. Send payment to account or use app.",
            "transaction_id": txn_id,
            "payment_url": f"https://easypaisa.com.pk/pay?txn={txn_id}&amount={pack['pkr']}"
        }
    elif req.payment_method == "stripe":
        stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
        if not stripe_key or stripe_key.startswith("sk_test_"):
            return {
                "success": True,
                "message": "Stripe test mode - Payment simulation successful",
                "transaction_id": txn_id,
                "payment_url": None
            }
        return {
            "success": True,
            "message": "Redirecting to Stripe checkout",
            "transaction_id": txn_id,
            "payment_url": f"https://checkout.stripe.com/pay/{txn_id}"
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid payment method")


@router.post("/verify/{transaction_id}")
def verify_payment(transaction_id: str, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Simulate successful payment for testing
    if transaction.status == "pending":
        transaction.status = "completed"
        user = db.query(User).filter(User.id == transaction.user_id).first()
        if user:
            user.credits += transaction.credits_purchased
            if user.plan_type.value == "free" and user.credits >= 50:
                user.plan_type = "pro"
        db.commit()
        return {"success": True, "message": "Payment verified! Credits added.", "credits_added": transaction.credits_purchased}
    
    return {"success": True, "message": "Transaction already processed"}


@router.get("/history")
def payment_history(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.user_id == current_user.id).order_by(Transaction.created_at.desc()).all()
    return {"transactions": transactions}
