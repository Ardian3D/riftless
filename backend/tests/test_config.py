"""Configuration loader tests for the RIFTLESS backend foundation."""

from __future__ import annotations

import os

import pytest

from app.core.config import Settings, clear_settings_cache, get_settings, load_settings
from app.main import create_app


def test_default_configuration_loads() -> None:
    settings = Settings()

    assert settings.app_name == "RIFTLESS API"
    assert settings.app_environment == "development"
    assert settings.app_version == "0.1.0"
    assert settings.api_prefix == ""
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.debug is False


def test_environment_variable_overrides() -> None:
    os.environ["RIFTLESS_APP_ENV"] = "staging"
    os.environ["RIFTLESS_APP_VERSION"] = "2.0.0-rc1"
    os.environ["RIFTLESS_API_PREFIX"] = "api/v1"
    os.environ["RIFTLESS_HOST"] = "0.0.0.0"
    os.environ["RIFTLESS_PORT"] = "9001"
    os.environ["RIFTLESS_DEBUG"] = "true"

    clear_settings_cache()
    settings = load_settings()

    assert settings.app_environment == "staging"
    assert settings.app_version == "2.0.0-rc1"
    assert settings.api_prefix == "/api/v1"
    assert settings.host == "0.0.0.0"
    assert settings.port == 9001
    assert settings.debug is True


def test_invalid_port_fails_configuration_loading() -> None:
    os.environ["RIFTLESS_PORT"] = "99999"
    clear_settings_cache()

    with pytest.raises(ValueError) as exc_info:
        load_settings()

    message = str(exc_info.value)
    assert "port" in message.lower()
    assert "Invalid RIFTLESS backend configuration" in message
    # Failure message must not dump raw environment values.
    assert "99999" not in message
    assert "RIFTLESS_PORT=99999" not in message
    assert "os.environ" not in message.lower()


def test_invalid_environment_label_fails_without_leaking_values() -> None:
    os.environ["RIFTLESS_APP_ENV"] = "not-a-real-env"
    clear_settings_cache()

    with pytest.raises(ValueError) as exc_info:
        load_settings()

    message = str(exc_info.value)
    assert "app_environment" in message
    assert "not-a-real-env" not in message
    assert "secret" not in message.lower()


def test_settings_cache_can_be_reset_between_loads() -> None:
    os.environ["RIFTLESS_APP_VERSION"] = "cache-a"
    clear_settings_cache()
    first = get_settings()
    assert first.app_version == "cache-a"

    os.environ["RIFTLESS_APP_VERSION"] = "cache-b"
    # Without clear, the lru_cache on get_settings still returns the prior value.
    second_cached = get_settings()
    assert second_cached.app_version == "cache-a"
    assert second_cached is first

    clear_settings_cache()
    third = get_settings()
    assert third.app_version == "cache-b"
    assert third is not first


def test_create_app_does_not_require_external_systems() -> None:
    """Application factory needs only local settings — no network/db/AI."""
    clear_settings_cache()
    settings = Settings(
        app_environment="development",
        app_version="import-safe",
        api_prefix="",
        host="127.0.0.1",
        port=8000,
        debug=False,
    )
    application = create_app(settings=settings)

    assert application.title == "RIFTLESS API"
    assert application.version == "import-safe"
    assert application.state.settings is settings
