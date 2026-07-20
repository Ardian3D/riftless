"""Shared Pydantic schemas for the RIFTLESS API."""

from app.schemas.common import ErrorBody, ErrorResponse, SuccessResponse

__all__ = [
    "ErrorBody",
    "ErrorResponse",
    "SuccessResponse",
]
