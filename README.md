# CNP Risk Scorer — PoC (FastAPI + scikit-learn + MySQL)

**Endpoints:** `/health`, `/score` (con green-lane activable con `SAFE_APPROVE=1`).  
**Decisión:** `APPROVE < 0.30` · `0.30–0.69 REVIEW` · `≥ 0.70 DECLINE`.

## 1) Levantar MySQL con datos de ejemplo
```bash
docker compose up -d
```
DB: `cnpdb`  |  Usuario: `cnp_user`  |  Password: `cnp_pass`

## 2) Ejecutar API
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edita si cambiaste credenciales
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 3) Cuerpos de ejemplo (Postman)
### A) Aprobación (green-lane)
```json
{
  "merchant_id": "m_low",
  "amount": 150.0,
  "currency": "MXN",
  "country": "MX",
  "email": "approve_demo_001@example.com",
  "ip": "10.77.66.55",
  "device_id": "dev_approve_001",
  "card_bin": "520157",
  "card_hash": "card_approve_001"
}
```
### B) Revisión
```json
{
  "merchant_id": "m_mid",
  "amount": 3000.0,
  "currency": "MXN",
  "country": "MX",
  "email": "repeat@example.com",
  "ip": "187.190.20.20",
  "device_id": "dev_y2",
  "card_bin": "520157",
  "card_hash": "card_mid"
}
```
### C) Rechazo
```json
{
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
```

## 4) CI/CD (GitHub Actions) + SonarQube
- Job **tests**: unit tests (excluye integration), cobertura y *coverage gate* ≥ 80%.
- Job **it-mysql**: pruebas de integración con servicio MySQL + `db/init.sql`.
- Job **sonarqube**: escaneo y **Quality Gate** (depende de tests + integration).

Secrets requeridos:
- `SONAR_HOST_URL` — URL SonarQube.
- `SONAR_TOKEN` — token para análisis.

## 5) Protección de rama
Ver `BRANCH_PROTECTION.md` para configurar checks obligatorios en `main`.
