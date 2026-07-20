# RIFTLESS Backend — Phase F5.1

Backend control-plane for RIFTLESS.

This package provides a FastAPI backend under `backend/`.  
It is **not** production-ready. External systems are **not** integrated.  
The frontend under repository-root `src/` is **not** connected to this API.

## Phase status

| Item | Status |
|------|--------|
| FastAPI application factory | Implemented (F4) |
| Configuration loader | Implemented (F4) |
| Standard success / error response shapes | Implemented (F4) |
| Exception handlers | Hardened (F4.2) |
| `GET /health` (process liveness only) | Implemented |
| `GET /ready` (local app + configuration only) | Implemented |
| `POST /api/v1/changes/intake` (`rename_column`) | **Implemented (F5.1)** |
| Deterministic normalization + fingerprint | **Implemented (F5.1)** |
| Blast-radius / risk / ALLOW·WARN·BLOCK | **Not implemented** |
| Remediation / SQL execution / validation engine | **Not implemented** |
| Database / ORM / migrations / persistence | **Not implemented** |
| Authentication / authorization | **Not implemented** |
| DeepSeek / Gemini / DataHub / GitHub | **Not implemented** |
| SQLGlot / DuckDB / dbt / writeback | **Not implemented** |
| Queues, workers, websockets, deployment | **Not implemented** |
| Frontend API wiring | **Not implemented** |

## Python requirement

- **Python 3.11+** (verified locally with Python 3.11.15)
- Declared in `pyproject.toml` as `requires-python = ">=3.11"`

## Folder structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── router.py
│   │   └── routes/
│   │       ├── health.py
│   │       └── changes.py          # POST /api/v1/changes/intake
│   ├── core/
│   │   ├── config.py
│   │   └── errors.py
│   ├── schemas/
│   │   ├── common.py
│   │   └── changes.py
│   └── services/
│       └── change_intake.py        # normalize + fingerprint
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_errors.py
│   ├── test_config.py
│   ├── test_contracts.py
│   └── test_change_intake.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Setup (Windows PowerShell)

**Run every command from the `backend/` directory.**

```powershell
cd backend
```

### 1. Create and activate a virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If `py -3.11` is unavailable:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 3. Run the development server

```powershell
python -m uvicorn app.main:app --reload
```

### 4. Run tests and compile check

```powershell
python -m pytest
python -m compileall app
```

## Environment variables

Prefix: `RIFTLESS_` (never `VITE_`).

| Variable | Default | Description |
|----------|---------|-------------|
| `RIFTLESS_APP_ENV` | `development` | `development` \| `staging` \| `production` |
| `RIFTLESS_APP_VERSION` | `0.1.0` | Version string exposed by health/ready |
| `RIFTLESS_API_PREFIX` | *(empty)* | Optional global route prefix |
| `RIFTLESS_HOST` | `127.0.0.1` | Dev server bind host |
| `RIFTLESS_PORT` | `8000` | Dev server bind port |
| `RIFTLESS_DEBUG` | `false` | FastAPI debug flag |

No credentials or API keys are required for F5.1.

---

## Change intake (F5.1)

### Endpoint

```http
POST /api/v1/changes/intake
```

- **HTTP 201** on success  
- Supports **only** `change_type: "rename_column"`  
- No persistence (`meta.persistence = "none"`)  
- No risk engine, remediation, SQL execution, DataHub, GitHub, or AI  

### Example request

```json
{
  "change_type": "rename_column",
  "asset": {
    "platform": "snowflake",
    "database": "analytics",
    "schema": "core",
    "name": "customers"
  },
  "source_column": "customer_id",
  "target_column": "account_id",
  "reason": "Standardize the customer identifier."
}
```

### Example response (shape)

```json
{
  "status": "ok",
  "data": {
    "intake_id": "550e8400-e29b-41d4-a716-446655440000",
    "submitted_input": { "...": "as accepted before business normalization" },
    "normalized_change": {
      "change_type": "rename_column",
      "asset": {
        "platform": "snowflake",
        "database": "analytics",
        "schema": "core",
        "name": "customers"
      },
      "source_column": "customer_id",
      "target_column": "account_id",
      "reason": "Standardize the customer identifier."
    },
    "content_fingerprint": "64-char lowercase sha256 hex",
    "artifact_version": "1.0"
  },
  "meta": {
    "operation": "change_intake",
    "phase": "F5.1",
    "supported_change_types": ["rename_column"],
    "persistence": "none"
  }
}
```

### Normalization rules

1. Trim leading/trailing whitespace on all strings.  
2. Lowercase controlled fields: `change_type`, `asset.platform`.  
3. Preserve casing (after trim) for `database`, `schema`, `name`, columns.  
4. `reason`: trim; keep content/casing; `null` when omitted or blank after trim.  
5. Reject when `source_column == target_column` after normalization.  
6. No typo correction, no AI, no SQL interpretation.

### submitted_input vs normalized_change

| Field | Meaning |
|-------|---------|
| `submitted_input` | Request as accepted by schema validation, **before** business normalization. |
| `normalized_change` | Deterministic normalized artifact used for fingerprinting. |

They are stored as **separate** objects. Submitted input is not overwritten.

### Content fingerprint

- Algorithm: **SHA-256**  
- Input: canonical JSON of **`normalized_change` only**  
- Canonical form: UTF-8, sorted keys, compact separators `(",", ":")`  
- Output: lowercase hexadecimal (64 chars)  
- `reason` is part of `normalized_change`, so different reasons → different fingerprints  

**Not** a digital signature, security proof, authorization token, blockchain hash, or ledger entry.  
It is only a **deterministic content identifier**.

### What intake does **not** do

- Does not persist artifacts to a database or filesystem  
- Does not run blast-radius or risk analysis  
- Does not return ALLOW / WARN / BLOCK  
- Does not remediate, execute SQL, or call external systems  

---

## Health vs readiness

| Endpoint | Meaning |
|----------|---------|
| `GET /health` | Process liveness only. |
| `GET /ready` | Local application/configuration readiness only. External systems are **not** checked. |

## Frontend note

The Vite + React app remains under repository-root `src/`.  
Bun may be unavailable on some audit machines; do not replace it with npm for this repository without an explicit decision.
