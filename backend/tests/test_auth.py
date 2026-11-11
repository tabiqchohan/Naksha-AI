import uuid


def test_health_and_security_headers(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_register_verify_login_and_me(client):
    username = f"auth{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "pass12345"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["credits"] == 3
    assert data["is_verified"] is False
    assert data["verification_token"]

    verified = client.post(
        "/api/v1/auth/email-verification/confirm",
        json={"token": data["verification_token"]},
    )
    assert verified.status_code == 200

    login = client.post("/api/v1/auth/login", data={"username": email, "password": "pass12345"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert login.json()["user"]["is_verified"] is True

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_duplicate_registration_and_weak_password(client, user):
    duplicate = client.post(
        "/api/v1/auth/register",
        json={"email": user["email"], "username": f"other{uuid.uuid4().hex[:5]}", "password": "pass12345"},
    )
    assert duplicate.status_code == 400

    weak = client.post(
        "/api/v1/auth/register",
        json={"email": f"weak{uuid.uuid4().hex[:6]}@example.com", "username": f"weak{uuid.uuid4().hex[:6]}", "password": "short"},
    )
    assert weak.status_code == 422


def test_password_reset_flow(client, user):
    requested = client.post("/api/v1/auth/password-reset/request", json={"email": user["email"]})
    assert requested.status_code == 200
    token = requested.json()["token"]
    assert token

    confirmed = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "newpass123"},
    )
    assert confirmed.status_code == 200
    assert client.post("/api/v1/auth/login", data={"username": user["username"], "password": user["password"]}).status_code == 401
    assert client.post("/api/v1/auth/login", data={"username": user["username"], "password": "newpass123"}).status_code == 200


def test_email_verification_request_authenticated(client, user):
    response = client.post("/api/v1/auth/email-verification/request", headers=user["headers"])
    assert response.status_code == 200
    assert response.json()["token"]
