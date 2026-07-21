"""Synchronous analysis run HTTP routes (phase F5.3 / F6.7).

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
    summary="Run synchronous change intake, risk evaluation, and optional validation",
    description=(
        "Accepts a change request and caller-provided evaluation context, "
        "optionally with validation check inputs (SQL, DuckDB fixture, dbt "
        "model). Runs F5.1 intake, F5.2 deterministic risk evaluation, and "
        "when requested F6 validation orchestration in-process within a "
        "single HTTP request.\n\n"
        "Runtime intake (intake_id, normalized_change, fingerprint) is created "
        "by RIFTLESS for the current request only and is used as the "
        "validation subject when validation is requested. Callers must not "
        "send intake references, fingerprints, or generated validation "
        "results.\n\n"
        "Risk decision and validation outcome are independent: BLOCK does "
        "not skip validation; validation FAIL does not rewrite risk to "
        "BLOCK. orchestration_status=completed means requested pipeline "
        "artifacts were formed — not ALLOW, not validation PASS, not "
        "deployment authorization, and not persistence.\n\n"
        "Does not open retrieval URLs, query DataHub/GitHub, use AI, mutate "
        "production, or authorize writeback/deployment. Standalone "
        "POST /api/v1/validations/execute remains available."
    ),
)
def analyze_run(
    payload: AnalysisRunRequest,
) -> SuccessResponse[AnalysisRunData]:
    """Synchronous handler: optional DuckDB/dbt work runs off the event loop."""
    data = orchestrate_analysis_run(payload)
    return SuccessResponse(
        status="ok",
        data=data,
        meta=analysis_run_meta(validation_requested=payload.validation is not None),
    )
