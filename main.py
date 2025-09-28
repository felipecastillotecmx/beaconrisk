import os, math
from typing import Optional, Literal, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import make_classification
import numpy as np
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "cnp_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "cnp_pass")
MYSQL_DB = os.getenv("MYSQL_DB", "cnpdb")

def get_engine() -> Engine:
    url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    return create_engine(url, pool_pre_ping=True, pool_recycle=180, pool_size=5, max_overflow=5)

engine = get_engine()

app = FastAPI(title="CNP Risk Scorer — PoC MySQL", version="0.3.0")

def build_model(seed: int = 42) -> Pipeline:
    X, y = make_classification(
        n_samples=3000, n_features=6, n_informative=4, weights=[0.9, 0.1], random_state=seed
    )
    pipe = Pipeline([("scaler", StandardScaler()),
                     ("clf", LogisticRegression(max_iter=1000, class_weight={0:1.0, 1:5.0}, random_state=seed))])
    pipe.fit(X, y)
    return pipe

model = build_model()

class ScoreRequest(BaseModel):
    merchant_id: str
    amount: float = Field(..., ge=0.0)
    currency: str = Field(..., min_length=3, max_length=3)
    country: str = Field(..., min_length=2, max_length=2)
    email: str
    ip: str
    device_id: str
    card_bin: str = Field(..., min_length=6, max_length=8)
    card_hash: str
    timestamp: Optional[str] = None

class ScoreResponse(BaseModel):
    risk_score: float
    decision: Literal["APPROVE","REVIEW","DECLINE"]
    thresholds: dict
    reasons: List[str]

def fetch_merchant_risk(eng: Engine, merchant_id: str) -> float:
    q = text("SELECT fraud_rate FROM merchants WHERE id = :m")
    with eng.connect() as conn:
        row = conn.execute(q, {"m": merchant_id}).fetchone()
        if not row:
            return 0.05
        return float(row[0])

def fetch_velocity(eng: Engine, email: str, ip: str, card_hash: str):
    with eng.connect() as conn:
        v_email = conn.execute(text('''
            SELECT COUNT(*) FROM transactions
            WHERE email = :e AND ts >= NOW() - INTERVAL 1 HOUR
        '''), {"e": email}).scalar()
        v_ip = conn.execute(text('''
            SELECT COUNT(*) FROM transactions
            WHERE ip = :ip AND ts >= NOW() - INTERVAL 1 HOUR
        '''), {"ip": ip}).scalar()
        v_card = conn.execute(text('''
            SELECT COUNT(*) FROM transactions
            WHERE card_hash = :c AND ts >= NOW() - INTERVAL 24 HOUR
        '''), {"c": card_hash}).scalar()
    return int(v_email or 0), int(v_ip or 0), int(v_card or 0)

def rule_based_score(amount: float, merchant_risk: float, vel_email: int, vel_ip: int, vel_card: int) -> float:
    amt_log = math.log1p(amount)
    base = 0.15 + 0.5*merchant_risk + 0.05*amt_log
    adj = 0.0
    if vel_email >= 3: adj += 0.20
    if vel_ip >= 5: adj += 0.10
    if vel_card >= 3: adj += 0.20
    if amount > 5000: adj += 0.10
    return max(0.0, min(1.0, base + adj))

def featurize_for_model(amount: float, merchant_risk: float, vel_email: int, vel_ip: int, vel_card: int):
    amt_log = math.log1p(amount)
    return np.array([[amt_log, merchant_risk, float(vel_email), float(vel_ip), float(vel_card), 1.0]], dtype=float)

def insert_txn(eng: Engine, req: ScoreRequest, decision: str, risk_score: float):
    q = text('''
        INSERT INTO transactions (ts, merchant_id, amount, currency, country, email, ip, device_id, card_bin, card_hash, decision, risk_score)
        VALUES (NOW(), :merchant_id, :amount, :currency, :country, :email, :ip, :device_id, :card_bin, :card_hash, :decision, :risk_score)
    ''')
    with eng.begin() as conn:
        conn.execute(q, {
            "merchant_id": req.merchant_id,
            "amount": req.amount,
            "currency": req.currency.upper(),
            "country": req.country.upper(),
            "email": req.email,
            "ip": req.ip,
            "device_id": req.device_id,
            "card_bin": req.card_bin,
            "card_hash": req.card_hash,
            "decision": decision,
            "risk_score": round(risk_score, 4)
        })

@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db = "ok"
    except Exception as e:
        db = f"error: {e}"
    return {"status":"ok", "db": db}

@app.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest):
    try:
        merchant_risk = fetch_merchant_risk(engine, req.merchant_id)
        vel_email, vel_ip, vel_card = fetch_velocity(engine, req.email, req.ip, req.card_hash)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    # --- Green lane (Solución A para PoC/Demo) ---
    SAFE_APPROVE = os.getenv("SAFE_APPROVE", "1") == "1"
    if SAFE_APPROVE and merchant_risk <= 0.02 and req.amount <= 200        and vel_email == 0 and vel_ip == 0 and vel_card == 0:
        decision = "APPROVE"
        prob = 0.25
        thresholds = {"approve": 0.30, "review": 0.70}
        reasons = ["safe_lane", "low_risk_profile"]
        try:
            insert_txn(engine, req, decision, prob)
        except Exception:
            pass
        return ScoreResponse(risk_score=round(prob,4), decision=decision, thresholds=thresholds, reasons=reasons)

    # Cálculo normal
    r_score = rule_based_score(req.amount, merchant_risk, vel_email, vel_ip, vel_card)
    X = featurize_for_model(req.amount, merchant_risk, vel_email, vel_ip, vel_card)
    m_prob = float(model.predict_proba(X)[0,1])
    prob = max(0.0, min(1.0, 0.5*m_prob + 0.5*r_score))

    thresholds = {"approve": 0.30, "review": 0.70}
    if prob < thresholds["approve"]:
        decision = "APPROVE"
    elif prob < thresholds["review"]:
        decision = "REVIEW"
    else:
        decision = "DECLINE"

    reasons = []
    if merchant_risk >= 0.12: reasons.append("merchant_high_risk")
    if req.amount > 5000: reasons.append("high_amount")
    if vel_email >= 3: reasons.append("velocity_email_1h")
    if vel_ip >= 5: reasons.append("velocity_ip_1h")
    if vel_card >= 3: reasons.append("velocity_card_24h")
    if not reasons: reasons = ["low_risk_profile"]

    try:
        insert_txn(engine, req, decision, prob)
    except Exception:
        pass

    return ScoreResponse(risk_score=round(prob,4), decision=decision, thresholds=thresholds, reasons=reasons[:3])
