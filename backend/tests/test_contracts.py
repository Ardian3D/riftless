"""Response envelope and schema consistency tests."""

from __future__ import annotations

from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.main import app, create_app
from app.schemas.common import ErrorBody, ErrorResponse, SuccessResponse


def _client() -> TestClient:
    return TestClient(app)


def test_success_response_schema_shape() -> None:
    payload = SuccessResponse(data={"value": 1}, meta={"source": "unit"})
    dumped = payload.model_dump()

    assert set(dumped.keys()) == {"status", "data", "meta"}
    assert dumped["status"] == "ok"
    assert dumped["data"] == {"value": 1}
    assert dumped["meta"] == {"source": "unit"}


def test_error_response_schema_allows_null_details() -> None:
    payload = ErrorResponse(
        error=ErrorBody(
            code="not_found",
            message="The requested resource was not found.",
            details=None,
        )
    )
    dumped = payload.model_dump()

    assert set(dumped.keys()) == {"status", "error"}
    assert dumped["status"] == "error"
    assert dumped["error"]["code"] == "not_found"
    assert dumped["error"]["details"] is None
    assert isinstance(dumped["error"]["message"], str)


def test_health_success_envelope_keys() -> None:
    body = _client().get("/health").json()
    assert set(body.keys()) == {"status", "data", "meta"}
    assert body["status"] == "ok"
    assert body["meta"] is not None


def test_ready_success_envelope_keys() -> None:
    body = _client().get("/ready").json()
    assert set(body.keys()) == {"status", "data", "meta"}
    assert body["status"] == "ok"
    assert body["data"]["scope"] == "local_application_and_configuration"


def test_error_envelope_keys_on_not_found() -> None:
    body = _client().get("/missing-path-for-contract").json()
    assert set(body.keys()) == {"status", "error"}
    assert body["status"] == "error"
    assert set(body["error"].keys()) == {"code", "message", "details"}
    assert body["error"]["code"] == "not_found"
    assert body["error"]["details"] is None


def test_validation_error_has_machine_readable_code() -> None:
    settings = Settings(app_version="contract-test")
    application = create_app(settings=settings)

    class Item(BaseModel):
        quantity: int = Field(ge=1)

    @application.post("/__test_only/contract-item")
    async def create_item(item: Item) -> dict[str, int]:
        return {"quantity": item.quantity}

    client = TestClient(application)
    body = client.post("/__test_only/contract-item", json={"quantity": 0}).json()

    assert body["status"] == "error"
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["error"]["code"], str)
    assert body["error"]["code"].isidentifier() or "_" in body["error"]["code"]
