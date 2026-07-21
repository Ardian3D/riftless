"""Deterministic validation aggregation (phase F6.1).

Pure functions only: no network, database, filesystem, subprocess, or AI.
Does not mutate input check lists. Does not invent engine results.

This module aggregates already-formed ValidationCheckResult values into a
ValidationArtifact. It does **not** run SQLGlot, DuckDB, or dbt.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from app.schemas.validation import (
    VALIDATION_ARTIFACT_VERSION,
    VALIDATION_SCOPE,
    CheckExecutionStatus,
    CheckOutcome,
    OverallExecutionStatus,
    ValidationArtifact,
    ValidationCheckResult,
)
from app.utils.fingerprint import is_sha256_hex


def _status_value(status: CheckExecutionStatus | str) -> str:
    if isinstance(status, CheckExecutionStatus):
        return status.value
    return str(status)


def _outcome_value(outcome: CheckOutcome | str | None) -> str | None:
    if outcome is None:
        return None
    if isinstance(outcome, CheckOutcome):
        return outcome.value
    return str(outcome)


def aggregate_execution_status(
    checks: Sequence[ValidationCheckResult],
) -> OverallExecutionStatus:
    """Compute overall execution status from check execution statuses.

    Rules:
    1. empty → NOT_RUN
    2. all COMPLETED → COMPLETED
    3. some COMPLETED and some not → PARTIAL
    4. no COMPLETED and at least one ERROR → EXECUTION_FAILED
    5. no COMPLETED and no ERROR but UNAVAILABLE/SKIPPED present → NOT_RUN
    """
    if not checks:
        return OverallExecutionStatus.NOT_RUN

    statuses = [_status_value(check.execution_status) for check in checks]
    completed = CheckExecutionStatus.COMPLETED.value
    error = CheckExecutionStatus.ERROR.value

    all_completed = all(status == completed for status in statuses)
    any_completed = any(status == completed for status in statuses)
    any_error = any(status == error for status in statuses)

    if all_completed:
        return OverallExecutionStatus.COMPLETED
    if any_completed:
        return OverallExecutionStatus.PARTIAL
    if any_error:
        return OverallExecutionStatus.EXECUTION_FAILED
    return OverallExecutionStatus.NOT_RUN


def aggregate_outcome(
    checks: Sequence[ValidationCheckResult],
) -> CheckOutcome:
    """Compute overall validation outcome from **required** checks only.

    Rules:
    1. Any required COMPLETED+FAIL → FAIL
    2. At least one required check and all required are COMPLETED+PASS → PASS
    3. Otherwise → INCONCLUSIVE
       (includes required INCONCLUSIVE, ERROR, UNAVAILABLE, SKIPPED,
        no required checks, empty list)

    Optional checks never turn PASS into FAIL.
    """
    required = [check for check in checks if check.required]
    if not required:
        return CheckOutcome.INCONCLUSIVE

    completed = CheckExecutionStatus.COMPLETED.value
    fail = CheckOutcome.FAIL.value
    passed = CheckOutcome.PASS.value

    for check in required:
        if (
            _status_value(check.execution_status) == completed
            and _outcome_value(check.outcome) == fail
        ):
            return CheckOutcome.FAIL

    all_required_pass = all(
        _status_value(check.execution_status) == completed
        and _outcome_value(check.outcome) == passed
        for check in required
    )
    if all_required_pass:
        return CheckOutcome.PASS

    return CheckOutcome.INCONCLUSIVE


def build_validation_artifact(
    *,
    subject_fingerprint: str,
    checks: Sequence[ValidationCheckResult],
) -> ValidationArtifact:
    """Build a ValidationArtifact from a subject fingerprint and check results.

    - Preserves check order (shallow copy of the sequence into a new list).
    - Does not mutate the input sequence or its items.
    - Generates a new validation_id each call.
    - Does not persist the artifact.
    """
    if not is_sha256_hex(subject_fingerprint):
        raise ValueError(
            "subject_fingerprint must be a 64-character lowercase hexadecimal SHA-256 digest"
        )

    # Preserve order without mutating the caller's list/tuple.
    ordered_checks = list(checks)

    execution_status = aggregate_execution_status(ordered_checks)
    outcome = aggregate_outcome(ordered_checks)

    return ValidationArtifact(
        validation_id=uuid.uuid4(),
        subject_fingerprint=subject_fingerprint,
        scope=VALIDATION_SCOPE,
        execution_status=execution_status,
        outcome=outcome,
        checks=ordered_checks,
        artifact_version=VALIDATION_ARTIFACT_VERSION,
    )
