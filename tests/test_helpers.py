import main

class FakeConn:
    def __init__(self, result=None, scalar_value=0):
        self._result = result
        self._scalar = scalar_value
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    def execute(self, q, params=None):
        class R:
            def __init__(self, row, scalar_value):
                self._row = row; self._scalar = scalar_value
            def fetchone(self): return self._row
            def scalar(self): return self._scalar
        # If SELECT fraud_rate ... expect .fetchone(); otherwise .scalar()
        sql = str(q)
        if "fraud_rate" in sql:
            return R(None, self._scalar)  # no row found
        return R(None, self._scalar)

class FakeEngine:
    def connect(self):
        return FakeConn(scalar_value=2)

def test_fetch_merchant_risk_default():
    # No row -> default 0.05
    assert main.fetch_merchant_risk(FakeEngine(), "missing") == 0.05

def test_fetch_velocity_counts():
    # scalar_value=2 -> each COUNT(*) returns 2
    v = main.fetch_velocity(FakeEngine(), "e@x.com", "1.1.1.1", "h")
    assert v == (2, 2, 2)
