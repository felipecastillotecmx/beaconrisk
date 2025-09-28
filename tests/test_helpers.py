import main

class FakeConn:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    def execute(self, q, params=None):
        class R:
            def __init__(self): self._row = None
            def fetchone(self): return self._row
            def scalar(self): return 2
        return R()

class FakeEngine:
    def connect(self): return FakeConn()

def test_fetch_merchant_risk_default():
    assert main.fetch_merchant_risk(FakeEngine(), "missing") == 0.05

def test_fetch_velocity_counts():
    assert main.fetch_velocity(FakeEngine(), "e@x.com", "1.1.1.1", "h") == (2,2,2)
