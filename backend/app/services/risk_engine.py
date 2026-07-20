"""Deterministic risk evaluation engine (phase F5.2).

Rules are explicit, ordered, and free of AI / external I/O.

Both evaluation_context and intake_reference are **caller-provided** in F5.2.
There is no artifact registry or persistence, so the server cannot prove that
an intake_id was issued by RIFTLESS or that the reference is authentic.

Fingerprint handling is a **consistency check** only:
- recompute SHA-256 over canonical JSON of normalized_change
- require an exact match with the supplied content_fingerprint
- do **not** claim provenance, authenticity, or tamper-proof integrity

Decisions are scoped to ``provided_context_only``.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from app.core.errors import AppError, ErrorCode
from app.schemas.risk import (
    POLICY_VERSION,
    DecisionLevel,
    RiskEvaluateRequest,
    RiskEvaluationData,
    RiskReason,
    SUPPORTED_ARTIFACT_VERSION,
)
from app.utils.fingerprint import fingerprint_payload, fingerprints_match

DecisionLevelName = Literal["ALLOW", "WARN", "BLOCK"]

_LEVEL_RANK: dict[DecisionLevelName, int] = {
    "ALLOW": 0,
    "WARN": 1,
    "BLOCK": 2,
}


def verify_intake_fingerprint(request: RiskEvaluateRequest) -> str:
    """Check fingerprint consistency for a caller-provided intake reference.

    Recomputes the F5.1 canonical SHA-256 of ``normalized_change`` and
    compares it to ``content_fingerprint``. On success, returns the
    consistency-checked fingerprint string.

    This is **not** provenance verification: a matching fingerprint only
    means the payload and fingerprint are schema-valid and consistent with
    each other. It does not prove the intake was issued by RIFTLESS.

    On mismatch: raises AppError without revealing the computed fingerprint
    or canonical JSON. Mismatch means inconsistency, not proven attack.
    """
    ref = request.intake_reference

    if ref.artifact_version != SUPPORTED_ARTIFACT_VERSION:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="The request could not be validated.",
            status_code=422,
            details=[
                {
                    "loc": ["body", "intake_reference", "artifact_version"],
                    "msg": "Unsupported artifact_version.",
                    "type": "value_error.unsupported_artifact_version",
                }
            ],
        )

    computed = fingerprint_payload(ref.normalized_change.fingerprint_payload())
    if not fingerprints_match(computed, ref.content_fingerprint):
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="The supplied fingerprint does not match the normalized change.",
            status_code=422,
            details=[
                {
                    "loc": ["body", "intake_reference", "content_fingerprint"],
                    "msg": "The supplied fingerprint does not match the normalized change.",
                    "type": "value_error.fingerprint_mismatch",
                }
            ],
        )
    return computed


def _evaluate_rules(context_snapshot: dict[str, Any]) -> list[RiskReason]:
    """Run all deterministic rules in stable order; collect every match.

    RULE 1 — protected_asset → BLOCK
    RULE 2 — incomplete_context → WARN
    RULE 3 — unknown_dependency_count → WARN (only when incomplete)
    RULE 4 — downstream_dependencies_present → WARN
    DEFAULT — no_risk_condition_detected → ALLOW (only if none of the above)
    """
    reasons: list[RiskReason] = []

    protected = bool(context_snapshot["protected_asset"])
    complete = bool(context_snapshot["context_complete"])
    dep_count = context_snapshot["downstream_dependency_count"]

    # RULE 1 — PROTECTED ASSET
    if protected:
        reasons.append(
            RiskReason(
                code="protected_asset",
                level="BLOCK",
                message="The supplied context marks this asset as protected.",
                evidence=None,
            )
        )

    # RULE 2 — INCOMPLETE CONTEXT
    if not complete:
        reasons.append(
            RiskReason(
                code="incomplete_context",
                level="WARN",
                message="The supplied dependency context is incomplete.",
                evidence=None,
            )
        )

    # RULE 3 — UNKNOWN DEPENDENCY COUNT
    # Only valid when context_complete = false (schema already constrains
    # complete=true + null). Still gated here for clarity.
    if dep_count is None and not complete:
        reasons.append(
            RiskReason(
                code="unknown_dependency_count",
                level="WARN",
                message="The downstream dependency count is unknown.",
                evidence=None,
            )
        )

    # RULE 4 — DOWNSTREAM DEPENDENCIES PRESENT
    if isinstance(dep_count, int) and dep_count > 0:
        reasons.append(
            RiskReason(
                code="downstream_dependencies_present",
                level="WARN",
                message="The supplied context reports downstream dependencies.",
                evidence={"downstream_dependency_count": dep_count},
            )
        )

    # DEFAULT — NO TRIGGERED RULE
    if not reasons:
        reasons.append(
            RiskReason(
                code="no_risk_condition_detected",
                level="ALLOW",
                message=(
                    "No blocking or warning condition was detected within "
                    "the supplied context."
                ),
                evidence=None,
            )
        )

    return reasons


def aggregate_decision(reasons: list[RiskReason]) -> DecisionLevel:
    """BLOCK > WARN > ALLOW over the full set of triggered reasons."""
    decision: DecisionLevelName = "ALLOW"
    for reason in reasons:
        level = reason.level
        if _LEVEL_RANK[level] > _LEVEL_RANK[decision]:
            decision = level
    return decision


def evaluate_risk(request: RiskEvaluateRequest) -> RiskEvaluationData:
    """Check fingerprint consistency, run rules, aggregate decision.

    Side-effect free: no network, database, filesystem, or AI calls.
    Persistence is intentionally none in F5.2.
    intake_id is accepted from the caller and is not looked up in storage.
    """
    matched_fingerprint = verify_intake_fingerprint(request)
    context_snapshot = request.evaluation_context.snapshot()
    reasons = _evaluate_rules(context_snapshot)
    decision = aggregate_decision(reasons)

    return RiskEvaluationData(
        evaluation_id=uuid.uuid4(),
        intake_id=request.intake_reference.intake_id,
        decision=decision,
        scope="provided_context_only",
        reasons=reasons,
        evaluated_content_fingerprint=matched_fingerprint,
        evaluation_context=context_snapshot,
        policy_version=POLICY_VERSION,
        artifact_version=request.intake_reference.artifact_version,
    )


def risk_meta() -> dict[str, Any]:
    """Honest operation metadata for the success envelope.

    Distinguishes:
    - evaluation_context origin/trust
    - intake_reference origin/trust
    - fingerprint consistency check result (matched only on success path)
    """
    return {
        "operation": "deterministic_risk_evaluation",
        "phase": "F5.2",
        "policy_version": POLICY_VERSION,
        "context_origin": "caller_provided",
        "context_trust": "unverified",
        "intake_reference_origin": "caller_provided",
        "intake_reference_trust": "unverified",
        "fingerprint_check": "matched",
        "model_used": False,
        "persistence": "none",
    }
