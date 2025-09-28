import numpy as np, math
from fastapi.testclient import TestClient
import main

class DummyModel:
    def __init__(self, p): self.p = p
    def predict_proba(self, X): return np.array([[1.0-self.p, self.p]])

def test_thresholds_and_boundaries(monkeypatch):
    # Simula modelo=0.30 y entorno "limpio" (pero SIN green lane)
    monkeypatch.setattr(main, "fetch_merchant_risk", lambda eng, m: 0.05)   # >0.02 => no green lane
    monkeypatch.setattr(main, "fetch_velocity", lambda eng, e, ip, c: (0,0,0))
    main.model = DummyModel(0.30)
    c = TestClient(main.app)
    j = c.post("/score", json={
        "merchant_id":"m_mid","amount":1.0,"currency":"MXN","country":"MX",
        "email":"e@x.com","ip":"1.1.1.1","device_id":"d","card_bin":"520157","card_hash":"h"
    }).json()
    # r_score real que usa la API con amount=1.0 y merchant_risk=0.05
    amt_log = math.log1p(1.0)
    r_score = max(0.0, min(1.0, 0.15 + 0.5*0.05 + 0.05*amt_log))
    expected = max(0.0, min(1.0, 0.5*0.30 + 0.5*r_score))
    assert abs(j["risk_score"] - expected) < 1e-6
    # Mapea correctamente umbrales
    t = j["thresholds"]
    if j["risk_score"] < t["approve"]:
        assert j["decision"] == "APPROVE"
    elif j["risk_score"] < t["review"]:
        assert j["decision"] == "REVIEW"
    else:
        assert j["decision"] == "DECLINE"
