"""Validation domain contracts for phase F6.1.

Contract-only: these types define the shared shape for future SQLGlot,
DuckDB, and dbt validators. No SQL is parsed or executed here. No dbt
command is run. Presence of check-kind names does **not** mean executors
exist.

Three concepts are kept separate:

1. **execution_status** — whether a validator actually ran to completion.
2. **outcome** — result of a check that completed (pass / fail / inconclusive).
3. **evidence** — bounded, safe structured proof items for a check.

Execution error is not validation failure. PASS is not deployment
authorization. COMPLETED is not PASS. UNAVAILABLE is not FAIL.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.utils.fingerprint import is_sha256_hex

# ---- Reasonable bounds (not security claims) ---------------------------------

_MAX_CODE = 128
_MAX_MESSAGE = 1000
_MAX_SUMMARY = 1000
_MAX_SCOPE = 256
_MAX_ENGINE_NAME = 64
_MAX_ENGINE_VERSION = 64
_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")

VALIDATION_ARTIFACT_VERSION = "1.0"
VALIDATION_SCOPE = "provided_artifacts_only"


# ---- Enums -------------------------------------------------------------------


class CheckKind(str, Enum):
    """Named validation check kinds (contract-only in F6.1).

    These labels will be used by future executors. Defining them here does
    **not** implement SQLGlot, DuckDB, or dbt execution.
    """

    SQL_PARSE = "sql_parse"
    DUCKDB_EXECUTION = "duckdb_execution"
    DBT_VALIDATION = "dbt_validation"


class CheckExecutionStatus(str, Enum):
    """Whether a single check was actually executed."""

    COMPLETED = "completed"
    ERROR = "error"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"


class CheckOutcome(str, Enum):
    """Result of a check that finished execution successfully.

    Only meaningful when execution_status is COMPLETED.
    PASS does not authorize deployment or production mutation.
    """

    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"


class OverallExecutionStatus(str, Enum):
    """Aggregate execution status across a set of checks."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    NOT_RUN = "not_run"
    EXECUTION_FAILED = "execution_failed"


# Overall validation outcome reuses CheckOutcome semantics (pass/fail/inconclusive).
OverallValidationOutcome = CheckOutcome


# ---- Evidence ----------------------------------------------------------------


def _reject_blank(value: str, *, field_name: str) -> str:
    if value is None or not str(value).strip():
        raise ValueError(f"{field_name} must not be blank")
    return value


def _safe_details_value(value: Any, *, path: str = "details") -> Any:
    """Allow only JSON-safe primitive trees (no arbitrary objects)."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return [
            _safe_details_value(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} keys must be strings")
            safe[key] = _safe_details_value(item, path=f"{path}.{key}")
        return safe
    raise ValueError(
        f"{path} must contain only null, bool, int, float, str, list, or object values"
    )


class ValidationEvidence(BaseModel):
    """Bounded evidence item for a single check.

    Evidence is scoped proof for a check result. It is **not** authorization,
    a cryptographic signature, provenance proof, blockchain record, or
    deployment approval.
    """

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=_MAX_CODE)
    message: str = Field(min_length=1, max_length=_MAX_MESSAGE)
    details: Any = Field(
        default=None,
        description="Optional structured primitive details. May be null.",
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        cleaned = _reject_blank(value, field_name="code").strip()
        if not _SNAKE_CASE.fullmatch(cleaned):
            raise ValueError(
                "code must be lowercase snake_case (e.g. parser_unavailable)"
            )
        if len(cleaned) > _MAX_CODE:
            raise ValueError(f"code must be at most {_MAX_CODE} characters")
        return cleaned

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        cleaned = _reject_blank(value, field_name="message").strip()
        lowered = cleaned.lower()
        if "traceback" in lowered:
            raise ValueError("message must not contain traceback content")
        # Reject obvious absolute Windows/Unix paths in messages.
        if re.search(r"[A-Za-z]:\\", cleaned) or re.search(r"(^|\s)/[\w.-]+/", cleaned):
            raise ValueError("message must not contain internal filesystem paths")
        return cleaned

    @field_validator("details")
    @classmethod
    def validate_details(cls, value: Any) -> Any:
        return _safe_details_value(value)


# ---- Check result ------------------------------------------------------------


class ValidationCheckResult(BaseModel):
    """Result of one validation check attempt.

    State invariants (rejected if violated — never auto-repaired):

    - COMPLETED → outcome required (pass | fail | inconclusive)
    - ERROR / UNAVAILABLE / SKIPPED → outcome must be null; evidence non-empty
    - PASS / FAIL / INCONCLUSIVE outcomes only when COMPLETED
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    check_id: UUID
    check_kind: CheckKind
    required: bool
    execution_status: CheckExecutionStatus
    outcome: CheckOutcome | None = None
    scope: str = Field(min_length=1, max_length=_MAX_SCOPE)
    summary: str = Field(min_length=1, max_length=_MAX_SUMMARY)
    evidence: list[ValidationEvidence] = Field(default_factory=list)
    engine_name: str | None = Field(default=None, max_length=_MAX_ENGINE_NAME)
    engine_version: str | None = Field(default=None, max_length=_MAX_ENGINE_VERSION)

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, value: str) -> str:
        return _reject_blank(value, field_name="scope").strip()

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        cleaned = _reject_blank(value, field_name="summary").strip()
        if "traceback" in cleaned.lower():
            raise ValueError("summary must not contain traceback content")
        return cleaned

    @field_validator("engine_name", "engine_version")
    @classmethod
    def validate_optional_engine_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("engine fields must be null or non-blank")
        return cleaned

    @model_validator(mode="after")
    def enforce_execution_outcome_invariants(self) -> ValidationCheckResult:
        status = self.execution_status
        if isinstance(status, CheckExecutionStatus):
            status_value = status.value
        else:
            status_value = str(status)

        outcome = self.outcome
        if isinstance(outcome, CheckOutcome):
            outcome_value = outcome.value
        elif outcome is None:
            outcome_value = None
        else:
            outcome_value = str(outcome)

        if status_value == CheckExecutionStatus.COMPLETED.value:
            if outcome_value is None:
                raise ValueError(
                    "outcome is required when execution_status is completed"
                )
            if outcome_value not in {
                CheckOutcome.PASS.value,
                CheckOutcome.FAIL.value,
                CheckOutcome.INCONCLUSIVE.value,
            }:
                raise ValueError("invalid outcome for completed check")
            return self

        # Non-completed statuses: outcome must be null; evidence required.
        if outcome_value is not None:
            raise ValueError(
                f"outcome must be null when execution_status is {status_value}"
            )
        if not self.evidence:
            raise ValueError(
                f"evidence must contain at least one item when execution_status is {status_value}"
            )
        return self


# ---- Validation artifact -----------------------------------------------------


class ValidationArtifact(BaseModel):
    """Aggregated validation result for a subject fingerprint.

    Not persisted in F6.1. Scope is always provided_artifacts_only.
    subject_fingerprint identifies content deterministically; it is not a
    signature, auth token, provenance proof, or ledger entry.
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    validation_id: UUID
    subject_fingerprint: str = Field(min_length=64, max_length=64)
    scope: Literal["provided_artifacts_only"] = "provided_artifacts_only"
    execution_status: OverallExecutionStatus
    outcome: CheckOutcome
    checks: list[ValidationCheckResult] = Field(default_factory=list)
    artifact_version: Literal["1.0"] = "1.0"

    @field_validator("subject_fingerprint")
    @classmethod
    def validate_subject_fingerprint(cls, value: str) -> str:
        if not is_sha256_hex(value):
            raise ValueError(
                "subject_fingerprint must be a 64-character lowercase hexadecimal SHA-256 digest"
            )
        return value
