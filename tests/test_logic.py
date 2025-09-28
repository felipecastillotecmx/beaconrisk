import numpy as np
from fastapi.testclient import TestClient
import main

class DummyModel:
    def __init__(self, p): self.p = p
    def predict_proba(self, X): return np.array([[1.0-self.p, self.p]])

def test_thresholds_and_boundaries(monkeypatch):
    monkeypatch.setattr(main, "fetch_merchant_risk", lambda eng, m: 0.05)
    monkeypatch.setattr(main, "fetch_velocity", lambda eng, e, ip, c: (0,0,0))
    main.model = DummyModel(0.30)
    c = TestClient(main.app)
    j = c.post("/score", json={
        "merchant_id":"m_mid","amount":1.0,"currency":"MXN","country":"MX",
        "email":"e@x.com","ip":"1.1.1.1","device_id":"d","card_bin":"520157","card_hash":"h"
    }).json()
    assert j["risk_score"] >= 0.30
    assert j["decision"] in {"REVIEW","DECLINE"}  # en el borde debe ser al menos REVIEW
