# RIFTLESS Backend — Phase F7.1

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
| SQLGlot SQL parse validator (`sql_parse`) | Implemented (F6.2) |
| DuckDB in-memory rename validator (`duckdb_execution`) | Implemented (F6.3) |
| dbt controlled project parse validator (`dbt_validation`) | Implemented (F6.4) |
| Validation orchestration service | Implemented (F6.5) |
| `POST /api/v1/validations/execute` (sync validation API) | Implemented (F6.6) |
| Analysis-run optional validation integration | Implemented (F6.7) |
| Advisory contract foundation | **Implemented (F7.1)** |
| Redacted context pack builder | **Not implemented** (F7.2) |
| DeepSeek / model provider client | **Not implemented** |
| Advisory HTTP endpoint | **Not implemented** |
| Artifact registry / durable intake provenance | **Not implemented** |
| Run history / GET run by ID | **Not implemented** |
| DataHub / GitHub / real blast-radius discovery | **Not implemented** |
| Remediation / production SQL mutation | **Not implemented** |
| Database / ORM / migrations / persistence | **Not implemented** |
| Authentication / authorization | **Not implemented** |
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
│   │       ├── runs.py             # POST /api/v1/runs/analyze
│   │       └── validations.py      # POST /api/v1/validations/execute
│   ├── core/
│   │   ├── config.py
│   │   └── errors.py
│   ├── schemas/
│   │   ├── common.py
│   │   ├── changes.py
│   │   ├── risk.py
│   │   ├── runs.py
│   │   ├── validation.py           # F6.1 validation contracts
│   │   ├── sql_validation.py       # F6.2 SQL dialect + parse input
│   │   ├── duckdb_validation.py    # F6.3 fixture + rename input
│   │   ├── dbt_validation.py       # F6.4 dbt parse input
│   │   ├── validation_plan.py      # F6.5 validation plan input
│   │   ├── validation_api.py       # F6.6 response meta
│   │   ├── run_validation.py       # F6.7 optional run validation input
│   │   └── advisory.py             # F7.1 advisory contracts
│   ├── services/
│   │   ├── change_intake.py
│   │   ├── risk_engine.py
│   │   ├── run_orchestrator.py     # F5.3 + F6.7 optional validation
│   │   ├── validation_engine.py    # F6.1 deterministic aggregation
│   │   ├── sql_parse_validator.py  # F6.2 SQLGlot parse validator
│   │   ├── duckdb_rename_validator.py  # F6.3 DuckDB in-memory rename
│   │   ├── dbt_parse_validator.py  # F6.4 controlled dbt parse
│   │   ├── validation_orchestrator.py  # F6.5 sequential orchestration
│   │   └── advisory_artifacts.py   # F7.1 pure advisory builders
│   └── utils/
│       ├── fingerprint.py          # shared SHA-256 canonical fingerprint
│       ├── advisory_fingerprint.py # F7.1 context-pack fingerprint
│       ├── sql_identifiers.py      # server-side identifier quoting
│       └── controlled_dbt_project.py  # F6.4 temp project builder
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_errors.py
│   ├── test_config.py
│   ├── test_contracts.py
│   ├── test_change_intake.py
│   ├── test_risk_evaluate.py
│   ├── test_runs_analyze.py        # F5.3 + F6.7
│   ├── test_validation_contracts.py
│   ├── test_sql_parse_validator.py
│   ├── test_duckdb_rename_validator.py
│   ├── test_dbt_parse_validator.py
│   ├── test_validation_orchestrator.py
│   ├── test_validation_execute_api.py
│   └── test_advisory_contracts.py  # F7.1
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

## Synchronous analysis run (F5.3 / F6.7)

### Endpoint

```http
POST /api/v1/runs/analyze
```

- **HTTP 200** on success (synchronous result returned in the same request)  
- In-process orchestration of F5.1 intake → F5.2 risk evaluation → optional F6 validation  
- **No** HTTP loopback to internal endpoints  
- **No** persistence, run retrieval, queue, worker, AI, DataHub, or GitHub  
- Handler is a synchronous `def` (blocking DuckDB/dbt run off the event loop)  

### Flow

```text
Change submitted
→ Intake created (F5.1 service)
→ Change normalized + fingerprint
→ Request-local intake reference (current request only)
→ Risk rules evaluated (F5.2 service)
→ Optional: server-composed ValidationPlanInput + F6.5 orchestrator
→ Run artifact (risk + optional ValidationArtifact)
```

### Example request (legacy — no validation)

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

### Example response (shape, without validation)

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
    "validation_artifact": null,
    "run_artifact_version": "1.1"
  },
  "meta": {
    "operation": "synchronous_analysis_run",
    "phase": "F6.7",
    "execution_mode": "in_process",
    "persistence": "none",
    "retrieval_available": false,
    "context_origin": "caller_provided",
    "context_trust": "unverified",
    "intake_reference_origin": "riftless_runtime",
    "intake_reference_scope": "current_request_only",
    "intake_reference_persisted": false,
    "model_used": false,
    "deployment_authorized": false,
    "validation_requested": false,
    "validation_executed": false,
    "validation_artifact_present": false
  }
}
```

### Provenance (honest)

| Concern | Value | Meaning |
|---------|-------|---------|
| Evaluation context | `caller_provided` / `unverified` | Still supplied by the client; not DataHub-backed. |
| Intake reference | `riftless_runtime` / `current_request_only` / not persisted | Created by RIFTLESS in this request only. **Not** durable provenance, registry match, or tamper-proof storage. |
| Standalone `POST /risk/evaluate` | still `caller_provided` / `unverified` | Unchanged from F5.2. |

### `orchestration_status: completed` means

- intake finished in the current request  
- deterministic evaluation finished  
- optional ValidationArtifact formed when requested  
- response artifact was assembled  

It does **not** mean ALLOW, validation PASS, deployment authorization, writeback, or persistence.

ALLOW / WARN / BLOCK remain scoped to `provided_context_only`.  
AI is not used.

See **Analysis-run validation integration (F6.7)** below for optional validation.

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
| `DUCKDB_EXECUTION` | `duckdb_execution` | Implemented in F6.3 (in-memory rename only) |
| `DBT_VALIDATION` | `dbt_validation` | Implemented in F6.4 (controlled project parse only) |

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

## DuckDB in-memory rename validator (F6.3)

F6.3 is the **second real validator**. It uses **DuckDB 1.5.4** (pinned in
`pyproject.toml`) to simulate a `rename_column` change against a structured
in-memory fixture table and returns a F6.1 `ValidationCheckResult` with
`check_kind = duckdb_execution`.

| Present in F6.3 | Not present in F6.3 |
|-----------------|---------------------|
| DuckDB runtime dependency | Validation HTTP endpoint |
| Structured fixture schema | Caller-provided SQL execution |
| Isolated `:memory:` rename check | Persistent DuckDB file |
| Parameter-bound fixture inserts | External DB / user database |
| Safe identifier quoting | Extension install/load |
| Unit tests | dbt / analysis-run integration |

### Security boundary

**Caller SQL is never accepted.** Request fields such as `sql`, `setup_sql`,
`migration_sql`, `assertion_sql`, `teardown_sql`, `command`, `query`, and
`script` are rejected. All executed SQL is **server-generated** from validated
structured input.

### Supported change

- Only `rename_column` (F5.1 `NormalizedChange`)
- Table name comes from `normalized_change.asset.name` (no separate table override)

### Fixture types (allowlisted)

| Enum value | DuckDB SQL type |
|------------|-----------------|
| `integer` | `INTEGER` |
| `bigint` | `BIGINT` |
| `double` | `DOUBLE` |
| `boolean` | `BOOLEAN` |
| `varchar` | `VARCHAR` |

Arbitrary DuckDB types (struct, list, date, decimal, …) are rejected. Cell
values are type-checked with **no silent coercion**.

### Resource limits

| Limit | Value |
|-------|------:|
| Min columns | 1 |
| Max columns | 64 |
| Max rows | 500 |
| Max total cells | 20 000 |
| Max column name length | 128 |
| Max varchar cell length | 4096 |

Column names must be unique case-insensitively. Duplicate / blank / control
characters are rejected before DuckDB opens.

### Connection isolation

For **every** check:

1. Open a new DuckDB connection with `database=":memory:"`  
2. Apply restrictions supported by DuckDB 1.5.4:  
   - `enable_external_access=false`  
   - `autoinstall_known_extensions=false`  
   - `autoload_known_extensions=false`  
   - `lock_configuration=true`  
3. Create table + insert rows (parameter binding)  
4. Run server-generated `ALTER TABLE … RENAME COLUMN …`  
5. Verify postconditions  
6. Close the connection in `finally`  

No shared connections, no file paths, no extension install/load, no ATTACH,
no COPY to/from files.

### Outcomes (honest)

| Situation | `execution_status` | `outcome` | Evidence code |
|-----------|--------------------|-----------|---------------|
| Rename + postconditions OK | `completed` | `pass` | `duckdb_rename_succeeded` |
| Source column missing in fixture | `completed` | `fail` | `duckdb_source_column_missing` |
| Target column already in fixture | `completed` | `fail` | `duckdb_target_column_exists` |
| DuckDB rejects rename | `completed` | `fail` | `duckdb_rename_failed` |
| Postcondition mismatch | `completed` | `fail` | `duckdb_postcondition_failed` |
| Fixture setup could not complete | `completed` | `inconclusive` | `duckdb_fixture_setup_inconclusive` |
| Unexpected engine failure | `error` | `null` | `duckdb_execution_error` |

Fixture setup failure is **INCONCLUSIVE** (rename was not tested), not FAIL.

### Scope of PASS

PASS means: the rename completed on the **supplied DuckDB in-memory fixture**
and limited postconditions held (source absent, target present, row count
preserved).

PASS does **not** mean:

- the same rename succeeds on Snowflake / Postgres / BigQuery  
- vendor behavior matches DuckDB  
- downstream systems are compatible  
- production data is safe  
- universal validation success  
- deployment authorization  

### Privacy

Evidence may include safe primitives (counts, booleans, stage labels).  
Evidence must **not** include fixture cell values, generated SQL, exception
messages, or tracebacks.

### Engine metadata

- `engine_name`: `duckdb`  
- `engine_version`: actual installed package version (runtime metadata)  
- Scope: `duckdb_in_memory_rename_simulation`  

### Wiring status

- **No** production validation route  
- **Not** connected to `POST /api/v1/runs/analyze`  
- Existing endpoints unchanged  

---

## Controlled dbt project parse validator (F6.4)

F6.4 is the **third real validator**. It uses **dbt-core 1.10.15** with
**dbt-duckdb 1.10.1** (pinned in `pyproject.toml`) to run allowlisted
`dbt parse` against a **server-generated temporary project** and returns a
F6.1 `ValidationCheckResult` with `check_kind = dbt_validation`.

Pinned companions remain unchanged:

- `duckdb==1.5.4`
- `sqlglot==30.12.0`

| Present in F6.4 | Not present in F6.4 |
|-----------------|---------------------|
| dbt-core + dbt-duckdb dependencies | Validation HTTP endpoint |
| Server-built temp project + profile | Caller project / profiles path |
| Allowlisted `dbt parse` only | `dbt run` / `build` / `test` / `deps` |
| Manifest verification | Packages, macros, seeds, snapshots |
| Timeout (60s) + sanitized env | Production database connection |
| Temp cleanup after every outcome | Analysis-run integration |

### Input contract

```json
{
  "model_name": "customers_renamed",
  "model_sql": "select customer_id as account_id from customers",
  "required": true
}
```

- `model_name`: lowercase snake_case `^[a-z][a-z0-9_]{0,63}$` (not a path)  
- `model_sql`: plain SQL only, max **100000** characters  
- Jinja openers `{{`, `{%`, `{#` are **rejected**  
- Caller cannot send: project/profiles paths, command, adapter, packages,
  macros, environment, or selectors  

### Temporary project (server-owned)

Per check, RIFTLESS creates a new temporary directory containing only:

- `dbt_project.yml` (project name `riftless_validation`)  
- `profiles.yml` (DuckDB `path: ':memory:'`)  
- `models/<model_name>.sql`  

No `packages.yml`, macros, seeds, snapshots, analyses, or custom tests.  
Materialization is server-fixed (`view`). The entire tree is deleted after
success, process failure, timeout, and unexpected error.

### Command allowlist

Only:

```text
dbt parse --project-dir … --profiles-dir … --target-path … --log-path …
```

- Argument list + `shell=False`  
- Executable from the backend virtual environment  
- Timeout: **60 seconds**  
- Never: run, build, test, seed, snapshot, compile, debug, deps, docs  

### Environment boundary

Subprocess environment is built explicitly (not a full parent env copy):

- minimal Windows process paths  
- isolated TEMP/HOME under the temp root  
- `DBT_SEND_ANONYMOUS_USAGE_STATS=False`, `DO_NOT_TRACK=1`  
- no API keys / GitHub / DataHub / DeepSeek / Gemini / `VITE_*` secrets  

Honest limit: no OS-level network sandbox is claimed. The validator does not
perform intentional network operations and does not run `dbt deps`.

### Outcomes (honest)

| Situation | `execution_status` | `outcome` | Evidence code |
|-----------|--------------------|-----------|---------------|
| Parse OK + verified manifest | `completed` | `pass` | `dbt_parse_succeeded` |
| dbt non-zero process exit | `error` | `null` | `dbt_parse_process_failed` |
| dbt / adapter unavailable | `unavailable` | `null` | `dbt_engine_unavailable` |
| Timeout | `error` | `null` | `dbt_execution_timeout` |
| Project setup failure | `error` | `null` | `dbt_project_setup_error` |
| Manifest missing/invalid/unexpected | `error` | `null` | `dbt_manifest_verification_error` |
| Other engine failure | `error` | `null` | `dbt_execution_error` |

F6.4 does **not** currently emit a proven caller-caused `FAIL`. Generic
non-zero dbt exits are treated as **execution ERROR**, not validation FAIL.
stdout/stderr are captured only for internal process handling and are **never**
classified into FAIL reasons or returned in evidence.

### dbt parse is not a SQL syntax validator

SQL grammar validation remains the responsibility of **F6.2 (SQLGlot)**.

On the pinned engines (`dbt-core==1.10.15`, `dbt-duckdb==1.10.1`), plain SQL
that is grammatically invalid can still:

- yield dbt parse exit code `0`  
- register the expected model in the manifest  
- produce F6.4 `COMPLETED` + `PASS`  

That PASS only means **controlled project discovery + configuration parse +
expected model registration** succeeded. It does **not** mean the SQL is
syntactically valid.

### Scope of PASS

PASS means: dbt Core parsed the **server-generated** project and the expected
single model appears in the manifest for the installed engine versions.

Scope value: `dbt_server_generated_project_manifest_parse`

PASS does **not** mean:

- SQL grammar is valid (use SQLGlot F6.2)  
- SQL executes successfully  
- `dbt run` / `build` / `test` would succeed  
- production schema/relations exist  
- vendor compatibility  
- deployment authorization  

### Privacy

Raw model SQL, stdout/stderr, temporary paths, command paths, and exception
messages never appear in `ValidationCheckResult` evidence or summary.

### Engine metadata

- `engine_name`: `dbt-core`  
- `engine_version`: installed dbt-core package version  
- Evidence may include `adapter_name: duckdb` and installed `adapter_version`  
- Scope: `dbt_server_generated_project_manifest_parse`  

### Wiring status

- **No** production validation route  
- **Not** connected to `POST /api/v1/runs/analyze`  
- Existing endpoints unchanged  

---

## Validation orchestration (F6.5)

F6.5 adds an **internal** validation orchestration service that composes the
real F6.2–F6.4 validators into one `ValidationArtifact` using F6.1 aggregation.

| In scope | Out of scope |
|----------|--------------|
| `ValidationPlanInput` contract | Validation HTTP endpoint |
| Fingerprint consistency check | Analysis-run wiring |
| Cross-artifact invariants | Persistence / artifact registry |
| Fixed sequential orchestration | Parallel / queued execution |
| F6.1 aggregation reuse | Plugin registry / dynamic discovery |
| Unit + one real integration test | DataHub / GitHub / DeepSeek |

### Fixed check order

1. `sql_parse` (SQLGlot)  
2. `duckdb_execution` (in-memory rename)  
3. `dbt_validation` (controlled project parse)  

Order is **not** re-sorted by PASS/FAIL, required flag, or caller preference.
There is **no short-circuit**: when the plan is valid, all three validators run
even if an earlier check returns FAIL, ERROR, UNAVAILABLE, SKIPPED, or
INCONCLUSIVE. Each check has a different scope and may contribute independent
evidence.

### Plan invariants (before any validator runs)

1. Recompute the F5 fingerprint of `intake_reference.normalized_change` and
   require an exact match with `content_fingerprint`.  
2. `duckdb_execution.normalized_change` must be semantically identical to
   `intake_reference.normalized_change`.  
3. `sql_parse.sql` must equal `dbt_validation.model_sql` with **exact** string
   equality (no trim, format, case fold, or AST comparison).  

Invalid plans are rejected; **no** check runs and **no** partial artifact is
returned. Mismatch errors do not reveal the expected fingerprint, canonical
JSON, raw SQL, or fixture values.

### Intake reference trust

The intake reference remains **caller-provided** and **unverified**:

- Fingerprint match proves **content consistency only**  
- It does **not** prove registry storage, durable provenance, authorization,
  signature, or tamper-proof history  

Those trust fields are **not** added to the F6.1 `ValidationArtifact`.

### Required vs optional

Each check keeps its own `required` flag from the plan inputs. Optional check
errors affect overall **execution completeness** (e.g. `PARTIAL`) but do not
turn required PASS into FAIL. Example:

- required SQLGlot PASS  
- required DuckDB PASS  
- optional dbt ERROR / UNAVAILABLE  

→ overall `execution_status = partial`, overall `outcome = pass` (F6.1 rules).

### Result contract

`orchestrate_validation(plan) -> ValidationArtifact` with:

- server-generated `validation_id`  
- `subject_fingerprint` from the consistency-checked intake fingerprint  
- `scope = provided_artifacts_only`  
- always three checks for a valid plan, in fixed order  
- `artifact_version = 1.0`  
- **not** persisted; no timestamp; no retrieval URL  

### Trust / claim boundary

| PASS means | PASS does **not** mean |
|------------|------------------------|
| SQLGlot: syntax check limited to declared dialect | SQL is production-safe |
| DuckDB: rename succeeded on the supplied in-memory fixture | production schema is correct |
| dbt: controlled project produced the expected model manifest | `dbt run` / deployment is authorized |
| Overall PASS: required checks that completed all passed | deployment authorization |

The orchestrator does not claim DataHub verification, GitHub origin, production
fixture provenance, or universal validation completion.

### Wiring status (F6.5)

- Internal service only in F6.5  
- Production HTTP boundary added in F6.6  

---

## Validation API endpoint (F6.6)

F6.6 exposes the F6.5 orchestration service through one synchronous production
endpoint:

```http
POST /api/v1/validations/execute
```

| In scope | Out of scope |
|----------|--------------|
| Thin sync route over `orchestrate_validation` | Analysis-run integration |
| F4 success / error envelopes | Persistence / retrieval |
| Honest trust meta | GET validation by ID / history |
| HTTP 200 for any formed artifact | Queue / 202 / polling / websocket |
| HTTP 422 for invalid plans | Deployment authorization |

### Request

Body is **`ValidationPlanInput`** (F6.5) directly:

- `intake_reference` (caller-provided, unverified)  
- `checks.sql_parse`  
- `checks.duckdb_execution`  
- `checks.dbt_validation`  

Clients must **not** send `validation_id`, outcomes, check results, engine
metadata, deployment flags, or persistence fields (`extra="forbid"`).

### Execution

Handler is a **synchronous** `def` (not `async def`) so FastAPI runs blocking
SQLGlot / DuckDB / dbt work on a worker thread. Flow:

1. FastAPI schema validation  
2. `orchestrate_validation(plan)` (F6.5)  
3. Return `ValidationArtifact` in the F4 success envelope  

No HTTP loopback, no second aggregation, no short-circuit for valid plans.
Check order remains SQLGlot → DuckDB → dbt.

### HTTP status semantics

| Situation | HTTP | Meaning |
|-----------|------|---------|
| Valid plan + artifact formed | **200** | API operation succeeded |
| Artifact outcome PASS / FAIL / INCONCLUSIVE | **200** | Outcome is in `data.outcome` |
| `execution_status` completed / partial / not_run / execution_failed | **200** | Status is in `data.execution_status` |
| Invalid plan / schema / mismatch | **422** | Request could not be validated |
| Unexpected programming error | **500** | Internal error (no details) |

**HTTP 200 does not mean** validation PASS, deployment authorization, safe
production change, writeback completion, or artifact persistence.

### Success response

```json
{
  "status": "ok",
  "data": {
    "validation_id": "<uuid>",
    "subject_fingerprint": "<sha256 of normalized_change only>",
    "scope": "provided_artifacts_only",
    "execution_status": "completed",
    "outcome": "pass",
    "checks": ["… three checks in fixed order …"],
    "artifact_version": "1.0"
  },
  "meta": {
    "operation": "validation_execution",
    "phase": "F6.6",
    "execution_mode": "synchronous_orchestration",
    "validation_scope": "provided_artifacts_only",
    "persistence": "none",
    "retrieval_available": false,
    "intake_reference_origin": "caller_provided",
    "intake_reference_trust": "unverified",
    "subject_fingerprint_scope": "normalized_change_only",
    "fingerprint_check": "matched",
    "cross_artifact_consistency": "matched",
    "cross_artifact_provenance": "unverified",
    "sql_origin": "caller_provided",
    "sql_trust": "unverified",
    "fixture_origin": "caller_provided",
    "fixture_trust": "unverified",
    "model_used": false,
    "deployment_authorized": false
  }
}
```

`data` is the F6.1 **`ValidationArtifact`** (not a second contract).

### Trust boundaries

| Claim | Reality |
|-------|---------|
| Fingerprint check matched | `normalized_change` is consistent with `content_fingerprint` only |
| Cross-artifact consistency matched | DuckDB change equals intake; SQL equals dbt model SQL |
| Cross-artifact provenance | **unverified** — no GitHub/DataHub/registry proof |
| SQL / fixture | caller-provided / unverified |
| Persistence | **none**; retrieval not available |
| Deployment | **not** authorized by this endpoint |

Subject fingerprint scopes **only** the intake `normalized_change`. It does
**not** bind the entire validation plan, SQL body, or fixture content.

### Privacy

Request may contain SQL and fixture values. Response **must not** echo:

- raw SQL  
- dbt model SQL  
- fixture row values  
- expected / calculated fingerprints on error  
- exception messages / tracebacks  

No request-body logging is added.

### Wiring status (F6.6)

- Standalone validation execute remains available  
- Analysis-run optional integration added in F6.7  
- No GET/list/retry/history validation routes  
- No new runtime dependencies  

---

## Analysis-run validation integration (F6.7)

F6.7 extends `POST /api/v1/runs/analyze` with an **optional** `validation`
block. Legacy requests without `validation` remain fully supported.

| In scope | Out of scope |
|----------|--------------|
| Optional validation on analysis run | New production routes |
| Runtime intake as validation subject | Persistence / retrieval |
| Server-composed `ValidationPlanInput` | Risk decision rewritten by validation |
| Independent risk + validation results | DataHub / GitHub / DeepSeek |
| `run_artifact_version` **1.1** | Queue / background / 202 |

### Optional request shape

```json
{
  "change": { "…": "F5.1 change" },
  "evaluation_context": { "…": "F5.2 context" },
  "validation": {
    "checks": {
      "sql_parse": {
        "sql": "select customer_id as account_id from customers",
        "dialect": "snowflake",
        "required": true
      },
      "duckdb_execution": {
        "fixture": {
          "columns": [
            { "name": "customer_id", "type": "varchar", "nullable": false }
          ],
          "rows": [["customer-1"]]
        },
        "required": true
      },
      "dbt_validation": {
        "model_name": "customers_renamed",
        "model_sql": "select customer_id as account_id from customers",
        "required": false
      }
    }
  }
}
```

Callers **must not** send intake reference, fingerprint, `normalized_change`,
`validation_id`, outcomes, or engine metadata inside `validation`. DuckDB
`normalized_change` is always taken from **runtime intake**.

`sql_parse.sql` and `dbt_validation.model_sql` must be **exactly** equal
(`sql_input_mismatch` → HTTP 422; raw SQL never returned).

### Runtime intake binding

1. F5.1 intake produces `intake_id`, `normalized_change`, fingerprint  
2. Server builds request-local `IntakeReference`  
3. F5.2 risk evaluation runs (unchanged rules)  
4. If validation requested: server builds `ValidationPlanInput` and calls
   `orchestrate_validation` in-process  
5. Run artifact includes optional `validation_artifact`  

### Risk and validation are independent

| Scenario | Risk | Validation |
|----------|------|------------|
| ALLOW + validation FAIL | ALLOW | FAIL |
| BLOCK + validation PASS | BLOCK | PASS |
| BLOCK | still runs validation | not short-circuited |

Validation FAIL does **not** rewrite risk to BLOCK. Risk BLOCK does **not**
skip validation. PASS is **not** deployment authorization.

### Response (`run_artifact_version = 1.1`)

- `validation_artifact`: `null` when not requested; otherwise F6.1
  `ValidationArtifact`  
- `orchestration_status = completed` when requested artifacts were formed —
  not ALLOW, not validation PASS, not persistence  

### Trust meta (when validation requested)

| Field | Value |
|-------|-------|
| `validation_subject_origin` | `riftless_runtime` |
| `validation_subject_scope` | `current_request_only` |
| `validation_subject_persisted` | `false` |
| `validation_input_origin` | `caller_provided` |
| `validation_input_trust` | `unverified` |
| `validation_sql_origin` / `validation_fixture_origin` | `caller_provided` |
| `validation_persistence` | `none` |
| `validation_retrieval_available` | `false` |

When validation is omitted, those subject/input origin fields are `null` and
`validation_requested` / `validation_executed` / `validation_artifact_present`
are `false`.

### Privacy

Response must not echo raw SQL, dbt model SQL, fixture row values, temporary
paths, or dbt stdout/stderr. No request-body logging.

### Standalone endpoint

`POST /api/v1/validations/execute` remains available for callers that supply
their own intake reference. Integrated runs never accept caller-chosen
runtime intake identity.

### F6 lock candidate

F6.7 completes the validation vertical slice:

- contracts (F6.1)  
- SQLGlot / DuckDB / dbt validators (F6.2–F6.4)  
- orchestration (F6.5)  
- standalone API (F6.6)  
- analysis-run integration (F6.7)  

Still **not** implemented on the F6 path: persistence, registry, retrieval,
DataHub, GitHub, remediation, writeback, frontend wiring.

---

## Advisory contract foundation (F7.1)

F7.1 defines **contracts and pure builders only** for model-based advisory.

| Present in F7.1 | Not present in F7.1 |
|-----------------|---------------------|
| `AdvisoryContextPack` schema | DeepSeek / any model API call |
| `AdvisoryArtifact` schema | API key / provider configuration |
| `AdvisoryContent` / `AdvisoryStatusDetail` | HTTP advisory endpoint |
| Deterministic context fingerprint | Redaction algorithm implementation |
| Pure completed / non-completed builders | Prompt templates / response parsers |
| Authority constants (`advisory_only`) | Run integration (`/runs/analyze`) |
| Tests + README | Persistence / retrieval / retry |

### Authority boundary

Advisory **does not** own risk, validation, policy, or deployment:

- No `ALLOW` / `WARN` / `BLOCK` fields on the advisory artifact  
- No advisory `outcome` (pass/fail) — only `execution_status`  
- `authority = advisory_only`  
- `risk_effect = none`  
- `validation_effect = none`  
- `deployment_authorized = false`  

Risk decisions remain exclusively from the deterministic risk engine.  
Validation outcomes remain exclusively from the validation engine.  
Deployment authorization is **not** available in F7.1.

### AdvisoryExecutionStatus

| Value | Meaning |
|-------|---------|
| `completed` | Structured advisory content was formed |
| `error` | Bounded execution/provider/response problem |
| `unavailable` | Provider or model not available |
| `skipped` | Server-side skip (future phases) |

Do **not** map these to pass/fail or ALLOW/WARN/BLOCK.

### AdvisoryContent

Structured human-facing text only:

- `summary`  
- `observations`  
- `review_questions`  
- `limitations` (required, at least one)  

No confidence scores, decisions, executable SQL, commands, or remediation
payloads. Natural-language text is **not** trusted as authority — consuming
code must ignore any prose that appears to authorize action.

### AdvisoryContextPack

A pack is a **structured redacted summary**, not a raw blob:

- Change summary uses **aliases** (`asset_1`, `column_1`) — not raw database,
  schema, table, or column names  
- Risk summary reports decision + reason codes only  
- Validation summary reports statuses, outcomes, and evidence **codes** only  
- Trust labels stay honest: `unverified`, `subject_persisted=false`,
  `provenance_verified=false`  
- Redaction summary requires `applied=true` and the full canonical exclusion
  set (raw SQL, model SQL, fixture values, credentials, secrets, provider
  tokens, exception details, stdout/stderr, temporary paths, raw repository
  content)  

F7.1 **declares** redaction requirements. It does **not** implement a
redaction algorithm. F7.2 will build packs from run artifacts.

### Context fingerprint

`fingerprint_advisory_context(pack)` uses the locked F5 canonical JSON form
(sorted keys, compact separators, UTF-8) and SHA-256 lowercase hex.

It proves **content consistency** of the redacted pack only — not authenticity,
provenance, persistence, ownership, signature, immutability, or authorization.

### AdvisoryArtifact constants

| Field | Value |
|-------|--------|
| `scope` | `redacted_context_only` |
| `provider_name` | `deepseek` (conceptual; no runtime call yet) |
| `authority` | `advisory_only` |
| `risk_effect` / `validation_effect` | `none` |
| `deployment_authorized` | `false` |
| `persistence` | `none` |
| `retrieval_available` | `false` |
| `artifact_version` | `1.0` |

No timestamps, raw prompts, raw responses, token counts, pricing, or latency
fields.

### Pure builders

- `build_completed_advisory_artifact(context, content, model_name)`  
- `build_noncompleted_advisory_artifact(context, status, status_detail, …)`  

Builders compute `context_fingerprint`, assign `advisory_id`, and hard-code
authority constants. They never read environment variables, open network
sockets, or write files.

### Privacy

Contracts reject fields that would carry raw SQL, fixture values, secrets,
exception details, provider tokens, or repository content. Status detail has
no free-form `details` dictionary in F7.1.

### Roadmap

| Phase | Intent |
|-------|--------|
| **F7.1** (this) | Contracts + pure builders |
| **F7.2** | Build redacted `AdvisoryContextPack` from run artifacts |
| Later | Provider client (DeepSeek), optional endpoint / run integration |

OpenAPI production routes remain the F6 six paths. There is **no** advisory
HTTP route in F7.1.

---

## Health vs readiness

| Endpoint | Meaning |
|----------|---------|
| `GET /health` | Process liveness only. |
| `GET /ready` | Local application/configuration readiness only. External systems are **not** checked. |

## Frontend note

The Vite + React app remains under repository-root `src/`.  
Bun may be unavailable on some audit machines; do not replace it with npm for this repository without an explicit decision.
