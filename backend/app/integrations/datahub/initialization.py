"""MCP initialize/initialized lifecycle; no tool calls are defined here."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config import DATAHUB_MCP_PROTOCOL_VERSION, DataHubMCPConfig
from .mcp_protocol import (
    DataHubMCPProtocolError, build_initialize_request, build_initialized_notification,
    parse_http_response, serialize_jsonrpc,
)
from .transport import DataHubMCPHTTPResponse, DataHubMCPTransport, classify_http_status


def _session_id(value: str | None) -> str | None:
    if value is None: return None
    value = value.strip()
    if not 1 <= len(value) <= 256 or any(not 0x21 <= ord(c) <= 0x7E for c in value):
        raise DataHubMCPProtocolError("invalid_initialize_result", "MCP session identifier is invalid.")
    return value


class DataHubMCPSession(BaseModel):
    """Normalized negotiated session; excludes secrets and raw provider data."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    endpoint_url: str
    protocol_version: str
    server_name: str = Field(min_length=1, max_length=256)
    server_version: str = Field(min_length=1, max_length=128)
    tools_supported: bool = True
    session_id: str | None = None

    @field_validator("protocol_version")
    @classmethod
    def protocol_ok(cls, value: str) -> str:
        if value != DATAHUB_MCP_PROTOCOL_VERSION: raise ValueError("protocol version mismatch")
        return value

    @field_validator("endpoint_url")
    @classmethod
    def endpoint_nonblank(cls, value: str) -> str:
        if not value.strip(): raise ValueError("endpoint is invalid")
        return value

    @field_validator("server_name", "server_version")
    @classmethod
    def text_ok(cls, value: str) -> str:
        value = value.strip()
        if not value or "\x00" in value or any(ord(c) < 32 and c not in "\t\n\r" for c in value): raise ValueError("server information is invalid")
        return value

    @field_validator("session_id")
    @classmethod
    def session_ok(cls, value: str | None) -> str | None: return _session_id(value)


def _header(headers: Any, name: str) -> str | None:
    return next((str(v) for k, v in headers.items() if k.lower() == name.lower()), None)


def _initialize_result(response: DataHubMCPHTTPResponse, *, config: DataHubMCPConfig):
    classify_http_status(response.status_code, expects_response=True)
    parsed = parse_http_response(response, expected_id=1)
    if parsed.error is not None or parsed.result is None:
        raise DataHubMCPProtocolError("invalid_initialize_result", "MCP initialize result is invalid.")
    result = parsed.result
    if result.get("protocolVersion") != DATAHUB_MCP_PROTOCOL_VERSION or not isinstance(result.get("capabilities"), dict):
        raise DataHubMCPProtocolError("protocol_version_mismatch", "MCP protocol negotiation failed.")
    capabilities = result["capabilities"]
    if "tools" not in capabilities or not isinstance(capabilities["tools"], dict):
        raise DataHubMCPProtocolError("tools_capability_missing", "DataHub MCP tools capability is unavailable.")
    info = result.get("serverInfo")
    if not isinstance(info, dict) or not isinstance(info.get("name"), str) or not isinstance(info.get("version"), str):
        raise DataHubMCPProtocolError("invalid_initialize_result", "MCP server information is invalid.")
    name, version = info["name"].strip(), info["version"].strip()
    if not 1 <= len(name) <= 256 or not 1 <= len(version) <= 128 or any(ord(c) < 32 for c in name + version):
        raise DataHubMCPProtocolError("invalid_initialize_result", "MCP server information is invalid.")
    session_id = _session_id(_header(response.headers, "MCP-Session-Id"))
    try:
        return DataHubMCPSession(endpoint_url=config.endpoint_url, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION, server_name=name, server_version=version, tools_supported=True, session_id=session_id)
    except ValueError:
        raise DataHubMCPProtocolError("invalid_initialize_result", "MCP initialize result is invalid.") from None


def initialize_datahub_mcp(*, config: DataHubMCPConfig, transport: DataHubMCPTransport) -> DataHubMCPSession:
    """Perform exactly initialize then initialized notification, once each."""
    if not isinstance(config, DataHubMCPConfig): raise TypeError("config must be DataHubMCPConfig")
    request = serialize_jsonrpc(build_initialize_request())
    first = transport.post_request(request, session_id=None, protocol_version=None)
    session = _initialize_result(first, config=config)
    notification = serialize_jsonrpc(build_initialized_notification())
    response = transport.post_notification(notification, session_id=session.session_id, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION)
    classify_http_status(response.status_code, expects_response=False, has_session=session.session_id is not None)
    if response.body:
        raise DataHubMCPProtocolError("initialization_notification_failed", "MCP initialized notification failed.")
    return session
