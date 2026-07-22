"""Fixed-purpose stdlib Streamable HTTP transport for the F8.2 boundary."""

from __future__ import annotations

import http.client
import socket
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Mapping, Protocol

from .config import DataHubMCPAuthMode, DataHubMCPConfig
from .mcp_protocol import DataHubMCPProtocolError


@dataclass(frozen=True)
class DataHubMCPHTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class DataHubMCPTransport(Protocol):
    def post_request(self, body: bytes, *, session_id: str | None, protocol_version: str | None) -> DataHubMCPHTTPResponse: ...
    def post_notification(self, body: bytes, *, session_id: str | None, protocol_version: str) -> DataHubMCPHTTPResponse: ...


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise DataHubMCPProtocolError("redirect_rejected", "MCP redirect was rejected.")


def classify_http_status(status: int, *, expects_response: bool, has_session: bool = False) -> None:
    if status == 200 and expects_response: return
    if status == 202 and not expects_response: return
    mapping = {
        300: ("redirect_rejected", False), 301: ("redirect_rejected", False), 302: ("redirect_rejected", False), 303: ("redirect_rejected", False), 307: ("redirect_rejected", False), 308: ("redirect_rejected", False),
        400: ("request_rejected", False), 401: ("authentication_failed", False), 403: ("authorization_failed", False),
        404: ("session_expired" if has_session else "endpoint_not_found", True), 405: ("method_not_allowed", False), 406: ("content_negotiation_failed", False),
        408: ("timeout", True), 409: ("request_conflict", False), 413: ("provider_request_too_large", False), 415: ("unsupported_media_type", False),
        422: ("request_rejected", False), 429: ("rate_limited", True),
    }
    if status in mapping:
        code, retryable = mapping[status]
    elif 500 <= status <= 599:
        code, retryable = "provider_unavailable", True
    elif 400 <= status <= 499:
        code, retryable = "request_failed", False
    else:
        code, retryable = "unexpected_status", False
    raise DataHubMCPProtocolError(code, "DataHub MCP request failed.", retryable=retryable)


class StdlibDataHubMCPStreamableHTTPTransport:
    """One-attempt POST transport with fixed headers, proxy, TLS, and limits."""

    def __init__(self, config: DataHubMCPConfig, *, opener=None) -> None:
        if not isinstance(config, DataHubMCPConfig): raise TypeError("config must be DataHubMCPConfig")
        self._config = config
        self._opener = opener or self._build_opener()

    @staticmethod
    def _build_opener():
        context = ssl.create_default_context()
        return urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect(), urllib.request.HTTPSHandler(context=context))

    def _headers(self, *, session_id: str | None, protocol_version: str | None, expect_response: bool) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "User-Agent": "riftless-datahub-mcp/1.0"}
        if self._config.auth_mode == DataHubMCPAuthMode.BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {self._config.access_token.get_secret_value()}"  # type: ignore[union-attr]
        if protocol_version is not None: headers["MCP-Protocol-Version"] = protocol_version
        if session_id is not None: headers["MCP-Session-Id"] = session_id
        return headers

    def _post(self, body: bytes, *, session_id: str | None, protocol_version: str | None, expects_response: bool) -> DataHubMCPHTTPResponse:
        if not isinstance(body, bytes) or len(body) > self._config.max_request_bytes:
            raise DataHubMCPProtocolError("request_too_large", "MCP request is too large.")
        request = urllib.request.Request(self._config.endpoint_url, data=body, headers=self._headers(session_id=session_id, protocol_version=protocol_version, expect_response=expects_response), method="POST")
        response = None
        try:
            response = self._opener.open(request, timeout=self._config.timeout_seconds)
            result = self._read_response(response)
        except urllib.error.HTTPError as exc:
            try:
                result = self._read_response(exc)
            finally:
                exc.close()
        except urllib.error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, socket.timeout) or isinstance(reason, TimeoutError): raise DataHubMCPProtocolError("timeout", "DataHub MCP request timed out.", retryable=True) from None
            if isinstance(reason, ssl.SSLError): raise DataHubMCPProtocolError("tls_failure", "DataHub MCP TLS connection failed.", retryable=False) from None
            raise DataHubMCPProtocolError("network_unavailable", "DataHub MCP provider is unavailable.", retryable=True) from None
        except (socket.timeout, TimeoutError):
            raise DataHubMCPProtocolError("timeout", "DataHub MCP request timed out.", retryable=True) from None
        except ssl.SSLError:
            raise DataHubMCPProtocolError("tls_failure", "DataHub MCP TLS connection failed.", retryable=False) from None
        finally:
            if response is not None:
                response.close()
        classify_http_status(result.status_code, expects_response=expects_response, has_session=session_id is not None)
        if not expects_response and result.body:
            raise DataHubMCPProtocolError("invalid_jsonrpc", "MCP notification response body is invalid.")
        return result

    def _read_response(self, response) -> DataHubMCPHTTPResponse:
        body = response.read(self._config.max_response_bytes + 1)
        if len(body) > self._config.max_response_bytes:
            raise DataHubMCPProtocolError("response_too_large", "MCP response is too large.")
        headers = {str(k): str(v) for k, v in response.headers.items()}
        return DataHubMCPHTTPResponse(status_code=int(response.status), headers=headers, body=body)

    def post_request(self, body: bytes, *, session_id: str | None, protocol_version: str | None) -> DataHubMCPHTTPResponse:
        return self._post(body, session_id=session_id, protocol_version=protocol_version, expects_response=True)

    def post_notification(self, body: bytes, *, session_id: str | None, protocol_version: str) -> DataHubMCPHTTPResponse:
        return self._post(body, session_id=session_id, protocol_version=protocol_version, expects_response=False)
