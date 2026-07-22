from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.integrations.datahub.config import (
    DATAHUB_MCP_MAX_REQUEST_BYTES, DATAHUB_MCP_MAX_RESPONSE_BYTES,
    DATAHUB_MCP_PROTOCOL_VERSION, DATAHUB_MCP_TIMEOUT_SECONDS,
    DataHubMCPAuthMode, DataHubMCPConfigurationError, DataHubMCPConfig,
    load_datahub_mcp_config, validate_datahub_mcp_endpoint,
)

REMOTE = "https://datahub.example.com/integrations/ai/mcp"


def test_missing_and_blank_configuration_is_optional() -> None:
    assert load_datahub_mcp_config({}) is None
    assert load_datahub_mcp_config({"DATAHUB_MCP_URL": " ", "DATAHUB_TOKEN": " \t"}) is None


def test_token_without_url_is_safe_error() -> None:
    with pytest.raises(DataHubMCPConfigurationError) as exc:
        load_datahub_mcp_config({"DATAHUB_TOKEN": "secret-token"})
    assert exc.value.code == "incomplete_configuration"
    assert "secret-token" not in str(exc.value)


def test_remote_requires_https_and_token() -> None:
    assert load_datahub_mcp_config({"DATAHUB_MCP_URL": REMOTE, "DATAHUB_TOKEN": "secret-token"}).auth_mode == DataHubMCPAuthMode.BEARER_TOKEN
    with pytest.raises(DataHubMCPConfigurationError): load_datahub_mcp_config({"DATAHUB_MCP_URL": REMOTE})
    with pytest.raises(DataHubMCPConfigurationError): load_datahub_mcp_config({"DATAHUB_MCP_URL": REMOTE, "DATAHUB_TOKEN": " "})
    with pytest.raises(DataHubMCPConfigurationError): load_datahub_mcp_config({"DATAHUB_MCP_URL": "http://tenant.example.com/mcp", "DATAHUB_TOKEN": "x"})


@pytest.mark.parametrize("url", [
    "http://localhost:8000/mcp", "http://127.0.0.1:8000/mcp", "http://[::1]:8000/mcp",
    "https://tenant.acryl.io/integrations/ai/mcp", "https://tenant.acryl.io/integrations/ai/mcp/", "https://datahub.example.com/mcp",
])
def test_valid_endpoints(url: str) -> None:
    assert validate_datahub_mcp_endpoint(url) == url


@pytest.mark.parametrize("url", [
    "file:///mcp", "ftp://example.com/mcp", "relative/mcp", "https:///mcp", "https://user:password@example.com/mcp",
    "https://example.com/mcp?token=secret", "https://example.com/mcp#fragment", "https://example.com/not-mcp",
    "https://example.com/mcp/../other", "https://example.com/%2fother", "https://example.com/mcp%5cother",
    "https://example.com/mcp%2e%2e/other", "http://0.0.0.0:8000/mcp", "http://192.168.1.2:8000/mcp", "http://169.254.169.254/mcp",
    "https://example.com:0/mcp", "https://example.com:65536/mcp", "https://example.com/mcp\\other",
])
def test_invalid_endpoints(url: str) -> None:
    with pytest.raises(DataHubMCPConfigurationError): validate_datahub_mcp_endpoint(url)


def test_endpoint_bounds_and_no_dns() -> None:
    with pytest.raises(DataHubMCPConfigurationError): validate_datahub_mcp_endpoint("https://" + "a" * 2040 + ".com/mcp")


def test_config_is_immutable_secret_safe_and_constants_locked() -> None:
    config = load_datahub_mcp_config({"DATAHUB_MCP_URL": REMOTE, "DATAHUB_TOKEN": "secret-token"})
    assert config is not None
    assert "secret-token" not in repr(config)
    assert "secret-token" not in str(config)
    assert config.protocol_version == DATAHUB_MCP_PROTOCOL_VERSION
    assert config.timeout_seconds == DATAHUB_MCP_TIMEOUT_SECONDS
    assert config.max_request_bytes == DATAHUB_MCP_MAX_REQUEST_BYTES
    assert config.max_response_bytes == DATAHUB_MCP_MAX_RESPONSE_BYTES
    with pytest.raises(ValidationError): DataHubMCPConfig(endpoint_url=REMOTE, auth_mode="bearer_token", access_token="x", timeout_seconds=1)
    with pytest.raises(ValidationError): DataHubMCPConfig(endpoint_url=REMOTE, auth_mode="bearer_token", access_token="x", token="bad")


def test_loopback_auth_modes_and_input_mapping_are_safe() -> None:
    source = {"DATAHUB_MCP_URL": "http://localhost:8000/mcp", "DATAHUB_TOKEN": " secret "}
    before = dict(source)
    config = load_datahub_mcp_config(source)
    assert config is not None and config.auth_mode == DataHubMCPAuthMode.BEARER_TOKEN
    assert source == before
    no_auth = load_datahub_mcp_config({"DATAHUB_MCP_URL": "http://localhost:8000/mcp"})
    assert no_auth is not None and no_auth.auth_mode == DataHubMCPAuthMode.NONE and no_auth.access_token is None
    with pytest.raises(ValidationError): DataHubMCPConfig(endpoint_url="http://localhost:8000/mcp", auth_mode="none", access_token="x")


def test_only_explicit_loader_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATAHUB_MCP_URL", REMOTE)
    monkeypatch.setenv("DATAHUB_TOKEN", "secret-token")
    assert load_datahub_mcp_config() is not None
