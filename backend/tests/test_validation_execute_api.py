"""Tests for POST /api/v1/validations/execute (phase F6.6)."""

from __future__ import annotations

import asyncio
import inspect
import json
import re
import uuid
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.routes import validations as validations_route
from app.main import app
from app.schemas.changes import AssetNormalized, NormalizedChange
from app.schemas.validation import (
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    OverallExecutionStatus,
    ValidationArtifact,
    ValidationCheckResult,
    ValidationEvidence,
)
from app.services.change_intake import compute_content_fingerprint

EXECUTE_PATH = "/api/v1/validations/execute"
INTAKE_PATH = "/api/v1/changes/intake"
RISK_PATH = "/api/v1/risk/evaluate"
RUNS_PATH = "/api/v1/runs/analyze"
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")

SECRET_SQL = "select secret_column_xyz_api_never_returned as account_id from customers"
SECRET_FIXTURE = "fixture_secret_api_cell_xyz_not_in_response"


def _client() -> TestClient:
    return TestClient(app)


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


def _fp(change: NormalizedChange | None = None) -> str:
    return compute_content_fingerprint(change or _change())


def _plan_body(
    *,
    sql: str = SECRET_SQL,
    dbt_sql: str | None = None,
    content_fingerprint: str | None = None,
    duckdb_change: dict[str, Any] | None = None,
    change: NormalizedChange | None = None,
    sql_required: bool = True,
    duckdb_required: bool = True,
    dbt_required: bool = False,
    extra_top: dict[str, Any] | None = None,
    fixture_rows: list[list[Any]] | None = None,
) -> dict[str, Any]:
    normalized = change or _change()
    change_payload = normalized.fingerprint_payload()
    body: dict[str, Any] = {
        "intake_reference": {
            "intake_id": str(uuid.uuid4()),
            "normalized_change": change_payload,
            "content_fingerprint": content_fingerprint or _fp(normalized),
            "artifact_version": "1.0",
        },
        "checks": {
            "sql_parse": {
                "sql": sql,
                "dialect": "snowflake",
                "required": sql_required,
            },
            "duckdb_execution": {
                "normalized_change": duckdb_change or change_payload,
                "fixture": {
                    "columns": [
                        {
                            "name": "customer_id",
                            "type": "varchar",
                            "nullable": False,
                        },
                        {
                            "name": "email",
                            "type": "varchar",
                            "nullable": True,
                        },
                    ],
                    "rows": fixture_rows
                    or [
                        [SECRET_FIXTURE, "one@example.test"],
                        ["customer-2", None],
                    ],
                },
                "required": duckdb_required,
            },
            "dbt_validation": {
                "model_name": "customers_renamed",
                "model_sql": dbt_sql if dbt_sql is not None else sql,
                "required": dbt_required,
            },
        },
    }
    if extra_top:
        body.update(extra_top)
    return body


def _evidence(code: str = "note") -> ValidationEvidence:
    return ValidationEvidence(code=code, message="Safe evidence.", details=None)


def _check(
    *,
    kind: CheckKind,
    execution_status: CheckExecutionStatus,
    outcome: CheckOutcome | None,
    required: bool = True,
) -> ValidationCheckResult:
    evidence: list[ValidationEvidence] = []
    if execution_status != CheckExecutionStatus.COMPLETED:
        evidence = [_evidence(f"{kind.value}_status")]
    else:
        evidence = [_evidence(f"{kind.value}_result")]
    return ValidationCheckResult(
        check_id=uuid.uuid4(),
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


def _artifact(
    *,
    subject_fingerprint: str,
    sql: ValidationCheckResult,
    duck: ValidationCheckResult,
    dbt: ValidationCheckResult,
    execution_status: OverallExecutionStatus,
    outcome: CheckOutcome,
) -> ValidationArtifact:
    return ValidationArtifact(
        validation_id=uuid.uuid4(),
        subject_fingerprint=subject_fingerprint,
        scope="provided_artifacts_only",
        execution_status=execution_status,
        outcome=outcome,
        checks=[sql, duck, dbt],
        artifact_version="1.0",
    )


def _mock_pass_artifact(fp: str, *, dbt_required: bool = False) -> ValidationArtifact:
    return _artifact(
        subject_fingerprint=fp,
        sql=_check(
            kind=CheckKind.SQL_PARSE,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
        ),
        duck=_check(
            kind=CheckKind.DUCKDB_EXECUTION,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
        ),
        dbt=_check(
            kind=CheckKind.DBT_VALIDATION,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            required=dbt_required,
        ),
        execution_status=OverallExecutionStatus.COMPLETED,
        outcome=CheckOutcome.PASS,
    )


# ---- Basic API ---------------------------------------------------------------


def test_valid_plan_http_200() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 200


def test_success_envelope_shape() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        payload = _client().post(EXECUTE_PATH, json=body).json()
    assert payload["status"] == "ok"
    assert "data" in payload
    assert "meta" in payload


def test_data_matches_validation_artifact_contract() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        data = _client().post(EXECUTE_PATH, json=body).json()["data"]
    assert set(data.keys()) == {
        "validation_id",
        "subject_fingerprint",
        "scope",
        "execution_status",
        "outcome",
        "checks",
        "artifact_version",
    }
    ValidationArtifact.model_validate(data)


def test_validation_id_is_uuid() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        data = _client().post(EXECUTE_PATH, json=body).json()["data"]
    uuid.UUID(data["validation_id"])


def test_checks_order_fixed() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        checks = _client().post(EXECUTE_PATH, json=body).json()["data"]["checks"]
    assert [c["check_kind"] for c in checks] == [
        "sql_parse",
        "duckdb_execution",
        "dbt_validation",
    ]


def test_subject_fingerprint_preserved() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        data = _client().post(EXECUTE_PATH, json=body).json()["data"]
    assert data["subject_fingerprint"] == fp
    assert SHA256_HEX.match(data["subject_fingerprint"])


def test_scope_provided_artifacts_only() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        data = _client().post(EXECUTE_PATH, json=body).json()["data"]
    assert data["scope"] == "provided_artifacts_only"


def test_artifact_version_1_0() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        data = _client().post(EXECUTE_PATH, json=body).json()["data"]
    assert data["artifact_version"] == "1.0"


# ---- HTTP semantics (200 independent of outcome) -----------------------------


def test_pass_artifact_http_200() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    art = _mock_pass_artifact(fp)
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=art,
    ):
        response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 200
    assert response.json()["data"]["outcome"] == "pass"


def test_fail_artifact_http_200() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    art = _artifact(
        subject_fingerprint=fp,
        sql=_check(
            kind=CheckKind.SQL_PARSE,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.FAIL,
        ),
        duck=_check(
            kind=CheckKind.DUCKDB_EXECUTION,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
        ),
        dbt=_check(
            kind=CheckKind.DBT_VALIDATION,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            required=False,
        ),
        execution_status=OverallExecutionStatus.COMPLETED,
        outcome=CheckOutcome.FAIL,
    )
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=art,
    ):
        response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 200
    assert response.json()["data"]["outcome"] == "fail"


def test_inconclusive_artifact_http_200() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    art = _artifact(
        subject_fingerprint=fp,
        sql=_check(
            kind=CheckKind.SQL_PARSE,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.INCONCLUSIVE,
        ),
        duck=_check(
            kind=CheckKind.DUCKDB_EXECUTION,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
        ),
        dbt=_check(
            kind=CheckKind.DBT_VALIDATION,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            required=False,
        ),
        execution_status=OverallExecutionStatus.COMPLETED,
        outcome=CheckOutcome.INCONCLUSIVE,
    )
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=art,
    ):
        response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 200
    assert response.json()["data"]["outcome"] == "inconclusive"


def test_partial_pass_artifact_http_200() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    art = _artifact(
        subject_fingerprint=fp,
        sql=_check(
            kind=CheckKind.SQL_PARSE,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
        ),
        duck=_check(
            kind=CheckKind.DUCKDB_EXECUTION,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
        ),
        dbt=_check(
            kind=CheckKind.DBT_VALIDATION,
            execution_status=CheckExecutionStatus.ERROR,
            outcome=None,
            required=False,
        ),
        execution_status=OverallExecutionStatus.PARTIAL,
        outcome=CheckOutcome.PASS,
    )
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=art,
    ):
        response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["execution_status"] == "partial"
    assert data["outcome"] == "pass"


def test_http_200_not_tied_to_pass_outcome() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    for outcome in (CheckOutcome.PASS, CheckOutcome.FAIL, CheckOutcome.INCONCLUSIVE):
        art = _artifact(
            subject_fingerprint=fp,
            sql=_check(
                kind=CheckKind.SQL_PARSE,
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=outcome if outcome != CheckOutcome.INCONCLUSIVE else CheckOutcome.INCONCLUSIVE,
            ),
            duck=_check(
                kind=CheckKind.DUCKDB_EXECUTION,
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.PASS
                if outcome != CheckOutcome.FAIL
                else CheckOutcome.FAIL,
            ),
            dbt=_check(
                kind=CheckKind.DBT_VALIDATION,
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.PASS,
                required=False,
            ),
            execution_status=OverallExecutionStatus.COMPLETED,
            outcome=outcome,
        )
        with patch(
            "app.api.routes.validations.orchestrate_validation",
            return_value=art,
        ):
            assert _client().post(EXECUTE_PATH, json=body).status_code == 200


# ---- Real integration --------------------------------------------------------


def test_real_api_integration_all_validators() -> None:
    """One real HTTP request: SQLGlot + DuckDB + dbt → valid artifact."""
    sql = "select customer_id as account_id from customers"
    body = _plan_body(sql=sql, dbt_required=False)
    response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    data = payload["data"]
    assert data["scope"] == "provided_artifacts_only"
    assert data["artifact_version"] == "1.0"
    assert data["subject_fingerprint"] == body["intake_reference"]["content_fingerprint"]
    assert [c["check_kind"] for c in data["checks"]] == [
        "sql_parse",
        "duckdb_execution",
        "dbt_validation",
    ]
    assert all(c["execution_status"] == "completed" for c in data["checks"])
    assert all(c["outcome"] == "pass" for c in data["checks"])
    assert data["execution_status"] == "completed"
    assert data["outcome"] == "pass"
    serialized = json.dumps(payload)
    assert SECRET_SQL not in serialized
    assert sql not in serialized
    assert SECRET_FIXTURE not in serialized


# ---- Trust metadata ----------------------------------------------------------


def test_meta_operation_and_phase() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        meta = _client().post(EXECUTE_PATH, json=body).json()["meta"]
    assert meta["operation"] == "validation_execution"
    assert meta["phase"] == "F6.6"


def test_meta_execution_mode_synchronous() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        meta = _client().post(EXECUTE_PATH, json=body).json()["meta"]
    assert meta["execution_mode"] == "synchronous_orchestration"


def test_meta_persistence_and_retrieval() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        meta = _client().post(EXECUTE_PATH, json=body).json()["meta"]
    assert meta["persistence"] == "none"
    assert meta["retrieval_available"] is False


def test_meta_intake_trust_boundaries() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        meta = _client().post(EXECUTE_PATH, json=body).json()["meta"]
    assert meta["intake_reference_origin"] == "caller_provided"
    assert meta["intake_reference_trust"] == "unverified"
    assert meta["subject_fingerprint_scope"] == "normalized_change_only"
    assert meta["fingerprint_check"] == "matched"


def test_meta_cross_artifact_and_sql_fixture_trust() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        meta = _client().post(EXECUTE_PATH, json=body).json()["meta"]
    assert meta["cross_artifact_consistency"] == "matched"
    assert meta["cross_artifact_provenance"] == "unverified"
    assert meta["sql_origin"] == "caller_provided"
    assert meta["sql_trust"] == "unverified"
    assert meta["fixture_origin"] == "caller_provided"
    assert meta["fixture_trust"] == "unverified"
    assert meta["model_used"] is False
    assert meta["deployment_authorized"] is False


# ---- Validation errors (422) -------------------------------------------------


def test_fingerprint_mismatch_http_422() -> None:
    body = _plan_body(content_fingerprint="a" * 64)
    response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 422
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "validation_error"
    text = json.dumps(payload)
    # Client sent a*64; expected/calculated fingerprint must not be leaked.
    assert _fp() not in text


def test_fingerprint_mismatch_does_not_run_validators() -> None:
    call_log: list[str] = []
    body = _plan_body(content_fingerprint="b" * 64)

    def _orch(_plan: Any) -> ValidationArtifact:
        call_log.append("orchestrate")
        raise AssertionError("orchestrator must not run")

    with (
        patch(
            "app.api.routes.validations.orchestrate_validation",
            side_effect=_orch,
        ),
        patch(
            "app.services.validation_orchestrator.run_sql_parse_check",
            side_effect=lambda *_a, **_k: call_log.append("sql"),
        ),
        patch(
            "app.services.validation_orchestrator.run_duckdb_rename_check",
            side_effect=lambda *_a, **_k: call_log.append("duckdb"),
        ),
        patch(
            "app.services.validation_orchestrator.run_dbt_parse_check",
            side_effect=lambda *_a, **_k: call_log.append("dbt"),
        ),
    ):
        response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 422
    assert call_log == []


def test_normalized_change_mismatch_http_422() -> None:
    other = _change(table="other_table").fingerprint_payload()
    body = _plan_body(duckdb_change=other)
    response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_sql_mismatch_http_422() -> None:
    body = _plan_body(sql="select 1 as account_id", dbt_sql="select 2 as account_id")
    response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 422
    text = json.dumps(response.json())
    assert "select 1" not in text
    assert "select 2" not in text


def test_missing_field_http_422() -> None:
    body = _plan_body()
    del body["checks"]["sql_parse"]
    response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 422
    assert response.json()["status"] == "error"


def test_unknown_top_level_field_http_422() -> None:
    body = _plan_body(extra_top={"decision": "ALLOW"})
    response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 422


def test_unknown_nested_field_http_422() -> None:
    body = _plan_body()
    body["checks"]["sql_parse"]["extra_field"] = "nope"
    response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 422


def test_client_sent_validation_id_rejected() -> None:
    body = _plan_body(extra_top={"validation_id": str(uuid.uuid4())})
    response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 422


def test_client_sent_outcome_rejected() -> None:
    body = _plan_body(extra_top={"outcome": "pass"})
    response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 422


def test_malformed_json_http_422() -> None:
    response = _client().post(
        EXECUTE_PATH,
        content=b"{not-json",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["status"] == "error"


# ---- Privacy -----------------------------------------------------------------


def test_raw_sql_not_in_success_response() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        text = json.dumps(_client().post(EXECUTE_PATH, json=body).json())
    assert SECRET_SQL not in text
    assert "secret_column_xyz_api_never_returned" not in text


def test_dbt_model_sql_not_in_success_response() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        text = json.dumps(_client().post(EXECUTE_PATH, json=body).json())
    assert body["checks"]["dbt_validation"]["model_sql"] not in text


def test_fixture_values_not_in_success_response() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ):
        text = json.dumps(_client().post(EXECUTE_PATH, json=body).json())
    assert SECRET_FIXTURE not in text


def test_raw_sql_not_in_error_response() -> None:
    body = _plan_body(sql="select secret_err_sql_xyz as x", dbt_sql="select other_err as y")
    text = json.dumps(_client().post(EXECUTE_PATH, json=body).json())
    assert "secret_err_sql_xyz" not in text
    assert "other_err" not in text


def test_expected_fingerprint_not_in_error_response() -> None:
    real_fp = _fp()
    body = _plan_body(content_fingerprint="c" * 64)
    text = json.dumps(_client().post(EXECUTE_PATH, json=body).json())
    assert real_fp not in text


def test_calculated_fingerprint_not_in_error_response() -> None:
    real_fp = _fp()
    body = _plan_body(content_fingerprint="d" * 64)
    text = json.dumps(_client().post(EXECUTE_PATH, json=body).json())
    assert real_fp not in text


def test_exception_message_not_leaked_on_500() -> None:
    body = _plan_body()

    def _boom(_plan: Any) -> ValidationArtifact:
        raise RuntimeError("sensitive internal boom detail xyz")

    client = TestClient(app, raise_server_exceptions=False)
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        side_effect=_boom,
    ):
        response = client.post(EXECUTE_PATH, json=body)
    assert response.status_code == 500
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "internal_error"
    assert payload["error"]["message"] == "An unexpected error occurred."
    assert payload["error"]["details"] is None
    text = json.dumps(payload)
    assert "sensitive internal boom" not in text
    assert "RuntimeError" not in text


# ---- Execution boundary ------------------------------------------------------


def test_route_handler_is_synchronous_not_coroutine() -> None:
    assert not inspect.iscoroutinefunction(validations_route.execute_validation)
    assert not asyncio.iscoroutinefunction(validations_route.execute_validation)


def test_route_calls_orchestrator_directly() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_pass_artifact(fp),
    ) as mock_orch:
        _client().post(EXECUTE_PATH, json=body)
        mock_orch.assert_called_once()
        arg = mock_orch.call_args[0][0]
        assert arg.intake_reference.content_fingerprint == fp


def test_no_http_loopback() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with (
        patch(
            "app.api.routes.validations.orchestrate_validation",
            return_value=_mock_pass_artifact(fp),
        ),
        patch("httpx.Client") as http_client,
        patch("urllib.request.urlopen") as urlopen,
    ):
        _client().post(EXECUTE_PATH, json=body)
        http_client.assert_not_called()
        urlopen.assert_not_called()


def test_route_does_not_aggregate_itself() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with (
        patch(
            "app.api.routes.validations.orchestrate_validation",
            return_value=_mock_pass_artifact(fp),
        ),
        patch(
            "app.services.validation_engine.build_validation_artifact",
            side_effect=AssertionError("route must not aggregate"),
        ),
    ):
        # Aggregation is inside orchestrator; with orchestrator mocked, build
        # must not be invoked from the route path.
        response = _client().post(EXECUTE_PATH, json=body)
    assert response.status_code == 200


def test_no_background_task() -> None:
    body = _plan_body()
    fp = body["intake_reference"]["content_fingerprint"]
    with (
        patch(
            "app.api.routes.validations.orchestrate_validation",
            return_value=_mock_pass_artifact(fp),
        ),
        patch("fastapi.BackgroundTasks.add_task", side_effect=AssertionError("no bg")),
        patch("asyncio.create_task", side_effect=AssertionError("no create_task")),
    ):
        assert _client().post(EXECUTE_PATH, json=body).status_code == 200


# ---- Regression --------------------------------------------------------------


def test_intake_endpoint_still_works() -> None:
    response = _client().post(
        INTAKE_PATH,
        json={
            "change_type": "rename_column",
            "asset": {
                "platform": "snowflake",
                "database": "analytics",
                "schema": "core",
                "name": "customers",
            },
            "source_column": "customer_id",
            "target_column": "account_id",
            "reason": None,
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "ok"


def test_risk_endpoint_still_works() -> None:
    intake = _client().post(
        INTAKE_PATH,
        json={
            "change_type": "rename_column",
            "asset": {
                "platform": "snowflake",
                "database": "analytics",
                "schema": "core",
                "name": "customers",
            },
            "source_column": "customer_id",
            "target_column": "account_id",
        },
    ).json()["data"]
    body = {
        "intake_reference": {
            "intake_id": intake["intake_id"],
            "normalized_change": intake["normalized_change"],
            "content_fingerprint": intake["content_fingerprint"],
            "artifact_version": intake["artifact_version"],
        },
        "evaluation_context": {
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        },
    }
    response = _client().post(RISK_PATH, json=body)
    assert response.status_code == 200
    assert response.json()["data"]["decision"] == "ALLOW"


def test_runs_analyze_endpoint_still_works() -> None:
    body = {
        "change": {
            "change_type": "rename_column",
            "asset": {
                "platform": "snowflake",
                "database": "analytics",
                "schema": "core",
                "name": "customers",
            },
            "source_column": "customer_id",
            "target_column": "account_id",
        },
        "evaluation_context": {
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        },
    }
    response = _client().post(RUNS_PATH, json=body)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_and_ready_still_work() -> None:
    assert _client().get("/health").status_code == 200
    assert _client().get("/ready").status_code == 200


def test_unknown_route_standard_404() -> None:
    response = _client().get("/api/v1/validations/does-not-exist")
    assert response.status_code == 404
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "not_found"
    assert "Not Found" not in payload["error"]["message"]


def test_openapi_includes_validations_execute() -> None:
    schema = app.openapi()
    paths = schema["paths"]
    assert "/api/v1/validations/execute" in paths
    assert "post" in paths["/api/v1/validations/execute"]
    # No retrieval / history routes.
    assert "/api/v1/validations/{id}" not in paths
    assert "/api/v1/validations" not in paths or "get" not in paths.get(
        "/api/v1/validations", {}
    )


def test_openapi_production_paths_exact_set() -> None:
    schema = app.openapi()
    methods: list[str] = []
    for path, ops in schema.get("paths", {}).items():
        for method in ops:
            if method in ("get", "post", "put", "patch", "delete"):
                methods.append(f"{method.upper()} {path}")
    assert sorted(methods) == sorted(
        [
            "GET /health",
            "GET /ready",
            "POST /api/v1/changes/intake",
            "POST /api/v1/risk/evaluate",
            "POST /api/v1/runs/analyze",
            "POST /api/v1/validations/execute",
        ]
    )
