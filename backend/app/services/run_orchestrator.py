"""Synchronous analysis run orchestration (phase F5.3).

Connects existing F5.1 intake and F5.2 risk services in-process:

    change request
    → process_change_intake (F5.1)
    → request-local intake reference
    → evaluate_risk (F5.2)
    → analysis run artifact

This module does **not** reimplement normalization, fingerprinting, or risk
rules. It only sequences services and assembles the run response.

Trust boundary (honest):
- evaluation_context remains caller_provided / unverified
- intake is produced by RIFTLESS runtime for the current request only
- intake is not persisted and has no durable provenance / registry match
- fingerprint remains a content-consistency mechanism only
"""

from __future__ import annotations

import uuid
from typing import Any

from app.schemas.changes import ChangeIntakeData, NormalizedChange
from app.schemas.risk import IntakeReference, RiskEvaluateRequest
from app.schemas.runs import (
    RUN_ARTIFACT_VERSION,
    AnalysisRunData,
    AnalysisRunRequest,
)
from app.services.change_intake import process_change_intake
from app.services.risk_engine import evaluate_risk


def _build_runtime_intake_reference(intake: ChangeIntakeData) -> IntakeReference:
    """Build a request-local intake reference from F5.1 service output.

    The reference exists only for the duration of the current orchestration
    call. It is not loaded from storage and is not durable.
    """
    return IntakeReference(
        intake_id=intake.intake_id,
        normalized_change=NormalizedChange.model_validate(intake.normalized_change),
        content_fingerprint=intake.content_fingerprint,
        artifact_version=intake.artifact_version,
    )


def orchestrate_analysis_run(request: AnalysisRunRequest) -> AnalysisRunData:
    """Run intake then risk evaluation synchronously in-process.

    Side-effect free beyond in-memory computation: no HTTP loopback, network,
    database, filesystem artifacts, or AI calls.
    """
    # STEP 2 — CHANGE INTAKE (F5.1 service, not HTTP)
    intake = process_change_intake(request.change)

    # STEP 3 — REQUEST-LOCAL INTAKE REFERENCE
    intake_reference = _build_runtime_intake_reference(intake)

    # STEP 4 — DETERMINISTIC RISK EVALUATION (F5.2 service, not HTTP)
    risk_request = RiskEvaluateRequest(
        intake_reference=intake_reference,
        evaluation_context=request.evaluation_context,
    )
    risk = evaluate_risk(risk_request)

    # Consistency guarantees for the combined artifact
    if risk.intake_id != intake.intake_id:
        # Defensive: should be impossible when using the reference above.
        raise RuntimeError("risk evaluation intake_id does not match change intake")
    if risk.evaluated_content_fingerprint != intake.content_fingerprint:
        raise RuntimeError(
            "risk evaluation fingerprint does not match change intake fingerprint"
        )

    # STEP 5 — RUN ARTIFACT
    return AnalysisRunData(
        run_id=uuid.uuid4(),
        orchestration_status="completed",
        change_intake=intake,
        risk_evaluation=risk,
        run_artifact_version=RUN_ARTIFACT_VERSION,
    )


def analysis_run_meta() -> dict[str, Any]:
    """Honest meta for the F5.3 success envelope.

    Distinguishes caller-provided evaluation context from runtime-generated,
    non-persisted intake used only within the current request.
    """
    return {
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
