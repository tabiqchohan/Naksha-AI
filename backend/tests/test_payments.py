import hashlib
import hmac
import json


def test_pricing_and_dev_purchase_flow(client, user):
    pricing = client.get("/api/v1/payments/pricing")
    assert pricing.status_code == 200
    assert "10" in pricing.json()["packs"] or 10 in pricing.json()["packs"]

    before = client.get("/api/v1/auth/me", headers=user["headers"]).json()["credits"]

    purchase = client.post(
        "/api/v1/payments/purchase",
        json={"credits": 10, "payment_method": "dev"},
        headers=user["headers"],
    )
    assert purchase.status_code == 200
    txn = purchase.json()["transaction_id"]
    assert txn

    verified = client.post(f"/api/v1/payments/verify/{txn}", headers=user["headers"])
    assert verified.status_code == 200
    assert verified.json()["success"] is True

    after = client.get("/api/v1/auth/me", headers=user["headers"]).json()["credits"]
    assert after == before + 10

    again = client.post(f"/api/v1/payments/verify/{txn}", headers=user["headers"])
    assert again.status_code == 200
    assert client.get("/api/v1/auth/me", headers=user["headers"]).json()["credits"] == after

    history = client.get("/api/v1/payments/history", headers=user["headers"])
    assert history.status_code == 200
    assert any(item["transaction_id"] == txn for item in history.json()["transactions"])


def test_jazzcash_webhook_signature(client, user, monkeypatch):
    monkeypatch.setenv("JAZZCASH_HASH_KEY", "test-secret")
    purchase = client.post(
        "/api/v1/payments/purchase",
        json={"credits": 10, "payment_method": "jazzcash"},
        headers=user["headers"],
    )
    txn = purchase.json()["transaction_id"]

    payload = json.dumps({"pp_TxnRefNo": txn, "pp_ResponseCode": "000"}).encode()
    signature = hmac.new(b"test-secret", payload, hashlib.sha256).hexdigest()

    invalid = client.post(
        "/api/v1/payments/webhook/jazzcash",
        content=payload,
        headers={"x-jazzcash-signature": "bad"},
    )
    assert invalid.status_code == 401

    valid = client.post(
        "/api/v1/payments/webhook/jazzcash",
        content=payload,
        headers={"x-jazzcash-signature": signature},
    )
    assert valid.status_code == 200
    assert valid.json()["processed"] is True


def test_invalid_credit_pack(client, user):
    response = client.post(
        "/api/v1/payments/purchase",
        json={"credits": 7, "payment_method": "dev"},
        headers=user["headers"],
    )
    assert response.status_code == 400
