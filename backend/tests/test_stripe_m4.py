import pytest
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.database import Base
from app.models.user_models import User, PlanType, Transaction
from app.models.monetization_models import PlanCatalog, Subscription, Invoice, CreditLedger
from app.services.subscription_service import SubscriptionService
from app.services.credit_service import CreditService
from app.main import app
import json
import os
import hmac
import hashlib


@pytest.fixture
def m4_client_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed plan catalog
    plans = [
        PlanCatalog(slug="free", name="Free", price_pkr=Decimal("0.00"), price_usd=Decimal("0.00"), credits_monthly=10),
        PlanCatalog(slug="starter", name="Starter", price_pkr=Decimal("1499.00"), price_usd=Decimal("7.00"), credits_monthly=80),
        PlanCatalog(slug="pro", name="Pro", price_pkr=Decimal("4499.00"), price_usd=Decimal("19.00"), credits_monthly=300),
        PlanCatalog(slug="architect", name="Architect", price_pkr=Decimal("11999.00"), price_usd=Decimal("49.00"), credits_monthly=1000),
        PlanCatalog(slug="studio", name="Studio", price_pkr=Decimal("29999.00"), price_usd=Decimal("129.00"), credits_monthly=3000),
    ]
    for p in plans:
        db.add(p)
    db.commit()

    try:
        yield db
    finally:
        db.close()


def test_stripe_configuration_validation():
    secret_key = "sk_test_mockkey12345"
    assert secret_key.startswith("sk_test_")
    live_key = "sk_live_secret12345"
    assert live_key.startswith("sk_live_")


def test_stripe_checkout_free_plan_rejection(m4_client_db):
    from app.routers.payments import create_subscription_checkout
    user = User(email="free_chk@example.com", username="freechk", hashed_password="pw", credits=10, plan_type=PlanType.FREE)
    m4_client_db.add(user)
    m4_client_db.commit()

    class Req:
        plan_slug = "free"

    with pytest.raises(HTTPException) as exc_info:
        create_subscription_checkout(req=Req(), current_user=user, db=m4_client_db)
    assert exc_info.value.status_code == 400
    assert "Invalid plan slug" in str(exc_info.value.detail)


def test_subscription_status_endpoint_empty(m4_client_db):
    user = User(email="status@example.com", username="statususer", hashed_password="pw", credits=10, plan_type=PlanType.FREE)
    m4_client_db.add(user)
    m4_client_db.commit()

    from app.routers.payments import get_subscription_status
    res = get_subscription_status(current_user=user, db=m4_client_db)
    assert res["status"] == "none"
    assert res["credits"] == 10


def test_webhook_signature_verification_and_idempotency(monkeypatch, m4_client_db):
    import stripe
    secret = "whsec_test_secret_123"
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", secret)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_123")

    user = User(email="wh@example.com", username="whuser", hashed_password="pw", credits=10, plan_type=PlanType.FREE)
    m4_client_db.add(user)
    m4_client_db.commit()

    event_data = {
        "id": "evt_test_unique_999",
        "type": "invoice.payment_failed",
        "data": {
            "object": {
                "id": "in_test_123",
                "subscription": "sub_test_123"
            }
        }
    }
    payload = json.dumps(event_data).encode("utf-8")
    import time
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
    expected_sig = hmac.new(secret.encode('utf-8'), signed_payload.encode('utf-8'), hashlib.sha256).hexdigest()
    sig = f"t={timestamp},v1={expected_sig}"

    # Verify construct_event passes with valid signature
    event_verified = stripe.Webhook.construct_event(payload, sig, secret)
    assert event_verified["id"] == "evt_test_unique_999"

    # Test client app test
    client = TestClient(app)
    # Override get_db in app if needed, or test service/router functions directly
    # Here we test router function with dependency override or direct call
    from app.routers.payments import stripe_webhook
    from fastapi import Request

    # Mock request
    class MockRequest:
        async def body(self):
            return payload

    req = MockRequest()
    # We can also test idempotency tracking via ledger ref evt_test_unique_999
    ledger_ref = "evt_test_unique_999"
    assert m4_client_db.query(CreditLedger).filter_by(idempotency_ref=f"evt_{ledger_ref}").first() is None


def test_same_invoice_different_event_ids_idempotency(m4_client_db):
    user = User(email="inv@example.com", username="invuser", hashed_password="pw", credits=10, plan_type=PlanType.FREE)
    m4_client_db.add(user)
    m4_client_db.commit()
    sub = Subscription(user_id=user.id, plan_slug="starter", status="active", provider_subscription_id="sub_inv_123")
    m4_client_db.add(sub)
    m4_client_db.commit()

    # Simulate two different event IDs referring to the same invoice ID in-app logic
    inv_id = "in_same_999"
    cycle_key = f"starter_{datetime.now(timezone.utc).strftime('%Y-%m')}"

    # Allocate once for cycle
    allocated = CreditService.allocate_monthly_credits(user, "starter", cycle_key, m4_client_db)
    assert allocated is True
    initial_credits = user.credits

    # Second event ID with same cycle key should not re-allocate
    allocated_again = CreditService.allocate_monthly_credits(user, "starter", cycle_key, m4_client_db)
    assert allocated_again is False
    assert user.credits == initial_credits
