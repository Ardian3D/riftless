"""Application error primitives and FastAPI exception handlers.

All client-facing failures use the standard error envelope:

    {
      "status": "error",
      "error": {"code": "...", "message": "...", "details": ...}
    }

Handlers never forward tracebacks, exception class names, raw exception
messages (for unexpected errors), environment values, or Starlette/FastAPI
internal detail strings such as ``"Not Found"``.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.common import ErrorBody, ErrorResponse


class ErrorCode(str, Enum):
    """Machine-readable error codes for the backend foundation."""

    CONFIGURATION_ERROR = "configuration_error"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    INTERNAL_ERROR = "internal_error"


class AppError(Exception):
    """Base application error that maps cleanly to the error response contract."""

    def __init__(
        self,
        *,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def error_response(
    *,
    code: str,
    message: str,
    status_code: int,
    details: Any = None,
) -> JSONResponse:
    """Build a JSONResponse that follows the standard error contract."""
    payload = ErrorResponse(
        status="error",
        error=ErrorBody(code=code, message=message, details=details),
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
    )


def _safe_validation_details(exc: RequestValidationError) -> list[dict[str, Any]]:
    """Extract limited, client-safe field errors from a validation failure.

    Includes only location, message, and type. Omits ``input``, ``ctx``,
    ``url``, and any other potentially sensitive or verbose fields.
    """
    safe: list[dict[str, Any]] = []
    for error in exc.errors():
        safe.append(
            {
                "loc": list(error.get("loc", ())),
                "msg": error.get("msg"),
                "type": error.get("type"),
            }
        )
    return safe


def register_exception_handlers(app: FastAPI) -> None:
    """Attach consistent exception handlers to a FastAPI application."""

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return error_response(
            code=exc.code.value,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return error_response(
            code=ErrorCode.VALIDATION_ERROR.value,
            message="The request could not be validated.",
            status_code=422,
            details=_safe_validation_details(exc),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        _request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        if exc.status_code == 404:
            # Never forward Starlette/FastAPI internal detail strings.
            return error_response(
                code=ErrorCode.NOT_FOUND.value,
                message="The requested resource was not found.",
                status_code=404,
                details=None,
            )

        if exc.status_code == 422:
            return error_response(
                code=ErrorCode.VALIDATION_ERROR.value,
                message="The request could not be validated.",
                status_code=422,
                details=None,
            )

        # Other HTTPException paths stay on the standard envelope without
        # leaking internal detail payloads, exception objects, or routes.
        if 400 <= exc.status_code < 500:
            return error_response(
                code=ErrorCode.VALIDATION_ERROR.value,
                message="The request could not be completed.",
                status_code=exc.status_code,
                details=None,
            )

        return error_response(
            code=ErrorCode.INTERNAL_ERROR.value,
            message="An unexpected error occurred.",
            status_code=exc.status_code if exc.status_code >= 500 else 500,
            details=None,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        # Keep the original exception bound for server-side diagnosis
        # (debuggers, future structured logging). Never expose class name,
        # message, or traceback to the client.
        _ = exc
        return error_response(
            code=ErrorCode.INTERNAL_ERROR.value,
            message="An unexpected error occurred.",
            status_code=500,
            details=None,
        )
