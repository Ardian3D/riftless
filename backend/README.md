# RIFTLESS Backend — Phase F4.2

Backend control-plane **foundation** for RIFTLESS.

This package provides a small, isolated FastAPI scaffold under `backend/`.  
It is **not** production-ready and does **not** integrate external systems yet.  
The frontend under repository-root `src/` is **not** connected to this API.

## Phase status

| Item | Status |
|------|--------|
| FastAPI application factory | Implemented |
| Configuration loader | Implemented |
| Standard success / error response shapes | Implemented |
| Exception handlers (not-found, validation, internal) | Hardened (F4.2) |
| `GET /health` (process liveness only) | Implemented |
| `GET /ready` (local app + configuration only) | Implemented |
| Backend tests (pytest) | Expanded (F4.2) |
| Database / ORM / migrations | **Not implemented** |
| Authentication / authorization | **Not implemented** |
| DeepSeek / Gemini / DataHub / GitHub | **Not implemented** |
| SQLGlot / DuckDB / dbt / writeback | **Not implemented** |
| Queues, workers, websockets, deployment | **Not implemented** |
| Frontend API wiring | **Not implemented** |
| CORS / API version prefix | **Not implemented** |

## Python requirement

- **Python 3.11+** (verified locally with Python 3.11.15)
- Declared in `pyproject.toml` as `requires-python = ">=3.11"`

## Folder structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # application factory + ASGI entrypoint
│   ├── api/
│   │   ├── router.py
│   │   └── routes/
│   │       └── health.py       # /health and /ready
│   ├── core/
│   │   ├── config.py           # settings loader
│   │   └── errors.py           # AppError + exception handlers
│   └── schemas/
│       └── common.py           # success / error envelopes
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_errors.py
│   ├── test_config.py
│   └── test_contracts.py
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

If `py -3.11` is unavailable on your machine, use:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If execution policy blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 3. Configure environment (optional)

```powershell
Copy-Item .env.example .env
```

Defaults are safe for local development if `.env` is omitted.  
No secrets or API keys are required for this foundation.

### 4. Run the development server

```powershell
python -m uvicorn app.main:app --reload
```

Default bind is controlled by configuration (`127.0.0.1:8000` unless overridden).

Open:

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/ready
- http://127.0.0.1:8000/docs (OpenAPI UI)

### 5. Run tests and compile check

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
| `RIFTLESS_API_PREFIX` | *(empty)* | Optional route prefix (e.g. `/api`) |
| `RIFTLESS_HOST` | `127.0.0.1` | Dev server bind host |
| `RIFTLESS_PORT` | `8000` | Dev server bind port |
| `RIFTLESS_DEBUG` | `false` | FastAPI debug flag |

No credentials or API keys are defined in this phase.  
Do not place `GEMINI_API_KEY` or other frontend secrets in backend env files.

## Application contract

- **Title:** RIFTLESS API  
- **Description:** Backend control-plane foundation for RIFTLESS.  
- **Entrypoint:** `app.main:app` via `create_app()`  
- Importing the app does **not** open network connections, databases, secret managers, AI providers, or background workers.

## Response contracts

### Success

```json
{
  "status": "ok",
  "data": {},
  "meta": null
}
```

### Error

```json
{
  "status": "error",
  "error": {
    "code": "not_found",
    "message": "The requested resource was not found.",
    "details": null
  }
}
```

| Code | Typical HTTP | Meaning |
|------|--------------|---------|
| `not_found` | 404 | Route or resource missing (`details` is always `null`) |
| `validation_error` | 422 | Request body/query failed validation |
| `internal_error` | 500 | Unexpected failure (no traceback to client) |
| `configuration_error` | *(startup)* | Invalid settings — fails process start |

## Health vs readiness

| Endpoint | Meaning |
|----------|---------|
| `GET /health` | **Process liveness only.** Service name + version. Does not claim database, DataHub, GitHub, AI, or validator health. |
| `GET /ready` | **Local application/configuration readiness only.** Confirms settings loaded and FastAPI app created. External dependencies are **not** checked. |

`/ready` includes a `limitations` list so clients do not assume external systems are available.

## Phase boundaries (not implemented)

- Database, ORM, migrations  
- AuthN / AuthZ  
- DeepSeek, Gemini, DataHub, GitHub integrations  
- SQLGlot, DuckDB, dbt, writeback  
- Deployment, queues, retry workers, websockets  
- Frontend ↔ backend HTTP integration  
- CORS and API versioning prefixes  

## Frontend note

The existing Vite + React app remains under repository-root `src/`.  
This backend package is intentionally separate.

**Audit machine note:** Bun was not available on PATH during F4.1/F4.2 verification.  
Frontend lint/build was not re-run via an alternate package manager; `package.json` / `bun.lock` were not modified.
