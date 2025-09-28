import types
import main

def test_health_db_error(monkeypatch):
    # Force engine.connect() to raise to cover error branch
    def boom():
        raise Exception("db down")
    monkeypatch.setattr(main.engine, "connect", lambda: boom())
    r = main.health()
    assert r["status"] == "ok"
    assert "error:" in r["db"]
