"""Change intake HTTP routes (phase F5.1).

Routing only — validation schemas and business logic live elsewhere.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.schemas.changes import ChangeIntakeData, ChangeIntakeRequest
from app.schemas.common import SuccessResponse
from app.services.change_intake import intake_meta, process_change_intake

router = APIRouter(tags=["changes"])


@router.post(
    "/changes/intake",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[ChangeIntakeData],
    summary="Accept and normalize a data change request",
    description=(
        "Validates and normalizes a single rename_column change request. "
        "Returns submitted_input, normalized_change, and a deterministic "
        "content fingerprint. Does not persist, analyze risk, remediate, "
        "or call external systems."
    ),
)
async def change_intake(
    payload: ChangeIntakeRequest,
) -> SuccessResponse[ChangeIntakeData]:
    data = process_change_intake(payload)
    return SuccessResponse(status="ok", data=data, meta=intake_meta())
