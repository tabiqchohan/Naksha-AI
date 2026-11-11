import os
import pathlib
import uuid

BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[1]
TEST_DB = BACKEND_ROOT / "_pytest.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["RATE_LIMIT_AUTH_PER_MINUTE"] = "1000"
os.environ["AUTH_DEBUG_TOKENS"] = "true"
os.environ["ALLOW_MANUAL_PAYMENT_VERIFY"] = "true"
os.environ["ENVIRONMENT"] = "test"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest.fixture
def user(client):
    username = f"user{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "pass12345"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    token = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    ).json()["access_token"]
    return {
        "username": username,
        "email": email,
        "password": password,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "register": response.json(),
    }


@pytest.fixture
def plan_factory(client):
    def make(headers, **overrides):
        payload = {
            "prompt": "5 marla modern house 3 bed",
            "plot_width": 25,
            "plot_length": 45,
            "building_type": "house",
            "floors": 1,
            "bedrooms": 3,
            "bathrooms": 2,
            "bylaws_pack": "pakistan_generic",
            "rate_per_sqft_pkr": 3456,
        }
        payload.update(overrides)
        return client.post("/api/v1/plans/generate", json=payload, headers=headers)

    return make
