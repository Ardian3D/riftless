"""Error-handler contract tests using test-only routes (not production)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.core.errors import register_exception_handlers
from app.main import create_app


class _EchoPayload(BaseModel):
    """Minimal request body used only to trigger validation errors in tests."""

    name: str = Field(min_length=1)
    count: int = Field(ge=0)


def _test_app_with_error_routes() -> FastAPI:
    """Build an isolated app with temporary routes for error-path coverage.

    These routes are intentionally absent from the production router.
    """
    settings = Settings(app_version="0.1.0-test")
    application = create_app(settings=settings)

    @application.post("/__test_only/echo")
    async def echo(payload: _EchoPayload) -> dict[str, Any]:
        return {"name": payload.name, "count": payload.count}

    @application.get("/__test_only/boom")
    async def boom() -> dict[str, Any]:
        raise RuntimeError("SECRET_INTERNAL_FAILURE_DO_NOT_LEAK")

    return application


def test_validation_error_uses_standard_contract() -> None:
    client = TestClient(_test_app_with_error_routes())
    response = client.post("/__test_only/echo", json={"name": "", "count": -1})

    assert response.status_code == 422
    body = response.json()

    assert body["status"] == "error"
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "The request could not be validated."
    assert isinstance(body["error"]["details"], list)
    assert len(body["error"]["details"]) >= 1

    for item in body["error"]["details"]:
        assert set(item.keys()) <= {"loc", "msg", "type"}
        assert "input" not in item
        assert "ctx" not in item

    raw = response.text.lower()
    assert "traceback" not in raw
    assert "exception" not in raw
    assert "detail" not in body


def test_internal_error_hides_exception_details() -> None:
    client = TestClient(
        _test_app_with_error_routes(),
        raise_server_exceptions=False,
    )
    response = client.get("/__test_only/boom")

    assert response.status_code == 500
    body = response.json()

    assert body == {
        "status": "error",
        "error": {
            "code": "internal_error",
            "message": "An unexpected error occurred.",
            "details": None,
        },
    }

    raw = response.text
    assert "SECRET_INTERNAL_FAILURE_DO_NOT_LEAK" not in raw
    assert "RuntimeError" not in raw
    assert "traceback" not in raw.lower()
    assert "detail" not in body


def test_handlers_register_on_bare_fastapi_instance() -> None:
    """Handlers remain usable when attached outside create_app (defensive)."""
    bare = FastAPI()
    register_exception_handlers(bare)

    @bare.get("/__test_only/bare-boom")
    async def bare_boom() -> dict[str, str]:
        raise ValueError("should-not-leak")

    client = TestClient(bare, raise_server_exceptions=False)
    response = client.get("/__test_only/bare-boom")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert body["error"]["details"] is None
    assert "should-not-leak" not in response.text
