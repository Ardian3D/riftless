"""F7.1 — Advisory contract foundation tests.

Contract-only: no DeepSeek, network, env secrets, endpoints, or persistence.
"""

from __future__ import annotations

import copy
import os
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.advisory import (
    ADVISORY_ARTIFACT_VERSION,
    ADVISORY_AUTHORITY,
    ADVISORY_PROVIDER_NAME,
    ADVISORY_SCOPE,
    REDACTION_EXCLUDED_CATEGORIES,
    AdvisoryArtifact,
    AdvisoryContent,
    AdvisoryContextPack,
    AdvisoryExecutionStatus,
    AdvisoryStatusDetail,
    AdvisoryChangeSummary,
    AdvisoryRiskSummary,
    AdvisoryValidationSummary,
    AdvisoryValidationCheckSummary,
    AdvisoryTrustSummary,
    AdvisoryRedactionSummary,
)
from app.services.advisory_artifacts import (
    build_completed_advisory_artifact,
    build_noncompleted_advisory_artifact,
)
from app.utils.advisory_fingerprint import fingerprint_advisory_context

# Fixed 64-char lowercase hex fingerprints for tests (not real digests of fixtures).
FP_A = "a" * 64
FP_B = "b" * 64
FP_C = "c" * 64


def _valid_content(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "summary": "A concise advisory overview for human reviewers.",
        "observations": ["Risk decision and validation remain independent."],
        "review_questions": ["Has a human reviewed the validation artifact?"],
        "limitations": [
            "This advisory does not authorize deployment.",
            "This advisory does not change deterministic risk.",
        ],
    }
    data.update(overrides)
    return data


def _valid_status_detail(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "code": "provider_unavailable",
        "message": "The advisory provider was not available.",
    }
    data.update(overrides)
    return data


def _valid_redaction(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "applied": True,
        "version": "1.0",
        "excluded_categories": list(REDACTION_EXCLUDED_CATEGORIES),
    }
    data.update(overrides)
    return data


def _valid_trust(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "subject_origin": "riftless_runtime",
        "subject_scope": "current_request_only",
        "subject_persisted": False,
        "input_origin": "caller_provided",
        "input_trust": "unverified",
        "provenance_verified": False,
    }
    data.update(overrides)
    return data


def _valid_validation_present(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "requested": True,
        "artifact_present": True,
        "execution_status": "completed",
        "outcome": "pass",
        "checks": [
            {
                "check_kind": "sql_parse",
                "required": True,
                "execution_status": "completed",
                "outcome": "pass",
                "evidence_codes": ["sql_parse_succeeded"],
            }
        ],
    }
    data.update(overrides)
    return data


def _valid_context(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "subject_fingerprint": FP_A,
        "change": {
            "change_type": "rename_column",
            "asset_platform": "snowflake",
            "asset_alias": "asset_1",
            "source_column_alias": "column_1",
            "target_column_alias": "column_2",
            "reason_present": False,
        },
        "risk": {
            "decision": "ALLOW",
            "reason_codes": [],
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        },
        "validation": _valid_validation_present(),
        "trust": _valid_trust(),
        "redaction": _valid_redaction(),
        "context_pack_version": "1.0",
    }
    data.update(overrides)
    return data


def _completed_artifact_payload(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "advisory_id": str(uuid.uuid4()),
        "subject_fingerprint": FP_A,
        "context_fingerprint": FP_B,
        "scope": "redacted_context_only",
        "execution_status": "completed",
        "content": _valid_content(),
        "status_detail": None,
        "provider_name": "deepseek",
        "model_name": "server-selected-model",
        "authority": "advisory_only",
        "risk_effect": "none",
        "validation_effect": "none",
        "deployment_authorized": False,
        "persistence": "none",
        "retrieval_available": False,
        "artifact_version": "1.0",
    }
    data.update(overrides)
    return data


# ---- AdvisoryContent ---------------------------------------------------------


def test_valid_content_accepted() -> None:
    content = AdvisoryContent.model_validate(_valid_content())
    assert content.summary.startswith("A concise")
    assert len(content.limitations) >= 1


def test_blank_summary_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContent.model_validate(_valid_content(summary="   "))


def test_summary_too_long_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContent.model_validate(_valid_content(summary="x" * 1201))


def test_duplicate_observation_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContent.model_validate(
            _valid_content(observations=["same", "same"])
        )


def test_duplicate_review_question_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContent.model_validate(
            _valid_content(review_questions=["Q?", "Q?"])
        )


def test_empty_limitations_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContent.model_validate(_valid_content(limitations=[]))


def test_duplicate_limitation_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContent.model_validate(
            _valid_content(limitations=["lim", "lim"])
        )


def test_unknown_content_field_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContent.model_validate(
            _valid_content(extra_field="nope")
        )


def test_decision_field_on_content_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContent.model_validate(_valid_content(decision="ALLOW"))


def test_remediation_sql_field_on_content_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContent.model_validate(
            _valid_content(remediation_sql="ALTER TABLE x")
        )


# ---- Status detail -----------------------------------------------------------


def test_valid_status_detail_accepted() -> None:
    detail = AdvisoryStatusDetail.model_validate(_valid_status_detail())
    assert detail.code == "provider_unavailable"


def test_invalid_status_code_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryStatusDetail.model_validate(
            _valid_status_detail(code="Not-Valid")
        )


def test_blank_status_message_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryStatusDetail.model_validate(
            _valid_status_detail(message="  ")
        )


def test_arbitrary_details_field_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryStatusDetail.model_validate(
            _valid_status_detail(details={"x": 1})
        )


def test_exception_detail_field_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryStatusDetail.model_validate(
            _valid_status_detail(exception="Traceback...")
        )


# ---- Artifact states ---------------------------------------------------------


def test_completed_artifact_valid() -> None:
    artifact = AdvisoryArtifact.model_validate(_completed_artifact_payload())
    assert artifact.execution_status == "completed"
    assert artifact.content is not None
    assert artifact.authority == ADVISORY_AUTHORITY
    assert artifact.deployment_authorized is False


def test_completed_without_content_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryArtifact.model_validate(
            _completed_artifact_payload(content=None)
        )


def test_completed_with_status_detail_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryArtifact.model_validate(
            _completed_artifact_payload(status_detail=_valid_status_detail())
        )


def test_completed_without_model_name_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryArtifact.model_validate(
            _completed_artifact_payload(model_name=None)
        )


def test_error_with_content_rejected() -> None:
    payload = _completed_artifact_payload(
        execution_status="error",
        content=_valid_content(),
        status_detail=_valid_status_detail(),
        model_name=None,
    )
    with pytest.raises(ValidationError):
        AdvisoryArtifact.model_validate(payload)


def test_error_without_status_detail_rejected() -> None:
    payload = _completed_artifact_payload(
        execution_status="error",
        content=None,
        status_detail=None,
        model_name=None,
    )
    with pytest.raises(ValidationError):
        AdvisoryArtifact.model_validate(payload)


def test_unavailable_valid() -> None:
    payload = _completed_artifact_payload(
        execution_status="unavailable",
        content=None,
        status_detail=_valid_status_detail(),
        model_name=None,
    )
    artifact = AdvisoryArtifact.model_validate(payload)
    assert artifact.execution_status == "unavailable"
    assert artifact.content is None


def test_skipped_valid() -> None:
    payload = _completed_artifact_payload(
        execution_status="skipped",
        content=None,
        status_detail={
            "code": "advisory_skipped",
            "message": "Advisory was not requested for this run.",
        },
        model_name=None,
    )
    artifact = AdvisoryArtifact.model_validate(payload)
    assert artifact.execution_status == "skipped"


def test_noncompleted_without_status_detail_rejected() -> None:
    payload = _completed_artifact_payload(
        execution_status="skipped",
        content=None,
        status_detail=None,
        model_name=None,
    )
    with pytest.raises(ValidationError):
        AdvisoryArtifact.model_validate(payload)


def test_invalid_subject_fingerprint_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryArtifact.model_validate(
            _completed_artifact_payload(subject_fingerprint="not-a-fingerprint")
        )


def test_uppercase_fingerprint_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryArtifact.model_validate(
            _completed_artifact_payload(subject_fingerprint="A" * 64)
        )


def test_invalid_context_fingerprint_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryArtifact.model_validate(
            _completed_artifact_payload(context_fingerprint="zz")
        )


def test_artifact_constants_cannot_override_authority() -> None:
    with pytest.raises(ValidationError):
        AdvisoryArtifact.model_validate(
            _completed_artifact_payload(authority="binding")
        )


def test_decision_field_on_artifact_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryArtifact.model_validate(
            _completed_artifact_payload(decision="ALLOW")
        )


def test_deployment_authorized_true_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryArtifact.model_validate(
            _completed_artifact_payload(deployment_authorized=True)
        )


# ---- Context pack ------------------------------------------------------------


def test_valid_context_pack_accepted() -> None:
    pack = AdvisoryContextPack.model_validate(_valid_context())
    assert pack.context_pack_version == "1.0"
    assert pack.redaction.applied is True
    assert pack.redaction.excluded_categories == list(REDACTION_EXCLUDED_CATEGORIES)


def test_raw_sql_field_on_context_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContextPack.model_validate(_valid_context(raw_sql="select 1"))


def test_fixture_field_on_context_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContextPack.model_validate(
            _valid_context(fixture={"rows": [["x"]]})
        )


def test_raw_asset_identifier_field_rejected() -> None:
    change = _valid_context()["change"].copy()
    change["source_column"] = "customer_id"
    with pytest.raises(ValidationError):
        AdvisoryContextPack.model_validate(_valid_context(change=change))


def test_invalid_alias_rejected() -> None:
    change = _valid_context()["change"].copy()
    change["asset_alias"] = "Asset-1"
    with pytest.raises(ValidationError):
        AdvisoryContextPack.model_validate(_valid_context(change=change))


def test_duplicate_risk_reason_code_rejected() -> None:
    risk = _valid_context()["risk"].copy()
    risk["reason_codes"] = ["protected_asset", "protected_asset"]
    with pytest.raises(ValidationError):
        AdvisoryContextPack.model_validate(_valid_context(risk=risk))


def test_validation_requested_false_invariant() -> None:
    pack = AdvisoryContextPack.model_validate(
        _valid_context(
            validation={
                "requested": False,
                "artifact_present": False,
                "execution_status": None,
                "outcome": None,
                "checks": [],
            }
        )
    )
    assert pack.validation.requested is False
    assert pack.validation.checks == []


def test_validation_requested_true_artifact_present_invariant() -> None:
    pack = AdvisoryContextPack.model_validate(_valid_context())
    assert pack.validation.requested is True
    assert pack.validation.artifact_present is True
    assert len(pack.validation.checks) >= 1


def test_validation_requested_true_empty_checks_mirrors_f6() -> None:
    """F6 empty ValidationArtifact is not_run + inconclusive with checks=[].

    AdvisoryValidationSummary must accept that projection without inventing
    synthetic checks or outcomes.
    """
    summary = AdvisoryValidationSummary.model_validate(
        {
            "requested": True,
            "artifact_present": True,
            "execution_status": "not_run",
            "outcome": "inconclusive",
            "checks": [],
        }
    )
    assert summary.requested is True
    assert summary.artifact_present is True
    assert summary.execution_status == "not_run"
    assert summary.outcome == "inconclusive"
    assert summary.checks == []

    pack = AdvisoryContextPack.model_validate(
        _valid_context(
            validation={
                "requested": True,
                "artifact_present": True,
                "execution_status": "not_run",
                "outcome": "inconclusive",
                "checks": [],
            }
        )
    )
    assert pack.validation.checks == []
    assert pack.validation.outcome == "inconclusive"


def test_validation_requested_true_null_outcome_rejected() -> None:
    """F6 ValidationArtifact.outcome is always pass|fail|inconclusive (never null)."""
    with pytest.raises(ValidationError):
        AdvisoryValidationSummary.model_validate(
            {
                "requested": True,
                "artifact_present": True,
                "execution_status": "not_run",
                "outcome": None,
                "checks": [],
            }
        )


def test_validation_check_null_outcome_for_noncompleted() -> None:
    """Per-check outcome may be null when F6 check is error/unavailable/skipped."""
    for status in ("error", "unavailable", "skipped"):
        check = AdvisoryValidationCheckSummary.model_validate(
            {
                "check_kind": "sql_parse",
                "required": True,
                "execution_status": status,
                "outcome": None,
                "evidence_codes": ["engine_error"],
            }
        )
        assert check.outcome is None
        assert check.execution_status == status


def test_validation_missing_artifact_when_requested_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContextPack.model_validate(
            _valid_context(
                validation={
                    "requested": True,
                    "artifact_present": False,
                    "execution_status": None,
                    "outcome": None,
                    "checks": [],
                }
            )
        )


def test_validation_evidence_details_rejected() -> None:
    checks = [
        {
            "check_kind": "sql_parse",
            "required": True,
            "execution_status": "completed",
            "outcome": "pass",
            "evidence_codes": ["ok"],
            "evidence_details": {"raw": "nope"},
        }
    ]
    with pytest.raises(ValidationError):
        AdvisoryContextPack.model_validate(
            _valid_context(validation=_valid_validation_present(checks=checks))
        )


def test_trust_persisted_true_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContextPack.model_validate(
            _valid_context(trust=_valid_trust(subject_persisted=True))
        )


def test_provenance_verified_true_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContextPack.model_validate(
            _valid_context(trust=_valid_trust(provenance_verified=True))
        )


def test_redaction_applied_false_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContextPack.model_validate(
            _valid_context(redaction=_valid_redaction(applied=False))
        )


def test_missing_excluded_category_rejected() -> None:
    incomplete = list(REDACTION_EXCLUDED_CATEGORIES)[:-1]
    with pytest.raises(ValidationError):
        AdvisoryContextPack.model_validate(
            _valid_context(redaction=_valid_redaction(excluded_categories=incomplete))
        )


def test_duplicate_excluded_category_rejected() -> None:
    cats = list(REDACTION_EXCLUDED_CATEGORIES) + ["raw_sql"]
    with pytest.raises(ValidationError):
        AdvisoryContextPack.model_validate(
            _valid_context(redaction=_valid_redaction(excluded_categories=cats))
        )


def test_unknown_context_field_rejected() -> None:
    with pytest.raises(ValidationError):
        AdvisoryContextPack.model_validate(_valid_context(blob="x"))


# ---- Fingerprint -------------------------------------------------------------


def test_same_input_same_fingerprint() -> None:
    pack1 = AdvisoryContextPack.model_validate(_valid_context())
    pack2 = AdvisoryContextPack.model_validate(_valid_context())
    assert fingerprint_advisory_context(pack1) == fingerprint_advisory_context(pack2)


def test_alias_change_changes_fingerprint() -> None:
    pack_a = AdvisoryContextPack.model_validate(_valid_context())
    change = _valid_context()["change"].copy()
    change["asset_alias"] = "asset_2"
    pack_b = AdvisoryContextPack.model_validate(_valid_context(change=change))
    assert fingerprint_advisory_context(pack_a) != fingerprint_advisory_context(pack_b)


def test_risk_decision_change_changes_fingerprint() -> None:
    pack_a = AdvisoryContextPack.model_validate(_valid_context())
    risk = _valid_context()["risk"].copy()
    risk["decision"] = "BLOCK"
    risk["reason_codes"] = ["protected_asset"]
    pack_b = AdvisoryContextPack.model_validate(_valid_context(risk=risk))
    assert fingerprint_advisory_context(pack_a) != fingerprint_advisory_context(pack_b)


def test_validation_summary_change_changes_fingerprint() -> None:
    pack_a = AdvisoryContextPack.model_validate(_valid_context())
    val = _valid_validation_present(outcome="fail")
    pack_b = AdvisoryContextPack.model_validate(_valid_context(validation=val))
    assert fingerprint_advisory_context(pack_a) != fingerprint_advisory_context(pack_b)


def test_trust_summary_change_changes_fingerprint() -> None:
    pack_a = AdvisoryContextPack.model_validate(_valid_context())
    trust = _valid_trust(subject_origin="caller_provided")
    pack_b = AdvisoryContextPack.model_validate(_valid_context(trust=trust))
    assert fingerprint_advisory_context(pack_a) != fingerprint_advisory_context(pack_b)


def test_fingerprint_is_64_lowercase_hex() -> None:
    pack = AdvisoryContextPack.model_validate(_valid_context())
    fp = fingerprint_advisory_context(pack)
    assert len(fp) == 64
    assert fp == fp.lower()
    assert all(c in "0123456789abcdef" for c in fp)


def test_fingerprint_does_not_mutate_context() -> None:
    pack = AdvisoryContextPack.model_validate(_valid_context())
    before = pack.model_dump(mode="json")
    fingerprint_advisory_context(pack)
    after = pack.model_dump(mode="json")
    assert before == after


# ---- Builders ----------------------------------------------------------------


def test_completed_builder_valid() -> None:
    context = AdvisoryContextPack.model_validate(_valid_context())
    content = AdvisoryContent.model_validate(_valid_content())
    artifact = build_completed_advisory_artifact(
        context=context,
        content=content,
        model_name="server-selected-model",
    )
    assert artifact.execution_status == "completed"
    assert artifact.content is not None
    assert artifact.provider_name == ADVISORY_PROVIDER_NAME
    assert artifact.scope == ADVISORY_SCOPE
    assert artifact.artifact_version == ADVISORY_ARTIFACT_VERSION


def test_completed_builder_uses_subject_fingerprint() -> None:
    context = AdvisoryContextPack.model_validate(
        _valid_context(subject_fingerprint=FP_C)
    )
    content = AdvisoryContent.model_validate(_valid_content())
    artifact = build_completed_advisory_artifact(
        context=context,
        content=content,
        model_name="model-x",
    )
    assert artifact.subject_fingerprint == FP_C


def test_completed_builder_computes_context_fingerprint() -> None:
    context = AdvisoryContextPack.model_validate(_valid_context())
    content = AdvisoryContent.model_validate(_valid_content())
    expected = fingerprint_advisory_context(context)
    artifact = build_completed_advisory_artifact(
        context=context,
        content=content,
        model_name="model-x",
    )
    assert artifact.context_fingerprint == expected


def test_noncompleted_error_builder_valid() -> None:
    context = AdvisoryContextPack.model_validate(_valid_context())
    detail = AdvisoryStatusDetail.model_validate(
        _valid_status_detail(code="provider_error", message="Provider error.")
    )
    artifact = build_noncompleted_advisory_artifact(
        context=context,
        execution_status=AdvisoryExecutionStatus.ERROR,
        status_detail=detail,
    )
    assert artifact.execution_status == "error"
    assert artifact.content is None
    assert artifact.status_detail is not None


def test_noncompleted_unavailable_builder_valid() -> None:
    context = AdvisoryContextPack.model_validate(_valid_context())
    detail = AdvisoryStatusDetail.model_validate(_valid_status_detail())
    artifact = build_noncompleted_advisory_artifact(
        context=context,
        execution_status="unavailable",
        status_detail=detail,
    )
    assert artifact.execution_status == "unavailable"


def test_noncompleted_skipped_builder_valid() -> None:
    context = AdvisoryContextPack.model_validate(_valid_context())
    detail = AdvisoryStatusDetail.model_validate(
        {"code": "advisory_skipped", "message": "Skipped by server policy."}
    )
    artifact = build_noncompleted_advisory_artifact(
        context=context,
        execution_status=AdvisoryExecutionStatus.SKIPPED,
        status_detail=detail,
    )
    assert artifact.execution_status == "skipped"


def test_noncompleted_builder_rejects_completed() -> None:
    context = AdvisoryContextPack.model_validate(_valid_context())
    detail = AdvisoryStatusDetail.model_validate(_valid_status_detail())
    with pytest.raises(ValueError, match="rejects completed"):
        build_noncompleted_advisory_artifact(
            context=context,
            execution_status=AdvisoryExecutionStatus.COMPLETED,
            status_detail=detail,
        )


def test_builders_do_not_read_environment() -> None:
    context = AdvisoryContextPack.model_validate(_valid_context())
    content = AdvisoryContent.model_validate(_valid_content())
    detail = AdvisoryStatusDetail.model_validate(_valid_status_detail())

    def _deny_getenv(*_a: Any, **_k: Any) -> str:
        raise AssertionError("builders must not read environment")

    with patch.dict(os.environ, {}, clear=False):
        with patch("os.getenv", side_effect=_deny_getenv):
            with patch("os.environ.get", side_effect=_deny_getenv):
                build_completed_advisory_artifact(
                    context=context,
                    content=content,
                    model_name="m",
                )
                build_noncompleted_advisory_artifact(
                    context=context,
                    execution_status="error",
                    status_detail=detail,
                )


def test_builders_do_not_perform_network_call() -> None:
    context = AdvisoryContextPack.model_validate(_valid_context())
    content = AdvisoryContent.model_validate(_valid_content())

    def _deny_urlopen(*_a: Any, **_k: Any) -> None:
        raise AssertionError("network forbidden")

    with patch("urllib.request.urlopen", side_effect=_deny_urlopen):
        artifact = build_completed_advisory_artifact(
            context=context,
            content=content,
            model_name="m",
        )
    assert artifact.content is not None


def test_builders_do_not_write_files(tmp_path: Path) -> None:
    context = AdvisoryContextPack.model_validate(_valid_context())
    content = AdvisoryContent.model_validate(_valid_content())
    before = {p.name for p in tmp_path.iterdir()} if tmp_path.exists() else set()
    build_completed_advisory_artifact(
        context=context,
        content=content,
        model_name="m",
    )
    after = {p.name for p in tmp_path.iterdir()} if tmp_path.exists() else set()
    assert before == after


def test_semantic_artifact_deterministic_except_advisory_id() -> None:
    context = AdvisoryContextPack.model_validate(_valid_context())
    content = AdvisoryContent.model_validate(_valid_content())
    a1 = build_completed_advisory_artifact(
        context=context, content=content, model_name="m"
    )
    a2 = build_completed_advisory_artifact(
        context=context, content=content, model_name="m"
    )
    d1 = a1.model_dump(mode="json")
    d2 = a2.model_dump(mode="json")
    assert d1["advisory_id"] != d2["advisory_id"]
    d1.pop("advisory_id")
    d2.pop("advisory_id")
    assert d1 == d2


def test_builders_do_not_mutate_inputs() -> None:
    context = AdvisoryContextPack.model_validate(_valid_context())
    content = AdvisoryContent.model_validate(_valid_content())
    ctx_before = copy.deepcopy(context.model_dump(mode="json"))
    content_before = copy.deepcopy(content.model_dump(mode="json"))
    build_completed_advisory_artifact(
        context=context, content=content, model_name="m"
    )
    assert context.model_dump(mode="json") == ctx_before
    assert content.model_dump(mode="json") == content_before


# ---- Regression --------------------------------------------------------------


def test_openapi_still_six_production_routes() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    paths = sorted(spec["paths"].keys())
    assert paths == [
        "/api/v1/changes/intake",
        "/api/v1/risk/evaluate",
        "/api/v1/runs/analyze",
        "/api/v1/validations/execute",
        "/health",
        "/ready",
    ]
    assert "advisory" not in " ".join(paths).lower()


def test_content_trims_summary_whitespace() -> None:
    content = AdvisoryContent.model_validate(
        _valid_content(summary="  padded summary  ")
    )
    assert content.summary == "padded summary"


def test_redaction_canonicalizes_category_order() -> None:
    reversed_cats = list(reversed(REDACTION_EXCLUDED_CATEGORIES))
    redaction = AdvisoryRedactionSummary.model_validate(
        _valid_redaction(excluded_categories=reversed_cats)
    )
    assert redaction.excluded_categories == list(REDACTION_EXCLUDED_CATEGORIES)


def test_execution_status_enum_values() -> None:
    assert {s.value for s in AdvisoryExecutionStatus} == {
        "completed",
        "error",
        "unavailable",
        "skipped",
    }
    assert "pass" not in {s.value for s in AdvisoryExecutionStatus}
    assert "allow" not in {s.value for s in AdvisoryExecutionStatus}
