"""Server-side configuration loader for the RIFTLESS API.

Uses pydantic-settings with explicit RIFTLESS_ environment variable names.
Importing and loading settings must not require network access, secrets
managers, or external services.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Minimal runtime configuration for the backend foundation.

    Environment variables use the RIFTLESS_ prefix and short names defined in
    ``backend/.env.example`` (for example ``RIFTLESS_APP_ENV``). Python
    attributes keep the clearer long names (for example ``app_environment``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = Field(default="RIFTLESS API", description="Public service name.")
    app_environment: Literal["development", "staging", "production"] = Field(
        default="development",
        validation_alias=AliasChoices("app_environment", "RIFTLESS_APP_ENV"),
        description="Deployment environment label.",
    )
    app_version: str = Field(
        default="0.1.0",
        validation_alias=AliasChoices("app_version", "RIFTLESS_APP_VERSION"),
        description="Application version string.",
    )
    api_prefix: str = Field(
        default="",
        validation_alias=AliasChoices("api_prefix", "RIFTLESS_API_PREFIX"),
        description="Optional URL prefix for API routes.",
    )
    host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("host", "RIFTLESS_HOST"),
        description="Development server bind host.",
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        validation_alias=AliasChoices("port", "RIFTLESS_PORT"),
        description="Development server bind port.",
    )
    debug: bool = Field(
        default=False,
        validation_alias=AliasChoices("debug", "RIFTLESS_DEBUG"),
        description="Enable FastAPI debug mode.",
    )

    @field_validator("api_prefix")
    @classmethod
    def normalize_api_prefix(cls, value: str) -> str:
        """Normalize prefix to empty string or a leading-slash path without trailing slash."""
        cleaned = (value or "").strip()
        if not cleaned or cleaned == "/":
            return ""
        if not cleaned.startswith("/"):
            cleaned = f"/{cleaned}"
        return cleaned.rstrip("/")

    @field_validator("app_version")
    @classmethod
    def validate_app_version(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("app_version must be a non-empty string")
        return cleaned

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("host must be a non-empty string")
        return cleaned


def load_settings() -> Settings:
    """Load and validate settings.

    Raises a clear ValueError on invalid configuration without echoing
    raw environment values that might be sensitive.
    """
    try:
        return Settings()
    except ValidationError as exc:
        field_names = sorted(
            {
                str(error.get("loc", ("unknown",))[0])
                for error in exc.errors()
                if error.get("loc")
            }
        )
        fields = ", ".join(field_names) if field_names else "unknown fields"
        raise ValueError(
            f"Invalid RIFTLESS backend configuration for: {fields}. "
            "Check environment variables against backend/.env.example."
        ) from None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor used by the application factory and routes."""
    return load_settings()


def clear_settings_cache() -> None:
    """Clear the settings cache (useful for tests)."""
    get_settings.cache_clear()
