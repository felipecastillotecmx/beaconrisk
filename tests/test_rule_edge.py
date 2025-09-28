import main

def test_rule_based_score_clamps_upper():
    s = main.rule_based_score(amount=1e7, merchant_risk=0.99, vel_email=99, vel_ip=99, vel_card=99)
    assert 0.0 <= s <= 1.0 and s == 1.0

def test_rule_based_score_clamps_lower():
    s = main.rule_based_score(amount=0.0, merchant_risk=0.0, vel_email=0, vel_ip=0, vel_card=0)
    assert 0.0 <= s <= 1.0
