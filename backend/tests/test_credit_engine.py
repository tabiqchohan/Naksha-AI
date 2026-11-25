import pytest
from decimal import Decimal
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from app.database import Base
from app.models.user_models import User, PlanType
from app.models.monetization_models import PlanCatalog, CreditLedger, CreditUsage
from app.services.credit_service import CreditService, OPERATION_COSTS


@pytest.fixture
def credit_db():
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


def test_operation_costs():
    assert CreditService.get_operation_cost("plan_generation") == 8
    assert CreditService.get_operation_cost("ai_consultation") == 2
    assert CreditService.get_operation_cost("boq_calculation") == 0
    assert CreditService.get_operation_cost("unknown_op") == 8  # default fallback


def test_reserve_and_commit_credits(credit_db):
    user = User(email="user1@example.com", username="user1", hashed_password="pw", credits=15, plan_type=PlanType.FREE)
    credit_db.add(user)
    credit_db.commit()
    credit_db.refresh(user)

    # Reserve credits for plan_generation (cost 8)
    usage = CreditService.reserve_credits(
        user=user,
        operation_type="plan_generation",
        idempotency_key="idemp_key_123",
        db=credit_db,
        payload={"plot_width": 30, "plot_length": 60}
    )

    assert usage.status == "reserved"
    assert usage.credit_cost == 8
    assert user.credits == 7  # 15 - 8

    # Verify ledger entry was created
    ledger = credit_db.query(CreditLedger).filter_by(user_id=user.id).first()
    assert ledger is not None
    assert ledger.amount == -8
    assert ledger.entry_type == "reservation"

    # Commit usage
    CreditService.commit_usage("idemp_key_123", credit_db)
    credit_db.refresh(usage)
    assert usage.status == "completed"


def test_insufficient_credits_rejection(credit_db):
    user = User(email="poor@example.com", username="pooruser", hashed_password="pw", credits=2, plan_type=PlanType.FREE)
    credit_db.add(user)
    credit_db.commit()
    credit_db.refresh(user)

    with pytest.raises(HTTPException) as exc_info:
        CreditService.reserve_credits(
            user=user,
            operation_type="plan_generation",
            idempotency_key="idemp_key_poor",
            db=credit_db
        )
    assert exc_info.value.status_code == 403
    assert "Insufficient credits" in str(exc_info.value.detail)


def test_idempotency_duplicate_request(credit_db):
    user = User(email="idemp@example.com", username="idempuser", hashed_password="pw", credits=20, plan_type=PlanType.FREE)
    credit_db.add(user)
    credit_db.commit()
    credit_db.refresh(user)

    # First call
    usage1 = CreditService.reserve_credits(
        user=user,
        operation_type="plan_revision",
        idempotency_key="dup_key_999",
        db=credit_db,
        payload={"notes": "add balcony"}
    )
    assert usage1.status == "reserved"
    assert user.credits == 17  # 20 - 3

    # Duplicate call with same idempotency_key and same payload
    usage2 = CreditService.reserve_credits(
        user=user,
        operation_type="plan_revision",
        idempotency_key="dup_key_999",
        db=credit_db,
        payload={"notes": "add balcony"}
    )
    assert usage2.id == usage1.id
    assert user.credits == 17  # Credits should not be deducted again


def test_idempotency_fingerprinting_conflicting_payload(credit_db):
    user = User(email="fp@example.com", username="fpuser", hashed_password="pw", credits=20, plan_type=PlanType.FREE)
    credit_db.add(user)
    credit_db.commit()
    credit_db.refresh(user)

    # First call with payload A
    CreditService.reserve_credits(
        user=user,
        operation_type="plan_generation",
        idempotency_key="key_fp_001",
        db=credit_db,
        payload={"floors": 1}
    )

    # Second call with same idempotency key but conflicting payload B should raise HTTP 400
    with pytest.raises(HTTPException) as exc_info:
        CreditService.reserve_credits(
            user=user,
            operation_type="plan_generation",
            idempotency_key="key_fp_001",
            db=credit_db,
            payload={"floors": 2}
        )
    assert exc_info.value.status_code == 400
    assert "conflicting payload" in str(exc_info.value.detail)


def test_idempotency_fingerprinting_conflicting_operation(credit_db):
    user = User(email="op@example.com", username="opuser", hashed_password="pw", credits=20, plan_type=PlanType.FREE)
    credit_db.add(user)
    credit_db.commit()
    credit_db.refresh(user)

    CreditService.reserve_credits(
        user=user,
        operation_type="plan_generation",
        idempotency_key="key_op_001",
        db=credit_db
    )

    with pytest.raises(HTTPException) as exc_info:
        CreditService.reserve_credits(
            user=user,
            operation_type="plan_repair",
            idempotency_key="key_op_001",
            db=credit_db
        )
    assert exc_info.value.status_code == 400
    assert "conflicting payload" in str(exc_info.value.detail)


def test_idempotency_different_user_rejection(credit_db):
    user1 = User(email="u1@example.com", username="u1", hashed_password="pw", credits=20, plan_type=PlanType.FREE)
    user2 = User(email="u2@example.com", username="u2", hashed_password="pw", credits=20, plan_type=PlanType.FREE)
    credit_db.add_all([user1, user2])
    credit_db.commit()
    credit_db.refresh(user1)
    credit_db.refresh(user2)

    CreditService.reserve_credits(
        user=user1,
        operation_type="plan_generation",
        idempotency_key="shared_key_123",
        db=credit_db
    )

    with pytest.raises(HTTPException) as exc_info:
        CreditService.reserve_credits(
            user=user2,
            operation_type="plan_generation",
            idempotency_key="shared_key_123",
            db=credit_db
        )
    assert exc_info.value.status_code == 400
    assert "mismatch for user" in str(exc_info.value.detail)


def test_release_reservation_and_refund(credit_db):
    user = User(email="fail@example.com", username="failuser", hashed_password="pw", credits=10, plan_type=PlanType.FREE)
    credit_db.add(user)
    credit_db.commit()
    credit_db.refresh(user)

    # Reserve
    CreditService.reserve_credits(
        user=user,
        operation_type="plan_generation",
        idempotency_key="fail_key_001",
        db=credit_db
    )
    assert user.credits == 2  # 10 - 8

    # Release reservation due to generation error / timeout
    CreditService.release_reservation("fail_key_001", "Generation failed due to upstream timeout", credit_db)

    usage = credit_db.query(CreditUsage).filter_by(idempotency_key="fail_key_001").first()
    assert usage.status == "released"
    assert usage.failure_reason == "Generation failed due to upstream timeout"
    assert user.credits == 10  # Refunded back to 10


def test_grant_purchase_and_monthly_allocation(credit_db):
    user = User(email="sub@example.com", username="subuser", hashed_password="pw", credits=5, plan_type=PlanType.FREE)
    credit_db.add(user)

    plan = PlanCatalog(
        slug="starter",
        name="Starter Plan",
        price_pkr=Decimal("1499.00"),
        price_usd=Decimal("7.00"),
        credits_monthly=80
    )
    credit_db.add(plan)
    credit_db.commit()
    credit_db.refresh(user)

    # Test credit pack purchase grant
    granted = CreditService.grant_purchase(user, "TXN-999888", 50, credit_db)
    assert granted is True
    assert user.credits == 55  # 5 + 50

    # Repeat purchase with same transaction ID (idempotent safeguard)
    granted_again = CreditService.grant_purchase(user, "TXN-999888", 50, credit_db)
    assert granted_again is False
    assert user.credits == 55

    # Test monthly credit allocation
    allocated = CreditService.allocate_monthly_credits(user, "starter", "2026-11", credit_db)
    assert allocated is True
    assert user.credits == 135  # 55 + 80

    # Repeat allocation for same cycle (idempotent safeguard)
    allocated_again = CreditService.allocate_monthly_credits(user, "starter", "2026-11", credit_db)
    assert allocated_again is False
    assert user.credits == 135
