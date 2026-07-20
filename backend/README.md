# RIFTLESS Backend — Phase F5.2

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
| `POST /api/v1/changes/intake` (`rename_column`) | Implemented (F5.1) |
| Deterministic normalization + fingerprint | Implemented (F5.1) |
| `POST /api/v1/risk/evaluate` (ALLOW / WARN / BLOCK) | **Implemented (F5.2)** |
| Shared fingerprint consistency check | **Implemented (F5.2)** |
| Artifact registry / intake provenance | **Not implemented** |
| DataHub / GitHub / real blast-radius discovery | **Not implemented** |
| Remediation / SQL execution / validation engine | **Not implemented** |
| Database / ORM / migrations / persistence | **Not implemented** |
| Authentication / authorization | **Not implemented** |
| DeepSeek / Gemini | **Not implemented** |
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
│   │       ├── changes.py          # POST /api/v1/changes/intake
│   │       └── risk.py             # POST /api/v1/risk/evaluate
│   ├── core/
│   │   ├── config.py
│   │   └── errors.py
│   ├── schemas/
│   │   ├── common.py
│   │   ├── changes.py
│   │   └── risk.py
│   ├── services/
│   │   ├── change_intake.py
│   │   └── risk_engine.py
│   └── utils/
│       └── fingerprint.py          # shared SHA-256 canonical fingerprint
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_errors.py
│   ├── test_config.py
│   ├── test_contracts.py
│   ├── test_change_intake.py
│   └── test_risk_evaluate.py
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

No credentials or API keys are required for F5.2.

---

## Change intake (F5.1)

### Endpoint

```http
POST /api/v1/changes/intake
```

- **HTTP 201** on success  
- Supports **only** `change_type: "rename_column"`  
- No persistence (`meta.persistence = "none"`)  

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

### Normalization rules

1. Trim leading/trailing whitespace on all strings.  
2. Lowercase controlled fields: `change_type`, `asset.platform`.  
3. Preserve casing (after trim) for `database`, `schema`, `name`, columns.  
4. `reason`: trim; keep content/casing; `null` when omitted or blank after trim.  
5. Reject when `source_column == target_column` after normalization.  

### Content fingerprint

- Algorithm: **SHA-256** over canonical JSON of **`normalized_change` only**  
- Canonical form: UTF-8, sorted keys, compact separators `(",", ":")`  
- Output: lowercase hexadecimal (64 chars)  
- Shared implementation: `app/utils/fingerprint.py` (used by F5.1 and F5.2)  

**Not** a digital signature, security proof, authorization token, blockchain hash, or ledger entry.

---

## Deterministic risk evaluation (F5.2)

### Endpoint

```http
POST /api/v1/risk/evaluate
```

- **HTTP 200** on success  
- Fingerprint **consistency check** before running rules  
- `evaluation_context` is **caller-provided** and **unverified**  
- `intake_reference` is **caller-provided** and **unverified** (no registry)  
- **No AI / language model** is used  
- Artifacts are **not** persisted  
- Decision scope: `provided_context_only`  

### Intake reference limitations (important)

F5.2 has **no artifact persistence** and **no intake registry**.

| Fact | Implication |
|------|-------------|
| Caller re-sends `intake_reference` | Server does not load the artifact from storage. |
| `intake_id` is a UUID from the request | Server does **not** prove the id was issued by RIFTLESS. |
| Fingerprint is recomputed and compared | Only a **consistency check** between `normalized_change` and `content_fingerprint`. |
| Match result | Payload is schema-valid and fingerprint-consistent — **not** authentic, trusted, or provenance-verified. |

Provenance verification can only appear after an official artifact persistence or registry phase exists.  
Fingerprint is **not** a signature, authentication mechanism, provenance proof, authorization token, blockchain hash, or ledger entry.

### Semantics (honest)

| Decision | Meaning in F5.2 |
|----------|-----------------|
| **ALLOW** | No BLOCK or WARN condition found in the **supplied** context. **Not** universal safety, deployment authorization, or validation success. |
| **WARN** | Uncertainty or potential impact that needs review. **Not** a validation-engine failure. |
| **BLOCK** | A deterministic policy condition was found in the supplied context. Future writeback phases may still **record** a BLOCK decision; BLOCK is not a production mutation. |

### Example request

```json
{
  "intake_reference": {
    "intake_id": "3f91a5db-e915-42c4-a3d6-8965d0386dbf",
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
    "content_fingerprint": "lowercase-sha256-hex-of-normalized-change",
    "artifact_version": "1.0"
  },
  "evaluation_context": {
    "context_complete": true,
    "downstream_dependency_count": 0,
    "protected_asset": false
  }
}
```

### Fingerprint consistency check

1. Recompute SHA-256 of `normalized_change` with the **same** canonical rules as F5.1.  
2. Compare to `content_fingerprint`.  
3. On match → proceed with rules; meta reports `fingerprint_check: "matched"`.  
4. On mismatch → **HTTP 422** with a neutral message (no expected fingerprint, no canonical JSON, no attack claim).  
5. Unsupported `artifact_version` → **HTTP 422** (no silent migration).  

Mismatch means the payload and fingerprint are **inconsistent**. It does not by itself prove attack or manipulation.

### Deterministic rules (stable order)

| # | Condition | Level | Code |
|---|-----------|-------|------|
| 1 | `protected_asset = true` | BLOCK | `protected_asset` |
| 2 | `context_complete = false` | WARN | `incomplete_context` |
| 3 | `downstream_dependency_count = null` (only when incomplete) | WARN | `unknown_dependency_count` |
| 4 | `downstream_dependency_count > 0` | WARN | `downstream_dependencies_present` |
| default | none of the above | ALLOW | `no_risk_condition_detected` |

**Precedence:** `BLOCK > WARN > ALLOW`  
All triggered rules are returned; evaluation does not stop at the first match.  
Reason order follows the rule table above.

### Example ALLOW response (shape)

```json
{
  "status": "ok",
  "data": {
    "evaluation_id": "server-generated-uuid",
    "intake_id": "3f91a5db-e915-42c4-a3d6-8965d0386dbf",
    "decision": "ALLOW",
    "scope": "provided_context_only",
    "reasons": [
      {
        "code": "no_risk_condition_detected",
        "level": "ALLOW",
        "message": "No blocking or warning condition was detected within the supplied context.",
        "evidence": null
      }
    ],
    "evaluated_content_fingerprint": "…",
    "evaluation_context": {
      "context_complete": true,
      "downstream_dependency_count": 0,
      "protected_asset": false
    },
    "policy_version": "1.0",
    "artifact_version": "1.0"
  },
  "meta": {
    "operation": "deterministic_risk_evaluation",
    "phase": "F5.2",
    "policy_version": "1.0",
    "context_origin": "caller_provided",
    "context_trust": "unverified",
    "intake_reference_origin": "caller_provided",
    "intake_reference_trust": "unverified",
    "fingerprint_check": "matched",
    "model_used": false,
    "persistence": "none"
  }
}
```

Meta distinguishes:

- **evaluation context** origin/trust (`context_*`)  
- **intake reference** origin/trust (`intake_reference_*`)  
- **fingerprint consistency** result (`fingerprint_check`)

### Example WARN (downstream deps)

`decision: "WARN"` with reason `downstream_dependencies_present` and evidence:

```json
{ "downstream_dependency_count": 3 }
```

### Example BLOCK (protected asset)

`decision: "BLOCK"` with reason `protected_asset`.  
If incomplete context is also supplied, WARN reasons are still listed; decision remains **BLOCK**.

### What risk evaluation does **not** do

- Does not query DataHub or GitHub  
- Does not claim complete blast radius or authoritative dependency graphs  
- Does not run SQL, validation engines, or remediation  
- Does not use DeepSeek / any LLM  
- Does not persist artifacts  
- Does not authorize deployment or production mutation  

`evaluation_context` is **not** a DataHub Context Pack. That pack is reserved for a later integration phase.

---

## Health vs readiness

| Endpoint | Meaning |
|----------|---------|
| `GET /health` | Process liveness only. |
| `GET /ready` | Local application/configuration readiness only. External systems are **not** checked. |

## Frontend note

The Vite + React app remains under repository-root `src/`.  
Bun may be unavailable on some audit machines; do not replace it with npm for this repository without an explicit decision.
