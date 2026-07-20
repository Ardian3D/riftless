"""Tests for POST /api/v1/risk/evaluate (phase F5.2)."""

from __future__ import annotations

import copy
import re
import uuid
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.changes import ChangeIntakeRequest
from app.services.change_intake import process_change_intake
from app.services.risk_engine import evaluate_risk
from app.schemas.risk import RiskEvaluateRequest

EVALUATE_PATH = "/api/v1/risk/evaluate"
INTAKE_PATH = "/api/v1/changes/intake"
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")

INTAKE_PAYLOAD: dict[str, Any] = {
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


def _make_intake_reference() -> dict[str, Any]:
    """Build a valid intake_reference via the real intake service (no network)."""
    result = process_change_intake(ChangeIntakeRequest.model_validate(INTAKE_PAYLOAD))
    return {
        "intake_id": str(result.intake_id),
        "normalized_change": result.normalized_change,
        "content_fingerprint": result.content_fingerprint,
        "artifact_version": result.artifact_version,
    }


def _evaluate_body(
    *,
    context: dict[str, Any],
    intake_reference: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "intake_reference": intake_reference or _make_intake_reference(),
        "evaluation_context": context,
    }


def test_allow_complete_zero_deps_unprotected() -> None:
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        }
    )
    response = _client().post(EVALUATE_PATH, json=body)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["decision"] == "ALLOW"
    assert data["scope"] == "provided_context_only"
    assert len(data["reasons"]) == 1
    assert data["reasons"][0]["code"] == "no_risk_condition_detected"
    assert data["reasons"][0]["level"] == "ALLOW"


def test_warn_incomplete_context() -> None:
    body = _evaluate_body(
        context={
            "context_complete": False,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        }
    )
    data = _client().post(EVALUATE_PATH, json=body).json()["data"]
    assert data["decision"] == "WARN"
    codes = [r["code"] for r in data["reasons"]]
    assert "incomplete_context" in codes
    assert "no_risk_condition_detected" not in codes


def test_warn_unknown_dependency_count() -> None:
    body = _evaluate_body(
        context={
            "context_complete": False,
            "downstream_dependency_count": None,
            "protected_asset": False,
        }
    )
    data = _client().post(EVALUATE_PATH, json=body).json()["data"]
    assert data["decision"] == "WARN"
    codes = [r["code"] for r in data["reasons"]]
    assert "unknown_dependency_count" in codes
    assert "incomplete_context" in codes


def test_warn_downstream_dependencies_present() -> None:
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 3,
            "protected_asset": False,
        }
    )
    data = _client().post(EVALUATE_PATH, json=body).json()["data"]
    assert data["decision"] == "WARN"
    assert len(data["reasons"]) == 1
    reason = data["reasons"][0]
    assert reason["code"] == "downstream_dependencies_present"
    assert reason["level"] == "WARN"
    assert reason["evidence"] == {"downstream_dependency_count": 3}


def test_block_protected_asset() -> None:
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": True,
        }
    )
    data = _client().post(EVALUATE_PATH, json=body).json()["data"]
    assert data["decision"] == "BLOCK"
    assert data["reasons"][0]["code"] == "protected_asset"
    assert data["reasons"][0]["level"] == "BLOCK"


def test_block_precedence_with_incomplete_context() -> None:
    body = _evaluate_body(
        context={
            "context_complete": False,
            "downstream_dependency_count": None,
            "protected_asset": True,
        }
    )
    data = _client().post(EVALUATE_PATH, json=body).json()["data"]
    assert data["decision"] == "BLOCK"
    codes = [r["code"] for r in data["reasons"]]
    assert codes == [
        "protected_asset",
        "incomplete_context",
        "unknown_dependency_count",
    ]
    levels = [r["level"] for r in data["reasons"]]
    assert levels == ["BLOCK", "WARN", "WARN"]


def test_all_triggered_reasons_returned_and_ordered() -> None:
    body = _evaluate_body(
        context={
            "context_complete": False,
            "downstream_dependency_count": 2,
            "protected_asset": True,
        }
    )
    data = _client().post(EVALUATE_PATH, json=body).json()["data"]
    codes = [r["code"] for r in data["reasons"]]
    assert codes == [
        "protected_asset",
        "incomplete_context",
        "downstream_dependencies_present",
    ]
    assert data["decision"] == "BLOCK"


def test_allow_reason_only_when_no_warn_or_block() -> None:
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        }
    )
    reasons = _client().post(EVALUATE_PATH, json=body).json()["data"]["reasons"]
    assert [r["code"] for r in reasons] == ["no_risk_condition_detected"]


def test_evaluation_id_is_uuid_and_intake_id_preserved() -> None:
    ref = _make_intake_reference()
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        },
        intake_reference=ref,
    )
    data = _client().post(EVALUATE_PATH, json=body).json()["data"]
    uuid.UUID(data["evaluation_id"])
    assert data["intake_id"] == ref["intake_id"]
    assert data["evaluated_content_fingerprint"] == ref["content_fingerprint"]
    assert SHA256_HEX.match(data["evaluated_content_fingerprint"])


def test_valid_fingerprint_accepted() -> None:
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        }
    )
    response = _client().post(EVALUATE_PATH, json=body)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_fingerprint_mismatch_rejected() -> None:
    ref = _make_intake_reference()
    original_fp = ref["content_fingerprint"]
    # Flip one hex character without leaving lowercase hex charset.
    bad_fp = ("0" if original_fp[0] != "0" else "1") + original_fp[1:]
    ref["content_fingerprint"] = bad_fp
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        },
        intake_reference=ref,
    )
    response = _client().post(EVALUATE_PATH, json=body)
    assert response.status_code == 422
    err = response.json()
    assert err["status"] == "error"
    assert err["error"]["code"] == "validation_error"
    assert (
        err["error"]["message"]
        == "The supplied fingerprint does not match the normalized change."
    )
    # Must not leak expected fingerprint, canonical JSON, or attack claims.
    raw = response.text.lower()
    assert "traceback" not in raw
    assert "canonical" not in raw
    assert original_fp not in response.text
    assert "tamper" not in raw
    assert "attack" not in raw
    assert "manipulat" not in raw


def test_malformed_fingerprint_rejected() -> None:
    ref = _make_intake_reference()
    ref["content_fingerprint"] = "NOT_A_VALID_FINGERPRINT"
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        },
        intake_reference=ref,
    )
    response = _client().post(EVALUATE_PATH, json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_uppercase_fingerprint_rejected() -> None:
    ref = _make_intake_reference()
    ref["content_fingerprint"] = ref["content_fingerprint"].upper()
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        },
        intake_reference=ref,
    )
    response = _client().post(EVALUATE_PATH, json=body)
    assert response.status_code == 422


def test_unsupported_artifact_version_rejected() -> None:
    ref = _make_intake_reference()
    ref["artifact_version"] = "9.9"
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        },
        intake_reference=ref,
    )
    response = _client().post(EVALUATE_PATH, json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_negative_dependency_count_rejected() -> None:
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": -1,
            "protected_asset": False,
        }
    )
    response = _client().post(EVALUATE_PATH, json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_complete_context_with_null_dependency_rejected() -> None:
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": None,
            "protected_asset": False,
        }
    )
    response = _client().post(EVALUATE_PATH, json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unknown_request_field_rejected() -> None:
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        }
    )
    body["unexpected"] = "nope"
    response = _client().post(EVALUATE_PATH, json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_client_cannot_send_decision() -> None:
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        }
    )
    body["decision"] = "ALLOW"
    response = _client().post(EVALUATE_PATH, json=body)
    assert response.status_code == 422


def test_deterministic_same_input_same_decision_and_reasons() -> None:
    ref = _make_intake_reference()
    body = _evaluate_body(
        context={
            "context_complete": False,
            "downstream_dependency_count": 5,
            "protected_asset": False,
        },
        intake_reference=ref,
    )
    first = _client().post(EVALUATE_PATH, json=body).json()["data"]
    second = _client().post(EVALUATE_PATH, json=copy.deepcopy(body)).json()["data"]

    assert first["decision"] == second["decision"]
    assert first["reasons"] == second["reasons"]
    assert first["scope"] == second["scope"]
    assert first["evaluation_id"] != second["evaluation_id"]
    assert first["evaluated_content_fingerprint"] == second[
        "evaluated_content_fingerprint"
    ]


def test_meta_honest_about_context_intake_and_fingerprint() -> None:
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        }
    )
    meta = _client().post(EVALUATE_PATH, json=body).json()["meta"]
    assert meta == {
        "operation": "deterministic_risk_evaluation",
        "phase": "F5.2",
        "policy_version": "1.0",
        "context_origin": "caller_provided",
        "context_trust": "unverified",
        "intake_reference_origin": "caller_provided",
        "intake_reference_trust": "unverified",
        "fingerprint_check": "matched",
        "model_used": False,
        "persistence": "none",
    }
    assert meta["intake_reference_origin"] == "caller_provided"
    assert meta["intake_reference_trust"] == "unverified"
    assert meta["fingerprint_check"] == "matched"


def test_meta_avoids_false_trust_terminology() -> None:
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        }
    )
    response = _client().post(EVALUATE_PATH, json=body)
    assert response.status_code == 200
    raw = response.text.lower()
    for forbidden in (
        "trusted",
        "authentic",
        "verified provenance",
        "tamper-proof",
        "tamper proof",
        "server-issued",
        "immutable",
    ):
        assert forbidden not in raw


def test_caller_provided_uuid_accepted_without_storage_lookup() -> None:
    """Any UUID with a fingerprint-consistent payload is accepted.

    Server does not claim the intake_id was found in a registry.
    """
    result = process_change_intake(ChangeIntakeRequest.model_validate(INTAKE_PAYLOAD))
    # Use a different valid UUID than the one process_change_intake generated.
    synthetic_id = str(uuid.uuid4())
    assert synthetic_id != str(result.intake_id)
    ref = {
        "intake_id": synthetic_id,
        "normalized_change": result.normalized_change,
        "content_fingerprint": result.content_fingerprint,
        "artifact_version": result.artifact_version,
    }
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        },
        intake_reference=ref,
    )
    response = _client().post(EVALUATE_PATH, json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["intake_id"] == synthetic_id
    assert payload["meta"]["intake_reference_trust"] == "unverified"
    assert payload["meta"]["fingerprint_check"] == "matched"
    assert payload["meta"]["persistence"] == "none"
    # No claim that the id was loaded from storage.
    assert "registry" not in response.text.lower()
    assert "found in storage" not in response.text.lower()


def test_service_layer_side_effect_free() -> None:
    ref = _make_intake_reference()
    payload = RiskEvaluateRequest.model_validate(
        {
            "intake_reference": ref,
            "evaluation_context": {
                "context_complete": True,
                "downstream_dependency_count": 0,
                "protected_asset": False,
            },
        }
    )
    a = evaluate_risk(payload)
    b = evaluate_risk(payload)
    assert a.decision == b.decision
    assert [r.model_dump() for r in a.reasons] == [r.model_dump() for r in b.reasons]
    assert a.evaluation_id != b.evaluation_id


def test_invalid_intake_id_rejected() -> None:
    ref = _make_intake_reference()
    ref["intake_id"] = "not-a-uuid"
    body = _evaluate_body(
        context={
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        },
        intake_reference=ref,
    )
    response = _client().post(EVALUATE_PATH, json=body)
    assert response.status_code == 422


def test_malformed_json_rejected() -> None:
    response = _client().post(
        EVALUATE_PATH,
        content=b"{not-json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["status"] == "error"


def test_regression_intake_health_ready() -> None:
    client = _client()
    intake = client.post(INTAKE_PATH, json=INTAKE_PAYLOAD)
    assert intake.status_code == 201
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
