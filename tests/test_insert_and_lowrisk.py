from fastapi.testclient import TestClient
import main

def test_insert_called_and_lowrisk_reason(monkeypatch):
    calls = []
    monkeypatch.setattr(main, "insert_txn", lambda *a, **k: calls.append(("ok", a[1].email)))
    monkeypatch.setattr(main, "fetch_merchant_risk", lambda eng, m: 0.01)
    monkeypatch.setattr(main, "fetch_velocity", lambda eng, e, ip, c: (0,0,0))
    c = TestClient(main.app)
    j = c.post("/score", json={
        "merchant_id":"m_low","amount":50.0,"currency":"MXN","country":"MX",
        "email":"benign@x.com","ip":"10.0.0.10","device_id":"d","card_bin":"520157","card_hash":"card_a1"
    }).json()
    assert "low_risk_profile" in j["reasons"]
    assert calls and calls[0][1] == "benign@x.com"
