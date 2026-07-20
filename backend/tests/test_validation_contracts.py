"""Unit tests for F6.1 validation contracts and aggregation."""

from __future__ import annotations

import copy
import uuid
from typing import Any

import pytest
from pydantic import ValidationError

from app.schemas.validation import (
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    OverallExecutionStatus,
    ValidationArtifact,
    ValidationCheckResult,
    ValidationEvidence,
)
from app.services.validation_engine import build_validation_artifact

SUBJECT_FP = "a" * 64


def _evidence(
    code: str = "check_note",
    message: str = "Safe evidence message.",
    details: Any = None,
) -> ValidationEvidence:
    return ValidationEvidence(code=code, message=message, details=details)


def _check(
    *,
    execution_status: CheckExecutionStatus,
    outcome: CheckOutcome | None,
    required: bool = True,
    evidence: list[ValidationEvidence] | None = None,
    check_kind: CheckKind = CheckKind.SQL_PARSE,
    scope: str = "rename_column syntax only",
    summary: str = "Check summary.",
    check_id: uuid.UUID | None = None,
) -> ValidationCheckResult:
    return ValidationCheckResult(
        check_id=check_id or uuid.uuid4(),
        check_kind=check_kind,
        required=required,
        execution_status=execution_status,
        outcome=outcome,
        scope=scope,
        summary=summary,
        evidence=evidence if evidence is not None else [],
        engine_name=None,
        engine_version=None,
    )


# ---- Schema / invariants -----------------------------------------------------


def test_completed_pass_valid() -> None:
    check = _check(
        execution_status=CheckExecutionStatus.COMPLETED,
        outcome=CheckOutcome.PASS,
    )
    assert check.execution_status == CheckExecutionStatus.COMPLETED.value
    assert check.outcome == CheckOutcome.PASS.value


def test_completed_fail_valid() -> None:
    check = _check(
        execution_status=CheckExecutionStatus.COMPLETED,
        outcome=CheckOutcome.FAIL,
        evidence=[_evidence(code="incompatible_type", message="Types conflict.")],
    )
    assert check.outcome == CheckOutcome.FAIL.value


def test_completed_inconclusive_valid() -> None:
    check = _check(
        execution_status=CheckExecutionStatus.COMPLETED,
        outcome=CheckOutcome.INCONCLUSIVE,
    )
    assert check.outcome == CheckOutcome.INCONCLUSIVE.value


def test_completed_outcome_null_rejected() -> None:
    with pytest.raises(ValidationError):
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=None,
        )


def test_error_with_outcome_rejected() -> None:
    with pytest.raises(ValidationError):
        _check(
            execution_status=CheckExecutionStatus.ERROR,
            outcome=CheckOutcome.FAIL,
            evidence=[_evidence(code="engine_error", message="Engine failed.")],
        )


def test_unavailable_with_outcome_rejected() -> None:
    with pytest.raises(ValidationError):
        _check(
            execution_status=CheckExecutionStatus.UNAVAILABLE,
            outcome=CheckOutcome.PASS,
            evidence=[_evidence(code="engine_missing", message="Not installed.")],
        )


def test_skipped_with_outcome_rejected() -> None:
    with pytest.raises(ValidationError):
        _check(
            execution_status=CheckExecutionStatus.SKIPPED,
            outcome=CheckOutcome.INCONCLUSIVE,
            evidence=[_evidence(code="skipped_reason", message="Skipped by policy.")],
        )


def test_error_without_evidence_rejected() -> None:
    with pytest.raises(ValidationError):
        _check(
            execution_status=CheckExecutionStatus.ERROR,
            outcome=None,
            evidence=[],
        )


def test_unavailable_without_evidence_rejected() -> None:
    with pytest.raises(ValidationError):
        _check(
            execution_status=CheckExecutionStatus.UNAVAILABLE,
            outcome=None,
            evidence=[],
        )


def test_skipped_without_evidence_rejected() -> None:
    with pytest.raises(ValidationError):
        _check(
            execution_status=CheckExecutionStatus.SKIPPED,
            outcome=None,
            evidence=[],
        )


def test_invalid_evidence_code_rejected() -> None:
    with pytest.raises(ValidationError):
        ValidationEvidence(code="Not-Snake", message="Bad code.")


def test_blank_scope_rejected() -> None:
    with pytest.raises(ValidationError):
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            scope="   ",
        )


def test_blank_summary_rejected() -> None:
    with pytest.raises(ValidationError):
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            summary="",
        )


def test_invalid_subject_fingerprint_rejected() -> None:
    with pytest.raises(ValidationError):
        ValidationArtifact(
            validation_id=uuid.uuid4(),
            subject_fingerprint="NOT_HEX",
            execution_status=OverallExecutionStatus.NOT_RUN,
            outcome=CheckOutcome.INCONCLUSIVE,
            checks=[],
        )


def test_error_with_evidence_valid() -> None:
    check = _check(
        execution_status=CheckExecutionStatus.ERROR,
        outcome=None,
        evidence=[_evidence(code="engine_error", message="Execution failed safely.")],
    )
    assert check.outcome is None
    assert len(check.evidence) == 1


# ---- Aggregation -------------------------------------------------------------


def test_empty_checks_not_run_inconclusive() -> None:
    artifact = build_validation_artifact(subject_fingerprint=SUBJECT_FP, checks=[])
    assert artifact.execution_status == OverallExecutionStatus.NOT_RUN.value
    assert artifact.outcome == CheckOutcome.INCONCLUSIVE.value
    assert artifact.checks == []


def test_all_required_pass_completed_pass() -> None:
    checks = [
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            required=True,
            check_kind=CheckKind.SQL_PARSE,
        ),
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            required=True,
            check_kind=CheckKind.DUCKDB_EXECUTION,
        ),
    ]
    artifact = build_validation_artifact(subject_fingerprint=SUBJECT_FP, checks=checks)
    assert artifact.execution_status == OverallExecutionStatus.COMPLETED.value
    assert artifact.outcome == CheckOutcome.PASS.value


def test_one_required_fail_overall_fail() -> None:
    checks = [
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            required=True,
        ),
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.FAIL,
            required=True,
            evidence=[_evidence(code="rule_fail", message="Found failure.")],
        ),
    ]
    artifact = build_validation_artifact(subject_fingerprint=SUBJECT_FP, checks=checks)
    assert artifact.outcome == CheckOutcome.FAIL.value
    assert artifact.execution_status == OverallExecutionStatus.COMPLETED.value


def test_required_pass_and_inconclusive_overall_inconclusive() -> None:
    checks = [
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            required=True,
        ),
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.INCONCLUSIVE,
            required=True,
        ),
    ]
    artifact = build_validation_artifact(subject_fingerprint=SUBJECT_FP, checks=checks)
    assert artifact.outcome == CheckOutcome.INCONCLUSIVE.value
    assert artifact.execution_status == OverallExecutionStatus.COMPLETED.value


def test_required_pass_and_error_partial_inconclusive() -> None:
    checks = [
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            required=True,
        ),
        _check(
            execution_status=CheckExecutionStatus.ERROR,
            outcome=None,
            required=True,
            evidence=[_evidence(code="engine_error", message="Crashed.")],
        ),
    ]
    artifact = build_validation_artifact(subject_fingerprint=SUBJECT_FP, checks=checks)
    assert artifact.execution_status == OverallExecutionStatus.PARTIAL.value
    assert artifact.outcome == CheckOutcome.INCONCLUSIVE.value


def test_all_error_execution_failed_inconclusive() -> None:
    checks = [
        _check(
            execution_status=CheckExecutionStatus.ERROR,
            outcome=None,
            required=True,
            evidence=[_evidence(code="engine_error", message="Error A.")],
        ),
        _check(
            execution_status=CheckExecutionStatus.ERROR,
            outcome=None,
            required=True,
            evidence=[_evidence(code="engine_error", message="Error B.")],
        ),
    ]
    artifact = build_validation_artifact(subject_fingerprint=SUBJECT_FP, checks=checks)
    assert artifact.execution_status == OverallExecutionStatus.EXECUTION_FAILED.value
    assert artifact.outcome == CheckOutcome.INCONCLUSIVE.value


def test_all_unavailable_not_run_inconclusive() -> None:
    checks = [
        _check(
            execution_status=CheckExecutionStatus.UNAVAILABLE,
            outcome=None,
            required=True,
            evidence=[_evidence(code="sqlglot_unavailable", message="Not installed.")],
            check_kind=CheckKind.SQL_PARSE,
        ),
        _check(
            execution_status=CheckExecutionStatus.UNAVAILABLE,
            outcome=None,
            required=True,
            evidence=[_evidence(code="duckdb_unavailable", message="Not installed.")],
            check_kind=CheckKind.DUCKDB_EXECUTION,
        ),
    ]
    artifact = build_validation_artifact(subject_fingerprint=SUBJECT_FP, checks=checks)
    assert artifact.execution_status == OverallExecutionStatus.NOT_RUN.value
    assert artifact.outcome == CheckOutcome.INCONCLUSIVE.value


def test_completed_and_skipped_partial() -> None:
    checks = [
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            required=True,
        ),
        _check(
            execution_status=CheckExecutionStatus.SKIPPED,
            outcome=None,
            required=False,
            evidence=[_evidence(code="skipped_optional", message="Not needed.")],
        ),
    ]
    artifact = build_validation_artifact(subject_fingerprint=SUBJECT_FP, checks=checks)
    assert artifact.execution_status == OverallExecutionStatus.PARTIAL.value
    assert artifact.outcome == CheckOutcome.PASS.value


def test_optional_fail_does_not_fail_required_pass() -> None:
    checks = [
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            required=True,
        ),
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.FAIL,
            required=False,
            evidence=[_evidence(code="optional_fail", message="Optional only.")],
        ),
    ]
    artifact = build_validation_artifact(subject_fingerprint=SUBJECT_FP, checks=checks)
    assert artifact.outcome == CheckOutcome.PASS.value
    assert artifact.execution_status == OverallExecutionStatus.COMPLETED.value
    assert len(artifact.checks) == 2


def test_no_required_check_inconclusive() -> None:
    checks = [
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            required=False,
        ),
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.FAIL,
            required=False,
            evidence=[_evidence(code="optional_fail", message="Optional fail.")],
        ),
    ]
    artifact = build_validation_artifact(subject_fingerprint=SUBJECT_FP, checks=checks)
    assert artifact.outcome == CheckOutcome.INCONCLUSIVE.value
    assert artifact.execution_status == OverallExecutionStatus.COMPLETED.value


def test_check_order_preserved() -> None:
    id_a = uuid.uuid4()
    id_b = uuid.uuid4()
    id_c = uuid.uuid4()
    checks = [
        _check(
            check_id=id_a,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            check_kind=CheckKind.SQL_PARSE,
        ),
        _check(
            check_id=id_b,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            check_kind=CheckKind.DUCKDB_EXECUTION,
        ),
        _check(
            check_id=id_c,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            check_kind=CheckKind.DBT_VALIDATION,
        ),
    ]
    artifact = build_validation_artifact(subject_fingerprint=SUBJECT_FP, checks=checks)
    assert [c.check_id for c in artifact.checks] == [id_a, id_b, id_c]


def test_validation_id_uuid_and_artifact_metadata() -> None:
    artifact = build_validation_artifact(subject_fingerprint=SUBJECT_FP, checks=[])
    uuid.UUID(str(artifact.validation_id))
    assert artifact.artifact_version == "1.0"
    assert artifact.scope == "provided_artifacts_only"
    assert artifact.subject_fingerprint == SUBJECT_FP


def test_build_does_not_mutate_input_list() -> None:
    original = [
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
        )
    ]
    snapshot = copy.deepcopy(original)
    artifact = build_validation_artifact(
        subject_fingerprint=SUBJECT_FP,
        checks=original,
    )
    assert original[0].check_id == snapshot[0].check_id
    assert original[0].outcome == snapshot[0].outcome
    # Artifact holds the same check objects by value/identity after list copy,
    # but the input list identity/length must remain unchanged.
    assert len(original) == 1
    assert len(artifact.checks) == 1
    original.append(
        _check(
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.FAIL,
            evidence=[_evidence()],
        )
    )
    assert len(artifact.checks) == 1


def test_invalid_fingerprint_in_builder_rejected() -> None:
    with pytest.raises(ValueError):
        build_validation_artifact(subject_fingerprint="zzzz", checks=[])


def test_check_kind_contract_values() -> None:
    assert CheckKind.SQL_PARSE.value == "sql_parse"
    assert CheckKind.DUCKDB_EXECUTION.value == "duckdb_execution"
    assert CheckKind.DBT_VALIDATION.value == "dbt_validation"


def test_evidence_details_primitives_only() -> None:
    ok = ValidationEvidence(
        code="detail_ok",
        message="Structured details allowed.",
        details={"count": 1, "flags": [True, False], "note": "x"},
    )
    assert ok.details["count"] == 1
    with pytest.raises(ValidationError):
        ValidationEvidence(
            code="detail_bad",
            message="Objects not allowed.",
            details={"obj": object()},
        )


def test_regression_existing_api_routes_still_registered() -> None:
    """F6.1 must not remove production routes; no validation route yet."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    # Existing production endpoints remain available (behavioral check).
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200

    # Path inventory via OpenAPI (stable across FastAPI routing internals).
    paths = set(app.openapi()["paths"].keys())
    assert "/health" in paths
    assert "/ready" in paths
    assert "/api/v1/changes/intake" in paths
    assert "/api/v1/risk/evaluate" in paths
    assert "/api/v1/runs/analyze" in paths
    # No production validation route in F6.1
    assert not any("validat" in path for path in paths)
