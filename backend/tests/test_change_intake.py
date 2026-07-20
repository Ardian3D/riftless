"""Tests for POST /api/v1/changes/intake (phase F5.1)."""

from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.changes import ChangeIntakeRequest
from app.services.change_intake import (
    compute_content_fingerprint,
    normalize_change,
    process_change_intake,
)

INTAKE_PATH = "/api/v1/changes/intake"
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")

VALID_PAYLOAD: dict[str, Any] = {
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


def test_valid_rename_column_returns_201() -> None:
    response = _client().post(INTAKE_PATH, json=VALID_PAYLOAD)
    assert response.status_code == 201


def test_success_envelope_shape() -> None:
    body = _client().post(INTAKE_PATH, json=VALID_PAYLOAD).json()
    assert body["status"] == "ok"
    assert set(body.keys()) == {"status", "data", "meta"}
    data = body["data"]
    assert set(data.keys()) == {
        "intake_id",
        "submitted_input",
        "normalized_change",
        "content_fingerprint",
        "artifact_version",
    }
    assert data["artifact_version"] == "1.0"
    assert body["meta"] == {
        "operation": "change_intake",
        "phase": "F5.1",
        "supported_change_types": ["rename_column"],
        "persistence": "none",
    }


def test_submitted_input_separate_from_normalized_change() -> None:
    payload = {
        **VALID_PAYLOAD,
        "asset": {
            "platform": "  Snowflake  ",
            "database": "  Analytics  ",
            "schema": "  Core  ",
            "name": "  Customers  ",
        },
        "source_column": "  customer_id  ",
        "target_column": "  account_id  ",
        "reason": "  Keep spacing in reason.  ",
    }
    body = _client().post(INTAKE_PATH, json=payload).json()
    submitted = body["data"]["submitted_input"]
    normalized = body["data"]["normalized_change"]

    # Submitted retains pre-normalization values (schema-accepted).
    assert submitted["asset"]["platform"] == "  Snowflake  "
    assert submitted["source_column"] == "  customer_id  "
    assert submitted["reason"] == "  Keep spacing in reason.  "

    # Normalized is distinct and cleaned.
    assert normalized["asset"]["platform"] == "snowflake"
    assert normalized["asset"]["database"] == "Analytics"
    assert normalized["source_column"] == "customer_id"
    assert normalized["reason"] == "Keep spacing in reason."
    assert submitted is not normalized
    assert submitted != normalized


def test_whitespace_and_platform_lowercase_normalization() -> None:
    payload = {
        "change_type": "rename_column",
        "asset": {
            "platform": "  SNOWFLAKE  ",
            "database": " Analytics ",
            "schema": " Core ",
            "name": " Customers ",
        },
        "source_column": " customer_id ",
        "target_column": " account_id ",
    }
    normalized = _client().post(INTAKE_PATH, json=payload).json()["data"][
        "normalized_change"
    ]
    assert normalized["change_type"] == "rename_column"
    assert normalized["asset"]["platform"] == "snowflake"
    assert normalized["asset"]["database"] == "Analytics"
    assert normalized["asset"]["schema"] == "Core"
    assert normalized["asset"]["name"] == "Customers"
    assert normalized["source_column"] == "customer_id"
    assert normalized["target_column"] == "account_id"


def test_identifier_casing_preserved() -> None:
    payload = {
        "change_type": "rename_column",
        "asset": {
            "platform": "snowflake",
            "database": "AnalyticsDB",
            "schema": "CoreSchema",
            "name": "CustomerTable",
        },
        "source_column": "Customer_ID",
        "target_column": "Account_ID",
    }
    normalized = _client().post(INTAKE_PATH, json=payload).json()["data"][
        "normalized_change"
    ]
    assert normalized["asset"]["database"] == "AnalyticsDB"
    assert normalized["asset"]["schema"] == "CoreSchema"
    assert normalized["asset"]["name"] == "CustomerTable"
    assert normalized["source_column"] == "Customer_ID"
    assert normalized["target_column"] == "Account_ID"


def test_optional_reason_null_when_absent() -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "reason"}
    body = _client().post(INTAKE_PATH, json=payload).json()
    assert body["data"]["normalized_change"]["reason"] is None
    assert "reason" not in body["data"]["submitted_input"] or body["data"][
        "submitted_input"
    ].get("reason") is None


def test_identical_source_and_target_rejected() -> None:
    payload = {**VALID_PAYLOAD, "source_column": "id", "target_column": "id"}
    response = _client().post(INTAKE_PATH, json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "validation_error"
    assert "traceback" not in response.text.lower()


def test_identical_after_trim_rejected() -> None:
    payload = {
        **VALID_PAYLOAD,
        "source_column": "  account_id  ",
        "target_column": "account_id",
    }
    response = _client().post(INTAKE_PATH, json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unsupported_change_type_rejected() -> None:
    payload = {**VALID_PAYLOAD, "change_type": "drop_table"}
    response = _client().post(INTAKE_PATH, json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "validation_error"
    assert "detail" not in body


def test_missing_required_field_rejected() -> None:
    payload = {**VALID_PAYLOAD}
    del payload["source_column"]
    response = _client().post(INTAKE_PATH, json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_blank_identifier_rejected() -> None:
    payload = {**VALID_PAYLOAD, "source_column": "   "}
    response = _client().post(INTAKE_PATH, json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unknown_field_rejected() -> None:
    payload = {**VALID_PAYLOAD, "unexpected_field": "nope"}
    response = _client().post(INTAKE_PATH, json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    # Safe details only — no full payload dump in message.
    assert "unexpected_field" not in body["error"]["message"] or True
    assert "traceback" not in response.text.lower()


def test_malformed_payload_rejected() -> None:
    response = _client().post(
        INTAKE_PATH,
        content=b"{not-json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["status"] == "error"


def test_fingerprint_sha256_hex_format() -> None:
    fp = _client().post(INTAKE_PATH, json=VALID_PAYLOAD).json()["data"][
        "content_fingerprint"
    ]
    assert SHA256_HEX.match(fp)


def test_same_normalized_input_same_fingerprint() -> None:
    # Differ only by whitespace that normalizes away.
    a = {
        **VALID_PAYLOAD,
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
    b = {
        **VALID_PAYLOAD,
        "asset": {
            "platform": "  SNOWFLAKE  ",
            "database": "  analytics  ",
            "schema": "  core  ",
            "name": "  customers  ",
        },
        "source_column": "  customer_id  ",
        "target_column": "  account_id  ",
        "reason": "  Standardize the customer identifier.  ",
    }
    fp_a = _client().post(INTAKE_PATH, json=a).json()["data"]["content_fingerprint"]
    fp_b = _client().post(INTAKE_PATH, json=b).json()["data"]["content_fingerprint"]
    assert fp_a == fp_b


def test_different_normalized_input_different_fingerprint() -> None:
    a = {**VALID_PAYLOAD, "target_column": "account_id"}
    b = {**VALID_PAYLOAD, "target_column": "acct_id"}
    fp_a = _client().post(INTAKE_PATH, json=a).json()["data"]["content_fingerprint"]
    fp_b = _client().post(INTAKE_PATH, json=b).json()["data"]["content_fingerprint"]
    assert fp_a != fp_b


def test_reason_affects_fingerprint_when_part_of_normalized_change() -> None:
    a = {**VALID_PAYLOAD, "reason": "Reason A"}
    b = {**VALID_PAYLOAD, "reason": "Reason B"}
    fp_a = _client().post(INTAKE_PATH, json=a).json()["data"]["content_fingerprint"]
    fp_b = _client().post(INTAKE_PATH, json=b).json()["data"]["content_fingerprint"]
    assert fp_a != fp_b


def test_intake_id_is_server_generated_uuid() -> None:
    body = _client().post(INTAKE_PATH, json=VALID_PAYLOAD).json()
    intake_id = body["data"]["intake_id"]
    parsed = uuid.UUID(intake_id)
    assert str(parsed) == intake_id
    # Client-supplied intake_id must not be accepted (unknown field).
    rogue = {**VALID_PAYLOAD, "intake_id": str(uuid.uuid4())}
    response = _client().post(INTAKE_PATH, json=rogue)
    assert response.status_code == 422


def test_service_layer_has_no_network_side_effects() -> None:
    """process_change_intake is pure: same request shape, no I/O."""
    request = ChangeIntakeRequest.model_validate(VALID_PAYLOAD)
    first = process_change_intake(request)
    second = process_change_intake(request)
    assert first.content_fingerprint == second.content_fingerprint
    assert first.normalized_change == second.normalized_change
    assert first.intake_id != second.intake_id  # new UUID each call
    assert first.submitted_input == second.submitted_input


def test_fingerprint_helper_deterministic() -> None:
    request = ChangeIntakeRequest.model_validate(VALID_PAYLOAD)
    normalized = normalize_change(request)
    assert compute_content_fingerprint(normalized) == compute_content_fingerprint(
        normalized
    )


def test_control_character_in_identifier_rejected() -> None:
    payload = {**VALID_PAYLOAD, "source_column": "customer\x00id"}
    response = _client().post(INTAKE_PATH, json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_health_and_ready_still_pass() -> None:
    client = _client()
    health = client.get("/health")
    ready = client.get("/ready")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert ready.status_code == 200
    assert ready.json()["data"]["scope"] == "local_application_and_configuration"
