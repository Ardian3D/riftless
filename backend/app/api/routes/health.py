"""Health and readiness endpoints for the backend foundation.

These endpoints only report local process and configuration status.
They intentionally do not probe databases, AI providers, DataHub,
GitHub, validators, or other external dependencies.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from app.core.config import Settings
from app.schemas.common import SuccessResponse

router = APIRouter(tags=["health"])


def _settings_from_request(request: Request) -> Settings:
    return request.app.state.settings


@router.get(
    "/health",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Liveness probe",
    description=(
        "Returns process liveness only. Does not claim database, DataHub, "
        "GitHub, AI provider, or validator availability."
    ),
)
async def health(request: Request) -> SuccessResponse[dict[str, Any]]:
    settings = _settings_from_request(request)
    return SuccessResponse(
        status="ok",
        data={
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_environment,
            "message": "Application process is responding.",
        },
        meta={
            "probe": "liveness",
            "scope": "process_only",
        },
    )


@router.get(
    "/ready",
    response_model=SuccessResponse[dict[str, Any]],
    summary="Readiness probe (local scope)",
    description=(
        "Reports local readiness: configuration loaded and FastAPI app created. "
        "External dependencies are not checked in the foundation phase."
    ),
)
async def ready(request: Request) -> SuccessResponse[dict[str, Any]]:
    settings = _settings_from_request(request)

    checks = {
        "configuration_loaded": True,
        "fastapi_application_created": True,
    }

    return SuccessResponse(
        status="ok",
        data={
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_environment,
            "ready": all(checks.values()),
            "scope": "local_application_and_configuration",
            "checks": checks,
            "limitations": [
                "Database connectivity is not checked (not implemented).",
                "DataHub availability is not checked.",
                "GitHub availability is not checked.",
                "DeepSeek / AI provider availability is not checked.",
                "Artifact storage is not checked.",
                "Validation workers are not checked.",
            ],
            "message": (
                "Local application and configuration are ready. "
                "External dependencies are out of scope for this phase."
            ),
        },
        meta={
            "probe": "readiness",
            "scope": "local_only",
            "phase": "F4.2",
        },
    )
