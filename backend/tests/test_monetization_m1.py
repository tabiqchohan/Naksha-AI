import pytest
from decimal import Decimal
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.database import Base
from app.models.user_models import User, PlanType, Transaction
from app.models.monetization_models import PlanCatalog, Subscription, Invoice, CreditLedger, CreditUsage


@pytest.fixture
def m1_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_plan_catalog_and_numeric_precision(m1_db):
    plan = PlanCatalog(
        slug="pro",
        name="Pro Plan",
        price_pkr=Decimal("4499.50"),
        price_usd=Decimal("19.99"),
        credits_monthly=300
    )
    m1_db.add(plan)
    m1_db.commit()
    m1_db.refresh(plan)

    assert plan.price_pkr == Decimal("4499.50")
    assert plan.price_usd == Decimal("19.99")


def test_subscription_plan_referential_integrity(m1_db):
    user = User(email="fk@example.com", username="fkuser", hashed_password="hashed")
    m1_db.add(user)
    m1_db.commit()
    m1_db.refresh(user)

    # Invalid plan reference should fail integrity check due to FK on plan_slug -> plan_catalog.slug
    invalid_sub = Subscription(
        user_id=user.id,
        plan_slug="nonexistent_plan",
        provider="stripe",
        status="active"
    )
    m1_db.add(invalid_sub)
    with pytest.raises(Exception):
        m1_db.commit()
    m1_db.rollback()

    # Valid plan reference
    valid_plan = PlanCatalog(slug="starter", name="Starter", price_pkr=Decimal("1499.00"), price_usd=Decimal("7.00"), credits_monthly=80)
    m1_db.add(valid_plan)
    m1_db.commit()

    valid_sub = Subscription(
        user_id=user.id,
        plan_slug="starter",
        provider="stripe",
        status="active"
    )
    m1_db.add(valid_sub)
    m1_db.commit()
    m1_db.refresh(valid_sub)

    assert valid_sub.plan.slug == "starter"
    assert valid_sub.plan.name == "Starter"


def test_credit_ledger_immutability(m1_db):
    user = User(email="immut@example.com", username="immutuser", hashed_password="hashed")
    m1_db.add(user)
    m1_db.commit()
    m1_db.refresh(user)

    entry = CreditLedger(
        user_id=user.id,
        entry_type="grant",
        amount=50,
        source="initial",
        idempotency_ref="ref_immut_001"
    )
    m1_db.add(entry)
    m1_db.commit()
    m1_db.refresh(entry)

    # Test update protection
    entry.amount = 100
    with pytest.raises(RuntimeError, match="strictly immutable"):
        m1_db.commit()
    m1_db.rollback()

    # Test delete protection
    m1_db.delete(entry)
    with pytest.raises(RuntimeError, match="strictly immutable"):
        m1_db.commit()
    m1_db.rollback()

    # Test compensating entry for correction
    comp_entry = CreditLedger(
        user_id=user.id,
        entry_type="admin_adjustment",
        amount=-20,
        source="correction",
        idempotency_ref="ref_comp_001",
        description="Compensating entry for correction"
    )
    m1_db.add(comp_entry)
    m1_db.commit()

    entries = m1_db.query(CreditLedger).filter_by(user_id=user.id).all()
    assert len(entries) == 2
    assert sum(e.amount for e in entries) == 30


def test_existing_compatibility(m1_db):
    user = User(email="comp@example.com", username="compuser", hashed_password="hashed", credits=10, plan_type=PlanType.FREE)
    m1_db.add(user)
    m1_db.commit()

    txn = Transaction(
        user_id=user.id,
        amount_pkr=Decimal("500.00"),
        amount_usd=Decimal("1.80"),
        credits_purchased=10,
        payment_method="dev",
        transaction_id="TXN-12345"
    )
    m1_db.add(txn)
    m1_db.commit()

    assert user.credits == 10
    assert user.plan_type == PlanType.FREE
    assert txn.amount_pkr == Decimal("500.00")
