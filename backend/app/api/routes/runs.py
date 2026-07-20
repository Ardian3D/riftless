"""Synchronous analysis run HTTP routes (phase F5.3).

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
    summary="Run synchronous change intake and risk evaluation",
    description=(
        "Accepts a change request and caller-provided evaluation context, "
        "then runs F5.1 intake and F5.2 deterministic risk evaluation "
        "in-process within a single HTTP request. Returns a combined run "
        "artifact. Does not persist runs, open retrieval URLs, query "
        "DataHub/GitHub, use AI, execute SQL, or authorize deployment. "
        "orchestration_status=completed means the pipeline finished, not "
        "that the decision is ALLOW or that validation/deployment succeeded."
    ),
)
async def analyze_run(
    payload: AnalysisRunRequest,
) -> SuccessResponse[AnalysisRunData]:
    data = orchestrate_analysis_run(payload)
    return SuccessResponse(status="ok", data=data, meta=analysis_run_meta())
