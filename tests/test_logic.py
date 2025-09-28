import main

def test_rule_based_score_monotonic():
    # Higher amount and higher merchant risk should not reduce score
    low = main.rule_based_score(amount=100, merchant_risk=0.01, vel_email=0, vel_ip=0, vel_card=0)
    high = main.rule_based_score(amount=8000, merchant_risk=0.15, vel_email=4, vel_ip=6, vel_card=5)
    assert high >= low

def test_thresholds_mapping(monkeypatch):
    monkeypatch.setattr(main, "fetch_merchant_risk", lambda eng, m: 0.05)
    monkeypatch.setattr(main, "fetch_velocity", lambda eng, e, ip, c: (0,0,0))
    app = main.app
    from fastapi.testclient import TestClient
    c = TestClient(app)
    p = {"merchant_id": "m_mid","amount": 1.0,"currency": "MXN","country": "MX","email": "e@x.com","ip":"1.1.1.1","device_id":"d","card_bin":"520157","card_hash":"h"}
    r = c.post("/score", json=p)
    j = r.json()
    # Decision must be consistent with thresholds
    t = j["thresholds"]
    score = j["risk_score"]
    if score < t["approve"]:
        assert j["decision"] == "APPROVE"
    elif score < t["review"]:
        assert j["decision"] == "REVIEW"
    else:
        assert j["decision"] == "DECLINE"
