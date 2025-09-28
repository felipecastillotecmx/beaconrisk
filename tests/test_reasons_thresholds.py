import numpy as np
from fastapi.testclient import TestClient
import main

class DummyModel:
    def __init__(self, p): self.p = p
    def predict_proba(self, X):
        return np.array([[1.0 - self.p, self.p]])

def base_payload(**kw):
    p = {
        "merchant_id": "m_low",
        "amount": 100.0,
        "currency": "MXN",
        "country": "MX",
        "email": "u@x.com",
        "ip": "1.1.1.1",
        "device_id": "d",
        "card_bin": "520157",
        "card_hash": "h"
    }
    p.update(kw)
    return p

def test_decision_approve_exact_boundary(monkeypatch):
    # Fuerza average 0.30 y desactiva green lane asegurando merchant_risk>0.02 o vel>0
    monkeypatch.setattr(main, "fetch_merchant_risk", lambda eng, m: 0.05)
    monkeypatch.setattr(main, "fetch_velocity", lambda eng, e, ip, c: (1,0,0))  # evita green lane
    monkeypatch.setattr(main, "rule_based_score", lambda *a, **k: 0.30)
    main.model = DummyModel(0.30)
    c = TestClient(main.app)
    j = c.post("/score", json=base_payload()).json()
    assert j["risk_score"] >= 0.30
    assert j["decision"] == "REVIEW"

def test_decision_decline_exact_boundary(monkeypatch):
    monkeypatch.setattr(main, "fetch_merchant_risk", lambda eng, m: 0.05)
    monkeypatch.setattr(main, "fetch_velocity", lambda eng, e, ip, c: (1,0,0))  # evita green lane
    monkeypatch.setattr(main, "rule_based_score", lambda *a, **k: 0.70)
    main.model = DummyModel(0.70)
    c = TestClient(main.app)
    j = c.post("/score", json=base_payload(amount=6000.0)).json()  # amount alto también evita green lane
    assert j["risk_score"] >= 0.70
    assert j["decision"] == "DECLINE"

def test_reasons_compose_and_limit(monkeypatch):
    monkeypatch.setattr(main, "fetch_merchant_risk", lambda eng, m: 0.15)
    monkeypatch.setattr(main, "fetch_velocity", lambda eng, e, ip, c: (5,6,7))
    main.model = DummyModel(0.9)
    c = TestClient(main.app)
    j = c.post("/score", json=base_payload(amount=9000.0, merchant_id="m_high", ip="187.190.10.10", email="fraud@x.com", card_hash="card_risky")).json()
    assert j["decision"] == "DECLINE"
    assert len(j["reasons"]) <= 3
    assert any(r.startswith("velocity_") for r in j["reasons"])
