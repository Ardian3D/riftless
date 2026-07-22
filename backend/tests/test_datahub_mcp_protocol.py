from __future__ import annotations

import json

import pytest

from app.integrations.datahub.config import DATAHUB_MCP_PROTOCOL_VERSION
from app.integrations.datahub.mcp_protocol import (
    DataHubMCPProtocolError, build_initialize_request, build_initialized_notification,
    parse_jsonrpc_response, parse_sse_response, parse_strict_json_object, serialize_jsonrpc,
)


def response(result: dict, request_id: int = 1) -> bytes:
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}).encode()


def test_exact_initialize_request_and_notification() -> None:
    request = build_initialize_request()
    assert request.model_dump(exclude_none=True) == {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": DATAHUB_MCP_PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "riftless", "version": "1.0.0"}}}
    assert serialize_jsonrpc(request).decode() == '{"id":1,"jsonrpc":"2.0","method":"initialize","params":{"capabilities":{},"clientInfo":{"name":"riftless","version":"1.0.0"},"protocolVersion":"2025-11-25"}}'
    assert build_initialized_notification().model_dump(exclude_none=True) == {"jsonrpc": "2.0", "method": "notifications/initialized"}


@pytest.mark.parametrize("payload", [
    b'{"jsonrpc":"2.0","id":1,"result":{},"result":{}}', b"NaN", b"Infinity", b"-Infinity",
    b"```json\n{}\n```", b"prose {}", b"{} {}", b"\x00{}", b"[]",
])
def test_strict_json_rejects_unsafe_shapes(payload: bytes) -> None:
    with pytest.raises((DataHubMCPProtocolError, ValueError)): parse_strict_json_object(payload)


def test_duplicate_keys_nested_and_error_data_not_exposed() -> None:
    with pytest.raises(DataHubMCPProtocolError): parse_strict_json_object(b'{"a":{"x":1,"x":2}}')
    parsed = parse_jsonrpc_response(b'{"jsonrpc":"2.0","id":1,"error":{"code":-1,"message":"bad","data":{"secret":"x"}}}', expected_id=1)
    assert parsed.error is not None and parsed.error.message == "bad"
    assert not hasattr(parsed.error, "data")


@pytest.mark.parametrize("payload", [
    b'{"jsonrpc":"1.0","id":1,"result":{}}', b'{"jsonrpc":"2.0","id":2,"result":{}}',
    b'{"jsonrpc":"2.0","id":1,"result":{},"error":{"code":1,"message":"x"}}',
    b'{"jsonrpc":"2.0","id":1,"error":{"code":"1","message":"x"}}',
    b'{"jsonrpc":"2.0","id":1,"result":[]}',
])
def test_response_contract_rejects_invalid_forms(payload: bytes) -> None:
    with pytest.raises(DataHubMCPProtocolError): parse_jsonrpc_response(payload, expected_id=1)


def test_json_response_accepts_result() -> None:
    parsed = parse_jsonrpc_response(response({"protocolVersion": DATAHUB_MCP_PROTOCOL_VERSION}), expected_id=1)
    assert parsed.result == {"protocolVersion": DATAHUB_MCP_PROTOCOL_VERSION}


def test_sse_single_multiline_comments_and_notifications() -> None:
    body = b": keepalive\r\nevent: message\r\ndata: {\"jsonrpc\":\"2.0\",\r\ndata: \"id\":1,\"result\":{}}\r\n\r\n"
    assert parse_sse_response(body, expected_id=1).result == {}
    body = b"data: {\"jsonrpc\":\"2.0\",\"method\":\"notifications/progress\"}\n\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{}}\n\n"
    assert parse_sse_response(body, expected_id=1).request_id == 1


@pytest.mark.parametrize("body", [
    b"data: {\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{}}\n\n",
    b"data: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{}}\n\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{}}\n\n",
    b"data: {\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"sampling/createMessage\"}\n\n",
    b"data: {bad}\n\n", b"field-without-colon\n\n", b"event: x\n\n",
])
def test_sse_rejects_invalid_or_unsafe_events(body: bytes) -> None:
    with pytest.raises(DataHubMCPProtocolError): parse_sse_response(body, expected_id=1)


def test_sse_limits() -> None:
    with pytest.raises(DataHubMCPProtocolError): parse_sse_response(b"data: " + b"x" * 65_537 + b"\n\n", expected_id=1)
    with pytest.raises(DataHubMCPProtocolError): parse_sse_response(b"data: " + b"x" * 8_193 + b"\n\n", expected_id=1)
