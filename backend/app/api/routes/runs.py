"""Synchronous analysis run HTTP routes (phase F5.3 / F6.7 / F7.5).

Routing only — orchestration and domain logic live in services.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.schemas.common import SuccessResponse
from app.schemas.runs import AnalysisRunData, AnalysisRunRequest
from app.services.run_orchestrator import analysis_run_meta, orchestrate_analysis_run

router = APIRouter(tags=["runs"])


@router.post(
    "/runs/analyze",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[AnalysisRunData],
    summary=(
        "Run synchronous change intake, risk evaluation, optional validation, "
        "and optional advisory"
    ),
    description=(
        "Accepts a change request and caller-provided evaluation context, "
        "optionally with validation check inputs (SQL, DuckDB fixture, dbt "
        "model) and/or an advisory request flag. Runs F5.1 intake, F5.2 "
        "deterministic risk evaluation, optional F6 validation orchestration, "
        "and optional F7 DeepSeek advisory execution in-process within a "
        "single HTTP request.\n\n"
        "Runtime intake (intake_id, normalized_change, fingerprint) is created "
        "by RIFTLESS for the current request only and is used as the "
        "validation subject and advisory context subject when those steps are "
        "requested. Callers must not send intake references, fingerprints, "
        "generated validation results, context packs, prompts, model names, "
        "provider URLs, or API keys.\n\n"
        "Risk decision, validation outcome, and advisory execution_status are "
        "independent: BLOCK does not skip validation or advisory; validation "
        "FAIL does not rewrite risk; advisory unavailable/error does not "
        "rewrite risk or validation. orchestration_status=completed means "
        "requested pipeline artifacts were formed — not ALLOW, not validation "
        "PASS, not advisory completed, not deployment authorization, and not "
        "persistence.\n\n"
        "Advisory uses a server-controlled redacted context projection only. "
        "DEEPSEEK_API_KEY is read only from the server environment when "
        "advisory is requested. Missing configuration yields an unavailable "
        "advisory artifact (HTTP 200), not a readiness failure.\n\n"
        "Does not open retrieval URLs, query DataHub/GitHub, mutate production, "
        "authorize writeback/deployment, retry providers, or expose a "
        "standalone advisory endpoint. Standalone "
        "POST /api/v1/validations/execute remains available."
    ),
)
def analyze_run(
    payload: AnalysisRunRequest,
) -> SuccessResponse[AnalysisRunData]:
    """Synchronous handler: optional DuckDB/dbt/DeepSeek work runs off the event loop."""
    data = orchestrate_analysis_run(payload)
    advisory_requested = (
        payload.advisory is not None and payload.advisory.requested is True
    )
    return SuccessResponse(
        status="ok",
        data=data,
        meta=analysis_run_meta(
            validation_requested=payload.validation is not None,
            advisory_requested=advisory_requested,
        ),
    )
