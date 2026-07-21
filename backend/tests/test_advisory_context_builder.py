"""F7.2 — Server-controlled redacted AdvisoryContextPack builder tests.

No DeepSeek, network, env secrets, endpoints, or persistence.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.advisory import REDACTION_EXCLUDED_CATEGORIES
from app.schemas.changes import ChangeIntakeData, ChangeIntakeRequest
from app.schemas.risk import (
    EvaluationContext,
    IntakeReference,
    RiskEvaluateRequest,
    RiskEvaluationData,
    RiskReason,
)
from app.schemas.validation import (
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    OverallExecutionStatus,
    ValidationArtifact,
    ValidationCheckResult,
    ValidationEvidence,
)
from app.services.advisory_context_builder import (
    AdvisoryContextBuildError,
    build_advisory_context_pack,
)
from app.services.change_intake import process_change_intake
from app.services.risk_engine import evaluate_risk
from app.services.validation_engine import build_validation_artifact
from app.utils.advisory_fingerprint import fingerprint_advisory_context
from app.utils.fingerprint import fingerprint_payload

# ---- Canary values (must never appear in serialized context pack) ------------

CANARY_DB = "CANARY_DB_ACME_ANALYTICS_ZZ9"
CANARY_SCHEMA = "CANARY_SCHEMA_CORE_ZZ9"
CANARY_ASSET = "CANARY_TABLE_CUSTOMERS_ZZ9"
CANARY_SOURCE = "CANARY_COL_CUSTOMER_ID_ZZ9"
CANARY_TARGET = "CANARY_COL_ACCOUNT_ID_ZZ9"
CANARY_REASON = "CANARY_REASON_TEXT_DO_NOT_LEAK_ZZ9"
CANARY_SQL = "SELECT CANARY_SQL_SECRET FROM nowhere"
CANARY_FIXTURE = "CANARY_FIXTURE_ROW_VALUE_ZZ9"
CANARY_DBT = "CANARY_DBT_STDOUT_LEAK_ZZ9"
CANARY_RISK_MSG = "CANARY_RISK_MESSAGE_DO_NOT_LEAK_ZZ9"
CANARY_EVIDENCE_MSG = "CANARY_EVIDENCE_MESSAGE_DO_NOT_LEAK_ZZ9"
CANARY_CHECK_SUMMARY = "CANARY_CHECK_SUMMARY_DO_NOT_LEAK_ZZ9"


def _change_request(**overrides: Any) -> ChangeIntakeRequest:
    data: dict[str, Any] = {
        "change_type": "rename_column",
        "asset": {
            "platform": "snowflake",
            "database": CANARY_DB,
            "schema": CANARY_SCHEMA,
            "name": CANARY_ASSET,
        },
        "source_column": CANARY_SOURCE,
        "target_column": CANARY_TARGET,
        "reason": CANARY_REASON,
    }
    data.update(overrides)
    return ChangeIntakeRequest.model_validate(data)


def _make_intake(**overrides: Any) -> ChangeIntakeData:
    return process_change_intake(_change_request(**overrides))


def _make_risk(
    intake: ChangeIntakeData,
    *,
    context_complete: bool = True,
    downstream_dependency_count: int | None = 0,
    protected_asset: bool = False,
) -> RiskEvaluationData:
    normalized = intake.normalized_change
    ref = IntakeReference(
        intake_id=intake.intake_id,
        normalized_change=normalized,
        content_fingerprint=intake.content_fingerprint,
        artifact_version=intake.artifact_version,
    )
    ctx = EvaluationContext(
        context_complete=context_complete,
        downstream_dependency_count=downstream_dependency_count,
        protected_asset=protected_asset,
    )
    return evaluate_risk(
        RiskEvaluateRequest(intake_reference=ref, evaluation_context=ctx)
    )


def _evidence(
    code: str = "sql_parse_succeeded",
    message: str = CANARY_EVIDENCE_MSG,
    details: Any = None,
) -> ValidationEvidence:
    return ValidationEvidence(code=code, message=message, details=details)


def _check(
    *,
    check_kind: CheckKind = CheckKind.SQL_PARSE,
    required: bool = True,
    execution_status: CheckExecutionStatus = CheckExecutionStatus.COMPLETED,
    outcome: CheckOutcome | None = CheckOutcome.PASS,
    evidence: list[ValidationEvidence] | None = None,
    summary: str = CANARY_CHECK_SUMMARY,
    engine_name: str | None = "sqlglot",
    engine_version: str | None = "30.12.0",
) -> ValidationCheckResult:
    if evidence is None:
        evidence = [_evidence()]
    # Non-completed requires outcome null and non-empty evidence.
    return ValidationCheckResult(
        check_id=uuid.uuid4(),
        check_kind=check_kind,
        required=required,
        execution_status=execution_status,
        outcome=outcome,
        scope="canary scope",
        summary=summary,
        evidence=evidence,
        engine_name=engine_name,
        engine_version=engine_version,
    )


def _make_validation(
    subject_fingerprint: str,
    *,
    checks: list[ValidationCheckResult] | None = None,
) -> ValidationArtifact:
    if checks is None:
        checks = [
            _check(
                check_kind=CheckKind.SQL_PARSE,
                evidence=[
                    _evidence(
                        code="sql_parse_succeeded",
                        details={"canary_sql": CANARY_SQL},
                    )
                ],
            ),
            _check(
                check_kind=CheckKind.DUCKDB_EXECUTION,
                evidence=[
                    _evidence(
                        code="rename_applied",
                        details={"fixture_row": CANARY_FIXTURE},
                    )
                ],
            ),
            _check(
                check_kind=CheckKind.DBT_VALIDATION,
                required=False,
                evidence=[
                    _evidence(
                        code="manifest_model_present",
                        details={"dbt_out": CANARY_DBT},
                    )
                ],
            ),
        ]
    return build_validation_artifact(
        subject_fingerprint=subject_fingerprint,
        checks=checks,
    )


def _pack_json(pack: Any) -> str:
    return json.dumps(pack.model_dump(mode="json"), ensure_ascii=False)


def _assert_no_canaries(text: str) -> None:
    for canary in (
        CANARY_DB,
        CANARY_SCHEMA,
        CANARY_ASSET,
        CANARY_SOURCE,
        CANARY_TARGET,
        CANARY_REASON,
        CANARY_SQL,
        CANARY_FIXTURE,
        CANARY_DBT,
        CANARY_RISK_MSG,
        CANARY_EVIDENCE_MSG,
        CANARY_CHECK_SUMMARY,
    ):
        assert canary not in text, f"canary leaked: {canary}"


# ---- Source consistency ------------------------------------------------------


def test_valid_change_risk_without_validation() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.subject_fingerprint == intake.content_fingerprint
    assert pack.validation.requested is False
    assert pack.validation.checks == []


def test_valid_change_risk_with_validation() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert pack.validation.requested is True
    assert pack.validation.artifact_present is True
    assert len(pack.validation.checks) == 3


def test_intake_fingerprint_mismatch_rejected() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    broken = intake.model_copy(
        update={"content_fingerprint": "b" * 64}
    )
    with pytest.raises(AdvisoryContextBuildError) as exc_info:
        build_advisory_context_pack(
            change_intake=broken,
            risk_evaluation=risk,
            validation_requested=False,
            validation_artifact=None,
        )
    assert exc_info.value.code == "intake_fingerprint_mismatch"


def test_calculated_fingerprint_not_in_error() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    computed = fingerprint_payload(
        intake.normalized_change
        if isinstance(intake.normalized_change, dict)
        else {}
    )
    # Force mismatch with a different valid hex fingerprint.
    broken = intake.model_copy(update={"content_fingerprint": "c" * 64})
    with pytest.raises(AdvisoryContextBuildError) as exc_info:
        build_advisory_context_pack(
            change_intake=broken,
            risk_evaluation=risk,
            validation_requested=False,
            validation_artifact=None,
        )
    err = f"{exc_info.value.code} {exc_info.value.message}"
    assert computed not in err
    assert "c" * 64 not in err
    assert intake.content_fingerprint not in err


def test_expected_fingerprint_not_in_error() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    expected = intake.content_fingerprint
    broken = intake.model_copy(update={"content_fingerprint": "d" * 64})
    with pytest.raises(AdvisoryContextBuildError) as exc_info:
        build_advisory_context_pack(
            change_intake=broken,
            risk_evaluation=risk,
            validation_requested=False,
            validation_artifact=None,
        )
    assert expected not in exc_info.value.message
    assert expected not in exc_info.value.code


def test_risk_subject_mismatch_rejected() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    mismatched = risk.model_copy(
        update={"evaluated_content_fingerprint": "e" * 64}
    )
    with pytest.raises(AdvisoryContextBuildError) as exc_info:
        build_advisory_context_pack(
            change_intake=intake,
            risk_evaluation=mismatched,
            validation_requested=False,
            validation_artifact=None,
        )
    assert exc_info.value.code == "risk_subject_mismatch"


def test_validation_not_requested_with_artifact_rejected() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    with pytest.raises(AdvisoryContextBuildError) as exc_info:
        build_advisory_context_pack(
            change_intake=intake,
            risk_evaluation=risk,
            validation_requested=False,
            validation_artifact=validation,
        )
    assert exc_info.value.code == "validation_presence_mismatch"


def test_validation_requested_with_null_artifact_rejected() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    with pytest.raises(AdvisoryContextBuildError) as exc_info:
        build_advisory_context_pack(
            change_intake=intake,
            risk_evaluation=risk,
            validation_requested=True,
            validation_artifact=None,
        )
    assert exc_info.value.code == "validation_presence_mismatch"


def test_validation_subject_mismatch_rejected() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation("f" * 64)
    with pytest.raises(AdvisoryContextBuildError) as exc_info:
        build_advisory_context_pack(
            change_intake=intake,
            risk_evaluation=risk,
            validation_requested=True,
            validation_artifact=validation,
        )
    assert exc_info.value.code == "validation_subject_mismatch"


def test_unsupported_change_type_rejected() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    bad_normalized = dict(intake.normalized_change)
    bad_normalized["change_type"] = "drop_table"
    # Keep fingerprint as-is so we fail on type before or at parse.
    broken = intake.model_copy(update={"normalized_change": bad_normalized})
    with pytest.raises(AdvisoryContextBuildError) as exc_info:
        build_advisory_context_pack(
            change_intake=broken,
            risk_evaluation=risk,
            validation_requested=False,
            validation_artifact=None,
        )
    assert exc_info.value.code == "unsupported_change_type"


def test_mismatch_does_not_return_partial_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    broken = intake.model_copy(update={"content_fingerprint": "a" * 64})
    # Ensure it's actually a mismatch for real content.
    if broken.content_fingerprint == intake.content_fingerprint:
        broken = intake.model_copy(update={"content_fingerprint": "b" * 64})
    result = None
    with pytest.raises(AdvisoryContextBuildError):
        result = build_advisory_context_pack(
            change_intake=broken,
            risk_evaluation=risk,
            validation_requested=False,
            validation_artifact=None,
        )
    assert result is None


# ---- Change redaction --------------------------------------------------------


def test_change_type_preserved() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.change.change_type == "rename_column"


def test_asset_platform_preserved() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.change.asset_platform == "snowflake"


def test_asset_alias_fixed() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.change.asset_alias == "asset_1"


def test_source_column_alias_fixed() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.change.source_column_alias == "column_1"


def test_target_column_alias_fixed() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.change.target_column_alias == "column_2"


def test_reason_present_true_when_reason_set() -> None:
    intake = _make_intake(reason=CANARY_REASON)
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.change.reason_present is True


def test_reason_present_false_when_reason_absent() -> None:
    intake = _make_intake(reason=None)
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.change.reason_present is False


def test_raw_database_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert CANARY_DB not in _pack_json(pack)


def test_raw_schema_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert CANARY_SCHEMA not in _pack_json(pack)


def test_raw_asset_name_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert CANARY_ASSET not in _pack_json(pack)


def test_raw_source_column_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert CANARY_SOURCE not in _pack_json(pack)


def test_raw_target_column_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert CANARY_TARGET not in _pack_json(pack)


def test_reason_text_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert CANARY_REASON not in _pack_json(pack)


def test_no_alias_mapping_field() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    dumped = pack.model_dump(mode="json")
    assert "alias_mapping" not in dumped
    assert "aliases" not in dumped
    assert "identifier_map" not in dumped


def test_raw_identifiers_not_in_exception() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    broken = intake.model_copy(update={"content_fingerprint": "b" * 64})
    with pytest.raises(AdvisoryContextBuildError) as exc_info:
        build_advisory_context_pack(
            change_intake=broken,
            risk_evaluation=risk,
            validation_requested=False,
            validation_artifact=None,
        )
    text = f"{exc_info.value.code}:{exc_info.value.message}"
    _assert_no_canaries(text)


# ---- Risk projection ---------------------------------------------------------


def test_risk_decision_preserved() -> None:
    intake = _make_intake()
    risk = _make_risk(intake, protected_asset=True)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.risk.decision == "BLOCK"
    assert risk.decision == "BLOCK"


def test_reason_codes_order_preserved() -> None:
    intake = _make_intake()
    # incomplete + unknown dep + (not protected)
    risk = _make_risk(
        intake,
        context_complete=False,
        downstream_dependency_count=None,
        protected_asset=False,
    )
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    source_codes = [r.code for r in risk.reasons]
    assert pack.risk.reason_codes == source_codes


def test_duplicate_reason_codes_deduped_first_occurrence() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    # Inject duplicate codes while keeping a valid RiskEvaluationData shape.
    reasons = list(risk.reasons) + [
        RiskReason(
            code=risk.reasons[0].code,
            level=risk.reasons[0].level,
            message=CANARY_RISK_MSG,
            evidence=None,
        )
    ]
    risk_dup = risk.model_copy(update={"reasons": reasons})
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk_dup,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.risk.reason_codes.count(risk.reasons[0].code) == 1
    assert pack.risk.reason_codes[0] == risk.reasons[0].code


def test_context_complete_preserved() -> None:
    intake = _make_intake()
    risk = _make_risk(intake, context_complete=True, downstream_dependency_count=2)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.risk.context_complete is True


def test_downstream_dependency_count_preserved() -> None:
    intake = _make_intake()
    risk = _make_risk(intake, downstream_dependency_count=7)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.risk.downstream_dependency_count == 7


def test_protected_asset_preserved() -> None:
    intake = _make_intake()
    risk = _make_risk(intake, protected_asset=True)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.risk.protected_asset is True


def test_risk_reason_message_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    reasons = [
        RiskReason(
            code="no_risk_condition_detected",
            level="ALLOW",
            message=CANARY_RISK_MSG,
            evidence=None,
        )
    ]
    risk_msg = risk.model_copy(update={"reasons": reasons, "decision": "ALLOW"})
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk_msg,
        validation_requested=False,
        validation_artifact=None,
    )
    assert CANARY_RISK_MSG not in _pack_json(pack)


def test_full_evaluation_context_object_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    dumped = pack.model_dump(mode="json")
    assert "evaluation_context" not in dumped
    assert "evaluation_context" not in dumped.get("risk", {})


def test_invalid_reason_code_fails_safely() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    reasons = [
        RiskReason(
            code="Not-Valid-Code",
            level="ALLOW",
            message=CANARY_RISK_MSG,
            evidence=None,
        )
    ]
    risk_bad = risk.model_copy(update={"reasons": reasons, "decision": "ALLOW"})
    with pytest.raises(AdvisoryContextBuildError) as exc_info:
        build_advisory_context_pack(
            change_intake=intake,
            risk_evaluation=risk_bad,
            validation_requested=False,
            validation_artifact=None,
        )
    assert CANARY_RISK_MSG not in exc_info.value.message
    assert "Not-Valid-Code" not in exc_info.value.message


# ---- Validation projection ---------------------------------------------------


def test_validation_not_requested_exact_empty_summary() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.validation.model_dump(mode="json") == {
        "requested": False,
        "artifact_present": False,
        "execution_status": None,
        "outcome": None,
        "checks": [],
    }


def test_validation_requested_preserves_overall_execution_status() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert pack.validation.execution_status == validation.execution_status


def test_validation_requested_preserves_overall_outcome() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert pack.validation.outcome == validation.outcome


def test_check_order_preserved() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    kinds = [c.check_kind for c in pack.validation.checks]
    source = [
        c.check_kind.value if hasattr(c.check_kind, "value") else c.check_kind
        for c in validation.checks
    ]
    assert kinds == source


def test_check_kind_preserved() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert pack.validation.checks[0].check_kind == "sql_parse"


def test_required_flag_preserved() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert pack.validation.checks[0].required is True
    assert pack.validation.checks[2].required is False


def test_check_execution_status_preserved() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert pack.validation.checks[0].execution_status == "completed"


def test_check_outcome_preserved() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert pack.validation.checks[0].outcome == "pass"


def test_evidence_codes_preserved() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert "sql_parse_succeeded" in pack.validation.checks[0].evidence_codes


def test_duplicate_evidence_codes_deduped() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    checks = [
        _check(
            evidence=[
                _evidence(code="sql_parse_succeeded"),
                _evidence(code="sql_parse_succeeded"),
                _evidence(code="extra_code"),
            ]
        )
    ]
    validation = _make_validation(intake.content_fingerprint, checks=checks)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    codes = pack.validation.checks[0].evidence_codes
    assert codes == ["sql_parse_succeeded", "extra_code"]


def test_evidence_message_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert CANARY_EVIDENCE_MSG not in _pack_json(pack)


def test_evidence_details_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    text = _pack_json(pack)
    dumped = pack.model_dump(mode="json")
    assert "canary_sql" not in text
    assert "fixture_row" not in text
    assert "dbt_out" not in text
    # No evidence details object is projected into the pack structure.
    for check in dumped["validation"]["checks"]:
        assert "details" not in check
        assert "evidence" not in check
        assert "message" not in check


def test_check_summary_text_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert CANARY_CHECK_SUMMARY not in _pack_json(pack)


def test_engine_name_version_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    text = _pack_json(pack)
    assert "sqlglot" not in text
    assert "engine_name" not in text
    assert "engine_version" not in text


def test_check_id_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    text = _pack_json(pack)
    assert "check_id" not in text
    for check in validation.checks:
        assert str(check.check_id) not in text


def test_raw_sql_canary_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert CANARY_SQL not in _pack_json(pack)


def test_fixture_value_canary_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert CANARY_FIXTURE not in _pack_json(pack)


def test_dbt_output_canary_not_in_pack() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert CANARY_DBT not in _pack_json(pack)


# ---- Trust and redaction -----------------------------------------------------


def test_trust_subject_origin() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.trust.subject_origin == "riftless_runtime"


def test_trust_subject_scope() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.trust.subject_scope == "current_request_only"


def test_subject_persisted_false() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.trust.subject_persisted is False


def test_input_origin_caller_provided() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.trust.input_origin == "caller_provided"


def test_input_trust_unverified() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.trust.input_trust == "unverified"


def test_provenance_verified_false() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.trust.provenance_verified is False


def test_redaction_applied_true() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.redaction.applied is True


def test_redaction_version_1_0() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.redaction.version == "1.0"


def test_excluded_categories_complete() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert set(pack.redaction.excluded_categories) == set(
        REDACTION_EXCLUDED_CATEGORIES
    )


def test_excluded_categories_canonical_order() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.redaction.excluded_categories == list(REDACTION_EXCLUDED_CATEGORIES)


def test_source_cannot_drive_redaction_summary() -> None:
    """Builder ignores any hypothetical source fields; always server constants."""
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.redaction.applied is True
    assert pack.redaction.version == "1.0"
    assert pack.redaction.excluded_categories == list(REDACTION_EXCLUDED_CATEGORIES)


def test_context_pack_version_1_0() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.context_pack_version == "1.0"


# ---- Purity and determinism --------------------------------------------------


def test_same_semantic_source_identical_pack() -> None:
    # Use fixed intake_id / evaluation_id by rebuilding from same normalized content.
    # process_change_intake generates new UUIDs; semantic pack fields exclude those.
    intake1 = _make_intake()
    risk1 = _make_risk(intake1)
    pack1 = build_advisory_context_pack(
        change_intake=intake1,
        risk_evaluation=risk1,
        validation_requested=False,
        validation_artifact=None,
    )
    # Second intake from identical request content → same fingerprint & summaries.
    intake2 = _make_intake()
    risk2 = _make_risk(intake2)
    pack2 = build_advisory_context_pack(
        change_intake=intake2,
        risk_evaluation=risk2,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack1.model_dump(mode="json") == pack2.model_dump(mode="json")


def test_source_artifacts_not_mutated() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = _make_validation(intake.content_fingerprint)
    intake_before = copy.deepcopy(intake.model_dump(mode="json"))
    risk_before = copy.deepcopy(risk.model_dump(mode="json"))
    val_before = copy.deepcopy(validation.model_dump(mode="json"))
    build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert intake.model_dump(mode="json") == intake_before
    assert risk.model_dump(mode="json") == risk_before
    assert validation.model_dump(mode="json") == val_before


def test_does_not_read_environment() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)

    def _deny(*_a: Any, **_k: Any) -> str:
        raise AssertionError("must not read environment")

    with patch("os.getenv", side_effect=_deny):
        with patch("os.environ.get", side_effect=_deny):
            build_advisory_context_pack(
                change_intake=intake,
                risk_evaluation=risk,
                validation_requested=False,
                validation_artifact=None,
            )


def test_does_not_perform_network_call() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)

    def _deny(*_a: Any, **_k: Any) -> None:
        raise AssertionError("network forbidden")

    with patch("urllib.request.urlopen", side_effect=_deny):
        build_advisory_context_pack(
            change_intake=intake,
            risk_evaluation=risk,
            validation_requested=False,
            validation_artifact=None,
        )


def test_does_not_run_subprocess() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)

    def _deny(*_a: Any, **_k: Any) -> None:
        raise AssertionError("subprocess forbidden")

    with patch("subprocess.run", side_effect=_deny):
        with patch("subprocess.Popen", side_effect=_deny):
            build_advisory_context_pack(
                change_intake=intake,
                risk_evaluation=risk,
                validation_requested=False,
                validation_artifact=None,
            )


def test_does_not_write_files(tmp_path: Path) -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    before = set(tmp_path.iterdir()) if tmp_path.exists() else set()
    build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    after = set(tmp_path.iterdir()) if tmp_path.exists() else set()
    assert before == after


def test_does_not_create_random_aliases() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    packs = [
        build_advisory_context_pack(
            change_intake=intake,
            risk_evaluation=risk,
            validation_requested=False,
            validation_artifact=None,
        )
        for _ in range(5)
    ]
    aliases = {
        (p.change.asset_alias, p.change.source_column_alias, p.change.target_column_alias)
        for p in packs
    }
    assert aliases == {("asset_1", "column_1", "column_2")}


def test_subject_fingerprint_matches_intake() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert pack.subject_fingerprint == intake.content_fingerprint


def test_advisory_context_fingerprint_stable() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    pack1 = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    pack2 = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=False,
        validation_artifact=None,
    )
    assert fingerprint_advisory_context(pack1) == fingerprint_advisory_context(pack2)
    assert len(fingerprint_advisory_context(pack1)) == 64


def test_risk_decision_change_changes_context_fingerprint() -> None:
    intake = _make_intake()
    risk_allow = _make_risk(intake, protected_asset=False)
    risk_block = _make_risk(intake, protected_asset=True)
    pack_a = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk_allow,
        validation_requested=False,
        validation_artifact=None,
    )
    pack_b = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk_block,
        validation_requested=False,
        validation_artifact=None,
    )
    assert fingerprint_advisory_context(pack_a) != fingerprint_advisory_context(pack_b)


def test_validation_result_change_changes_context_fingerprint() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    val_pass = _make_validation(intake.content_fingerprint)
    val_fail = _make_validation(
        intake.content_fingerprint,
        checks=[
            _check(
                outcome=CheckOutcome.FAIL,
                evidence=[_evidence(code="sql_parse_failed")],
            )
        ],
    )
    pack_a = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=val_pass,
    )
    pack_b = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=val_fail,
    )
    assert fingerprint_advisory_context(pack_a) != fingerprint_advisory_context(pack_b)


# ---- F7.4A — F6 ValidationArtifact projection compatibility ------------------


def _project_validation(
    intake: ChangeIntakeData,
    risk: RiskEvaluationData,
    validation: ValidationArtifact,
) -> Any:
    return build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    ).validation


def test_f6_completed_pass_projects() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = build_validation_artifact(
        subject_fingerprint=intake.content_fingerprint,
        checks=[
            _check(
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.PASS,
                required=True,
            )
        ],
    )
    assert validation.execution_status == OverallExecutionStatus.COMPLETED.value
    assert validation.outcome == CheckOutcome.PASS.value
    summary = _project_validation(intake, risk, validation)
    assert summary.execution_status == validation.execution_status
    assert summary.outcome == validation.outcome
    assert len(summary.checks) == 1
    assert summary.checks[0].outcome == "pass"


def test_f6_completed_fail_projects() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = build_validation_artifact(
        subject_fingerprint=intake.content_fingerprint,
        checks=[
            _check(
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.FAIL,
                required=True,
                evidence=[_evidence(code="rule_fail")],
            )
        ],
    )
    assert validation.outcome == CheckOutcome.FAIL.value
    summary = _project_validation(intake, risk, validation)
    assert summary.outcome == validation.outcome
    assert summary.execution_status == OverallExecutionStatus.COMPLETED.value


def test_f6_completed_inconclusive_projects() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = build_validation_artifact(
        subject_fingerprint=intake.content_fingerprint,
        checks=[
            _check(
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.PASS,
                required=True,
            ),
            _check(
                check_kind=CheckKind.DUCKDB_EXECUTION,
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.INCONCLUSIVE,
                required=True,
            ),
        ],
    )
    assert validation.execution_status == OverallExecutionStatus.COMPLETED.value
    assert validation.outcome == CheckOutcome.INCONCLUSIVE.value
    summary = _project_validation(intake, risk, validation)
    assert summary.outcome == "inconclusive"
    assert summary.execution_status == "completed"


def test_f6_partial_with_outcome_projects() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = build_validation_artifact(
        subject_fingerprint=intake.content_fingerprint,
        checks=[
            _check(
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.PASS,
                required=True,
            ),
            _check(
                check_kind=CheckKind.DUCKDB_EXECUTION,
                execution_status=CheckExecutionStatus.ERROR,
                outcome=None,
                required=True,
                evidence=[_evidence(code="engine_error")],
            ),
        ],
    )
    assert validation.execution_status == OverallExecutionStatus.PARTIAL.value
    assert validation.outcome == CheckOutcome.INCONCLUSIVE.value
    summary = _project_validation(intake, risk, validation)
    assert summary.execution_status == "partial"
    assert summary.outcome == "inconclusive"
    assert summary.checks[1].execution_status == "error"
    assert summary.checks[1].outcome is None


def test_f6_execution_failed_with_inconclusive_projects() -> None:
    """F6 never nulls overall outcome; execution_failed aggregates to inconclusive."""
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = build_validation_artifact(
        subject_fingerprint=intake.content_fingerprint,
        checks=[
            _check(
                execution_status=CheckExecutionStatus.ERROR,
                outcome=None,
                required=True,
                evidence=[_evidence(code="engine_error")],
            )
        ],
    )
    assert validation.execution_status == OverallExecutionStatus.EXECUTION_FAILED.value
    assert validation.outcome == CheckOutcome.INCONCLUSIVE.value
    summary = _project_validation(intake, risk, validation)
    assert summary.execution_status == "execution_failed"
    assert summary.outcome == "inconclusive"
    # Must not invent FAIL for execution failure.
    assert summary.outcome != "fail"


def test_f6_not_run_empty_checks_projects() -> None:
    """F6 empty checks → not_run + inconclusive; F7 must accept empty checks."""
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = build_validation_artifact(
        subject_fingerprint=intake.content_fingerprint,
        checks=[],
    )
    assert validation.execution_status == OverallExecutionStatus.NOT_RUN.value
    assert validation.outcome == CheckOutcome.INCONCLUSIVE.value
    assert validation.checks == []
    summary = _project_validation(intake, risk, validation)
    assert summary.requested is True
    assert summary.artifact_present is True
    assert summary.execution_status == "not_run"
    assert summary.outcome == "inconclusive"
    assert summary.checks == []


def test_f6_not_run_unavailable_projects() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = build_validation_artifact(
        subject_fingerprint=intake.content_fingerprint,
        checks=[
            _check(
                execution_status=CheckExecutionStatus.UNAVAILABLE,
                outcome=None,
                required=True,
                evidence=[_evidence(code="sqlglot_unavailable")],
            )
        ],
    )
    assert validation.execution_status == OverallExecutionStatus.NOT_RUN.value
    assert validation.outcome == CheckOutcome.INCONCLUSIVE.value
    summary = _project_validation(intake, risk, validation)
    assert summary.execution_status == "not_run"
    assert summary.outcome == "inconclusive"
    assert summary.checks[0].execution_status == "unavailable"
    assert summary.checks[0].outcome is None


def test_f6_optional_fail_required_pass_projects() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = build_validation_artifact(
        subject_fingerprint=intake.content_fingerprint,
        checks=[
            _check(
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.PASS,
                required=True,
            ),
            _check(
                check_kind=CheckKind.DBT_VALIDATION,
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.FAIL,
                required=False,
                evidence=[_evidence(code="optional_fail")],
            ),
        ],
    )
    assert validation.outcome == CheckOutcome.PASS.value
    summary = _project_validation(intake, risk, validation)
    assert summary.outcome == "pass"
    assert summary.checks[1].required is False
    assert summary.checks[1].outcome == "fail"


def test_f6_all_required_error_unavailable_skipped_projects() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = build_validation_artifact(
        subject_fingerprint=intake.content_fingerprint,
        checks=[
            _check(
                check_kind=CheckKind.SQL_PARSE,
                execution_status=CheckExecutionStatus.ERROR,
                outcome=None,
                required=True,
                evidence=[_evidence(code="engine_error")],
            ),
            _check(
                check_kind=CheckKind.DUCKDB_EXECUTION,
                execution_status=CheckExecutionStatus.UNAVAILABLE,
                outcome=None,
                required=True,
                evidence=[_evidence(code="duckdb_unavailable")],
            ),
            _check(
                check_kind=CheckKind.DBT_VALIDATION,
                execution_status=CheckExecutionStatus.SKIPPED,
                outcome=None,
                required=True,
                evidence=[_evidence(code="skipped_required")],
            ),
        ],
    )
    # Mix of error + non-error without completed → execution_failed (any ERROR).
    assert validation.execution_status == OverallExecutionStatus.EXECUTION_FAILED.value
    assert validation.outcome == CheckOutcome.INCONCLUSIVE.value
    summary = _project_validation(intake, risk, validation)
    assert summary.execution_status == "execution_failed"
    assert summary.outcome == "inconclusive"
    assert [c.outcome for c in summary.checks] == [None, None, None]
    assert [c.execution_status for c in summary.checks] == [
        "error",
        "unavailable",
        "skipped",
    ]


def test_f6_check_error_null_outcome_json_null() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = build_validation_artifact(
        subject_fingerprint=intake.content_fingerprint,
        checks=[
            _check(
                execution_status=CheckExecutionStatus.ERROR,
                outcome=None,
                required=True,
                evidence=[_evidence(code="engine_error")],
            )
        ],
    )
    pack = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    dumped = pack.model_dump(mode="json")
    assert dumped["validation"]["checks"][0]["outcome"] is None
    # JSON serialization must keep null, not omit or invent an outcome.
    text = json.dumps(dumped, ensure_ascii=False)
    assert '"outcome": null' in text
    assert dumped["validation"]["outcome"] == "inconclusive"
    assert dumped["validation"]["outcome"] != "pass"
    assert dumped["validation"]["outcome"] != "fail"

def test_f6_empty_checks_fingerprint_stable() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = build_validation_artifact(
        subject_fingerprint=intake.content_fingerprint,
        checks=[],
    )
    pack1 = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    pack2 = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert fingerprint_advisory_context(pack1) == fingerprint_advisory_context(pack2)
    assert pack1.validation.checks == []


def test_f6_no_synthetic_outcome_on_execution_failed() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = build_validation_artifact(
        subject_fingerprint=intake.content_fingerprint,
        checks=[
            _check(
                execution_status=CheckExecutionStatus.ERROR,
                outcome=None,
                required=True,
                evidence=[_evidence(code="engine_error")],
            )
        ],
    )
    summary = _project_validation(intake, risk, validation)
    # Mirror F6 only — never promote execution_failed to FAIL.
    assert summary.execution_status == "execution_failed"
    assert summary.outcome == "inconclusive"
    assert summary.checks[0].outcome is None


def test_f6_source_validation_artifact_not_mutated_empty_checks() -> None:
    intake = _make_intake()
    risk = _make_risk(intake)
    validation = build_validation_artifact(
        subject_fingerprint=intake.content_fingerprint,
        checks=[],
    )
    before = copy.deepcopy(validation.model_dump(mode="json"))
    build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=True,
        validation_artifact=validation,
    )
    assert validation.model_dump(mode="json") == before


# ---- Regression --------------------------------------------------------------


def test_openapi_still_six_routes() -> None:
    client = TestClient(app)
    paths = sorted(client.get("/openapi.json").json()["paths"].keys())
    assert paths == [
        "/api/v1/changes/intake",
        "/api/v1/risk/evaluate",
        "/api/v1/runs/analyze",
        "/api/v1/validations/execute",
        "/health",
        "/ready",
    ]
    assert "advisory" not in " ".join(paths).lower()
