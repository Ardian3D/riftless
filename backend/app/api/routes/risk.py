"""Deterministic risk evaluation HTTP routes (phase F5.2).

Routing only — schemas and rule logic live elsewhere.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.schemas.common import SuccessResponse
from app.schemas.risk import RiskEvaluateRequest, RiskEvaluationData
from app.services.risk_engine import evaluate_risk, risk_meta

router = APIRouter(tags=["risk"])


@router.post(
    "/risk/evaluate",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[RiskEvaluationData],
    summary="Evaluate risk for a caller-provided intake reference (deterministic)",
    description=(
        "Accepts a caller-provided intake_reference and evaluation_context. "
        "Performs a fingerprint consistency check on normalized_change "
        "(schema-valid and fingerprint-consistent), then applies explicit "
        "deterministic rules. Intake provenance is unverified: there is no "
        "artifact registry in F5.2. Does not query DataHub, GitHub, AI "
        "providers, or persistence. Decisions are scoped to "
        "provided_context_only and are not deployment authorization."
    ),
)
async def risk_evaluate(
    payload: RiskEvaluateRequest,
) -> SuccessResponse[RiskEvaluationData]:
    data = evaluate_risk(payload)
    return SuccessResponse(status="ok", data=data, meta=risk_meta())
