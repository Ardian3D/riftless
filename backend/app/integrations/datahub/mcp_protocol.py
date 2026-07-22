"""Strict internal MCP JSON-RPC and bounded Streamable HTTP response contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

from .config import DATAHUB_MCP_MAX_RESPONSE_BYTES, DATAHUB_MCP_PROTOCOL_VERSION

_MAX_METHOD = 256
_MAX_MESSAGE = 512
_MAX_SERVER_NAME = 256
_MAX_SERVER_VERSION = 128
_MAX_SESSION_ID = 256


class DataHubMCPProtocolError(ValueError):
    """Safe protocol error with stable code and retry classification."""

    _RETRYABLE = frozenset({"timeout", "network_unavailable", "rate_limited", "provider_unavailable", "session_expired"})

    def __init__(self, code: str, message: str, *, retryable: bool | None = None) -> None:
        self.code = code
        self.message = message
        self.retryable = code in self._RETRYABLE if retryable is None else retryable
        super().__init__(message)


def _reject_constant(value: str) -> None:
    raise ValueError("non-standard JSON number")


def _duplicate_key(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def parse_strict_json_object(payload: bytes | str) -> dict[str, Any]:
    """Decode exactly one strict UTF-8 JSON object without retaining raw text."""
    if isinstance(payload, bytes):
        try:
            text = payload.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise DataHubMCPProtocolError("invalid_utf8", "MCP response encoding is invalid.") from None
    elif isinstance(payload, str):
        text = payload
    else:
        raise DataHubMCPProtocolError("invalid_json", "MCP response JSON is invalid.")
    if not text.strip() or "\x00" in text:
        raise DataHubMCPProtocolError("invalid_json", "MCP response JSON is invalid.")
    try:
        value = json.loads(text, object_pairs_hook=_duplicate_key, parse_constant=_reject_constant)
    except (json.JSONDecodeError, ValueError, TypeError):
        raise DataHubMCPProtocolError("invalid_json", "MCP response JSON is invalid.") from None
    if not isinstance(value, dict):
        raise DataHubMCPProtocolError("invalid_json", "MCP response must be a JSON object.")
    return value


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MCPRequest(_Strict):
    jsonrpc: str = "2.0"
    id: StrictInt = Field(gt=0)
    method: str = Field(min_length=1, max_length=_MAX_METHOD)
    params: dict[str, Any] | None = None

    @field_validator("jsonrpc")
    @classmethod
    def version_ok(cls, value: str) -> str:
        if value != "2.0": raise ValueError("jsonrpc must be 2.0")
        return value

    @field_validator("method")
    @classmethod
    def method_ok(cls, value: str) -> str:
        value = value.strip()
        if not value: raise ValueError("method must not be blank")
        if "\x00" in value or any(ord(c) < 32 for c in value): raise ValueError("method contains control characters")
        return value


class MCPNotification(_Strict):
    jsonrpc: str = "2.0"
    method: str = Field(min_length=1, max_length=_MAX_METHOD)
    params: dict[str, Any] | None = None

    @field_validator("jsonrpc")
    @classmethod
    def version_ok(cls, value: str) -> str:
        if value != "2.0": raise ValueError("jsonrpc must be 2.0")
        return value

    @field_validator("method")
    @classmethod
    def method_ok(cls, value: str) -> str:
        value = value.strip()
        if not value: raise ValueError("method must not be blank")
        return value


class MCPErrorSummary(_Strict):
    code: int
    message: str = Field(min_length=1, max_length=_MAX_MESSAGE)

    @field_validator("code")
    @classmethod
    def code_ok(cls, value: int) -> int:
        if isinstance(value, bool): raise ValueError("error code must be integer")
        return value

    @field_validator("message")
    @classmethod
    def message_ok(cls, value: str) -> str:
        value = value.strip()
        if not value or "\x00" in value or any(ord(c) < 32 and c not in "\t\n\r" for c in value): raise ValueError("error message is invalid")
        return value


@dataclass(frozen=True)
class MCPResponse:
    request_id: int
    result: dict[str, Any] | None = None
    error: MCPErrorSummary | None = None


def build_initialize_request() -> MCPRequest:
    return MCPRequest(id=1, method="initialize", params={"protocolVersion": DATAHUB_MCP_PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "riftless", "version": "1.0.0"}})


def build_initialized_notification() -> MCPNotification:
    return MCPNotification(method="notifications/initialized")


def serialize_jsonrpc(value: BaseModel) -> bytes:
    try:
        return json.dumps(value.model_dump(exclude_none=True), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        raise DataHubMCPProtocolError("invalid_json", "MCP request serialization failed.") from None


def parse_jsonrpc_response(payload: bytes | str, *, expected_id: int) -> MCPResponse:
    data = parse_strict_json_object(payload)
    if "method" in data:
        raise DataHubMCPProtocolError("server_request_unsupported", "MCP server request is unsupported.")
    if data.get("jsonrpc") != "2.0" or data.get("id") != expected_id:
        raise DataHubMCPProtocolError("response_id_mismatch", "MCP response does not match the request.")
    has_result, has_error = "result" in data, "error" in data
    if has_result == has_error:
        raise DataHubMCPProtocolError("invalid_jsonrpc", "MCP response result/error shape is invalid.")
    if has_result:
        if not isinstance(data["result"], dict): raise DataHubMCPProtocolError("invalid_jsonrpc", "MCP response result is invalid.")
        return MCPResponse(request_id=expected_id, result=data["result"])
    error = data["error"]
    if not isinstance(error, dict) or not isinstance(error.get("code"), int) or isinstance(error.get("code"), bool) or not isinstance(error.get("message"), str):
        raise DataHubMCPProtocolError("invalid_jsonrpc", "MCP response error is invalid.")
    try:
        summary = MCPErrorSummary(code=error["code"], message=error["message"])
    except ValueError:
        raise DataHubMCPProtocolError("invalid_jsonrpc", "MCP response error is invalid.") from None
    return MCPResponse(request_id=expected_id, error=summary)


def _content_type(headers: Mapping[str, str]) -> tuple[str, str | None]:
    raw = next((v for k, v in headers.items() if k.lower() == "content-type"), "")
    parts = [part.strip() for part in raw.split(";")]
    if not parts or not parts[0]: raise DataHubMCPProtocolError("invalid_content_type", "MCP response content type is invalid.")
    charset = None
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            if key.strip().lower() == "charset": charset = value.strip().strip('"')
    if charset is not None and charset.lower() != "utf-8": raise DataHubMCPProtocolError("invalid_content_type", "MCP response charset is unsupported.")
    return parts[0].lower(), charset


def parse_http_response(response: Any, *, expected_id: int) -> MCPResponse:
    if len(response.body) > DATAHUB_MCP_MAX_RESPONSE_BYTES: raise DataHubMCPProtocolError("response_too_large", "MCP response is too large.")
    encoding = next((v for k, v in response.headers.items() if k.lower() == "content-encoding"), "").strip().lower()
    if encoding not in {"", "identity"}: raise DataHubMCPProtocolError("unsupported_content_encoding", "MCP response encoding is unsupported.")
    content_type, _ = _content_type(response.headers)
    if content_type == "application/json": return parse_jsonrpc_response(response.body, expected_id=expected_id)
    if content_type == "text/event-stream": return parse_sse_response(response.body, expected_id=expected_id)
    raise DataHubMCPProtocolError("invalid_content_type", "MCP response content type is unsupported.")


def parse_sse_response(payload: bytes, *, expected_id: int) -> MCPResponse:
    if len(payload) > DATAHUB_MCP_MAX_RESPONSE_BYTES: raise DataHubMCPProtocolError("response_too_large", "MCP response is too large.")
    try: text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError: raise DataHubMCPProtocolError("invalid_utf8", "MCP response encoding is invalid.") from None
    events: list[dict[str, Any]] = []
    data_lines: list[str] = []
    event_bytes = 0
    event_name: str | None = None
    def dispatch() -> None:
        nonlocal data_lines, event_bytes, event_name
        if not data_lines:
            data_lines, event_name, event_bytes = [], None, 0
            return
        if event_bytes > 65_536: raise DataHubMCPProtocolError("invalid_sse", "MCP SSE event is too large.")
        events.append(parse_strict_json_object("\n".join(data_lines)))
        data_lines, event_name, event_bytes = [], None, 0
        if len(events) > 64: raise DataHubMCPProtocolError("invalid_sse", "MCP SSE event limit exceeded.")
    for raw_line in text.splitlines(keepends=True):
        line_bytes = len(raw_line.encode("utf-8"))
        if line_bytes > 8192: raise DataHubMCPProtocolError("invalid_sse", "MCP SSE line is too large.")
        if raw_line.endswith("\r\n"): line = raw_line[:-2]
        elif raw_line.endswith("\n"): line = raw_line[:-1]
        elif raw_line.endswith("\r"): line = raw_line[:-1]
        else: line = raw_line
        if line == "": dispatch(); continue
        if line.startswith(":"): continue
        field, separator, value = line.partition(":")
        if not separator: raise DataHubMCPProtocolError("invalid_sse", "MCP SSE framing is invalid.")
        if field == "data":
            if value.startswith(" "): value = value[1:]
            data_lines.append(value); event_bytes += len(value.encode("utf-8"))
        elif field == "event": event_name = value
        elif field in {"id", "retry"}: continue
        else: raise DataHubMCPProtocolError("invalid_sse", "MCP SSE field is unsupported.")
    if data_lines: dispatch()
    if not events: raise DataHubMCPProtocolError("invalid_sse", "MCP SSE contained no response.")
    matching: list[MCPResponse] = []
    for event in events:
        if "method" in event:
            if "id" in event: raise DataHubMCPProtocolError("server_request_unsupported", "MCP server request is unsupported.")
            if event.get("method") not in {"notifications/progress", "notifications/message"}: raise DataHubMCPProtocolError("server_request_unsupported", "MCP server notification is unsupported.")
            continue
        try: matching.append(_response_from_data(event, expected_id))
        except DataHubMCPProtocolError: raise
    if len(matching) != 1: raise DataHubMCPProtocolError("response_id_mismatch", "MCP SSE response did not match exactly once.")
    return matching[0]


def _response_from_data(data: dict[str, Any], expected_id: int) -> MCPResponse:
    if data.get("jsonrpc") != "2.0" or isinstance(data.get("id"), bool) or data.get("id") != expected_id: raise DataHubMCPProtocolError("response_id_mismatch", "MCP response does not match the request.")
    return parse_jsonrpc_response(json.dumps(data, ensure_ascii=False, separators=(",", ":")), expected_id=expected_id)
