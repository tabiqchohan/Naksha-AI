import hashlib
import hmac
import json
import pytest


def test_local_subscription_checkout_and_status(client, user):
    # Test local subscription checkout for JazzCash
    res = client.post(
        "/api/v1/payments/subscription/local-checkout",
        json={"plan_slug": "starter", "payment_method": "jazzcash"},
        headers=user["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "transaction_id" in data
    assert data["amount_pkr"] == 1499

    txn_id = data["transaction_id"]

    # Test transaction status inquiry
    status_res = client.get(
        f"/api/v1/payments/transaction/{txn_id}",
        headers=user["headers"],
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "pending"
    assert status_res.json()["payment_method"] == "jazzcash"


def test_jazzcash_subscription_webhook_flow(client, user, monkeypatch):
    monkeypatch.setenv("JAZZCASH_HASH_KEY", "test-jc-secret")

    # Initiate local subscription checkout for Pro plan via JazzCash
    res = client.post(
        "/api/v1/payments/subscription/local-checkout",
        json={"plan_slug": "pro", "payment_method": "jazzcash"},
        headers=user["headers"],
    )
    assert res.status_code == 200
    txn_id = res.json()["transaction_id"]

    # Build valid webhook payload & signature
    payload = json.dumps({"pp_TxnRefNo": txn_id, "pp_ResponseCode": "000"}).encode()
    signature = hmac.new(b"test-jc-secret", payload, hashlib.sha256).hexdigest()

    # Test invalid signature rejection
    invalid_res = client.post(
        "/api/v1/payments/webhook/jazzcash",
        content=payload,
        headers={"x-jazzcash-signature": "bad_sig"},
    )
    assert invalid_res.status_code == 401

    # Test valid signature processing
    valid_res = client.post(
        "/api/v1/payments/webhook/jazzcash",
        content=payload,
        headers={"x-jazzcash-signature": signature},
    )
    assert valid_res.status_code == 200
    assert valid_res.json()["processed"] is True

    # Verify subscription is now active and credits added
    sub_res = client.get(
        "/api/v1/payments/subscription/status",
        headers=user["headers"],
    )
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["status"] == "active"
    assert sub_data["plan_slug"] == "pro"
    assert sub_data["credits"] >= 300


def test_easypaisa_subscription_webhook_flow(client, user, monkeypatch):
    monkeypatch.setenv("EASYPAISA_HASH_KEY", "test-ep-secret")

    # Initiate local subscription checkout for Architect plan via Easypaisa
    res = client.post(
        "/api/v1/payments/subscription/local-checkout",
        json={"plan_slug": "architect", "payment_method": "easypaisa"},
        headers=user["headers"],
    )
    assert res.status_code == 200
    txn_id = res.json()["transaction_id"]

    # Build valid webhook payload & signature
    payload = json.dumps({"orderRefNum": txn_id, "transactionStatus": "success"}).encode()
    signature = hmac.new(b"test-ep-secret", payload, hashlib.sha256).hexdigest()

    valid_res = client.post(
        "/api/v1/payments/webhook/easypaisa",
        content=payload,
        headers={"x-easypaisa-signature": signature},
    )
    assert valid_res.status_code == 200
    assert valid_res.json()["processed"] is True

    # Verify subscription active and credits added
    sub_res = client.get(
        "/api/v1/payments/subscription/status",
        headers=user["headers"],
    )
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "active"
    assert sub_res.json()["plan_slug"] == "architect"


def test_local_subscription_manual_renewal(client, user, monkeypatch):
    monkeypatch.setenv("JAZZCASH_HASH_KEY", "test-jc-secret")

    # First checkout & activate starter sub
    res = client.post(
        "/api/v1/payments/subscription/local-checkout",
        json={"plan_slug": "starter", "payment_method": "jazzcash"},
        headers=user["headers"],
    )
    txn_id = res.json()["transaction_id"]
    payload = json.dumps({"pp_TxnRefNo": txn_id, "pp_ResponseCode": "000"}).encode()
    signature = hmac.new(b"test-jc-secret", payload, hashlib.sha256).hexdigest()
    client.post("/api/v1/payments/webhook/jazzcash", content=payload, headers={"x-jazzcash-signature": signature})

    # Now request manual renewal
    renew_res = client.post(
        "/api/v1/payments/subscription/local-renew",
        headers=user["headers"],
    )
    assert renew_res.status_code == 200
    renew_data = renew_res.json()
    assert renew_data["success"] is True
    assert "transaction_id" in renew_data
    assert renew_data["amount_pkr"] == 1499
