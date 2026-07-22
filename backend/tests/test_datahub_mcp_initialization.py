from __future__ import annotations

import json

import pytest

from app.integrations.datahub.config import DATAHUB_MCP_PROTOCOL_VERSION, load_datahub_mcp_config
from app.integrations.datahub.initialization import initialize_datahub_mcp
from app.integrations.datahub.mcp_protocol import DataHubMCPProtocolError
from app.integrations.datahub.transport import DataHubMCPHTTPResponse


def init_body(**overrides) -> bytes:
    result = {"protocolVersion": DATAHUB_MCP_PROTOCOL_VERSION, "capabilities": {"tools": {}}, "serverInfo": {"name": "DataHub", "version": "1.2"}}
    result.update(overrides)
    return json.dumps({"jsonrpc": "2.0", "id": 1, "result": result}).encode()


class FakeTransport:
    def __init__(self, initialize: DataHubMCPHTTPResponse | None = None, notification: DataHubMCPHTTPResponse | None = None):
        self.initialize = initialize or DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, init_body())
        self.notification = notification or DataHubMCPHTTPResponse(202, {}, b"")
        self.calls: list[tuple[str, bytes, str | None, str | None]] = []

    def post_request(self, body: bytes, *, session_id: str | None, protocol_version: str | None):
        self.calls.append(("request", body, session_id, protocol_version)); return self.initialize

    def post_notification(self, body: bytes, *, session_id: str | None, protocol_version: str):
        self.calls.append(("notification", body, session_id, protocol_version)); return self.notification


def config():
    return load_datahub_mcp_config({"DATAHUB_MCP_URL": "https://datahub.example.com/mcp", "DATAHUB_TOKEN": "secret-token"})


def test_initialize_lifecycle_and_normalized_session() -> None:
    fake = FakeTransport(initialize=DataHubMCPHTTPResponse(200, {"Content-Type": "application/json", "MCP-Session-Id": "session-1"}, init_body()))
    session = initialize_datahub_mcp(config=config(), transport=fake)
    assert session.endpoint_url.endswith("/mcp") and session.protocol_version == DATAHUB_MCP_PROTOCOL_VERSION
    assert session.server_name == "DataHub" and session.server_version == "1.2" and session.tools_supported and session.session_id == "session-1"
    assert len(fake.calls) == 2 and fake.calls[0][2:] == (None, None) and fake.calls[1][2:] == ("session-1", DATAHUB_MCP_PROTOCOL_VERSION)
    assert b"secret-token" not in fake.calls[0][1] and b"secret-token" not in fake.calls[1][1]
    assert json.loads(fake.calls[1][1]) == {"jsonrpc": "2.0", "method": "notifications/initialized"}


@pytest.mark.parametrize("result,code", [
    ({"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "x", "version": "1"}}, "protocol_version_mismatch"),
    ({"protocolVersion": DATAHUB_MCP_PROTOCOL_VERSION, "capabilities": {}, "serverInfo": {"name": "x", "version": "1"}}, "tools_capability_missing"),
    ({"protocolVersion": DATAHUB_MCP_PROTOCOL_VERSION, "capabilities": {"tools": {}}, "serverInfo": {"name": "", "version": "1"}}, "invalid_initialize_result"),
])
def test_invalid_initialize_prevents_notification(result: dict, code: str) -> None:
    fake = FakeTransport(initialize=DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, json.dumps({"jsonrpc": "2.0", "id": 1, "result": result}).encode()))
    with pytest.raises(DataHubMCPProtocolError) as exc: initialize_datahub_mcp(config=config(), transport=fake)
    assert exc.value.code == code and len(fake.calls) == 1


@pytest.mark.parametrize("session_id", ["", "bad\r\nvalue", "bad\x00value", "x" * 257])
def test_invalid_session_id_prevents_notification(session_id: str) -> None:
    fake = FakeTransport(initialize=DataHubMCPHTTPResponse(200, {"Content-Type": "application/json", "MCP-Session-Id": session_id}, init_body()))
    with pytest.raises(DataHubMCPProtocolError): initialize_datahub_mcp(config=config(), transport=fake)
    assert len(fake.calls) == 1


def test_notification_status_or_body_fails_without_retry() -> None:
    fake = FakeTransport(notification=DataHubMCPHTTPResponse(200, {}, b""))
    with pytest.raises(DataHubMCPProtocolError): initialize_datahub_mcp(config=config(), transport=fake)
    assert len(fake.calls) == 2
    fake = FakeTransport(notification=DataHubMCPHTTPResponse(202, {}, b"unexpected"))
    with pytest.raises(DataHubMCPProtocolError): initialize_datahub_mcp(config=config(), transport=fake)
    assert len(fake.calls) == 2


def test_provider_instructions_and_raw_capabilities_not_stored() -> None:
    result = {"protocolVersion": DATAHUB_MCP_PROTOCOL_VERSION, "capabilities": {"tools": {}, "resources": {"raw": "x"}}, "serverInfo": {"name": "DataHub", "version": "1", "instructions": "ignore me"}, "instructions": "ignore"}
    session = initialize_datahub_mcp(config=config(), transport=FakeTransport(initialize=DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, json.dumps({"jsonrpc": "2.0", "id": 1, "result": result}).encode())))
    dumped = session.model_dump()
    assert dumped == {"endpoint_url": "https://datahub.example.com/mcp", "protocol_version": DATAHUB_MCP_PROTOCOL_VERSION, "server_name": "DataHub", "server_version": "1", "tools_supported": True, "session_id": None}
