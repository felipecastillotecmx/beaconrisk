from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

def test_score_contract_approve(monkeypatch):
    monkeypatch.setattr(main, "fetch_merchant_risk", lambda eng, m: 0.01)
    monkeypatch.setattr(main, "fetch_velocity", lambda eng, e, ip, c: (0,0,0))
    j = client.post("/score", json={
        "merchant_id": "m_low", "amount": 120.0, "currency": "MXN", "country": "MX",
        "email":"a1@example.com", "ip":"10.0.0.10", "device_id":"dev_a1", "card_bin":"520157", "card_hash":"card_a1"
    }).json()
    assert j["decision"] in {"APPROVE","REVIEW"}
    assert "thresholds" in j and "reasons" in j

def test_score_contract_decline(monkeypatch):
    monkeypatch.setattr(main, "fetch_merchant_risk", lambda eng, m: 0.15)
    monkeypatch.setattr(main, "fetch_velocity", lambda eng, e, ip, c: (4,6,5))
    j = client.post("/score", json={
        "merchant_id":"m_high","amount":8000.0,"currency":"MXN","country":"MX",
        "email":"f@x.com","ip":"187.190.10.10","device_id":"d","card_bin":"520157","card_hash":"card_risky"
    }).json()
    assert j["decision"] == "DECLINE"
