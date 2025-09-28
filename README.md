# CNP Risk Scorer — PoC (FastAPI + scikit-learn + MySQL)

## 1) Levantar MySQL con datos de ejemplo
```bash
docker compose up -d
```
DB: `cnpdb`  |  Usuario: `cnp_user`  |  Password: `cnp_pass`

## 2) Ejecutar API
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 3) Endpoints
- `GET /health`
- `POST /score`

## 4) Umbrales de decisión
- `APPROVE` < 0.30  |  `REVIEW` 0.30–0.69  |  `DECLINE` ≥ 0.70

## 5) Bodies Postman (resultados distintos)
### A) Revisión
```json
{
  "merchant_id": "m_low",
  "amount": 120.0,
  "currency": "MXN",
  "country": "MX",
  "email": "a1@example.com",
  "ip": "10.0.0.10",
  "device_id": "dev_a1",
  "card_bin": "520157",
  "card_hash": "card_a1"
}
```

### B) Declinado
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

### C) Aprobado
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

> Con las semillas de `db/init.sql`, estos 3 casos devuelven **APPROVE**, **REVIEW** y **DECLINE** respectivamente.


---

## CI/CD con GitHub Actions + SonarQube

### Secrets requeridos (en el repo)
- `SONAR_HOST_URL` — URL de tu SonarQube (self-hosted).
- `SONAR_TOKEN` — Token de proyecto/usuario con permisos de análisis.

### Flujo
1. Al hacer *push/PR* a `main`:
   - **Job tests**: ejecuta `pytest` con cobertura y sube `coverage.xml` como artefacto.
   - **Job sonarqube** (depende de `tests`): descarga `coverage.xml`, corre el escaneo y **espera el Quality Gate**.
2. Umbrales recomendados (configurar en SonarQube → Quality Gates) para **New Code**:
   - Coverage ≥ 80%, Bugs/Vulnerabilities = 0, Code Smells críticos = 0.


## Protección de rama (recomendado)
Configura `main` para requerir los checks:

- `CI — Tests & SonarQube / Unit tests & coverage`
- `CI — Tests & SonarQube / SonarQube Scan & Quality Gate`

Consulta `BRANCH_PROTECTION.md` para hacerlo por UI o con `gh`.
