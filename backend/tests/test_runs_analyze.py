"""Tests for POST /api/v1/runs/analyze (phase F5.3 / F6.7)."""

from __future__ import annotations

import asyncio
import copy
import inspect
import json
import re
import uuid
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.routes import runs as runs_route
from app.main import app
from app.schemas.changes import ChangeIntakeRequest, NormalizedChange
from app.schemas.risk import EvaluationContext, IntakeReference, RiskEvaluateRequest
from app.schemas.runs import AnalysisRunRequest
from app.schemas.validation import (
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    OverallExecutionStatus,
    ValidationArtifact,
    ValidationCheckResult,
    ValidationEvidence,
)
from app.services.change_intake import process_change_intake
from app.services.risk_engine import evaluate_risk, risk_meta
from app.services.run_orchestrator import orchestrate_analysis_run

ANALYZE_PATH = "/api/v1/runs/analyze"
INTAKE_PATH = "/api/v1/changes/intake"
EVALUATE_PATH = "/api/v1/risk/evaluate"
VALIDATIONS_PATH = "/api/v1/validations/execute"
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")

CHANGE: dict[str, Any] = {
    "change_type": "rename_column",
    "asset": {
        "platform": "snowflake",
        "database": "analytics",
        "schema": "core",
        "name": "customers",
    },
    "source_column": "customer_id",
    "target_column": "account_id",
    "reason": "Standardize the customer identifier.",
}

SECRET_SQL = "select secret_run_sql_xyz as account_id from customers"
SECRET_FIXTURE = "fixture_run_secret_cell_xyz"


def _client() -> TestClient:
    return TestClient(app)


def _body(
    context: dict[str, Any],
    change: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "change": change or copy.deepcopy(CHANGE),
        "evaluation_context": context,
    }
    if validation is not None:
        payload["validation"] = validation
    return payload


def _allow_ctx() -> dict[str, Any]:
    return {
        "context_complete": True,
        "downstream_dependency_count": 0,
        "protected_asset": False,
    }


def _warn_ctx() -> dict[str, Any]:
    return {
        "context_complete": True,
        "downstream_dependency_count": 3,
        "protected_asset": False,
    }


def _block_ctx() -> dict[str, Any]:
    return {
        "context_complete": False,
        "downstream_dependency_count": None,
        "protected_asset": True,
    }


def _validation_block(
    *,
    sql: str = SECRET_SQL,
    dbt_sql: str | None = None,
    dbt_required: bool = False,
    fixture_rows: list[list[Any]] | None = None,
) -> dict[str, Any]:
    return {
        "checks": {
            "sql_parse": {
                "sql": sql,
                "dialect": "snowflake",
                "required": True,
            },
            "duckdb_execution": {
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
                "required": True,
            },
            "dbt_validation": {
                "model_name": "customers_renamed",
                "model_sql": dbt_sql if dbt_sql is not None else sql,
                "required": dbt_required,
            },
        }
    }


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


def _mock_artifact(
    fp: str,
    *,
    outcome: CheckOutcome = CheckOutcome.PASS,
    execution_status: OverallExecutionStatus = OverallExecutionStatus.COMPLETED,
    sql_outcome: CheckOutcome | None = None,
    duck_outcome: CheckOutcome | None = None,
    dbt_status: CheckExecutionStatus = CheckExecutionStatus.COMPLETED,
    dbt_outcome: CheckOutcome | None = CheckOutcome.PASS,
    dbt_required: bool = False,
) -> ValidationArtifact:
    sql_out = sql_outcome if sql_outcome is not None else outcome
    duck_out = duck_outcome if duck_outcome is not None else CheckOutcome.PASS
    return ValidationArtifact(
        validation_id=uuid.uuid4(),
        subject_fingerprint=fp,
        scope="provided_artifacts_only",
        execution_status=execution_status,
        outcome=outcome,
        checks=[
            _check(
                kind=CheckKind.SQL_PARSE,
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=sql_out,
            ),
            _check(
                kind=CheckKind.DUCKDB_EXECUTION,
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=duck_out,
            ),
            _check(
                kind=CheckKind.DBT_VALIDATION,
                execution_status=dbt_status,
                outcome=dbt_outcome,
                required=dbt_required,
            ),
        ],
        artifact_version="1.0",
    )


# ---- Backward compatibility (no validation) ----------------------------------


def test_allow_run_http_200() -> None:
    response = _client().post(ANALYZE_PATH, json=_body(_allow_ctx()))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["risk_evaluation"]["decision"] == "ALLOW"
    assert data["orchestration_status"] == "completed"


def test_warn_run_http_200() -> None:
    response = _client().post(ANALYZE_PATH, json=_body(_warn_ctx()))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["risk_evaluation"]["decision"] == "WARN"
    assert data["orchestration_status"] == "completed"


def test_block_run_http_200() -> None:
    response = _client().post(ANALYZE_PATH, json=_body(_block_ctx()))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["risk_evaluation"]["decision"] == "BLOCK"
    assert data["orchestration_status"] == "completed"


def test_legacy_request_without_validation_http_200() -> None:
    response = _client().post(ANALYZE_PATH, json=_body(_allow_ctx()))
    assert response.status_code == 200
    data = response.json()["data"]
    assert "change_intake" in data
    assert "risk_evaluation" in data


def test_validation_artifact_null_when_not_requested() -> None:
    data = _client().post(ANALYZE_PATH, json=_body(_allow_ctx())).json()["data"]
    assert data["validation_artifact"] is None


def test_meta_validation_not_requested() -> None:
    meta = _client().post(ANALYZE_PATH, json=_body(_allow_ctx())).json()["meta"]
    assert meta["validation_requested"] is False
    assert meta["validation_executed"] is False
    assert meta["validation_artifact_present"] is False


def test_success_envelope_shape() -> None:
    body = _client().post(ANALYZE_PATH, json=_body(_allow_ctx())).json()
    assert body["status"] == "ok"
    assert set(body.keys()) == {"status", "data", "meta"}
    data = body["data"]
    assert set(data.keys()) == {
        "run_id",
        "orchestration_status",
        "change_intake",
        "risk_evaluation",
        "validation_artifact",
        "run_artifact_version",
    }
    assert data["run_artifact_version"] == "1.1"
    assert data["validation_artifact"] is None


def test_run_intake_evaluation_ids_are_uuids() -> None:
    data = _client().post(ANALYZE_PATH, json=_body(_allow_ctx())).json()["data"]
    uuid.UUID(data["run_id"])
    uuid.UUID(data["change_intake"]["intake_id"])
    uuid.UUID(data["risk_evaluation"]["evaluation_id"])


def test_intake_id_and_fingerprint_consistency() -> None:
    data = _client().post(ANALYZE_PATH, json=_body(_allow_ctx())).json()["data"]
    assert data["risk_evaluation"]["intake_id"] == data["change_intake"]["intake_id"]
    assert (
        data["risk_evaluation"]["evaluated_content_fingerprint"]
        == data["change_intake"]["content_fingerprint"]
    )
    assert SHA256_HEX.match(data["change_intake"]["content_fingerprint"])


def test_matches_standalone_intake_normalized_and_fingerprint() -> None:
    response = _client().post(ANALYZE_PATH, json=_body(_allow_ctx()))
    run = response.json()["data"]
    standalone = process_change_intake(ChangeIntakeRequest.model_validate(CHANGE))
    assert run["change_intake"]["normalized_change"] == standalone.normalized_change
    assert run["change_intake"]["content_fingerprint"] == standalone.content_fingerprint


def test_matches_standalone_risk_decision_and_reasons() -> None:
    run = _client().post(ANALYZE_PATH, json=_body(_warn_ctx())).json()["data"]
    intake = process_change_intake(ChangeIntakeRequest.model_validate(CHANGE))
    risk_req = RiskEvaluateRequest(
        intake_reference=IntakeReference(
            intake_id=intake.intake_id,
            normalized_change=NormalizedChange.model_validate(
                intake.normalized_change
            ),
            content_fingerprint=intake.content_fingerprint,
            artifact_version=intake.artifact_version,
        ),
        evaluation_context=EvaluationContext.model_validate(_warn_ctx()),
    )
    standalone = evaluate_risk(risk_req)
    assert run["risk_evaluation"]["decision"] == standalone.decision
    assert run["risk_evaluation"]["reasons"] == [
        r.model_dump(mode="json") for r in standalone.reasons
    ]
    assert run["risk_evaluation"]["scope"] == standalone.scope
    assert run["risk_evaluation"]["policy_version"] == standalone.policy_version


def test_identical_source_target_rejected() -> None:
    change = {**CHANGE, "source_column": "id", "target_column": "id"}
    response = _client().post(ANALYZE_PATH, json=_body(_allow_ctx(), change=change))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unsupported_change_type_rejected() -> None:
    change = {**CHANGE, "change_type": "drop_table"}
    response = _client().post(ANALYZE_PATH, json=_body(_allow_ctx(), change=change))
    assert response.status_code == 422


def test_invalid_evaluation_context_rejected() -> None:
    response = _client().post(
        ANALYZE_PATH,
        json=_body(
            {
                "context_complete": True,
                "downstream_dependency_count": None,
                "protected_asset": False,
            }
        ),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unknown_field_rejected() -> None:
    body = _body(_allow_ctx())
    body["extra_field"] = "nope"
    response = _client().post(ANALYZE_PATH, json=body)
    assert response.status_code == 422


def test_client_sent_run_id_rejected() -> None:
    body = _body(_allow_ctx())
    body["run_id"] = str(uuid.uuid4())
    response = _client().post(ANALYZE_PATH, json=body)
    assert response.status_code == 422


def test_client_sent_decision_rejected() -> None:
    body = _body(_allow_ctx())
    body["decision"] = "ALLOW"
    response = _client().post(ANALYZE_PATH, json=body)
    assert response.status_code == 422


def test_client_sent_fingerprint_rejected() -> None:
    body = _body(_allow_ctx())
    body["content_fingerprint"] = "a" * 64
    response = _client().post(ANALYZE_PATH, json=body)
    assert response.status_code == 422


def test_malformed_json_rejected() -> None:
    response = _client().post(
        ANALYZE_PATH,
        content=b"{not-json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["status"] == "error"


def test_meta_honest_orchestration_contract_without_validation() -> None:
    meta = _client().post(ANALYZE_PATH, json=_body(_allow_ctx())).json()["meta"]
    assert meta["operation"] == "synchronous_analysis_run"
    assert meta["phase"] == "F6.7"
    assert meta["execution_mode"] == "in_process"
    assert meta["persistence"] == "none"
    assert meta["retrieval_available"] is False
    assert meta["context_origin"] == "caller_provided"
    assert meta["context_trust"] == "unverified"
    assert meta["intake_reference_origin"] == "riftless_runtime"
    assert meta["intake_reference_scope"] == "current_request_only"
    assert meta["intake_reference_persisted"] is False
    assert meta["model_used"] is False
    assert meta["deployment_authorized"] is False
    assert meta["validation_requested"] is False
    assert meta["validation_executed"] is False
    assert meta["validation_artifact_present"] is False
    assert meta["validation_persistence"] == "none"
    assert meta["validation_retrieval_available"] is False
    assert meta["validation_subject_origin"] is None
    assert meta["validation_subject_scope"] is None
    assert meta["validation_subject_persisted"] is False
    assert meta["validation_input_origin"] is None
    assert meta["validation_input_trust"] is None
    assert meta["validation_sql_origin"] is None
    assert meta["validation_fixture_origin"] is None


def test_completed_independent_of_decision() -> None:
    for ctx in (_allow_ctx(), _warn_ctx(), _block_ctx()):
        data = _client().post(ANALYZE_PATH, json=_body(ctx)).json()["data"]
        assert data["orchestration_status"] == "completed"


def test_deterministic_content_and_decision_ids_may_differ() -> None:
    body = _body(_block_ctx())
    first = _client().post(ANALYZE_PATH, json=body).json()["data"]
    second = _client().post(ANALYZE_PATH, json=copy.deepcopy(body)).json()["data"]

    assert first["change_intake"]["normalized_change"] == second["change_intake"][
        "normalized_change"
    ]
    assert first["change_intake"]["content_fingerprint"] == second["change_intake"][
        "content_fingerprint"
    ]
    assert first["risk_evaluation"]["decision"] == second["risk_evaluation"]["decision"]
    assert first["risk_evaluation"]["reasons"] == second["risk_evaluation"]["reasons"]
    assert first["run_id"] != second["run_id"]
    assert first["change_intake"]["intake_id"] != second["change_intake"]["intake_id"]
    assert (
        first["risk_evaluation"]["evaluation_id"]
        != second["risk_evaluation"]["evaluation_id"]
    )


def test_orchestrator_service_in_process_no_http() -> None:
    request = AnalysisRunRequest(
        change=ChangeIntakeRequest.model_validate(CHANGE),
        evaluation_context=EvaluationContext.model_validate(_allow_ctx()),
    )
    result = orchestrate_analysis_run(request)
    assert result.orchestration_status == "completed"
    assert result.risk_evaluation.decision == "ALLOW"
    assert result.risk_evaluation.intake_id == result.change_intake.intake_id
    assert result.validation_artifact is None
    assert result.run_artifact_version == "1.1"


def test_standalone_risk_meta_still_caller_provided() -> None:
    intake = process_change_intake(ChangeIntakeRequest.model_validate(CHANGE))
    body = {
        "intake_reference": {
            "intake_id": str(intake.intake_id),
            "normalized_change": intake.normalized_change,
            "content_fingerprint": intake.content_fingerprint,
            "artifact_version": intake.artifact_version,
        },
        "evaluation_context": _allow_ctx(),
    }
    meta = _client().post(EVALUATE_PATH, json=body).json()["meta"]
    assert meta["intake_reference_origin"] == "caller_provided"
    assert meta["intake_reference_trust"] == "unverified"
    assert meta["fingerprint_check"] == "matched"
    assert meta["context_origin"] == "caller_provided"
    assert meta["context_trust"] == "unverified"
    assert risk_meta()["intake_reference_origin"] == "caller_provided"


def test_missing_change_rejected() -> None:
    response = _client().post(
        ANALYZE_PATH,
        json={"evaluation_context": _allow_ctx()},
    )
    assert response.status_code == 422


def test_missing_evaluation_context_rejected() -> None:
    response = _client().post(
        ANALYZE_PATH,
        json={"change": CHANGE},
    )
    assert response.status_code == 422


def test_negative_dependency_count_rejected() -> None:
    response = _client().post(
        ANALYZE_PATH,
        json=_body(
            {
                "context_complete": True,
                "downstream_dependency_count": -1,
                "protected_asset": False,
            }
        ),
    )
    assert response.status_code == 422


# ---- Validation integration --------------------------------------------------


def test_valid_analysis_with_validation_http_200() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())
    fp_holder: dict[str, str] = {}

    def _orch(plan: Any) -> ValidationArtifact:
        fp_holder["fp"] = plan.intake_reference.content_fingerprint
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        response = _client().post(ANALYZE_PATH, json=body)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["validation_artifact"] is not None
    assert data["validation_artifact"]["subject_fingerprint"] == data["change_intake"][
        "content_fingerprint"
    ]
    assert data["validation_artifact"]["subject_fingerprint"] == fp_holder["fp"]


def test_validation_artifact_uses_f61_contract() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    ValidationArtifact.model_validate(data["validation_artifact"])


def test_validation_checks_order_fixed() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        checks = _client().post(ANALYZE_PATH, json=body).json()["data"][
            "validation_artifact"
        ]["checks"]
    assert [c["check_kind"] for c in checks] == [
        "sql_parse",
        "duckdb_execution",
        "dbt_validation",
    ]


def test_validation_subject_fingerprint_matches_intake() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    assert (
        data["validation_artifact"]["subject_fingerprint"]
        == data["change_intake"]["content_fingerprint"]
    )


def test_runtime_intake_id_used_in_validation_plan() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())
    captured: dict[str, Any] = {}

    def _orch(plan: Any) -> ValidationArtifact:
        captured["intake_id"] = str(plan.intake_reference.intake_id)
        captured["fp"] = plan.intake_reference.content_fingerprint
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    assert captured["intake_id"] == data["change_intake"]["intake_id"]
    assert captured["fp"] == data["change_intake"]["content_fingerprint"]


def test_caller_cannot_send_intake_reference_in_validation() -> None:
    validation = _validation_block()
    validation["intake_reference"] = {"intake_id": str(uuid.uuid4())}
    response = _client().post(
        ANALYZE_PATH, json=_body(_allow_ctx(), validation=validation)
    )
    assert response.status_code == 422


def test_caller_cannot_send_normalized_change_in_validation() -> None:
    validation = _validation_block()
    validation["checks"]["duckdb_execution"]["normalized_change"] = CHANGE
    response = _client().post(
        ANALYZE_PATH, json=_body(_allow_ctx(), validation=validation)
    )
    assert response.status_code == 422


def test_caller_cannot_send_content_fingerprint_in_validation() -> None:
    validation = _validation_block()
    validation["content_fingerprint"] = "a" * 64
    response = _client().post(
        ANALYZE_PATH, json=_body(_allow_ctx(), validation=validation)
    )
    assert response.status_code == 422


def test_caller_cannot_send_validation_id() -> None:
    validation = _validation_block()
    validation["validation_id"] = str(uuid.uuid4())
    response = _client().post(
        ANALYZE_PATH, json=_body(_allow_ctx(), validation=validation)
    )
    assert response.status_code == 422


def test_caller_cannot_send_validation_outcome() -> None:
    validation = _validation_block()
    validation["outcome"] = "pass"
    response = _client().post(
        ANALYZE_PATH, json=_body(_allow_ctx(), validation=validation)
    )
    assert response.status_code == 422


def test_sql_mismatch_http_422() -> None:
    validation = _validation_block(
        sql="select 1 as account_id",
        dbt_sql="select 2 as account_id",
    )
    response = _client().post(
        ANALYZE_PATH, json=_body(_allow_ctx(), validation=validation)
    )
    assert response.status_code == 422
    text = json.dumps(response.json())
    assert "select 1" not in text
    assert "select 2" not in text
    assert "sql_input_mismatch" in text.lower() or "identical" in text.lower()


def test_invalid_fixture_http_422() -> None:
    validation = _validation_block()
    validation["checks"]["duckdb_execution"]["fixture"] = {
        "columns": [],
        "rows": [],
    }
    response = _client().post(
        ANALYZE_PATH, json=_body(_allow_ctx(), validation=validation)
    )
    assert response.status_code == 422


def test_invalid_dbt_input_http_422() -> None:
    validation = _validation_block()
    validation["checks"]["dbt_validation"]["model_name"] = "Invalid-Name"
    response = _client().post(
        ANALYZE_PATH, json=_body(_allow_ctx(), validation=validation)
    )
    assert response.status_code == 422


def test_raw_sql_not_in_response() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        text = json.dumps(_client().post(ANALYZE_PATH, json=body).json())
    assert SECRET_SQL not in text
    assert "secret_run_sql_xyz" not in text


def test_fixture_values_not_in_response() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        text = json.dumps(_client().post(ANALYZE_PATH, json=body).json())
    assert SECRET_FIXTURE not in text


# ---- Independent risk / validation semantics ---------------------------------


def test_risk_allow_validation_pass_independent() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(
            plan.intake_reference.content_fingerprint,
            outcome=CheckOutcome.PASS,
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    assert data["risk_evaluation"]["decision"] == "ALLOW"
    assert data["validation_artifact"]["outcome"] == "pass"


def test_risk_allow_validation_fail_independent() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(
            plan.intake_reference.content_fingerprint,
            outcome=CheckOutcome.FAIL,
            sql_outcome=CheckOutcome.FAIL,
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    assert data["risk_evaluation"]["decision"] == "ALLOW"
    assert data["validation_artifact"]["outcome"] == "fail"


def test_risk_warn_validation_pass_independent() -> None:
    body = _body(_warn_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    assert data["risk_evaluation"]["decision"] == "WARN"
    assert data["validation_artifact"]["outcome"] == "pass"


def test_risk_block_validation_pass_independent() -> None:
    body = _body(_block_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    assert data["risk_evaluation"]["decision"] == "BLOCK"
    assert data["validation_artifact"]["outcome"] == "pass"


def test_risk_block_still_runs_validation() -> None:
    body = _body(_block_ctx(), validation=_validation_block())
    called = {"n": 0}

    def _orch(plan: Any) -> ValidationArtifact:
        called["n"] += 1
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    assert called["n"] == 1
    assert data["validation_artifact"] is not None
    assert data["risk_evaluation"]["decision"] == "BLOCK"


def test_validation_fail_does_not_change_risk() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(
            plan.intake_reference.content_fingerprint,
            outcome=CheckOutcome.FAIL,
            sql_outcome=CheckOutcome.FAIL,
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    assert data["risk_evaluation"]["decision"] == "ALLOW"
    assert data["validation_artifact"]["outcome"] == "fail"


def test_validation_inconclusive_does_not_change_risk() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(
            plan.intake_reference.content_fingerprint,
            outcome=CheckOutcome.INCONCLUSIVE,
            sql_outcome=CheckOutcome.INCONCLUSIVE,
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    assert data["risk_evaluation"]["decision"] == "ALLOW"
    assert data["validation_artifact"]["outcome"] == "inconclusive"


def test_validation_partial_does_not_change_risk() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(
            plan.intake_reference.content_fingerprint,
            outcome=CheckOutcome.PASS,
            execution_status=OverallExecutionStatus.PARTIAL,
            dbt_status=CheckExecutionStatus.ERROR,
            dbt_outcome=None,
            dbt_required=False,
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    assert data["risk_evaluation"]["decision"] == "ALLOW"
    assert data["validation_artifact"]["execution_status"] == "partial"
    assert data["orchestration_status"] == "completed"


def test_completed_not_dependent_on_risk_allow() -> None:
    body = _body(_block_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    assert data["orchestration_status"] == "completed"
    assert data["risk_evaluation"]["decision"] == "BLOCK"


def test_completed_not_dependent_on_validation_pass() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(
            plan.intake_reference.content_fingerprint,
            outcome=CheckOutcome.FAIL,
            sql_outcome=CheckOutcome.FAIL,
        )

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    assert data["orchestration_status"] == "completed"
    assert data["validation_artifact"]["outcome"] == "fail"


# ---- Meta and execution boundary ---------------------------------------------


def test_meta_when_validation_requested() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        meta = _client().post(ANALYZE_PATH, json=body).json()["meta"]
    assert meta["validation_requested"] is True
    assert meta["validation_executed"] is True
    assert meta["validation_artifact_present"] is True
    assert meta["validation_subject_origin"] == "riftless_runtime"
    assert meta["validation_subject_scope"] == "current_request_only"
    assert meta["validation_subject_persisted"] is False
    assert meta["validation_input_origin"] == "caller_provided"
    assert meta["validation_input_trust"] == "unverified"
    assert meta["validation_sql_origin"] == "caller_provided"
    assert meta["validation_fixture_origin"] == "caller_provided"
    assert meta["validation_persistence"] == "none"
    assert meta["validation_retrieval_available"] is False
    assert meta["deployment_authorized"] is False
    assert meta["phase"] == "F6.7"


def test_route_handler_is_synchronous() -> None:
    assert not inspect.iscoroutinefunction(runs_route.analyze_run)
    assert not asyncio.iscoroutinefunction(runs_route.analyze_run)


def test_no_http_loopback_with_validation() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with (
        patch(
            "app.services.run_orchestrator.orchestrate_validation",
            side_effect=_orch,
        ),
        patch("httpx.Client") as http_client,
        patch("urllib.request.urlopen") as urlopen,
    ):
        assert _client().post(ANALYZE_PATH, json=body).status_code == 200
        http_client.assert_not_called()
        urlopen.assert_not_called()


def test_run_orchestrator_calls_validation_orchestrator_directly() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())
    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
    ) as mock_orch:
        mock_orch.side_effect = lambda plan: _mock_artifact(
            plan.intake_reference.content_fingerprint
        )
        _client().post(ANALYZE_PATH, json=body)
        mock_orch.assert_called_once()


def test_no_background_task() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())

    def _orch(plan: Any) -> ValidationArtifact:
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with (
        patch(
            "app.services.run_orchestrator.orchestrate_validation",
            side_effect=_orch,
        ),
        patch("asyncio.create_task", side_effect=AssertionError("no create_task")),
    ):
        assert _client().post(ANALYZE_PATH, json=body).status_code == 200


def test_duckdb_uses_runtime_normalized_change() -> None:
    body = _body(_allow_ctx(), validation=_validation_block())
    captured: dict[str, Any] = {}

    def _orch(plan: Any) -> ValidationArtifact:
        captured["duck_change"] = plan.checks.duckdb_execution.normalized_change.fingerprint_payload()
        captured["intake_change"] = plan.intake_reference.normalized_change.fingerprint_payload()
        return _mock_artifact(plan.intake_reference.content_fingerprint)

    with patch(
        "app.services.run_orchestrator.orchestrate_validation",
        side_effect=_orch,
    ):
        data = _client().post(ANALYZE_PATH, json=body).json()["data"]
    assert captured["duck_change"] == captured["intake_change"]
    assert captured["duck_change"] == data["change_intake"]["normalized_change"]


# ---- Real integration --------------------------------------------------------


def test_real_analyze_with_validation_all_engines() -> None:
    """One real request: intake + risk + SQLGlot + DuckDB + dbt."""
    sql = "select customer_id as account_id from customers"
    body = _body(
        _allow_ctx(),
        validation=_validation_block(sql=sql, dbt_required=False),
    )
    response = _client().post(ANALYZE_PATH, json=body)
    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]
    assert data["orchestration_status"] == "completed"
    assert data["run_artifact_version"] == "1.1"
    assert data["risk_evaluation"]["decision"] == "ALLOW"
    assert data["validation_artifact"] is not None
    va = data["validation_artifact"]
    assert va["scope"] == "provided_artifacts_only"
    assert va["subject_fingerprint"] == data["change_intake"]["content_fingerprint"]
    assert [c["check_kind"] for c in va["checks"]] == [
        "sql_parse",
        "duckdb_execution",
        "dbt_validation",
    ]
    assert all(c["execution_status"] == "completed" for c in va["checks"])
    assert all(c["outcome"] == "pass" for c in va["checks"])
    assert va["outcome"] == "pass"
    serialized = json.dumps(payload)
    assert SECRET_SQL not in serialized
    assert sql not in serialized
    assert SECRET_FIXTURE not in serialized
    assert payload["meta"]["validation_requested"] is True
    assert payload["meta"]["validation_subject_origin"] == "riftless_runtime"


# ---- Regression --------------------------------------------------------------


def test_regression_intake_risk_health_ready_validations() -> None:
    client = _client()
    assert client.post(INTAKE_PATH, json=CHANGE).status_code == 201
    intake = process_change_intake(ChangeIntakeRequest.model_validate(CHANGE))
    risk_body = {
        "intake_reference": {
            "intake_id": str(intake.intake_id),
            "normalized_change": intake.normalized_change,
            "content_fingerprint": intake.content_fingerprint,
            "artifact_version": intake.artifact_version,
        },
        "evaluation_context": _allow_ctx(),
    }
    assert client.post(EVALUATE_PATH, json=risk_body).status_code == 200
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200

    # Standalone validations/execute still uses caller-provided intake.
    sql = "select customer_id as account_id from customers"
    validation_body = {
        "intake_reference": {
            "intake_id": str(intake.intake_id),
            "normalized_change": intake.normalized_change,
            "content_fingerprint": intake.content_fingerprint,
            "artifact_version": intake.artifact_version,
        },
        "checks": {
            "sql_parse": {"sql": sql, "dialect": "snowflake", "required": True},
            "duckdb_execution": {
                "normalized_change": intake.normalized_change,
                "fixture": {
                    "columns": [
                        {
                            "name": "customer_id",
                            "type": "varchar",
                            "nullable": False,
                        }
                    ],
                    "rows": [["customer-1"]],
                },
                "required": True,
            },
            "dbt_validation": {
                "model_name": "customers_renamed",
                "model_sql": sql,
                "required": False,
            },
        },
    }
    with patch(
        "app.api.routes.validations.orchestrate_validation",
        return_value=_mock_artifact(intake.content_fingerprint),
    ):
        assert client.post(VALIDATIONS_PATH, json=validation_body).status_code == 200


def test_unknown_route_standard_404() -> None:
    response = _client().get("/api/v1/runs/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_openapi_paths_unchanged_six_routes() -> None:
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


def test_jinja_in_dbt_rejected() -> None:
    validation = _validation_block(sql="select 1 as x")
    validation["checks"]["sql_parse"]["sql"] = "select {{ col }} as x"
    validation["checks"]["dbt_validation"]["model_sql"] = "select {{ col }} as x"
    response = _client().post(
        ANALYZE_PATH, json=_body(_allow_ctx(), validation=validation)
    )
    assert response.status_code == 422
