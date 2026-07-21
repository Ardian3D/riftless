"""Server-controlled redacted AdvisoryContextPack builder (phase F7.2).

Builds an F7.1 AdvisoryContextPack from current-request RIFTLESS artifacts
using explicit allowlisted field projection. Does **not**:
- call DeepSeek or any model
- read environment / API keys
- open network sockets or subprocesses
- write files
- dump entire source artifacts into the pack
- implement semantic secret/SQL scanning

``redaction.applied=true`` means allowlisted projection excluded the
declared categories from the generated pack — not that natural-language
secret detection ran.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.schemas.advisory import (
    ADVISORY_CONTEXT_PACK_VERSION,
    ADVISORY_REDACTION_VERSION,
    REDACTION_EXCLUDED_CATEGORIES,
    AdvisoryChangeSummary,
    AdvisoryContextPack,
    AdvisoryRedactionSummary,
    AdvisoryRiskSummary,
    AdvisoryTrustSummary,
    AdvisoryValidationCheckSummary,
    AdvisoryValidationSummary,
)
from app.schemas.changes import ChangeIntakeData, NormalizedChange
from app.schemas.risk import RiskEvaluationData
from app.schemas.validation import ValidationArtifact, ValidationCheckResult
from app.services.change_intake import compute_content_fingerprint
from app.utils.fingerprint import fingerprints_match

# Fixed canonical aliases for the single rename_column operation (F7.2).
_ASSET_ALIAS = "asset_1"
_SOURCE_COLUMN_ALIAS = "column_1"
_TARGET_COLUMN_ALIAS = "column_2"

_SUPPORTED_CHANGE_TYPE = "rename_column"
_SUPPORTED_ARTIFACT_VERSION = "1.0"


class AdvisoryContextBuildError(Exception):
    """Bounded, safe failure while building an advisory context pack.

    Carries only a machine code and human message. Never stores fingerprints,
    identifiers, SQL, fixture values, or artifact dumps.
    """

    def __init__(self, *, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def _safe_fail(code: str, message: str) -> None:
    raise AdvisoryContextBuildError(code=code, message=message)


def _dedupe_first(items: list[str]) -> list[str]:
    """Preserve first-occurrence order; drop later duplicates."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _parse_normalized_change(intake: ChangeIntakeData) -> NormalizedChange:
    """Load normalized_change dict into the F5 schema (allowlisted path)."""
    raw = intake.normalized_change
    if not isinstance(raw, dict):
        _safe_fail(
            "unsupported_change_type",
            "Change intake normalized payload is not a supported object.",
        )
    change_type = raw.get("change_type")
    if change_type != _SUPPORTED_CHANGE_TYPE:
        _safe_fail(
            "unsupported_change_type",
            "Only rename_column is supported for advisory context packs.",
        )
    try:
        return NormalizedChange.model_validate(raw)
    except ValidationError:
        _safe_fail(
            "unsupported_change_type",
            "Change intake normalized payload failed schema validation.",
        )
        raise  # pragma: no cover — _safe_fail always raises


def _verify_intake_fingerprint(
    intake: ChangeIntakeData,
    normalized: NormalizedChange,
) -> str:
    """Recompute F5 fingerprint; return verified subject fingerprint string."""
    if intake.artifact_version != _SUPPORTED_ARTIFACT_VERSION:
        _safe_fail(
            "unsupported_change_type",
            "Change intake artifact version is not supported.",
        )
    computed = compute_content_fingerprint(normalized)
    if not fingerprints_match(computed, intake.content_fingerprint):
        # Never include computed or expected fingerprint in the error.
        _safe_fail(
            "intake_fingerprint_mismatch",
            "Change intake content fingerprint is inconsistent with the "
            "normalized change.",
        )
    return intake.content_fingerprint


def _verify_risk_subject(
    risk: RiskEvaluationData,
    *,
    subject_fingerprint: str,
) -> None:
    if risk.artifact_version != _SUPPORTED_ARTIFACT_VERSION:
        _safe_fail(
            "risk_subject_mismatch",
            "Risk evaluation artifact version is not supported.",
        )
    if not fingerprints_match(
        risk.evaluated_content_fingerprint, subject_fingerprint
    ):
        _safe_fail(
            "risk_subject_mismatch",
            "Risk evaluation subject fingerprint does not match the change "
            "intake fingerprint.",
        )


def _verify_validation_presence(
    *,
    validation_requested: bool,
    validation_artifact: ValidationArtifact | None,
    subject_fingerprint: str,
) -> None:
    if not validation_requested:
        if validation_artifact is not None:
            _safe_fail(
                "validation_presence_mismatch",
                "Validation artifact must be absent when validation was not "
                "requested.",
            )
        return

    if validation_artifact is None:
        _safe_fail(
            "validation_presence_mismatch",
            "Validation artifact is required when validation was requested.",
        )
        return  # pragma: no cover

    if validation_artifact.artifact_version != _SUPPORTED_ARTIFACT_VERSION:
        _safe_fail(
            "validation_subject_mismatch",
            "Validation artifact version is not supported.",
        )
    if not fingerprints_match(
        validation_artifact.subject_fingerprint, subject_fingerprint
    ):
        _safe_fail(
            "validation_subject_mismatch",
            "Validation artifact subject fingerprint does not match the "
            "change intake fingerprint.",
        )


def _project_change_summary(normalized: NormalizedChange) -> AdvisoryChangeSummary:
    """Allowlisted change fields + fixed canonical aliases."""
    return AdvisoryChangeSummary(
        change_type=_SUPPORTED_CHANGE_TYPE,
        asset_platform=normalized.asset.platform,
        asset_alias=_ASSET_ALIAS,
        source_column_alias=_SOURCE_COLUMN_ALIAS,
        target_column_alias=_TARGET_COLUMN_ALIAS,
        reason_present=normalized.reason is not None,
    )


def _project_risk_summary(risk: RiskEvaluationData) -> AdvisoryRiskSummary:
    """Allowlisted risk fields; reason codes only (no messages/evidence)."""
    codes = _dedupe_first([reason.code for reason in risk.reasons])
    context = risk.evaluation_context
    if not isinstance(context, dict):
        _safe_fail(
            "risk_subject_mismatch",
            "Risk evaluation context snapshot is not a supported object.",
        )
    try:
        context_complete = bool(context["context_complete"])
        protected_asset = bool(context["protected_asset"])
        downstream = context.get("downstream_dependency_count")
    except (KeyError, TypeError):
        _safe_fail(
            "risk_subject_mismatch",
            "Risk evaluation context snapshot is missing required fields.",
        )
        raise  # pragma: no cover

    try:
        return AdvisoryRiskSummary(
            decision=risk.decision,
            reason_codes=codes,
            context_complete=context_complete,
            downstream_dependency_count=downstream,
            protected_asset=protected_asset,
        )
    except ValidationError:
        _safe_fail(
            "risk_subject_mismatch",
            "Risk evaluation fields are not compatible with the advisory "
            "risk summary contract.",
        )
        raise  # pragma: no cover


def _project_check(check: ValidationCheckResult) -> AdvisoryValidationCheckSummary:
    codes = _dedupe_first([item.code for item in check.evidence])
    try:
        return AdvisoryValidationCheckSummary(
            check_kind=check.check_kind,
            required=check.required,
            execution_status=check.execution_status,
            outcome=check.outcome,
            evidence_codes=codes,
        )
    except ValidationError:
        _safe_fail(
            "validation_subject_mismatch",
            "Validation check fields are not compatible with the advisory "
            "validation summary contract.",
        )
        raise  # pragma: no cover


def _project_validation_summary(
    *,
    validation_requested: bool,
    validation_artifact: ValidationArtifact | None,
) -> AdvisoryValidationSummary:
    if not validation_requested:
        return AdvisoryValidationSummary(
            requested=False,
            artifact_present=False,
            execution_status=None,
            outcome=None,
            checks=[],
        )

    assert validation_artifact is not None  # enforced by presence check
    check_summaries = [
        _project_check(check) for check in validation_artifact.checks
    ]
    try:
        return AdvisoryValidationSummary(
            requested=True,
            artifact_present=True,
            execution_status=validation_artifact.execution_status,
            outcome=validation_artifact.outcome,
            checks=check_summaries,
        )
    except ValidationError:
        _safe_fail(
            "validation_subject_mismatch",
            "Validation artifact fields are not compatible with the advisory "
            "validation summary contract.",
        )
        raise  # pragma: no cover


def _server_trust_summary() -> AdvisoryTrustSummary:
    """Fixed trust labels for current-request runtime sources only."""
    return AdvisoryTrustSummary(
        subject_origin="riftless_runtime",
        subject_scope="current_request_only",
        subject_persisted=False,
        input_origin="caller_provided",
        input_trust="unverified",
        provenance_verified=False,
    )


def _server_redaction_summary() -> AdvisoryRedactionSummary:
    """Server-owned redaction declaration with full canonical exclusions."""
    return AdvisoryRedactionSummary(
        applied=True,
        version=ADVISORY_REDACTION_VERSION,
        excluded_categories=list(REDACTION_EXCLUDED_CATEGORIES),
    )


def build_advisory_context_pack(
    *,
    change_intake: ChangeIntakeData,
    risk_evaluation: RiskEvaluationData,
    validation_requested: bool,
    validation_artifact: ValidationArtifact | None,
) -> AdvisoryContextPack:
    """Build a redacted AdvisoryContextPack from current-request artifacts.

    Pure and deterministic for the same semantic sources. Does not mutate
    inputs. Does not accept caller-provided aliases, trust, or redaction.
    """
    if not isinstance(change_intake, ChangeIntakeData):
        raise TypeError("change_intake must be a ChangeIntakeData")
    if not isinstance(risk_evaluation, RiskEvaluationData):
        raise TypeError("risk_evaluation must be a RiskEvaluationData")
    if validation_artifact is not None and not isinstance(
        validation_artifact, ValidationArtifact
    ):
        raise TypeError("validation_artifact must be ValidationArtifact or None")

    normalized = _parse_normalized_change(change_intake)
    subject_fingerprint = _verify_intake_fingerprint(change_intake, normalized)
    _verify_risk_subject(risk_evaluation, subject_fingerprint=subject_fingerprint)
    _verify_validation_presence(
        validation_requested=validation_requested,
        validation_artifact=validation_artifact,
        subject_fingerprint=subject_fingerprint,
    )

    change_summary = _project_change_summary(normalized)
    risk_summary = _project_risk_summary(risk_evaluation)
    validation_summary = _project_validation_summary(
        validation_requested=validation_requested,
        validation_artifact=validation_artifact,
    )

    return AdvisoryContextPack(
        subject_fingerprint=subject_fingerprint,
        change=change_summary,
        risk=risk_summary,
        validation=validation_summary,
        trust=_server_trust_summary(),
        redaction=_server_redaction_summary(),
        context_pack_version=ADVISORY_CONTEXT_PACK_VERSION,
    )
