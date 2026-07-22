from __future__ import annotations

import urllib.request

import pytest

from app.integrations.datahub.config import load_datahub_mcp_config
from app.integrations.datahub.mcp_protocol import DataHubMCPProtocolError
from app.integrations.datahub.transport import (
    DataHubMCPHTTPResponse, StdlibDataHubMCPStreamableHTTPTransport, classify_http_status,
)


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, body: bytes = b"{}", status: int = 200, headers: dict[str, str] | None = None):
        self._body, self.status, self.headers, self.closed = body, status, headers or dict(self.headers), False

    def read(self, limit: int) -> bytes:
        assert limit == 1_048_577
        return self._body

    def close(self) -> None: self.closed = True


class FakeOpener:
    def __init__(self, response: FakeResponse): self.response, self.request, self.timeout = response, None, None
    def open(self, request, timeout): self.request, self.timeout = request, timeout; return self.response


def config(token: str | None = "secret-token"):
    values = {"DATAHUB_MCP_URL": "https://datahub.example.com/mcp"}
    if token is not None: values["DATAHUB_TOKEN"] = token
    return load_datahub_mcp_config(values)


def test_transport_headers_endpoint_and_limits() -> None:
    fake = FakeOpener(FakeResponse())
    transport = StdlibDataHubMCPStreamableHTTPTransport(config(), opener=fake)
    transport.post_request(b"{}", session_id="sid", protocol_version="2025-11-25")
    assert fake.request.full_url == "https://datahub.example.com/mcp"
    assert fake.request.method == "POST" and fake.timeout == 30.0
    headers = {k.lower(): v for k, v in fake.request.header_items()}
    assert headers["content-type"] == "application/json"
    assert headers["accept"] == "application/json, text/event-stream"
    assert headers["authorization"] == "Bearer secret-token"
    assert headers["mcp-protocol-version"] == "2025-11-25"
    assert headers["mcp-session-id"] == "sid"
    assert headers["user-agent"] == "riftless-datahub-mcp/1.0"
    assert "cookie" not in headers and "origin" not in headers and "referer" not in headers
    assert fake.response.closed


def test_initialize_headers_omit_negotiated_headers_and_none_auth() -> None:
    fake = FakeOpener(FakeResponse())
    no_auth_config = load_datahub_mcp_config({"DATAHUB_MCP_URL": "http://localhost:8000/mcp"})
    transport = StdlibDataHubMCPStreamableHTTPTransport(no_auth_config, opener=fake)
    transport.post_request(b"{}", session_id=None, protocol_version=None)
    headers = {k.lower(): v for k, v in fake.request.header_items()}
    assert "authorization" not in headers and "mcp-session-id" not in headers and "mcp-protocol-version" not in headers


def test_request_too_large_before_opener() -> None:
    fake = FakeOpener(FakeResponse())
    transport = StdlibDataHubMCPStreamableHTTPTransport(config(), opener=fake)
    with pytest.raises(DataHubMCPProtocolError) as exc: transport.post_request(b"x" * 65_537, session_id=None, protocol_version=None)
    assert exc.value.code == "request_too_large" and fake.request is None


@pytest.mark.parametrize("status,code", [(202, "unexpected_status"), (204, "unexpected_status"), (401, "authentication_failed"), (403, "authorization_failed"), (404, "endpoint_not_found"), (405, "method_not_allowed"), (406, "content_negotiation_failed"), (413, "provider_request_too_large"), (415, "unsupported_media_type"), (429, "rate_limited"), (500, "provider_unavailable")])
def test_http_status_mapping(status: int, code: str) -> None:
    with pytest.raises(DataHubMCPProtocolError) as exc: classify_http_status(status, expects_response=True)
    assert exc.value.code == code


def test_notification_requires_202_and_empty_body() -> None:
    classify_http_status(202, expects_response=False)
    with pytest.raises(DataHubMCPProtocolError): classify_http_status(202, expects_response=True)
    fake = FakeOpener(FakeResponse(body=b"unexpected", status=202))
    transport = StdlibDataHubMCPStreamableHTTPTransport(config(), opener=fake)
    with pytest.raises(DataHubMCPProtocolError): transport.post_notification(b"{}", session_id=None, protocol_version="2025-11-25")


def test_response_size_and_content_encoding() -> None:
    fake = FakeOpener(FakeResponse(body=b"x" * 1_048_577))
    transport = StdlibDataHubMCPStreamableHTTPTransport(config(), opener=fake)
    with pytest.raises(DataHubMCPProtocolError) as exc: transport.post_request(b"{}", session_id=None, protocol_version=None)
    assert exc.value.code == "response_too_large"
    fake = FakeOpener(FakeResponse(headers={"Content-Encoding": "gzip"}))
    transport = StdlibDataHubMCPStreamableHTTPTransport(config(), opener=fake)
    response = transport.post_request(b"{}", session_id=None, protocol_version=None)
    assert response.headers["Content-Encoding"] == "gzip"
