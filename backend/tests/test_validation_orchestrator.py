"""Unit and integration tests for F6.5 validation orchestration."""

from __future__ import annotations

import copy
import json
import uuid
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.schemas.changes import AssetNormalized, NormalizedChange
from app.schemas.dbt_validation import DbtParseInput
from app.schemas.duckdb_validation import (
    DuckDbFixture,
    DuckDbFixtureColumn,
    DuckDbRenameInput,
)
from app.schemas.risk import IntakeReference
from app.schemas.sql_validation import SqlDialect, SqlParseInput
from app.schemas.validation import (
    VALIDATION_ARTIFACT_VERSION,
    VALIDATION_SCOPE,
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    OverallExecutionStatus,
    ValidationArtifact,
    ValidationCheckResult,
    ValidationEvidence,
)
from app.schemas.validation_plan import ValidationPlanChecks, ValidationPlanInput
from app.services.change_intake import compute_content_fingerprint
from app.services.validation_orchestrator import CHECK_ORDER, orchestrate_validation

SECRET_SQL = "select secret_column_xyz_never_in_artifact as account_id from customers"
SECRET_FIXTURE_VALUE = "fixture_secret_cell_xyz_not_in_artifact"


# ---- Fixtures / builders -----------------------------------------------------


def _change(
    *,
    table: str = "customers",
    source: str = "customer_id",
    target: str = "account_id",
) -> NormalizedChange:
    return NormalizedChange(
        change_type="rename_column",
        asset=AssetNormalized(
            platform="snowflake",
            database="analytics",
            schema="core",
            name=table,
        ),
        source_column=source,
        target_column=target,
        reason=None,
    )


def _fingerprint(change: NormalizedChange) -> str:
    return compute_content_fingerprint(change)


def _intake_reference(
    change: NormalizedChange | None = None,
    *,
    content_fingerprint: str | None = None,
    intake_id: uuid.UUID | None = None,
) -> IntakeReference:
    normalized = change or _change()
    return IntakeReference(
        intake_id=intake_id or uuid.uuid4(),
        normalized_change=normalized,
        content_fingerprint=content_fingerprint or _fingerprint(normalized),
        artifact_version="1.0",
    )


def _fixture(
    columns: list[dict[str, Any]] | None = None,
    rows: list[list[Any]] | None = None,
) -> DuckDbFixture:
    if columns is None:
        columns = [
            {"name": "customer_id", "type": "varchar", "nullable": False},
            {"name": "email", "type": "varchar", "nullable": True},
        ]
    if rows is None:
        rows = [
            [SECRET_FIXTURE_VALUE, "one@example.test"],
            ["customer-2", None],
        ]
    return DuckDbFixture(
        columns=[DuckDbFixtureColumn(**col) for col in columns],
        rows=rows,
    )


def _sql(sql: str = SECRET_SQL) -> SqlParseInput:
    return SqlParseInput(sql=sql, dialect=SqlDialect.SNOWFLAKE, required=True)


def _duckdb(
    change: NormalizedChange | None = None,
    *,
    required: bool = True,
) -> DuckDbRenameInput:
    return DuckDbRenameInput(
        normalized_change=change or _change(),
        fixture=_fixture(),
        required=required,
    )


def _dbt(
    *,
    model_sql: str = SECRET_SQL,
    required: bool = False,
) -> DbtParseInput:
    return DbtParseInput(
        model_name="customers_renamed",
        model_sql=model_sql,
        required=required,
    )


def _plan(
    *,
    change: NormalizedChange | None = None,
    sql: str = SECRET_SQL,
    sql_required: bool = True,
    duckdb_required: bool = True,
    dbt_required: bool = False,
    content_fingerprint: str | None = None,
    duckdb_change: NormalizedChange | None = None,
    dbt_sql: str | None = None,
) -> ValidationPlanInput:
    normalized = change or _change()
    return ValidationPlanInput(
        intake_reference=_intake_reference(
            normalized, content_fingerprint=content_fingerprint
        ),
        checks=ValidationPlanChecks(
            sql_parse=SqlParseInput(
                sql=sql,
                dialect=SqlDialect.SNOWFLAKE,
                required=sql_required,
            ),
            duckdb_execution=DuckDbRenameInput(
                normalized_change=duckdb_change or normalized,
                fixture=_fixture(),
                required=duckdb_required,
            ),
            dbt_validation=DbtParseInput(
                model_name="customers_renamed",
                model_sql=dbt_sql if dbt_sql is not None else sql,
                required=dbt_required,
            ),
        ),
    )


def _evidence(code: str = "note", message: str = "Safe evidence.") -> ValidationEvidence:
    return ValidationEvidence(code=code, message=message, details=None)


def _check_result(
    *,
    kind: CheckKind,
    execution_status: CheckExecutionStatus,
    outcome: CheckOutcome | None,
    required: bool = True,
    check_id: uuid.UUID | None = None,
) -> ValidationCheckResult:
    evidence: list[ValidationEvidence] = []
    if execution_status != CheckExecutionStatus.COMPLETED:
        evidence = [_evidence(code=f"{kind.value}_status", message="Bounded status.")]
    elif outcome == CheckOutcome.FAIL:
        evidence = [_evidence(code=f"{kind.value}_failed", message="Check failed.")]
    elif outcome == CheckOutcome.PASS:
        evidence = [_evidence(code=f"{kind.value}_ok", message="Check passed.")]
    else:
        evidence = [_evidence(code=f"{kind.value}_inconclusive", message="Inconclusive.")]

    return ValidationCheckResult(
        check_id=check_id or uuid.uuid4(),
        check_kind=kind,
        required=required,
        execution_status=execution_status,
        outcome=outcome,
        scope=f"{kind.value} scope",
        summary=f"{kind.value} summary",
        evidence=evidence,
        engine_name=None,
        engine_version=None,
    )


def _mock_pass(kind: CheckKind, *, required: bool = True) -> ValidationCheckResult:
    return _check_result(
        kind=kind,
        execution_status=CheckExecutionStatus.COMPLETED,
        outcome=CheckOutcome.PASS,
        required=required,
    )


def _mock_fail(kind: CheckKind, *, required: bool = True) -> ValidationCheckResult:
    return _check_result(
        kind=kind,
        execution_status=CheckExecutionStatus.COMPLETED,
        outcome=CheckOutcome.FAIL,
        required=required,
    )


def _mock_error(kind: CheckKind, *, required: bool = True) -> ValidationCheckResult:
    return _check_result(
        kind=kind,
        execution_status=CheckExecutionStatus.ERROR,
        outcome=None,
        required=required,
    )


def _mock_unavailable(kind: CheckKind, *, required: bool = True) -> ValidationCheckResult:
    return _check_result(
        kind=kind,
        execution_status=CheckExecutionStatus.UNAVAILABLE,
        outcome=None,
        required=required,
    )


def _mock_inconclusive(kind: CheckKind, *, required: bool = True) -> ValidationCheckResult:
    return _check_result(
        kind=kind,
        execution_status=CheckExecutionStatus.COMPLETED,
        outcome=CheckOutcome.INCONCLUSIVE,
        required=required,
    )


# ---- Plan contract -----------------------------------------------------------


def test_valid_complete_plan_accepted() -> None:
    plan = _plan()
    assert plan.intake_reference.artifact_version == "1.0"
    assert plan.checks.sql_parse.dialect == SqlDialect.SNOWFLAKE
    assert plan.checks.dbt_validation.required is False


def test_unknown_plan_field_rejected() -> None:
    change = _change()
    with pytest.raises(ValidationError):
        ValidationPlanInput.model_validate(
            {
                "intake_reference": _intake_reference(change).model_dump(mode="json"),
                "checks": {
                    "sql_parse": _sql().model_dump(mode="json"),
                    "duckdb_execution": _duckdb(change).model_dump(mode="json"),
                    "dbt_validation": _dbt().model_dump(mode="json"),
                },
                "decision": "ALLOW",
            }
        )


def test_unknown_checks_field_rejected() -> None:
    change = _change()
    with pytest.raises(ValidationError):
        ValidationPlanChecks.model_validate(
            {
                "sql_parse": _sql().model_dump(mode="json"),
                "duckdb_execution": _duckdb(change).model_dump(mode="json"),
                "dbt_validation": _dbt().model_dump(mode="json"),
                "extra_check": {"sql": "select 1"},
            }
        )


def test_invalid_intake_reference_rejected() -> None:
    change = _change()
    with pytest.raises(ValidationError):
        ValidationPlanInput.model_validate(
            {
                "intake_reference": {
                    "intake_id": "not-a-uuid",
                    "normalized_change": change.fingerprint_payload(),
                    "content_fingerprint": _fingerprint(change),
                    "artifact_version": "1.0",
                },
                "checks": {
                    "sql_parse": _sql().model_dump(mode="json"),
                    "duckdb_execution": _duckdb(change).model_dump(mode="json"),
                    "dbt_validation": _dbt().model_dump(mode="json"),
                },
            }
        )


def test_fingerprint_mismatch_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _plan(content_fingerprint="a" * 64)
    text = str(exc_info.value).lower()
    assert "fingerprint" in text
    # Must not leak the expected/computed fingerprint or canonical JSON.
    assert _fingerprint(_change()) not in str(exc_info.value)


def test_fingerprint_mismatch_does_not_run_validators() -> None:
    call_log: list[str] = []

    def _sql_side(*_a: Any, **_k: Any) -> ValidationCheckResult:
        call_log.append("sql")
        return _mock_pass(CheckKind.SQL_PARSE)

    def _duck_side(*_a: Any, **_k: Any) -> ValidationCheckResult:
        call_log.append("duckdb")
        return _mock_pass(CheckKind.DUCKDB_EXECUTION)

    def _dbt_side(*_a: Any, **_k: Any) -> ValidationCheckResult:
        call_log.append("dbt")
        return _mock_pass(CheckKind.DBT_VALIDATION)

    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            side_effect=_sql_side,
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            side_effect=_duck_side,
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            side_effect=_dbt_side,
        ),
    ):
        with pytest.raises(ValidationError):
            _plan(content_fingerprint="b" * 64)

    assert call_log == []


def test_duckdb_normalized_change_mismatch_rejected() -> None:
    other = _change(source="other_id", target="account_id")
    with pytest.raises(ValidationError) as exc_info:
        _plan(duckdb_change=other)
    assert "normalized_change" in str(exc_info.value).lower()


def test_normalized_change_mismatch_does_not_run_validators() -> None:
    call_log: list[str] = []

    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            side_effect=lambda *_a, **_k: call_log.append("sql") or _mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            side_effect=lambda *_a, **_k: call_log.append("duckdb")
            or _mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            side_effect=lambda *_a, **_k: call_log.append("dbt")
            or _mock_pass(CheckKind.DBT_VALIDATION),
        ),
    ):
        with pytest.raises(ValidationError):
            _plan(duckdb_change=_change(table="other_table"))

    assert call_log == []


def test_sql_and_dbt_model_sql_mismatch_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        _plan(sql="select 1 as account_id", dbt_sql="select 2 as account_id")
    text = str(exc_info.value).lower()
    assert "sql" in text
    assert "select 1" not in str(exc_info.value)
    assert "select 2" not in str(exc_info.value)


def test_sql_mismatch_does_not_run_validators() -> None:
    call_log: list[str] = []

    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            side_effect=lambda *_a, **_k: call_log.append("sql") or _mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            side_effect=lambda *_a, **_k: call_log.append("duckdb")
            or _mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            side_effect=lambda *_a, **_k: call_log.append("dbt")
            or _mock_pass(CheckKind.DBT_VALIDATION),
        ),
    ):
        with pytest.raises(ValidationError):
            _plan(sql="select a as b", dbt_sql="select c as d")

    assert call_log == []


# ---- Orchestration order / structure -----------------------------------------


def test_validators_run_in_fixed_order() -> None:
    call_log: list[str] = []
    plan = _plan()

    def _sql_side(inp: SqlParseInput) -> ValidationCheckResult:
        call_log.append("sql_parse")
        return _mock_pass(CheckKind.SQL_PARSE, required=inp.required)

    def _duck_side(inp: DuckDbRenameInput) -> ValidationCheckResult:
        call_log.append("duckdb_execution")
        return _mock_pass(CheckKind.DUCKDB_EXECUTION, required=inp.required)

    def _dbt_side(inp: DbtParseInput) -> ValidationCheckResult:
        call_log.append("dbt_validation")
        return _mock_pass(CheckKind.DBT_VALIDATION, required=inp.required)

    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            side_effect=_sql_side,
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            side_effect=_duck_side,
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            side_effect=_dbt_side,
        ),
    ):
        artifact = orchestrate_validation(plan)

    assert call_log == list(CHECK_ORDER)
    assert [c.check_kind for c in artifact.checks] == [
        CheckKind.SQL_PARSE.value,
        CheckKind.DUCKDB_EXECUTION.value,
        CheckKind.DBT_VALIDATION.value,
    ]


def test_no_http_loopback() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
        patch("httpx.Client") as http_client,
        patch("urllib.request.urlopen") as urlopen,
    ):
        orchestrate_validation(plan)
        http_client.assert_not_called()
        urlopen.assert_not_called()


def test_valid_plan_always_three_checks() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_error(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert len(artifact.checks) == 3


def test_check_order_stable() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_fail(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    kinds = [c.check_kind for c in artifact.checks]
    assert kinds == [
        CheckKind.SQL_PARSE.value,
        CheckKind.DUCKDB_EXECUTION.value,
        CheckKind.DBT_VALIDATION.value,
    ]


def test_subject_fingerprint_preserved() -> None:
    plan = _plan()
    expected = plan.intake_reference.content_fingerprint
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert artifact.subject_fingerprint == expected


def test_validation_id_is_uuid() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert isinstance(artifact.validation_id, uuid.UUID)


def test_artifact_scope_provided_artifacts_only() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert artifact.scope == VALIDATION_SCOPE
    assert artifact.scope == "provided_artifacts_only"


def test_artifact_version_is_1_0() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert artifact.artifact_version == VALIDATION_ARTIFACT_VERSION
    assert artifact.artifact_version == "1.0"


# ---- Aggregation scenarios ---------------------------------------------------


def test_three_required_pass_completed_pass() -> None:
    plan = _plan(dbt_required=True)
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=True),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert artifact.execution_status == OverallExecutionStatus.COMPLETED.value
    assert artifact.outcome == CheckOutcome.PASS.value


def test_required_sql_fail_overall_fail() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_fail(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert artifact.execution_status == OverallExecutionStatus.COMPLETED.value
    assert artifact.outcome == CheckOutcome.FAIL.value


def test_required_duckdb_fail_overall_fail() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_fail(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert artifact.outcome == CheckOutcome.FAIL.value


def test_required_dbt_error_partial_inconclusive() -> None:
    plan = _plan(dbt_required=True)
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_error(CheckKind.DBT_VALIDATION, required=True),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert artifact.execution_status == OverallExecutionStatus.PARTIAL.value
    assert artifact.outcome == CheckOutcome.INCONCLUSIVE.value


def test_optional_dbt_error_required_pass_partial_pass() -> None:
    plan = _plan(dbt_required=False)
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_error(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert artifact.execution_status == OverallExecutionStatus.PARTIAL.value
    assert artifact.outcome == CheckOutcome.PASS.value


def test_optional_dbt_unavailable_required_pass_partial_pass() -> None:
    plan = _plan(dbt_required=False)
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_unavailable(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert artifact.execution_status == OverallExecutionStatus.PARTIAL.value
    assert artifact.outcome == CheckOutcome.PASS.value


def test_required_sql_inconclusive_overall_inconclusive() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_inconclusive(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert artifact.outcome == CheckOutcome.INCONCLUSIVE.value


def test_no_short_circuit_after_sql_fail() -> None:
    call_log: list[str] = []
    plan = _plan()

    def _sql_side(_inp: SqlParseInput) -> ValidationCheckResult:
        call_log.append("sql_parse")
        return _mock_fail(CheckKind.SQL_PARSE)

    def _duck_side(_inp: DuckDbRenameInput) -> ValidationCheckResult:
        call_log.append("duckdb_execution")
        return _mock_pass(CheckKind.DUCKDB_EXECUTION)

    def _dbt_side(_inp: DbtParseInput) -> ValidationCheckResult:
        call_log.append("dbt_validation")
        return _mock_pass(CheckKind.DBT_VALIDATION, required=False)

    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            side_effect=_sql_side,
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            side_effect=_duck_side,
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            side_effect=_dbt_side,
        ),
    ):
        artifact = orchestrate_validation(plan)

    assert call_log == list(CHECK_ORDER)
    assert len(artifact.checks) == 3
    assert artifact.outcome == CheckOutcome.FAIL.value


def test_no_short_circuit_after_duckdb_fail() -> None:
    call_log: list[str] = []
    plan = _plan()

    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            side_effect=lambda *_a, **_k: (
                call_log.append("sql_parse") or _mock_pass(CheckKind.SQL_PARSE)
            ),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            side_effect=lambda *_a, **_k: (
                call_log.append("duckdb_execution")
                or _mock_fail(CheckKind.DUCKDB_EXECUTION)
            ),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            side_effect=lambda *_a, **_k: (
                call_log.append("dbt_validation")
                or _mock_pass(CheckKind.DBT_VALIDATION, required=False)
            ),
        ),
    ):
        artifact = orchestrate_validation(plan)

    assert call_log == list(CHECK_ORDER)
    assert artifact.checks[2].check_kind == CheckKind.DBT_VALIDATION.value


def test_no_short_circuit_after_engine_error() -> None:
    call_log: list[str] = []
    plan = _plan()

    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            side_effect=lambda *_a, **_k: (
                call_log.append("sql_parse") or _mock_error(CheckKind.SQL_PARSE)
            ),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            side_effect=lambda *_a, **_k: (
                call_log.append("duckdb_execution")
                or _mock_pass(CheckKind.DUCKDB_EXECUTION)
            ),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            side_effect=lambda *_a, **_k: (
                call_log.append("dbt_validation")
                or _mock_pass(CheckKind.DBT_VALIDATION, required=False)
            ),
        ),
    ):
        artifact = orchestrate_validation(plan)

    assert call_log == list(CHECK_ORDER)
    assert len(artifact.checks) == 3


def test_all_check_results_retained() -> None:
    sql_id = uuid.uuid4()
    duck_id = uuid.uuid4()
    dbt_id = uuid.uuid4()
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_check_result(
                kind=CheckKind.SQL_PARSE,
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.PASS,
                check_id=sql_id,
            ),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_check_result(
                kind=CheckKind.DUCKDB_EXECUTION,
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.FAIL,
                check_id=duck_id,
            ),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_check_result(
                kind=CheckKind.DBT_VALIDATION,
                execution_status=CheckExecutionStatus.ERROR,
                outcome=None,
                required=False,
                check_id=dbt_id,
            ),
        ),
    ):
        artifact = orchestrate_validation(plan)

    assert [c.check_id for c in artifact.checks] == [sql_id, duck_id, dbt_id]
    assert artifact.checks[0].outcome == CheckOutcome.PASS.value
    assert artifact.checks[1].outcome == CheckOutcome.FAIL.value
    assert artifact.checks[2].execution_status == CheckExecutionStatus.ERROR.value


def test_required_flags_preserved() -> None:
    plan = _plan(sql_required=True, duckdb_required=True, dbt_required=False)
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE, required=True),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION, required=True),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert [c.required for c in artifact.checks] == [True, True, False]


# ---- Real integration (single plan) ------------------------------------------


def test_real_integration_all_three_validators_pass() -> None:
    """One real plan: SQLGlot + DuckDB + dbt (minimal subprocess)."""
    sql = "select customer_id as account_id from customers"
    plan = _plan(sql=sql, dbt_required=False)
    artifact = orchestrate_validation(plan)

    assert isinstance(artifact, ValidationArtifact)
    assert len(artifact.checks) == 3
    assert artifact.scope == "provided_artifacts_only"
    assert artifact.artifact_version == "1.0"
    assert artifact.subject_fingerprint == plan.intake_reference.content_fingerprint

    kinds = [c.check_kind for c in artifact.checks]
    assert kinds == [
        CheckKind.SQL_PARSE.value,
        CheckKind.DUCKDB_EXECUTION.value,
        CheckKind.DBT_VALIDATION.value,
    ]

    sql_check, duck_check, dbt_check = artifact.checks
    assert sql_check.execution_status == CheckExecutionStatus.COMPLETED.value
    assert sql_check.outcome == CheckOutcome.PASS.value
    assert duck_check.execution_status == CheckExecutionStatus.COMPLETED.value
    assert duck_check.outcome == CheckOutcome.PASS.value
    assert dbt_check.execution_status == CheckExecutionStatus.COMPLETED.value
    assert dbt_check.outcome == CheckOutcome.PASS.value

    assert artifact.execution_status == OverallExecutionStatus.COMPLETED.value
    assert artifact.outcome == CheckOutcome.PASS.value

    # Privacy: raw SQL / fixture secrets must not appear in serialization.
    serialized = json.dumps(artifact.model_dump(mode="json"))
    assert SECRET_SQL not in serialized
    assert sql not in serialized or sql == SECRET_SQL  # real sql is different
    assert "select customer_id as account_id from customers" not in serialized
    assert SECRET_FIXTURE_VALUE not in serialized


def test_real_sqlglot_pass_in_artifact() -> None:
    sql = "select customer_id as account_id from customers"
    plan = _plan(sql=sql)
    # Avoid slow dbt for this focused assertion.
    with patch(
        "app.services.validation_orchestrator.run_dbt_parse_check",
        return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
    ):
        artifact = orchestrate_validation(plan)
    sql_check = artifact.checks[0]
    assert sql_check.check_kind == CheckKind.SQL_PARSE.value
    assert sql_check.outcome == CheckOutcome.PASS.value
    assert sql_check.engine_name == "sqlglot"


def test_real_duckdb_pass_in_artifact() -> None:
    sql = "select customer_id as account_id from customers"
    plan = _plan(sql=sql)
    with patch(
        "app.services.validation_orchestrator.run_dbt_parse_check",
        return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
    ):
        artifact = orchestrate_validation(plan)
    duck_check = artifact.checks[1]
    assert duck_check.check_kind == CheckKind.DUCKDB_EXECUTION.value
    assert duck_check.outcome == CheckOutcome.PASS.value
    assert duck_check.engine_name == "duckdb"


def test_real_dbt_pass_in_artifact() -> None:
    sql = "select customer_id as account_id from customers"
    plan = _plan(sql=sql)
    # Run real dbt only; mock the faster validators for isolation of dbt claim.
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
    ):
        artifact = orchestrate_validation(plan)
    dbt_check = artifact.checks[2]
    assert dbt_check.check_kind == CheckKind.DBT_VALIDATION.value
    assert dbt_check.outcome == CheckOutcome.PASS.value
    assert dbt_check.engine_name == "dbt-core"


# ---- Determinism / mutation --------------------------------------------------


def test_same_input_same_semantic_artifact_except_ids() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        first = orchestrate_validation(plan)
        second = orchestrate_validation(plan)

    assert first.subject_fingerprint == second.subject_fingerprint
    assert first.execution_status == second.execution_status
    assert first.outcome == second.outcome
    assert first.scope == second.scope
    assert first.artifact_version == second.artifact_version
    assert [c.check_kind for c in first.checks] == [c.check_kind for c in second.checks]
    assert [c.outcome for c in first.checks] == [c.outcome for c in second.checks]
    assert first.validation_id != second.validation_id


def test_input_plan_not_mutated() -> None:
    plan = _plan()
    before = plan.model_dump(mode="json")
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        orchestrate_validation(plan)
    assert plan.model_dump(mode="json") == before


def test_check_order_unchanged_after_aggregation() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_fail(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_error(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    assert [c.check_kind for c in artifact.checks] == list(CHECK_ORDER)


# ---- Safety ------------------------------------------------------------------


def test_orchestrator_does_not_write_artifact_files(tmp_path: Any) -> None:
    plan = _plan()
    before = {p.name for p in tmp_path.iterdir()} if tmp_path.exists() else set()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
        patch("builtins.open", side_effect=AssertionError("orchestrator must not open files")),
        patch("pathlib.Path.write_text", side_effect=AssertionError("no write_text")),
        patch("pathlib.Path.write_bytes", side_effect=AssertionError("no write_bytes")),
    ):
        orchestrate_validation(plan)
    after = {p.name for p in tmp_path.iterdir()} if tmp_path.exists() else set()
    assert before == after


def test_orchestrator_does_not_open_database_directly() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
        patch("duckdb.connect", side_effect=AssertionError("orchestrator must not connect")),
    ):
        orchestrate_validation(plan)


def test_orchestrator_does_not_run_subprocess_directly() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
        patch(
            "subprocess.run",
            side_effect=AssertionError("orchestrator must not subprocess"),
        ),
        patch(
            "subprocess.Popen",
            side_effect=AssertionError("orchestrator must not Popen"),
        ),
    ):
        orchestrate_validation(plan)


def test_orchestrator_does_not_network() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
        patch("socket.socket", side_effect=AssertionError("no network")),
    ):
        orchestrate_validation(plan)


def test_raw_sql_not_in_artifact_serialization() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    serialized = json.dumps(artifact.model_dump(mode="json"))
    assert SECRET_SQL not in serialized
    assert "secret_column_xyz" not in serialized


def test_fixture_values_not_in_artifact_serialization() -> None:
    plan = _plan()
    with (
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            return_value=_mock_pass(CheckKind.SQL_PARSE),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            return_value=_mock_pass(CheckKind.DUCKDB_EXECUTION),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            return_value=_mock_pass(CheckKind.DBT_VALIDATION, required=False),
        ),
    ):
        artifact = orchestrate_validation(plan)
    serialized = json.dumps(artifact.model_dump(mode="json"))
    assert SECRET_FIXTURE_VALUE not in serialized


def test_decision_field_rejected_on_plan() -> None:
    change = _change()
    payload = {
        "intake_reference": _intake_reference(change).model_dump(mode="json"),
        "checks": {
            "sql_parse": _sql().model_dump(mode="json"),
            "duckdb_execution": _duckdb(change).model_dump(mode="json"),
            "dbt_validation": _dbt().model_dump(mode="json"),
        },
        "outcome": "pass",
    }
    with pytest.raises(ValidationError):
        ValidationPlanInput.model_validate(payload)


def test_deep_copy_plan_still_valid() -> None:
    plan = _plan()
    cloned = ValidationPlanInput.model_validate(copy.deepcopy(plan.model_dump(mode="json")))
    assert cloned.intake_reference.content_fingerprint == plan.intake_reference.content_fingerprint
