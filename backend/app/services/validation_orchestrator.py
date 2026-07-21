"""Validation orchestration service (phase F6.5).

Runs the real F6.2–F6.4 validators in a fixed sequential order and assembles
a ValidationArtifact via the F6.1 aggregation pure functions.

This module does **not**:
- expose an HTTP endpoint
- short-circuit on FAIL / ERROR / UNAVAILABLE
- persist artifacts
- call validators over HTTP
- invent a second aggregation implementation
"""

from __future__ import annotations

from app.schemas.validation import ValidationArtifact
from app.schemas.validation_plan import (
    ValidationPlanInput,
    assert_validation_plan_invariants,
)
from app.services.dbt_parse_validator import run_dbt_parse_check
from app.services.duckdb_rename_validator import run_duckdb_rename_check
from app.services.sql_parse_validator import run_sql_parse_check
from app.services.validation_engine import build_validation_artifact

# Fixed orchestration order (never reordered by outcome or required flag).
CHECK_ORDER = (
    "sql_parse",
    "duckdb_execution",
    "dbt_validation",
)


def orchestrate_validation(plan: ValidationPlanInput) -> ValidationArtifact:
    """Run SQLGlot → DuckDB → dbt and aggregate into a ValidationArtifact.

    Step 1 — re-assert plan / cross-artifact invariants (reject before any run).
    Step 2 — ``run_sql_parse_check``
    Step 3 — ``run_duckdb_rename_check``
    Step 4 — ``run_dbt_parse_check``
    Step 5 — collect results in fixed order
    Step 6 — ``build_validation_artifact`` (F6.1 aggregation)
    Step 7 — return the artifact (not persisted)

    All three validators run when the plan is valid (no short-circuit).
    Unexpected exceptions from orchestration itself are not converted into a
    fake PASS/FAIL artifact — they propagate to the future integration boundary.
    """
    subject_fingerprint = assert_validation_plan_invariants(plan)

    # Fixed sequential order. Do not reorder or skip based on outcomes.
    sql_result = run_sql_parse_check(plan.checks.sql_parse)
    duckdb_result = run_duckdb_rename_check(plan.checks.duckdb_execution)
    dbt_result = run_dbt_parse_check(plan.checks.dbt_validation)

    check_results = [sql_result, duckdb_result, dbt_result]

    return build_validation_artifact(
        subject_fingerprint=subject_fingerprint,
        checks=check_results,
    )
