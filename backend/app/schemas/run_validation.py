"""Optional validation inputs for analysis runs (phase F6.7).

Caller supplies SQL, fixture, and dbt model inputs only. Runtime intake
identity (intake_id, normalized_change, fingerprint) is never accepted from
the client for integrated runs.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.dbt_validation import DbtParseInput
from app.schemas.duckdb_validation import DuckDbFixture
from app.schemas.sql_validation import SqlParseInput

# Fields that would let the caller invent runtime intake provenance or inject
# generated validation results into an analysis run.
_FORBIDDEN_RUN_VALIDATION_KEYS = frozenset(
    {
        "intake_reference",
        "intake_id",
        "normalized_change",
        "content_fingerprint",
        "artifact_version",
        "validation_id",
        "validation_artifact",
        "validation_result",
        "outcome",
        "execution_status",
        "decision",
        "check_results",
        "checks_results",
        "results",
        "engine_name",
        "engine_version",
        "engine_metadata",
        "subject_fingerprint",
        "run_id",
    }
)

_FORBIDDEN_DUCKDB_KEYS = frozenset(
    {
        "normalized_change",
        "intake_reference",
        "intake_id",
        "content_fingerprint",
        "sql",
        "model_sql",
        "setup_sql",
        "query",
        "script",
        "command",
        "arguments",
        "args",
    }
)


class RunDuckDbCheckInput(BaseModel):
    """Caller-facing DuckDB check for integrated runs.

    ``normalized_change`` is supplied by the server from runtime intake —
    never by the caller.
    """

    model_config = ConfigDict(extra="forbid")

    fixture: DuckDbFixture
    required: bool = True

    @model_validator(mode="before")
    @classmethod
    def reject_runtime_or_sql_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            forbidden = _FORBIDDEN_DUCKDB_KEYS.intersection(data.keys())
            if forbidden:
                raise ValueError(
                    "run DuckDB check must not include runtime identity or SQL "
                    "fields: "
                    + ", ".join(sorted(forbidden))
                )
        return data


class RunValidationChecks(BaseModel):
    """Fixed check inputs supplied by the caller for an analysis run."""

    model_config = ConfigDict(extra="forbid")

    sql_parse: SqlParseInput
    duckdb_execution: RunDuckDbCheckInput
    dbt_validation: DbtParseInput


class RunValidationInput(BaseModel):
    """Optional validation block on POST /api/v1/runs/analyze.

    Does not accept intake reference, fingerprint, or generated results.
    Enforces exact SQL equality between SQLGlot and dbt model SQL.
    """

    model_config = ConfigDict(extra="forbid")

    checks: RunValidationChecks

    @model_validator(mode="before")
    @classmethod
    def reject_forbidden_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            forbidden = _FORBIDDEN_RUN_VALIDATION_KEYS.intersection(data.keys())
            if forbidden:
                raise ValueError(
                    "run validation must not include runtime identity or "
                    "generated result fields: "
                    + ", ".join(sorted(forbidden))
                )
        return data

    @model_validator(mode="after")
    def enforce_sql_equality(self) -> RunValidationInput:
        """Exact string equality — no trim, format, or case folding."""
        if self.checks.sql_parse.sql != self.checks.dbt_validation.model_sql:
            # Safe reason code only — never include either SQL string.
            raise ValueError(
                "sql_input_mismatch: SQLGlot sql and dbt model_sql must be identical"
            )
        return self
