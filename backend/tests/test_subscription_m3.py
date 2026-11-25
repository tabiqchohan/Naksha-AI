import pytest
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from app.database import Base
from app.models.user_models import User, PlanType
from app.models.monetization_models import PlanCatalog, Subscription, CreditLedger
from app.services.credit_service import CreditService
from app.services.subscription_service import SubscriptionService, add_months


@pytest.fixture
def m3_db():
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


def test_month_end_date_arithmetic():
    dt = datetime(2026, 1, 31, tzinfo=timezone.utc)
    next_dt = add_months(dt, 1)
    assert next_dt.month == 2
    assert next_dt.day == 28  # 2026 is not leap year

    leap_dt = datetime(2024, 1, 31, tzinfo=timezone.utc)
    next_leap = add_months(leap_dt, 1)
    assert next_leap.month == 2
    assert next_leap.day == 29  # 2024 is leap year


def test_subscription_lifecycle_and_allocation(m3_db):
    user = User(email="subuser@example.com", username="subuser", hashed_password="pw", credits=10, plan_type=PlanType.FREE)
    m3_db.add(user)
    m3_db.commit()
    m3_db.refresh(user)

    # Create starter subscription (pending)
    sub = SubscriptionService.create_subscription(user, "starter", "dev", m3_db)
    assert sub.status == "pending"
    assert sub.plan_slug == "starter"

    # Activate subscription
    activated_sub = SubscriptionService.activate_subscription(sub.id, m3_db)
    assert activated_sub.status == "active"
    # Starter allocation is 80 credits + initial balance 10 = 90 credits
    assert user.credits == 90

    # Test idempotent cycle processing (should not duplicate credits)
    processed = SubscriptionService.process_billing_cycle(activated_sub, m3_db)
    assert processed is False  # Already processed for this cycle
    assert user.credits == 90


def test_rollover_policy_caps(m3_db):
    user = User(email="roll@example.com", username="rolluser", hashed_password="pw", credits=50, plan_type=PlanType.FREE)
    m3_db.add(user)
    m3_db.commit()
    m3_db.refresh(user)

    sub = SubscriptionService.create_subscription(user, "starter", "dev", m3_db)
    SubscriptionService.activate_subscription(sub.id, m3_db)

    # Starter cap is 50% of 80 = 40 credits rollover max
    cap = SubscriptionService.get_rollover_cap("starter")
    assert cap == 0.5

    pro_cap = SubscriptionService.get_rollover_cap("pro")
    assert pro_cap == 1.0


def test_plan_upgrade_and_downgrade(m3_db):
    user = User(email="upgrade@example.com", username="upuser", hashed_password="pw", credits=10, plan_type=PlanType.FREE)
    m3_db.add(user)
    m3_db.commit()
    m3_db.refresh(user)

    # Upgrade to Pro
    pro_sub = SubscriptionService.change_plan(user, "pro", m3_db)
    assert pro_sub.status == "active"
    assert pro_sub.plan_slug == "pro"
    # Pro allocation is 300 + initial 10 = 310 credits
    assert user.credits == 310

    # Downgrade to Starter (creates new active sub, cancels old pro sub)
    starter_sub = SubscriptionService.change_plan(user, "starter", m3_db)
    assert starter_sub.plan_slug == "starter"
    assert starter_sub.status == "active"
