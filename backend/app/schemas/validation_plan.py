"""Validation plan input contracts (phase F6.5).

Composes existing F5/F6 input schemas into a single internal plan for the
validation orchestrator. Does **not** define HTTP request bodies, outcomes,
or engine metadata from the caller.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.dbt_validation import DbtParseInput
from app.schemas.duckdb_validation import DuckDbRenameInput
from app.schemas.risk import IntakeReference
from app.schemas.sql_validation import SqlParseInput
from app.utils.fingerprint import fingerprint_payload, fingerprints_match

# Caller must not inject decisions, outcomes, generated results, or engine
# metadata into a validation plan.
_FORBIDDEN_PLAN_KEYS = frozenset(
    {
        "decision",
        "outcome",
        "execution_status",
        "validation_id",
        "validation_result",
        "check_results",
        "checks_results",
        "results",
        "artifact",
        "engine_name",
        "engine_version",
        "engine_metadata",
        "generated_check_result",
        "generated_check_results",
    }
)


class ValidationPlanChecks(BaseModel):
    """Fixed set of check inputs for F6.5 orchestration.

    Field order is documentation only; orchestration order is fixed in the
    service layer (sql_parse → duckdb_execution → dbt_validation).
    """

    model_config = ConfigDict(extra="forbid")

    sql_parse: SqlParseInput
    duckdb_execution: DuckDbRenameInput
    dbt_validation: DbtParseInput


class ValidationPlanInput(BaseModel):
    """Internal plan for orchestrating F6.2–F6.4 validators.

    - Reuses ``IntakeReference``, ``SqlParseInput``, ``DuckDbRenameInput``,
      and ``DbtParseInput`` without copying their rules.
    - Rejects unknown fields and outcome/decision injection.
    - Enforces fingerprint consistency and cross-artifact invariants before
      any validator runs.
    """

    model_config = ConfigDict(extra="forbid")

    intake_reference: IntakeReference
    checks: ValidationPlanChecks

    @model_validator(mode="before")
    @classmethod
    def reject_forbidden_plan_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            forbidden = _FORBIDDEN_PLAN_KEYS.intersection(data.keys())
            if forbidden:
                raise ValueError(
                    "plan must not include decision, outcome, or generated "
                    "result fields: "
                    + ", ".join(sorted(forbidden))
                )
        return data

    @model_validator(mode="after")
    def enforce_plan_invariants(self) -> ValidationPlanInput:
        """Fingerprint + cross-artifact consistency (no silent repair)."""
        assert_validation_plan_invariants(self)
        return self


def assert_validation_plan_invariants(plan: ValidationPlanInput) -> str:
    """Validate fingerprint and cross-artifact invariants.

    Returns the consistency-checked subject fingerprint on success.

    Raises ``ValueError`` without revealing the expected fingerprint, canonical
    JSON, raw SQL, or fixture values. Does **not** prove intake provenance,
    storage, authorization, or tamper-proof history.
    """
    ref = plan.intake_reference

    if ref.artifact_version != "1.0":
        raise ValueError("Unsupported artifact_version.")

    computed = fingerprint_payload(ref.normalized_change.fingerprint_payload())
    if not fingerprints_match(computed, ref.content_fingerprint):
        # Do not include computed fingerprint or canonical JSON in the message.
        raise ValueError(
            "The supplied fingerprint does not match the normalized change."
        )

    intake_change = ref.normalized_change.fingerprint_payload()
    duckdb_change = plan.checks.duckdb_execution.normalized_change.fingerprint_payload()
    if intake_change != duckdb_change:
        raise ValueError(
            "DuckDB normalized_change must match intake_reference.normalized_change."
        )

    if plan.checks.sql_parse.sql != plan.checks.dbt_validation.model_sql:
        raise ValueError("SQLGlot sql and dbt model_sql must be identical.")

    return ref.content_fingerprint
