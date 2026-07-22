"""Synchronous analysis run orchestration (phase F5.3 / F6.7 / F7.5).

Connects existing services in-process:

    change request
    → process_change_intake (F5.1)
    → request-local intake reference
    → evaluate_risk (F5.2)
    → optional orchestrate_validation (F6.5) using runtime intake
    → optional build_advisory_context_pack (F7.2)
    → optional execute_deepseek_advisory (F7.4)
    → analysis run artifact

This module does **not** reimplement normalization, fingerprinting, risk
rules, validators, aggregation, context redaction, or provider execution.
It only sequences services and assembles the run response.

Trust boundary (honest):
- evaluation_context remains caller_provided / unverified
- intake is produced by RIFTLESS runtime for the current request only
- intake is not persisted and has no durable provenance / registry match
- optional validation subject uses the same runtime intake (current request)
- SQL / fixture / dbt model remain caller_provided / unverified
- risk decision, validation outcome, and advisory execution are independent
- advisory input is a server-controlled redacted projection only
- provider output is untrusted natural language (authority = advisory_only)
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from app.schemas.advisory import AdvisoryArtifact
from app.schemas.changes import ChangeIntakeData, NormalizedChange
from app.schemas.duckdb_validation import DuckDbRenameInput
from app.schemas.risk import IntakeReference, RiskEvaluateRequest
from app.schemas.run_validation import RunValidationInput
from app.schemas.runs import (
    RUN_ARTIFACT_VERSION,
    AnalysisRunData,
    AnalysisRunRequest,
)
from app.schemas.validation import ValidationArtifact
from app.schemas.validation_plan import ValidationPlanChecks, ValidationPlanInput
from app.services.advisory_context_builder import build_advisory_context_pack
from app.services.change_intake import process_change_intake
from app.services.deepseek_http_transport import (
    DeepSeekTransport,
    StdlibDeepSeekHTTPSTransport,
)
from app.services.deepseek_provider_config import load_deepseek_provider_config
from app.services.deepseek_provider_execution import execute_deepseek_advisory
from app.services.risk_engine import evaluate_risk
from app.services.validation_orchestrator import orchestrate_validation


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


def _build_validation_plan(
    *,
    intake_reference: IntakeReference,
    validation: RunValidationInput,
) -> ValidationPlanInput:
    """Compose a ValidationPlanInput from runtime intake + caller check inputs.

    DuckDB ``normalized_change`` is always taken from runtime intake — never
    from the caller.
    """
    duckdb_input = DuckDbRenameInput(
        normalized_change=intake_reference.normalized_change,
        fixture=validation.checks.duckdb_execution.fixture,
        required=validation.checks.duckdb_execution.required,
    )
    return ValidationPlanInput(
        intake_reference=intake_reference,
        checks=ValidationPlanChecks(
            sql_parse=validation.checks.sql_parse,
            duckdb_execution=duckdb_input,
            dbt_validation=validation.checks.dbt_validation,
        ),
    )


def _advisory_requested(request: AnalysisRunRequest) -> bool:
    return request.advisory is not None and request.advisory.requested is True


def _execute_optional_advisory(
    *,
    intake: ChangeIntakeData,
    risk: Any,
    validation_requested: bool,
    validation_artifact: ValidationArtifact | None,
    advisory_environ: Mapping[str, str] | None,
    advisory_transport: DeepSeekTransport | None,
) -> AdvisoryArtifact:
    """Build F7.2 context then execute F7.4 provider boundary.

    ``AdvisoryContextBuildError`` and other programming/invariant failures
    propagate (HTTP 500 at the route). Provider/network/parser failures are
    already mapped by F7.4 into noncompleted AdvisoryArtifact values.
    """
    context = build_advisory_context_pack(
        change_intake=intake,
        risk_evaluation=risk,
        validation_requested=validation_requested,
        validation_artifact=validation_artifact,
    )

    config = load_deepseek_provider_config(advisory_environ)

    transport: DeepSeekTransport
    if advisory_transport is not None:
        transport = advisory_transport
    else:
        transport = StdlibDeepSeekHTTPSTransport()

    return execute_deepseek_advisory(
        context,
        config=config,
        transport=transport,
    )


def orchestrate_analysis_run(
    request: AnalysisRunRequest,
    *,
    advisory_environ: Mapping[str, str] | None = None,
    advisory_transport: DeepSeekTransport | None = None,
) -> AnalysisRunData:
    """Run intake, risk, optional validation, and optional advisory in-process.

    Keyword-only ``advisory_environ`` / ``advisory_transport`` are internal
    test injection points. They are never part of the HTTP request schema.
    Production callers omit them (server ``os.environ`` + stdlib HTTPS).

    Side-effect free beyond in-memory computation, bounded validator engines,
    and at most one DeepSeek HTTPS attempt when advisory is requested.
    No durable storage, retrieval, retry, or AI decision authority.
    """
    # STEP 1 — CHANGE INTAKE (F5.1 service, not HTTP)
    intake = process_change_intake(request.change)

    # STEP 2 — REQUEST-LOCAL INTAKE REFERENCE
    intake_reference = _build_runtime_intake_reference(intake)

    # STEP 3 — DETERMINISTIC RISK EVALUATION (F5.2 service, not HTTP)
    risk_request = RiskEvaluateRequest(
        intake_reference=intake_reference,
        evaluation_context=request.evaluation_context,
    )
    risk = evaluate_risk(risk_request)

    # Consistency guarantees for the combined artifact
    if risk.intake_id != intake.intake_id:
        raise RuntimeError("risk evaluation intake_id does not match change intake")
    if risk.evaluated_content_fingerprint != intake.content_fingerprint:
        raise RuntimeError(
            "risk evaluation fingerprint does not match change intake fingerprint"
        )

    # STEP 4 — OPTIONAL VALIDATION (F6.5 service, not HTTP)
    # Risk decision never short-circuits validation. Validation never rewrites
    # the risk decision. Advisory never short-circuits either.
    validation_artifact: ValidationArtifact | None = None
    validation_requested = request.validation is not None
    if validation_requested:
        plan = _build_validation_plan(
            intake_reference=intake_reference,
            validation=request.validation,  # type: ignore[arg-type]
        )
        validation_artifact = orchestrate_validation(plan)

        if (
            validation_artifact.subject_fingerprint
            != intake.content_fingerprint
        ):
            raise RuntimeError(
                "validation subject fingerprint does not match change intake fingerprint"
            )

    # STEP 5 / 6 — OPTIONAL ADVISORY (F7.2 context + F7.4 provider)
    # Independent of risk decision and validation outcome. BLOCK / FAIL never
    # skip advisory when requested. Advisory status never rewrites risk or
    # validation and never changes orchestration_status.
    advisory_requested = _advisory_requested(request)
    advisory_artifact: AdvisoryArtifact | None = None
    if advisory_requested:
        advisory_artifact = _execute_optional_advisory(
            intake=intake,
            risk=risk,
            validation_requested=validation_requested,
            validation_artifact=validation_artifact,
            advisory_environ=advisory_environ,
            advisory_transport=advisory_transport,
        )

    # STEP 7 — RUN ARTIFACT
    return AnalysisRunData(
        run_id=uuid.uuid4(),
        orchestration_status="completed",
        change_intake=intake,
        risk_evaluation=risk,
        validation_artifact=validation_artifact,
        advisory_requested=advisory_requested,
        advisory_artifact=advisory_artifact,
        run_artifact_version=RUN_ARTIFACT_VERSION,
    )


def analysis_run_meta(
    *,
    validation_requested: bool,
    advisory_requested: bool = False,
) -> dict[str, Any]:
    """Honest meta for the analysis-run success envelope.

    Distinguishes caller-provided evaluation context and validation inputs
    from runtime-generated, non-persisted intake used only within the current
    request. Risk, validation, and advisory remain independent policy surfaces.
    """
    meta: dict[str, Any] = {
        "operation": "synchronous_analysis_run",
        "phase": "F7.5",
        "execution_mode": "in_process",
        "persistence": "none",
        "retrieval_available": False,
        "context_origin": "caller_provided",
        "context_trust": "unverified",
        "intake_reference_origin": "riftless_runtime",
        "intake_reference_scope": "current_request_only",
        "intake_reference_persisted": False,
        "model_used": advisory_requested,
        "deployment_authorized": False,
        "validation_requested": validation_requested,
        "validation_executed": validation_requested,
        "validation_artifact_present": validation_requested,
        "validation_persistence": "none",
        "validation_retrieval_available": False,
        "advisory_requested": advisory_requested,
        "advisory_executed": advisory_requested,
        "advisory_artifact_present": advisory_requested,
        "advisory_persistence": "none",
        "advisory_retrieval_available": False,
        "advisory_authority": "advisory_only" if advisory_requested else None,
        "advisory_input_origin": (
            "server_controlled_redacted_projection" if advisory_requested else None
        ),
        "advisory_source_scope": (
            "current_request_only" if advisory_requested else None
        ),
        "advisory_provider_output_trust": (
            "untrusted_natural_language" if advisory_requested else None
        ),
    }

    if validation_requested:
        meta.update(
            {
                "validation_subject_origin": "riftless_runtime",
                "validation_subject_scope": "current_request_only",
                "validation_subject_persisted": False,
                "validation_input_origin": "caller_provided",
                "validation_input_trust": "unverified",
                "validation_sql_origin": "caller_provided",
                "validation_fixture_origin": "caller_provided",
            }
        )
    else:
        meta.update(
            {
                "validation_subject_origin": None,
                "validation_subject_scope": None,
                "validation_subject_persisted": False,
                "validation_input_origin": None,
                "validation_input_trust": None,
                "validation_sql_origin": None,
                "validation_fixture_origin": None,
            }
        )

    return meta
