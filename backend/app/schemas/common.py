"""Standard success and error response shapes for the RIFTLESS API."""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Envelope for successful API responses."""

    status: Literal["ok"] = "ok"
    data: T
    meta: dict[str, Any] | None = Field(
        default=None,
        description="Optional response metadata. May be null.",
    )


class ErrorBody(BaseModel):
    """Machine-readable error payload nested under status=error."""

    code: str = Field(description="Machine-readable error code.")
    message: str = Field(description="Safe, client-facing error message.")
    details: Any = Field(
        default=None,
        description="Optional structured details. May be null. Never includes tracebacks.",
    )


class ErrorResponse(BaseModel):
    """Envelope for failed API responses."""

    status: Literal["error"] = "error"
    error: ErrorBody
