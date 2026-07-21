"""Validation execution HTTP routes (phase F6.6).

Thin synchronous boundary over the F6.5 orchestration service.
Does not re-implement plan invariants, validators, or aggregation.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.schemas.common import SuccessResponse
from app.schemas.validation import ValidationArtifact
from app.schemas.validation_api import validation_execution_meta
from app.schemas.validation_plan import ValidationPlanInput
from app.services.validation_orchestrator import orchestrate_validation

router = APIRouter(tags=["validations"])


@router.post(
    "/validations/execute",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[ValidationArtifact],
    summary="Execute synchronous multi-engine validation orchestration",
    description=(
        "Accepts a ValidationPlanInput (caller-provided intake reference, "
        "SQLGlot parse input, DuckDB rename fixture, and dbt model SQL). "
        "Runs fingerprint consistency and cross-artifact invariant checks, "
        "then executes SQLGlot → DuckDB → dbt in fixed order without "
        "short-circuit. Returns a ValidationArtifact (F6.1) inside the "
        "standard success envelope.\n\n"
        "HTTP 200 means the API request was processed and a valid artifact "
        "was formed — not that outcome is PASS, that every check completed, "
        "or that deployment is authorized. PASS / FAIL / INCONCLUSIVE and "
        "completed / partial / not_run / execution_failed are all returned "
        "with HTTP 200.\n\n"
        "Invalid plans yield HTTP 422. Artifacts are not persisted; "
        "retrieval is not available. Intake reference, SQL, and fixtures "
        "remain caller-provided and unverified. Subject fingerprint scopes "
        "only the intake normalized_change. Does not call DataHub, GitHub, "
        "AI providers, or authorize writeback/deployment. Not connected to "
        "POST /api/v1/runs/analyze."
    ),
)
def execute_validation(
    payload: ValidationPlanInput,
) -> SuccessResponse[ValidationArtifact]:
    """Synchronous handler: blocking validators run off the main event loop."""
    data = orchestrate_validation(payload)
    return SuccessResponse(status="ok", data=data, meta=validation_execution_meta())
