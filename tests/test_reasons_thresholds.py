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
    # Force average of model and rule to 0.30 -> REVIEW (since < approve is only for strict <0.30)
    monkeypatch.setattr(main, "rule_based_score", lambda *a, **k: 0.30)
    main.model = DummyModel(0.30)
    c = TestClient(main.app)
    j = c.post("/score", json=base_payload()).json()
    assert j["risk_score"] >= 0.30 and j["decision"] == "REVIEW"

def test_decision_decline_exact_boundary(monkeypatch):
    monkeypatch.setattr(main, "rule_based_score", lambda *a, **k: 0.70)
    main.model = DummyModel(0.70)
    c = TestClient(main.app)
    j = c.post("/score", json=base_payload(amount=6000.0)).json()
    assert j["risk_score"] >= 0.70 and j["decision"] == "DECLINE"

def test_reasons_compose_and_limit(monkeypatch):
    # High merchant risk + high velocities -> multiple reasons, should be truncated to 3
    monkeypatch.setattr(main, "fetch_merchant_risk", lambda eng, m: 0.15)
    monkeypatch.setattr(main, "fetch_velocity", lambda eng, e, ip, c: (5,6,7))
    main.model = DummyModel(0.9)
    c = TestClient(main.app)
    j = c.post("/score", json=base_payload(amount=9000.0, merchant_id="m_high", ip="187.190.10.10", email="fraud@x.com", card_hash="card_risky")).json()
    assert j["decision"] == "DECLINE"
    assert len(j["reasons"]) <= 3
    # Ensure at least one velocity reason is present
    assert any(r.startswith("velocity_") for r in j["reasons"])
