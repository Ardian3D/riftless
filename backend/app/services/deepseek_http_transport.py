"""Bounded HTTPS transport for DeepSeek advisory (phase F7.4).

Standard-library only (``urllib``, ``ssl``, ``socket``). Injectable via
``DeepSeekTransport`` so tests never open live sockets.

Security policy:
- exact fixed destination only
- TLS verification enabled (default context)
- redirects disabled
- environment proxies disabled
- no cookies / no Accept-Encoding compression preference
- bounded response body read (limit + 1)
"""

from __future__ import annotations

import socket
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Mapping, Protocol

# Fixed server-owned destination — never overridden by env or caller.
DEEPSEEK_CHAT_COMPLETIONS_URL = "https://api.deepseek.com/chat/completions"

DEEPSEEK_REQUEST_TIMEOUT_SECONDS = 60.0
DEEPSEEK_MAX_REQUEST_BYTES = 65536
DEEPSEEK_MAX_HTTP_RESPONSE_BYTES = 131072


class DeepSeekTransportError(Exception):
    """Bounded transport failure. Stores only safe code + message."""

    def __init__(self, *, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

    def __repr__(self) -> str:
        return f"DeepSeekTransportError(code={self.code!r})"


@dataclass(frozen=True, slots=True)
class DeepSeekHTTPResponse:
    """Bounded HTTP response value. No request headers/body or secrets."""

    status_code: int
    content_type: str | None
    body: bytes
    final_url: str


class DeepSeekTransport(Protocol):
    """Narrow injectable transport used by the advisory executor."""

    def post(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> DeepSeekHTTPResponse:
        """POST ``body`` to ``url`` and return a bounded response."""
        ...


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject all HTTP redirects so Authorization is never forwarded."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise DeepSeekTransportError(
            code="redirect_rejected",
            message="HTTP redirects are not allowed for DeepSeek transport.",
        )


class StdlibDeepSeekHTTPSTransport:
    """Concrete HTTPS transport using urllib with locked security policy."""

    def post(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> DeepSeekHTTPResponse:
        if url != DEEPSEEK_CHAT_COMPLETIONS_URL:
            raise DeepSeekTransportError(
                code="invalid_destination",
                message="DeepSeek transport destination is not allowed.",
            )
        if not isinstance(body, (bytes, bytearray)):
            raise DeepSeekTransportError(
                code="network_unavailable",
                message="DeepSeek transport request body is invalid.",
            )
        if max_response_bytes < 1:
            raise DeepSeekTransportError(
                code="network_unavailable",
                message="DeepSeek transport response limit is invalid.",
            )

        # Build request without Accept-Encoding so we do not prefer compression.
        # Do not log headers (may contain Authorization).
        req_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        for key, value in headers.items():
            # Only allow the Authorization header through from the executor.
            if key.lower() == "authorization":
                req_headers["Authorization"] = value
            elif key.lower() in {"content-type", "accept"}:
                continue  # fixed above
            else:
                # Reject unexpected headers rather than forwarding them.
                raise DeepSeekTransportError(
                    code="invalid_destination",
                    message="DeepSeek transport received unexpected headers.",
                )

        request = urllib.request.Request(
            url=DEEPSEEK_CHAT_COMPLETIONS_URL,
            data=bytes(body),
            headers=req_headers,
            method="POST",
        )

        context = ssl.create_default_context()
        # Empty ProxyHandler disables HTTP_PROXY / HTTPS_PROXY / ALL_PROXY.
        https_handler = urllib.request.HTTPSHandler(context=context)
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            https_handler,
            _NoRedirectHandler(),
        )

        try:
            response = opener.open(request, timeout=timeout_seconds)
        except DeepSeekTransportError:
            raise
        except urllib.error.HTTPError as exc:
            # HTTPError is also a file-like response — read body under limit.
            return self._read_http_error(exc, max_response_bytes=max_response_bytes)
        except TimeoutError as exc:
            raise DeepSeekTransportError(
                code="timeout",
                message="DeepSeek transport request timed out.",
            ) from None
        except socket.timeout as exc:
            raise DeepSeekTransportError(
                code="timeout",
                message="DeepSeek transport request timed out.",
            ) from None
        except ssl.SSLError as exc:
            raise DeepSeekTransportError(
                code="tls_failure",
                message="DeepSeek transport TLS verification failed.",
            ) from None
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, (TimeoutError, socket.timeout)):
                raise DeepSeekTransportError(
                    code="timeout",
                    message="DeepSeek transport request timed out.",
                ) from None
            if isinstance(reason, ssl.SSLError):
                raise DeepSeekTransportError(
                    code="tls_failure",
                    message="DeepSeek transport TLS verification failed.",
                ) from None
            raise DeepSeekTransportError(
                code="network_unavailable",
                message="DeepSeek transport network is unavailable.",
            ) from None
        except OSError as exc:
            raise DeepSeekTransportError(
                code="network_unavailable",
                message="DeepSeek transport network is unavailable.",
            ) from None

        try:
            return self._read_response(response, max_response_bytes=max_response_bytes)
        finally:
            try:
                response.close()
            except Exception:  # pragma: no cover — best-effort close
                pass

    def _read_http_error(
        self,
        exc: urllib.error.HTTPError,
        *,
        max_response_bytes: int,
    ) -> DeepSeekHTTPResponse:
        try:
            return self._read_response(exc, max_response_bytes=max_response_bytes)
        finally:
            try:
                exc.close()
            except Exception:  # pragma: no cover
                pass

    def _read_response(
        self,
        response: object,
        *,
        max_response_bytes: int,
    ) -> DeepSeekHTTPResponse:
        status_code = int(getattr(response, "status", getattr(response, "code", 0)))
        headers = getattr(response, "headers", None)
        content_type: str | None = None
        content_length: int | None = None
        if headers is not None:
            raw_ct = headers.get("Content-Type")
            if raw_ct is not None:
                content_type = str(raw_ct)
            raw_cl = headers.get("Content-Length")
            if raw_cl is not None:
                try:
                    content_length = int(str(raw_cl).strip())
                except (TypeError, ValueError):
                    content_length = None

        if content_length is not None and content_length > max_response_bytes:
            raise DeepSeekTransportError(
                code="response_too_large",
                message="DeepSeek transport response exceeds the size limit.",
            )

        # final_url without credentials; urllib exposes geturl().
        final_url = str(getattr(response, "geturl", lambda: DEEPSEEK_CHAT_COMPLETIONS_URL)())
        if final_url != DEEPSEEK_CHAT_COMPLETIONS_URL:
            # Redirect somehow produced a different final URL — reject.
            raise DeepSeekTransportError(
                code="redirect_rejected",
                message="HTTP redirects are not allowed for DeepSeek transport.",
            )

        read_limit = max_response_bytes + 1
        try:
            body = response.read(read_limit)  # type: ignore[attr-defined]
        except TimeoutError:
            raise DeepSeekTransportError(
                code="timeout",
                message="DeepSeek transport request timed out.",
            ) from None
        except OSError:
            raise DeepSeekTransportError(
                code="network_unavailable",
                message="DeepSeek transport network is unavailable.",
            ) from None

        if not isinstance(body, (bytes, bytearray)):
            raise DeepSeekTransportError(
                code="network_unavailable",
                message="DeepSeek transport network is unavailable.",
            )
        body_bytes = bytes(body)
        if len(body_bytes) > max_response_bytes:
            raise DeepSeekTransportError(
                code="response_too_large",
                message="DeepSeek transport response exceeds the size limit.",
            )

        return DeepSeekHTTPResponse(
            status_code=status_code,
            content_type=content_type,
            body=body_bytes,
            final_url=final_url,
        )
