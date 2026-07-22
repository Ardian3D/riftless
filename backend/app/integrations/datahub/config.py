"""Explicit, secret-safe DataHub MCP configuration boundary."""

from __future__ import annotations

import ipaddress
import re
from enum import Enum
from types import MappingProxyType
from typing import Mapping
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

DATAHUB_MCP_PROTOCOL_VERSION = "2025-11-25"
DATAHUB_MCP_TIMEOUT_SECONDS = 30.0
DATAHUB_MCP_MAX_REQUEST_BYTES = 65_536
DATAHUB_MCP_MAX_RESPONSE_BYTES = 1_048_576
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class DataHubMCPConfigurationError(ValueError):
    """Safe configuration error; never includes endpoint or secret values."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class DataHubMCPAuthMode(str, Enum):
    BEARER_TOKEN = "bearer_token"
    NONE = "none"


def _safe_url_text(value: str) -> str:
    if not isinstance(value, str):
        raise DataHubMCPConfigurationError("invalid_endpoint", "DataHub MCP endpoint is invalid.")
    if not value or len(value) > 2048 or value != value.strip():
        raise DataHubMCPConfigurationError("invalid_endpoint", "DataHub MCP endpoint is invalid.")
    if _CONTROL.search(value) or any(ch.isspace() for ch in value) or "\\" in value:
        raise DataHubMCPConfigurationError("invalid_endpoint", "DataHub MCP endpoint is invalid.")
    if re.search(r"%2f|%5c|%2e", value, flags=re.IGNORECASE):
        raise DataHubMCPConfigurationError("invalid_endpoint", "DataHub MCP endpoint is invalid.")
    return value


def validate_datahub_mcp_endpoint(value: str) -> str:
    """Validate a server-controlled MCP URL without DNS resolution."""
    raw = _safe_url_text(value)
    try:
        parts = urlsplit(raw)
        hostname = parts.hostname
        port = parts.port
    except (ValueError, UnicodeError):
        raise DataHubMCPConfigurationError("invalid_endpoint", "DataHub MCP endpoint is invalid.") from None
    if parts.scheme not in {"http", "https"} or not hostname:
        raise DataHubMCPConfigurationError("invalid_endpoint", "DataHub MCP endpoint is invalid.")
    if parts.username is not None or parts.password is not None:
        raise DataHubMCPConfigurationError("invalid_endpoint", "DataHub MCP endpoint is invalid.")
    if parts.query or parts.fragment or not parts.path:
        raise DataHubMCPConfigurationError("invalid_endpoint", "DataHub MCP endpoint is invalid.")
    path = parts.path
    segments = path.rstrip("/").split("/")
    if not segments or segments[-1] != "mcp" or any(segment in {".", ".."} for segment in segments):
        raise DataHubMCPConfigurationError("invalid_endpoint", "DataHub MCP endpoint is invalid.")
    if port is not None and not 1 <= port <= 65_535:
        raise DataHubMCPConfigurationError("invalid_endpoint", "DataHub MCP endpoint is invalid.")
    normalized_host = hostname.lower().rstrip(".")
    is_loopback = normalized_host in _LOOPBACK_HOSTS
    if not is_loopback:
        try:
            is_loopback = ipaddress.ip_address(normalized_host).is_loopback
        except ValueError:
            is_loopback = False
    if parts.scheme == "http" and not is_loopback:
        raise DataHubMCPConfigurationError("insecure_remote_endpoint", "Remote DataHub MCP endpoints require HTTPS.")
    return raw


class DataHubMCPConfig(BaseModel):
    """Immutable server-owned MCP transport configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True, repr=True)

    endpoint_url: str
    auth_mode: DataHubMCPAuthMode
    access_token: SecretStr | None = None
    protocol_version: str = DATAHUB_MCP_PROTOCOL_VERSION
    timeout_seconds: float = DATAHUB_MCP_TIMEOUT_SECONDS
    max_request_bytes: int = DATAHUB_MCP_MAX_REQUEST_BYTES
    max_response_bytes: int = DATAHUB_MCP_MAX_RESPONSE_BYTES

    @field_validator("endpoint_url")
    @classmethod
    def endpoint_ok(cls, value: str) -> str:
        return validate_datahub_mcp_endpoint(value)

    @field_validator("access_token")
    @classmethod
    def token_ok(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return None
        token = value.get_secret_value()
        if not token or token != token.strip() or _CONTROL.search(token):
            raise DataHubMCPConfigurationError("incomplete_configuration", "DataHub MCP configuration is incomplete.")
        if len(token) > 4096:
            raise DataHubMCPConfigurationError("incomplete_configuration", "DataHub MCP configuration is incomplete.")
        return SecretStr(token)

    @model_validator(mode="after")
    def constants_and_auth(self) -> "DataHubMCPConfig":
        if self.protocol_version != DATAHUB_MCP_PROTOCOL_VERSION or self.timeout_seconds != DATAHUB_MCP_TIMEOUT_SECONDS or self.max_request_bytes != DATAHUB_MCP_MAX_REQUEST_BYTES or self.max_response_bytes != DATAHUB_MCP_MAX_RESPONSE_BYTES:
            raise DataHubMCPConfigurationError("invalid_configuration", "DataHub MCP transport settings are server-owned.")
        host = urlsplit(self.endpoint_url).hostname or ""
        is_loopback = host.lower().rstrip(".") in _LOOPBACK_HOSTS
        try:
            is_loopback = is_loopback or ipaddress.ip_address(host).is_loopback
        except ValueError:
            pass
        if self.auth_mode == DataHubMCPAuthMode.BEARER_TOKEN and self.access_token is None:
            raise DataHubMCPConfigurationError("authentication_required", "DataHub MCP authentication is required.")
        if self.auth_mode == DataHubMCPAuthMode.NONE and self.access_token is not None:
            raise DataHubMCPConfigurationError("invalid_configuration", "DataHub MCP authentication mode is invalid.")
        if not is_loopback and self.auth_mode != DataHubMCPAuthMode.BEARER_TOKEN:
            raise DataHubMCPConfigurationError("authentication_required", "DataHub MCP authentication is required.")
        return self


def load_datahub_mcp_config(environ: Mapping[str, str] | None = None) -> DataHubMCPConfig | None:
    """Load only the two server-side variables when explicitly called."""
    source = MappingProxyType(dict(environ)) if environ is not None else None
    import os

    values = source if source is not None else os.environ
    raw_url = values.get("DATAHUB_MCP_URL", "")
    raw_token = values.get("DATAHUB_TOKEN", "")
    url = raw_url.strip() if isinstance(raw_url, str) else ""
    token = raw_token.strip() if isinstance(raw_token, str) else ""
    if not url and not token:
        return None
    if not url:
        raise DataHubMCPConfigurationError("incomplete_configuration", "DataHub MCP configuration is incomplete.")
    endpoint = validate_datahub_mcp_endpoint(url)
    host = urlsplit(endpoint).hostname or ""
    is_loopback = host.lower().rstrip(".") in _LOOPBACK_HOSTS
    try:
        is_loopback = is_loopback or ipaddress.ip_address(host).is_loopback
    except ValueError:
        pass
    if not is_loopback and not token:
        raise DataHubMCPConfigurationError("authentication_required", "DataHub MCP authentication is required.")
    mode = DataHubMCPAuthMode.BEARER_TOKEN if token else DataHubMCPAuthMode.NONE
    return DataHubMCPConfig(endpoint_url=endpoint, auth_mode=mode, access_token=SecretStr(token) if token else None)
