import os, uuid, pymysql, pytest
from fastapi.testclient import TestClient
import main

pytestmark = pytest.mark.integration

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "cnp_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "cnp_pass")
MYSQL_DB = os.getenv("MYSQL_DB", "cnpdb")

def _conn():
    return pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB, autocommit=True)

def test_health_db_ok():
    r = main.health()
    assert r["status"] == "ok"
    assert r["db"] == "ok"

def test_score_inserts_and_decides():
    c = TestClient(main.app)
    email = f"approve_it_{uuid.uuid4().hex[:8]}@example.com"
    ip = f"10.200.{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}"
    card = f"card_it_{uuid.uuid4().hex[:8]}"
    payload = {
        "merchant_id": "m_low",
        "amount": 150.0,
        "currency": "MXN",
        "country": "MX",
        "email": email,
        "ip": ip,
        "device_id": "dev_it",
        "card_bin": "520157",
        "card_hash": card
    }
    with _conn() as cn:
        with cn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM transactions")
            before = cur.fetchone()[0]
    j = c.post("/score", json=payload).json()
    assert j["decision"] == "APPROVE"
    assert j["risk_score"] < j["thresholds"]["approve"]
    with _conn() as cn:
        with cn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM transactions")
            after = cur.fetchone()[0]
            assert after == before + 1

def test_decline_with_seeded_high_risk():
    c = TestClient(main.app)
    payload = {
        "merchant_id": "m_high",
        "amount": 8000.0,
        "currency": "MXN",
        "country": "MX",
        "email": "fraudster@example.com",
        "ip": "187.190.10.10",
        "device_id": "dev_x9",
        "card_bin": "520157",
        "card_hash": "card_risky"
    }
    j = c.post("/score", json=payload).json()
    assert j["decision"] == "DECLINE"
