"""Health, readiness, not-found, and application-import contract tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import Settings, clear_settings_cache
from app.main import app, create_app


def _client() -> TestClient:
    return TestClient(app)


def test_health_endpoint_success_contract() -> None:
    client = _client()
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert "data" in body
    assert "meta" in body
    assert body["data"]["service"] == "RIFTLESS API"
    assert body["data"]["version"]
    assert isinstance(body["data"]["version"], str)
    assert body["meta"]["probe"] == "liveness"
    assert body["meta"]["scope"] == "process_only"


def test_health_uses_configuration_version() -> None:
    settings = Settings(app_version="1.2.3-config")
    application = create_app(settings=settings)
    client = TestClient(application)

    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["data"]["version"] == "1.2.3-config"
    assert body["data"]["service"] == settings.app_name


def test_ready_endpoint_local_scope() -> None:
    client = _client()
    response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["data"]["ready"] is True
    assert body["data"]["scope"] == "local_application_and_configuration"
    assert body["data"]["checks"]["configuration_loaded"] is True
    assert body["data"]["checks"]["fastapi_application_created"] is True
    assert set(body["data"]["checks"].keys()) == {
        "configuration_loaded",
        "fastapi_application_created",
    }
    # External systems must not appear as performed checks.
    for forbidden in (
        "database",
        "datahub",
        "github",
        "deepseek",
        "gemini",
        "artifact",
        "validation_worker",
    ):
        assert forbidden not in body["data"]["checks"]

    assert isinstance(body["data"]["limitations"], list)
    assert len(body["data"]["limitations"]) > 0
    assert body["meta"]["scope"] == "local_only"
    joined = " ".join(body["data"]["limitations"]).lower()
    assert "database" in joined
    assert "datahub" in joined


def test_not_found_uses_standard_error_contract() -> None:
    client = _client()
    response = client.get("/this-route-does-not-exist")

    assert response.status_code == 404
    body = response.json()

    assert body == {
        "status": "error",
        "error": {
            "code": "not_found",
            "message": "The requested resource was not found.",
            "details": None,
        },
    }
    # Must not look like FastAPI's default {"detail": "..."} shape.
    assert "detail" not in body
    # Must never leak traceback or framework internals.
    raw = response.text.lower()
    assert "traceback" not in raw
    assert "starlette" not in raw
    assert "exception" not in raw


def test_application_import_is_side_effect_free() -> None:
    """Importing and creating the app must not require network/db/secrets."""
    clear_settings_cache()
    settings = Settings(
        app_environment="development",
        app_version="0.1.0-test",
        api_prefix="",
        host="127.0.0.1",
        port=8000,
        debug=False,
    )
    application = create_app(settings=settings)

    assert application.title == "RIFTLESS API"
    assert application.version == "0.1.0-test"
    assert application.state.settings is settings

    # Module-level app must also exist and be a FastAPI instance.
    assert app.title == "RIFTLESS API"
