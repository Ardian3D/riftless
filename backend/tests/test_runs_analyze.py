"""Tests for POST /api/v1/runs/analyze (phase F5.3)."""

from __future__ import annotations

import copy
import re
import uuid
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.changes import ChangeIntakeRequest, NormalizedChange
from app.schemas.risk import EvaluationContext, IntakeReference, RiskEvaluateRequest
from app.schemas.runs import AnalysisRunRequest
from app.services.change_intake import process_change_intake
from app.services.risk_engine import evaluate_risk, risk_meta
from app.services.run_orchestrator import orchestrate_analysis_run

ANALYZE_PATH = "/api/v1/runs/analyze"
INTAKE_PATH = "/api/v1/changes/intake"
EVALUATE_PATH = "/api/v1/risk/evaluate"
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


def _client() -> TestClient:
    return TestClient(app)


def _body(context: dict[str, Any], change: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "change": change or copy.deepcopy(CHANGE),
        "evaluation_context": context,
    }


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
        "run_artifact_version",
    }
    assert data["run_artifact_version"] == "1.0"


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
    # complete=true with null dependency count
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


def test_meta_honest_orchestration_contract() -> None:
    meta = _client().post(ANALYZE_PATH, json=_body(_allow_ctx())).json()["meta"]
    assert meta == {
        "operation": "synchronous_analysis_run",
        "phase": "F5.3",
        "execution_mode": "in_process",
        "persistence": "none",
        "retrieval_available": False,
        "context_origin": "caller_provided",
        "context_trust": "unverified",
        "intake_reference_origin": "riftless_runtime",
        "intake_reference_scope": "current_request_only",
        "intake_reference_persisted": False,
        "model_used": False,
        "validation_executed": False,
        "deployment_authorized": False,
    }


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
    """Direct service call works without going through HTTP endpoints."""
    request = AnalysisRunRequest(
        change=ChangeIntakeRequest.model_validate(CHANGE),
        evaluation_context=EvaluationContext.model_validate(_allow_ctx()),
    )
    result = orchestrate_analysis_run(request)
    assert result.orchestration_status == "completed"
    assert result.risk_evaluation.decision == "ALLOW"
    assert result.risk_evaluation.intake_id == result.change_intake.intake_id


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
    # risk_meta helper stays aligned with endpoint
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


def test_regression_intake_risk_health_ready() -> None:
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
