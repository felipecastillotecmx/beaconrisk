import main

def test_health_db_error(monkeypatch):
    class BoomCtx:
        def __enter__(self): raise Exception("db down")
        def __exit__(self, exc_type, exc, tb): return False
    monkeypatch.setattr(main.engine, "connect", lambda: BoomCtx())
    r = main.health()
    assert r["status"] == "ok"
    assert "error:" in r["db"]
