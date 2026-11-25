import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.models.user_models import User
from app.models.monetization_models import PlanCatalog, AdminAuditLog
from app.auth.auth_utils import get_password_hash


@pytest.fixture(autouse=True)
def setup_admin_test_data():
    db = SessionLocal()
    try:
        # Ensure plan catalog exists
        if not db.query(PlanCatalog).first():
            plans = [
                PlanCatalog(slug="free", name="Free", price_pkr=Decimal("0.00"), price_usd=Decimal("0.00"), credits_monthly=10),
                PlanCatalog(slug="starter", name="Starter", price_pkr=Decimal("1499.00"), price_usd=Decimal("7.00"), credits_monthly=80),
                PlanCatalog(slug="pro", name="Pro", price_pkr=Decimal("4499.00"), price_usd=Decimal("19.00"), credits_monthly=300),
            ]
            for p in plans:
                db.add(p)
            db.commit()
    finally:
        db.close()
    yield


def get_auth_headers(client: TestClient, email: str, password: str, is_admin: bool = False):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                username=email.split("@")[0],
                hashed_password=get_password_hash(password),
                is_active=True,
                is_admin=is_admin,
                credits=100
            )
            db.add(user)
            db.commit()
        else:
            user.is_admin = is_admin
            db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_access_forbidden_for_regular_user(client):
    headers = get_auth_headers(client, "regular_user_m6@example.com", "password123", is_admin=False)
    response = client.get("/api/v1/admin/dashboard", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Administrator privileges required"


def test_admin_dashboard_success(client):
    headers = get_auth_headers(client, "admin_user_m6@example.com", "adminpass123", is_admin=True)
    response = client.get("/api/v1/admin/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert data["metrics"]["total_users"] >= 1


def test_admin_plan_management(client):
    headers = get_auth_headers(client, "admin_plan_m6@example.com", "adminpass123", is_admin=True)

    # List plans
    resp = client.get("/api/v1/admin/plans", headers=headers)
    assert resp.status_code == 200
    plans = resp.json()["plans"]
    assert len(plans) >= 3

    # Update plan price & credits
    update_resp = client.put(
        "/api/v1/admin/plans/starter",
        json={"price_pkr": 1699.00, "credits_monthly": 90},
        headers=headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["success"] is True
    assert update_resp.json()["plan"]["price_pkr"] == 1699.00
    assert update_resp.json()["plan"]["credits_monthly"] == 90


def test_admin_user_management_and_credit_adjustment(client):
    admin_headers = get_auth_headers(client, "admin_mgmt_m6@example.com", "adminpass123", is_admin=True)

    # Create a target user
    db = SessionLocal()
    target = User(
        email="target_m6@example.com",
        username="targetuser_m6",
        hashed_password=get_password_hash("pass123"),
        credits=50
    )
    db.add(target)
    db.commit()
    target_id = target.id
    db.close()

    # List users
    users_resp = client.get("/api/v1/admin/users?search=target_m6", headers=admin_headers)
    assert users_resp.status_code == 200
    assert users_resp.json()["total"] >= 1

    # Inspect user credits history
    credits_resp = client.get(f"/api/v1/admin/users/{target_id}/credits", headers=admin_headers)
    assert credits_resp.status_code == 200
    assert credits_resp.json()["credits"] == 50

    # Adjust user credits (grant 50)
    adj_resp = client.post(
        f"/api/v1/admin/users/{target_id}/adjust-credits",
        json={
            "amount": 50,
            "reason": "Promotional bonus grant for M6 launch",
            "reference_id": "promo_m6_test_001"
        },
        headers=admin_headers
    )
    assert adj_resp.status_code == 200
    assert adj_resp.json()["success"] is True
    assert adj_resp.json()["new_credits"] == 100

    # Verify audit logs created
    audit_resp = client.get("/api/v1/admin/audit-logs", headers=admin_headers)
    assert audit_resp.status_code == 200
    logs = audit_resp.json()["audit_logs"]
    assert len(logs) >= 1


def test_admin_audit_log_immutability():
    db = SessionLocal()
    admin_user = db.query(User).filter_by(is_admin=True).first()
    if not admin_user:
        admin_user = User(email="audadmin_m6@example.com", username="audadmin_m6", hashed_password="pw", is_admin=True)
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

    log = AdminAuditLog(
        admin_user_id=admin_user.id,
        action_type="TEST_ACTION",
        target_resource="test",
        reason="Testing immutability",
        request_id="req_imm_m6_001"
    )
    db.add(log)
    db.commit()

    # Attempt update
    log.reason = "Modified reason"
    with pytest.raises(RuntimeError, match="strictly immutable"):
        db.commit()
    db.rollback()

    # Attempt delete
    db.delete(log)
    with pytest.raises(RuntimeError, match="strictly immutable"):
        db.commit()
    db.rollback()
    db.close()
