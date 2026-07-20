# RIFTLESS Backend — Phase F6.2

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
| `POST /api/v1/risk/evaluate` (ALLOW / WARN / BLOCK) | Implemented (F5.2) |
| Shared fingerprint consistency check | Implemented (F5.2) |
| `POST /api/v1/runs/analyze` (sync orchestration) | Implemented (F5.3) |
| Validation domain contracts (schemas + aggregation) | Implemented (F6.1) |
| SQLGlot SQL parse validator (`sql_parse`) | **Implemented (F6.2)** |
| Validation HTTP endpoint | **Not implemented** |
| DuckDB execution validator | **Not implemented** |
| dbt validation executor | **Not implemented** |
| Artifact registry / durable intake provenance | **Not implemented** |
| Run history / GET run by ID | **Not implemented** |
| DataHub / GitHub / real blast-radius discovery | **Not implemented** |
| Remediation / SQL execution / production mutation | **Not implemented** |
| Database / ORM / migrations / persistence | **Not implemented** |
| Authentication / authorization | **Not implemented** |
| DeepSeek / Gemini | **Not implemented** |
| Writeback / deployment handoff | **Not implemented** |
| Queues, workers, websockets | **Not implemented** |
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
│   │       ├── risk.py             # POST /api/v1/risk/evaluate
│   │       └── runs.py             # POST /api/v1/runs/analyze
│   ├── core/
│   │   ├── config.py
│   │   └── errors.py
│   ├── schemas/
│   │   ├── common.py
│   │   ├── changes.py
│   │   ├── risk.py
│   │   ├── runs.py
│   │   ├── validation.py           # F6.1 validation contracts
│   │   └── sql_validation.py       # F6.2 SQL dialect + parse input
│   ├── services/
│   │   ├── change_intake.py
│   │   ├── risk_engine.py
│   │   ├── run_orchestrator.py
│   │   ├── validation_engine.py    # F6.1 deterministic aggregation
│   │   └── sql_parse_validator.py  # F6.2 SQLGlot parse validator
│   └── utils/
│       └── fingerprint.py          # shared SHA-256 canonical fingerprint
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_errors.py
│   ├── test_config.py
│   ├── test_contracts.py
│   ├── test_change_intake.py
│   ├── test_risk_evaluate.py
│   ├── test_runs_analyze.py
│   ├── test_validation_contracts.py
│   └── test_sql_parse_validator.py
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

No credentials or API keys are required for F5–F6.1.

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

## Synchronous analysis run (F5.3)

### Endpoint

```http
POST /api/v1/runs/analyze
```

- **HTTP 200** on success (synchronous result returned in the same request)  
- In-process orchestration of F5.1 intake → F5.2 risk evaluation  
- **No** HTTP loopback to internal endpoints  
- **No** persistence, run retrieval, queue, worker, AI, SQL, DataHub, or GitHub  

### Flow

```text
Change submitted
→ Intake created (F5.1 service)
→ Change normalized + fingerprint
→ Request-local intake reference (current request only)
→ Risk rules evaluated (F5.2 service)
→ ALLOW / WARN / BLOCK returned in one run artifact
```

### Example request

```json
{
  "change": {
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
  "evaluation_context": {
    "context_complete": true,
    "downstream_dependency_count": 0,
    "protected_asset": false
  }
}
```

Clients must **not** send `run_id`, `intake_id`, `evaluation_id`, fingerprints,
`normalized_change`, `decision`, reasons, approvals, or policy versions.

### Example response (shape)

```json
{
  "status": "ok",
  "data": {
    "run_id": "server-generated-uuid",
    "orchestration_status": "completed",
    "change_intake": {
      "intake_id": "…",
      "submitted_input": { "…" : "…" },
      "normalized_change": { "…" : "…" },
      "content_fingerprint": "…",
      "artifact_version": "1.0"
    },
    "risk_evaluation": {
      "evaluation_id": "…",
      "intake_id": "same as change_intake.intake_id",
      "decision": "ALLOW",
      "scope": "provided_context_only",
      "reasons": [ { "code": "no_risk_condition_detected", "level": "ALLOW", "message": "…", "evidence": null } ],
      "evaluated_content_fingerprint": "same as change_intake.content_fingerprint",
      "evaluation_context": { "…" : "…" },
      "policy_version": "1.0",
      "artifact_version": "1.0"
    },
    "run_artifact_version": "1.0"
  },
  "meta": {
    "operation": "synchronous_analysis_run",
    "phase": "F5.3",
    "execution_mode": "in_process",
    "persistence": "none",
    "retrieval_available": false,
    "context_origin": "caller_provided",
    "context_trust": "unverified",
    "intake_reference_origin": "riftless_runtime",
    "intake_reference_scope": "current_request_only",
    "intake_reference_persisted": false,
    "model_used": false,
    "validation_executed": false,
    "deployment_authorized": false
  }
}
```

### Provenance (honest)

| Concern | F5.3 value | Meaning |
|---------|------------|---------|
| Evaluation context | `caller_provided` / `unverified` | Still supplied by the client; not DataHub-backed. |
| Intake reference | `riftless_runtime` / `current_request_only` / not persisted | Created by RIFTLESS in this request only. **Not** durable provenance, registry match, or tamper-proof storage. |
| Standalone `POST /risk/evaluate` | still `caller_provided` / `unverified` | Unchanged from F5.2. |

### `orchestration_status: completed` means

- intake finished in the current request  
- deterministic evaluation finished  
- response artifact was assembled  

It does **not** mean ALLOW, validation success, deployment authorization, writeback, or persistence.

ALLOW / WARN / BLOCK remain scoped to `provided_context_only`.  
AI is not used. Validation engine is not executed.

---

## Validation contract foundation (F6.1)

F6.1 defines the **shared domain contracts** that future SQLGlot, DuckDB, and
dbt validators will use. It does **not** run any validator.

| Present in F6.1 | Not present in F6.1 |
|-----------------|---------------------|
| Schemas / enums | Validation HTTP endpoint |
| State invariants | SQLGlot parsing |
| Evidence / check-result / artifact shapes | DuckDB execution |
| Deterministic aggregation pure functions | dbt CLI / subprocess |
| Unit tests | Persistence / artifact registry |
| | Plugin registry / executor base classes |

Check-kind enum values (`sql_parse`, `duckdb_execution`, `dbt_validation`) are
**contract names only**. Their presence does **not** mean those executors exist.

### Three separate concepts

| Concept | Meaning |
|---------|---------|
| **execution_status** | Did the validator actually finish running? |
| **outcome** | What did a completed check conclude within its scope? |
| **evidence** | Bounded, safe structured proof items for that check |

Do **not** conflate:

| Confusion | Correct reading |
|-----------|-----------------|
| FAIL = ERROR | FAIL is a completed check that found a problem; ERROR means execution itself failed |
| PASS = deployment authorization | PASS is scoped check success only |
| COMPLETED = PASS | COMPLETED only means the check finished and produced an outcome |
| UNAVAILABLE = FAIL | UNAVAILABLE means the engine/prerequisite was missing |

### Check kinds (contract-only)

| Enum | Serialized value | F6.1 status |
|------|------------------|-------------|
| `SQL_PARSE` | `sql_parse` | Implemented in F6.2 (SQLGlot parse only) |
| `DUCKDB_EXECUTION` | `duckdb_execution` | Name only — no DuckDB |
| `DBT_VALIDATION` | `dbt_validation` | Name only — no dbt |

### Check execution status

| Status | Serialized | Meaning |
|--------|------------|---------|
| `COMPLETED` | `completed` | Validator finished and produced an outcome |
| `ERROR` | `error` | Validator was attempted but could not finish |
| `UNAVAILABLE` | `unavailable` | Validator or prerequisite not available |
| `SKIPPED` | `skipped` | Validator intentionally not run for an explicit reason |

### Check / overall outcome

| Outcome | Serialized | Meaning |
|---------|------------|---------|
| `PASS` | `pass` | Completed check found no failure in its tested scope |
| `FAIL` | `fail` | Completed check found a failing condition in its tested scope |
| `INCONCLUSIVE` | `inconclusive` | Completed but evidence insufficient, or overall cannot decide |

**PASS does not mean:** universally safe change, all downstream systems safe,
deployment authorized, production mutation allowed, or human approval present.

### State invariants (check result)

Invalid combinations are **rejected** (schema/domain validation error). They
are never auto-repaired.

1. `COMPLETED` → `outcome` required (`pass` \| `fail` \| `inconclusive`)
2. `ERROR` → `outcome` null; at least one evidence item
3. `UNAVAILABLE` → `outcome` null; at least one evidence item
4. `SKIPPED` → `outcome` null; at least one evidence item
5. `PASS` / `FAIL` / `INCONCLUSIVE` only when `execution_status` is `COMPLETED`

### Validation evidence

```json
{
  "code": "machine_readable_code",
  "message": "Safe human-readable explanation.",
  "details": null
}
```

- `code`: lowercase snake_case, non-empty, length-bounded  
- `message`: human-readable, non-empty; no traceback or filesystem paths  
- `details`: optional structured primitives only (no exception objects)  

Evidence is **not** authorization, cryptographic signature, provenance proof,
blockchain record, or deployment approval.

### Validation check result (shape)

```json
{
  "check_id": "<UUID>",
  "check_kind": "sql_parse | duckdb_execution | dbt_validation",
  "required": true,
  "execution_status": "completed | error | unavailable | skipped",
  "outcome": "pass | fail | inconclusive | null",
  "scope": "bounded description",
  "summary": "Safe concise summary.",
  "evidence": [],
  "engine_name": null,
  "engine_version": null
}
```

- `check_id` is server-generated UUID  
- `required` controls whether the check affects overall outcome  
- `engine_name` / `engine_version` stay null until a real executor exists  
- No timestamps in F6.1  

### Validation artifact (shape)

```json
{
  "validation_id": "<UUID>",
  "subject_fingerprint": "<64 lowercase SHA-256 hex>",
  "scope": "provided_artifacts_only",
  "execution_status": "completed | partial | not_run | execution_failed",
  "outcome": "pass | fail | inconclusive",
  "checks": [],
  "artifact_version": "1.0"
}
```

- Scope is always `provided_artifacts_only`  
- Artifact is **not** persisted in F6.1  
- `subject_fingerprint` uses the same 64-char lowercase SHA-256 format as F5  
- Fingerprint is content identity only — **not** signature, auth, provenance,
  authorization, tamper-proof storage, blockchain, or ledger  

### Overall execution status (aggregation)

| Status | Rule |
|--------|------|
| `not_run` | Empty checks, or no COMPLETED and no ERROR (only UNAVAILABLE/SKIPPED) |
| `completed` | Every check is COMPLETED |
| `partial` | Some COMPLETED and some not |
| `execution_failed` | No COMPLETED and at least one ERROR |

### Overall outcome (required checks only)

| Outcome | Rule |
|---------|------|
| `fail` | Any **required** check is COMPLETED + FAIL |
| `pass` | At least one required check exists and **all** required are COMPLETED + PASS |
| `inconclusive` | Everything else (empty required set, required ERROR/UNAVAILABLE/SKIPPED/INCONCLUSIVE, optional-only lists) |

**Required vs optional:**

- Only `required: true` checks drive overall outcome.  
- Optional FAIL cannot turn a required-PASS aggregate into FAIL.  
- Optional checks still appear in `checks` and still affect overall
  **execution_status** (e.g. COMPLETED + SKIPPED → `partial`).  
- No required checks → overall outcome `inconclusive`.  

Aggregation is a pure function (`build_validation_artifact`): no network,
database, filesystem, subprocess, or AI. Input check order is preserved;
input lists are not mutated.

### What F6.1 does **not** do

- No validation production route  
- No SQL parse / execute  
- No dbt command  
- No DuckDB or dbt dependencies (SQLGlot added in F6.2)  
- No persistence, registry, queue, worker, or retry  
- No DataHub / GitHub / DeepSeek / remediation / writeback  
- No frontend wiring  

---

## SQLGlot parse validator (F6.2)

F6.2 is the **first real validator**. It uses **SQLGlot 30.12.0** (pinned in
`pyproject.toml`) to parse SQL syntax for a declared dialect and returns a
F6.1 `ValidationCheckResult` with `check_kind = sql_parse`.

| Present in F6.2 | Not present in F6.2 |
|-----------------|---------------------|
| SQLGlot runtime dependency | Validation HTTP endpoint |
| `SqlDialect` + `SqlParseInput` | DuckDB execution |
| `run_sql_parse_check` service | dbt validation |
| Real `sql_parse` check results | SQL execution / database connection |
| Unit tests | Analysis-run integration |
| | Schema resolution / object existence |
| | Transpilation / rewrite / remediation |

### Supported dialects (F6.2)

Exact serialized values only (no aliases):

| Dialect | Value |
|---------|-------|
| Snowflake | `snowflake` |
| PostgreSQL | `postgres` |
| BigQuery | `bigquery` |
| DuckDB | `duckdb` |

Unsupported strings (`postgresql`, `bq`, `sf`, …) are rejected by the input
schema **before** the parser runs.

Declaring a dialect only means SQLGlot is invoked with that dialect name. It
does **not** mean a database is connected or that vendor runtime behavior is
verified.

### Input contract

```json
{
  "sql": "SELECT ...",
  "dialect": "snowflake",
  "required": true
}
```

- SQL max length: **100000** characters  
- Blank / whitespace-only SQL rejected  
- Null bytes and other C0 controls (except tab / LF / CR) rejected  
- SQL is **not** rewritten or reformatted before parse  
- Extra fields forbidden  
- Raw SQL is **never** copied into evidence or summary  

### Outcomes (honest)

| Situation | `execution_status` | `outcome` | Evidence code |
|-----------|--------------------|-----------|---------------|
| Syntax accepted, ≥1 statement | `completed` | `pass` | `sql_parse_succeeded` |
| Syntax error detected | `completed` | `fail` | `sql_parse_failed` |
| Comment-only / no statement | `completed` | `fail` | `sql_no_statement` |
| Unexpected engine failure | `error` | `null` | `sql_parser_execution_error` |

**Parse failure ≠ execution error.**  
`FAIL` means the parser finished and found a syntax problem.  
`ERROR` means the parser itself did not complete.

### Scope of PASS

PASS means: SQLGlot found **no syntax error** for the declared dialect with
the installed engine version.

PASS does **not** mean:

- the query can be executed  
- tables or columns exist  
- semantic correctness  
- production safety  
- universal change safety  
- deployment authorization  

### Engine metadata

- `engine_name`: `sqlglot`  
- `engine_version`: actual installed package version (runtime metadata)  
- Scope: `sql_syntax_for_declared_dialect`  

### Privacy

Evidence may include only safe primitives such as `dialect`,
`statement_count`, `error_count`, and optional line/column integers.  
Evidence must **not** include raw SQL, SQL snippets, exception messages,
tracebacks, or filesystem paths.

### Wiring status

- **No** production validation route  
- **Not** connected to `POST /api/v1/runs/analyze`  
- Existing endpoints unchanged  

---

## Health vs readiness

| Endpoint | Meaning |
|----------|---------|
| `GET /health` | Process liveness only. |
| `GET /ready` | Local application/configuration readiness only. External systems are **not** checked. |

## Frontend note

The Vite + React app remains under repository-root `src/`.  
Bun may be unavailable on some audit machines; do not replace it with npm for this repository without an explicit decision.
