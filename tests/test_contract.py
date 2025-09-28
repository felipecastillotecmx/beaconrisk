from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

def test_health_includes_status():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_score_contract_approve(monkeypatch):
    # Mock DB-dependent helpers to avoid hitting MySQL
    monkeypatch.setattr(main, "fetch_merchant_risk", lambda eng, m: 0.01)   # low risk
    monkeypatch.setattr(main, "fetch_velocity", lambda eng, e, ip, c: (0,0,0))
    payload = {
        "merchant_id": "m_low",
        "amount": 120.0,
        "currency": "MXN",
        "country": "MX",
        "email": "a1@example.com",
        "ip": "10.0.0.10",
        "device_id": "dev_a1",
        "card_bin": "520157",
        "card_hash": "card_a1"
    }
    r = client.post("/score", json=payload)
    assert r.status_code == 200
    j = r.json()
    assert 0.0 <= j["risk_score"] <= 1.0
    assert j["decision"] == "APPROVE"
    assert "thresholds" in j and "reasons" in j

def test_score_contract_review(monkeypatch):
    monkeypatch.setattr(main, "fetch_merchant_risk", lambda eng, m: 0.08)   # mid risk
    monkeypatch.setattr(main, "fetch_velocity", lambda eng, e, ip, c: (1,1,0))
    payload = {
        "merchant_id": "m_mid",
        "amount": 3000.0,
        "currency": "MXN",
        "country": "MX",
        "email": "repeat@example.com",
        "ip": "187.190.20.20",
        "device_id": "dev_y2",
        "card_bin": "520157",
        "card_hash": "card_mid"
    }
    r = client.post("/score", json=payload)
    assert r.status_code == 200
    assert r.json()["decision"] == "REVIEW"

def test_score_contract_decline(monkeypatch):
    monkeypatch.setattr(main, "fetch_merchant_risk", lambda eng, m: 0.15)   # high risk
    monkeypatch.setattr(main, "fetch_velocity", lambda eng, e, ip, c: (4,6,5))  # high velocity
    payload = {
        "merchant_id": "m_high",
        "amount": 8000.0,
        "currency": "MXN",
        "country": "MX",
        "email": "fraudster@example.com",
        "ip": "187.190.10.10",
        "device_id": "dev_x9",
        "card_bin": "520157",
        "card_hash": "card_risky"
    }
    r = client.post("/score", json=payload)
    assert r.status_code == 200
    assert r.json()["decision"] == "DECLINE"
