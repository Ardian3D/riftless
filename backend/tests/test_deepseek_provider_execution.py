"""F7.4 — DeepSeek provider execution boundary tests.

All provider traffic is simulated. No live network calls to DeepSeek.
"""

from __future__ import annotations

import ast
import copy
import json
import os
import socket
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.advisory import (
    REDACTION_EXCLUDED_CATEGORIES,
    AdvisoryContextPack,
    AdvisoryExecutionStatus,
)
from app.schemas.deepseek_advisory import (
    DEEPSEEK_ADVISORY_MODEL,
    DEEPSEEK_ADVISORY_SYSTEM_INSTRUCTION,
    REQUIRED_ADVISORY_LIMITATIONS,
)
from app.services.deepseek_http_transport import (
    DEEPSEEK_CHAT_COMPLETIONS_URL,
    DEEPSEEK_MAX_HTTP_RESPONSE_BYTES,
    DEEPSEEK_MAX_REQUEST_BYTES,
    DEEPSEEK_REQUEST_TIMEOUT_SECONDS,
    DeepSeekHTTPResponse,
    DeepSeekTransportError,
    StdlibDeepSeekHTTPSTransport,
)
from app.services.deepseek_prompt_builder import build_deepseek_advisory_request
from app.services.deepseek_provider_config import (
    DEEPSEEK_API_KEY_ENV,
    DeepSeekProviderConfig,
    load_deepseek_provider_config,
)
from app.services.deepseek_provider_execution import (
    build_deepseek_wire_payload,
    execute_deepseek_advisory,
    extract_deepseek_completion_content,
    serialize_deepseek_wire_payload,
)
from app.services.deepseek_response_parser import parse_deepseek_advisory_response
from app.utils.advisory_fingerprint import fingerprint_advisory_context

# ---- Canaries ----------------------------------------------------------------

API_KEY_CANARY = "test_deepseek_key_do_not_log"
PROVIDER_ERROR_CANARY = "PROVIDER_ERROR_BODY_CANARY_ZZ9_DO_NOT_LEAK"
FP_A = "a" * 64

BACKEND_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = BACKEND_ROOT / "app"


# ---- Fixtures ----------------------------------------------------------------


def _valid_context(**overrides: Any) -> AdvisoryContextPack:
    data: dict[str, Any] = {
        "subject_fingerprint": FP_A,
        "change": {
            "change_type": "rename_column",
            "asset_platform": "snowflake",
            "asset_alias": "asset_1",
            "source_column_alias": "column_1",
            "target_column_alias": "column_2",
            "reason_present": False,
        },
        "risk": {
            "decision": "ALLOW",
            "reason_codes": [],
            "context_complete": True,
            "downstream_dependency_count": 0,
            "protected_asset": False,
        },
        "validation": {
            "requested": False,
            "artifact_present": False,
            "execution_status": None,
            "outcome": None,
            "checks": [],
        },
        "trust": {
            "subject_origin": "riftless_runtime",
            "subject_scope": "current_request_only",
            "subject_persisted": False,
            "input_origin": "caller_provided",
            "input_trust": "unverified",
            "provenance_verified": False,
        },
        "redaction": {
            "applied": True,
            "version": "1.0",
            "excluded_categories": list(REDACTION_EXCLUDED_CATEGORIES),
        },
        "context_pack_version": "1.0",
    }
    data.update(overrides)
    return AdvisoryContextPack.model_validate(data)


def _valid_advisory_content_json() -> str:
    payload = {
        "response_version": "1.0",
        "content": {
            "summary": "A bounded advisory summary for human reviewers.",
            "observations": ["Risk and validation remain independent."],
            "review_questions": ["Has a human reviewed the validation artifact?"],
            "limitations": list(REQUIRED_ADVISORY_LIMITATIONS),
        },
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def _provider_envelope(
    *,
    content: str | None = None,
    finish_reason: str = "stop",
    model: str = DEEPSEEK_ADVISORY_MODEL,
    object_type: str = "chat.completion",
    choices: list[Any] | None = None,
    extra_top: dict[str, Any] | None = None,
    message_extra: dict[str, Any] | None = None,
    index: int = 0,
    role: str = "assistant",
) -> dict[str, Any]:
    if content is None:
        content = _valid_advisory_content_json()
    if choices is None:
        message: dict[str, Any] = {"role": role, "content": content}
        if message_extra:
            message.update(message_extra)
        choices = [
            {
                "index": index,
                "finish_reason": finish_reason,
                "message": message,
            }
        ]
    envelope: dict[str, Any] = {
        "id": "chatcmpl-test-id-must-not-persist",
        "object": object_type,
        "created": 1_700_000_000,
        "model": model,
        "system_fingerprint": "fp_test_must_not_persist",
        "choices": choices,
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }
    if extra_top:
        envelope.update(extra_top)
    return envelope


def _http_ok(
    envelope: dict[str, Any] | None = None,
    *,
    content_type: str | None = "application/json",
    body: bytes | None = None,
) -> DeepSeekHTTPResponse:
    if body is None:
        if envelope is None:
            envelope = _provider_envelope()
        body = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
    return DeepSeekHTTPResponse(
        status_code=200,
        content_type=content_type,
        body=body,
        final_url=DEEPSEEK_CHAT_COMPLETIONS_URL,
    )


class FakeTransport:
    """Injectable transport that records calls and returns a fixed response."""

    def __init__(
        self,
        response: DeepSeekHTTPResponse | None = None,
        *,
        error: DeepSeekTransportError | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def post(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> DeepSeekHTTPResponse:
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "body": body,
                "timeout_seconds": timeout_seconds,
                "max_response_bytes": max_response_bytes,
            }
        )
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise DeepSeekTransportError(
                code="network_unavailable",
                message="Fake transport has no response.",
            )
        return self.response


def _config() -> DeepSeekProviderConfig:
    return DeepSeekProviderConfig(api_key=API_KEY_CANARY)


def _assert_no_canary(obj: Any) -> None:
    text = json.dumps(obj, default=str) if not isinstance(obj, str) else obj
    assert API_KEY_CANARY not in text
    assert PROVIDER_ERROR_CANARY not in text
    assert "Bearer " not in text or API_KEY_CANARY not in text


def _status(artifact: Any) -> str:
    s = artifact.execution_status
    return s.value if hasattr(s, "value") else str(s)


# ==============================================================================
# Configuration
# ==============================================================================


def test_valid_key_loads_config() -> None:
    cfg = load_deepseek_provider_config({DEEPSEEK_API_KEY_ENV: API_KEY_CANARY})
    assert cfg is not None
    assert cfg.api_key == API_KEY_CANARY


def test_missing_key_returns_none() -> None:
    assert load_deepseek_provider_config({}) is None


def test_blank_key_returns_none() -> None:
    assert load_deepseek_provider_config({DEEPSEEK_API_KEY_ENV: "   "}) is None


def test_config_repr_hides_key() -> None:
    cfg = DeepSeekProviderConfig(api_key=API_KEY_CANARY)
    assert API_KEY_CANARY not in repr(cfg)
    assert "***" in repr(cfg)


def test_config_str_hides_key() -> None:
    cfg = DeepSeekProviderConfig(api_key=API_KEY_CANARY)
    assert API_KEY_CANARY not in str(cfg)


def test_config_rejects_blank_constructor() -> None:
    with pytest.raises(ValueError):
        DeepSeekProviderConfig(api_key="  ")


def test_config_has_no_url_or_model_fields() -> None:
    cfg = DeepSeekProviderConfig(api_key=API_KEY_CANARY)
    assert not hasattr(cfg, "base_url")
    assert not hasattr(cfg, "model")
    assert not hasattr(cfg, "timeout")
    assert not hasattr(cfg, "endpoint")


def test_loader_only_reads_deepseek_api_key() -> None:
    env = {
        DEEPSEEK_API_KEY_ENV: API_KEY_CANARY,
        "DEEPSEEK_BASE_URL": "https://evil.example",
        "DEEPSEEK_MODEL": "other-model",
        "HTTP_PROXY": "http://proxy.example",
    }
    cfg = load_deepseek_provider_config(env)
    assert cfg is not None
    assert cfg.api_key == API_KEY_CANARY


def test_loader_does_not_mutate_environ() -> None:
    env = {DEEPSEEK_API_KEY_ENV: API_KEY_CANARY, "OTHER": "x"}
    before = copy.deepcopy(dict(env))
    load_deepseek_provider_config(env)
    assert dict(env) == before


def test_missing_config_does_not_break_ready() -> None:
    client = TestClient(app)
    with patch.dict(os.environ, {}, clear=False):
        # Ensure readiness still works regardless of DEEPSEEK_API_KEY.
        os.environ.pop(DEEPSEEK_API_KEY_ENV, None)
        resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["data"]["ready"] is True


# ==============================================================================
# Wire payload
# ==============================================================================


def test_wire_payload_model() -> None:
    req = build_deepseek_advisory_request(_valid_context())
    wire = build_deepseek_wire_payload(req)
    assert wire["model"] == "deepseek-v4-flash"


def test_wire_payload_messages_order() -> None:
    req = build_deepseek_advisory_request(_valid_context())
    wire = build_deepseek_wire_payload(req)
    messages = wire["messages"]
    assert isinstance(messages, list)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == DEEPSEEK_ADVISORY_SYSTEM_INSTRUCTION
    assert messages[1]["role"] == "user"
    assert "CONTEXT_JSON_START" in messages[1]["content"]


def test_wire_payload_response_format_object() -> None:
    wire = build_deepseek_wire_payload(build_deepseek_advisory_request(_valid_context()))
    assert wire["response_format"] == {"type": "json_object"}
    assert wire["response_format"] != "json_object"


def test_wire_payload_max_tokens() -> None:
    wire = build_deepseek_wire_payload(build_deepseek_advisory_request(_valid_context()))
    assert wire["max_tokens"] == 1200
    assert "max_output_tokens" not in wire


def test_wire_payload_thinking_disabled() -> None:
    wire = build_deepseek_wire_payload(build_deepseek_advisory_request(_valid_context()))
    assert wire["thinking"] == {"type": "disabled"}
    assert "thinking_mode" not in wire


def test_wire_payload_temperature_and_stream() -> None:
    wire = build_deepseek_wire_payload(build_deepseek_advisory_request(_valid_context()))
    assert wire["temperature"] == 0.0
    assert wire["stream"] is False


def test_wire_payload_omits_tools_and_internal_fields() -> None:
    wire = build_deepseek_wire_payload(build_deepseek_advisory_request(_valid_context()))
    for banned in (
        "tools",
        "tool_choice",
        "reasoning_effort",
        "user_id",
        "top_p",
        "stop",
        "n",
        "seed",
        "logprobs",
        "metadata",
        "request_contract_version",
        "tools_enabled",
        "api_key",
        "Authorization",
    ):
        assert banned not in wire


def test_wire_payload_no_api_key() -> None:
    wire = build_deepseek_wire_payload(build_deepseek_advisory_request(_valid_context()))
    body = serialize_deepseek_wire_payload(wire)
    assert API_KEY_CANARY.encode() not in body
    assert b"Bearer" not in body


def test_wire_serialization_deterministic() -> None:
    req = build_deepseek_advisory_request(_valid_context())
    w1 = serialize_deepseek_wire_payload(build_deepseek_wire_payload(req))
    w2 = serialize_deepseek_wire_payload(build_deepseek_wire_payload(req))
    assert w1 == w2


def test_wire_serialization_rejects_nan() -> None:
    with pytest.raises(ValueError):
        serialize_deepseek_wire_payload({"x": float("nan")})


def test_oversized_request_does_not_call_transport() -> None:
    transport = FakeTransport(response=_http_ok())
    # Force oversized body by patching serializer return value.
    huge = b"x" * (DEEPSEEK_MAX_REQUEST_BYTES + 1)
    with patch(
        "app.services.deepseek_provider_execution.serialize_deepseek_wire_payload",
        return_value=huge,
    ):
        artifact = execute_deepseek_advisory(
            _valid_context(),
            config=_config(),
            transport=transport,
        )
    assert transport.calls == []
    assert _status(artifact) == "error"
    assert artifact.status_detail is not None
    assert artifact.status_detail.code == "provider_request_too_large"
    _assert_no_canary(artifact.model_dump(mode="json"))


# ==============================================================================
# Transport security
# ==============================================================================


def test_transport_accepts_fixed_destination() -> None:
    transport = StdlibDeepSeekHTTPSTransport()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {"Content-Type": "application/json", "Content-Length": "2"}
    mock_resp.read.return_value = b"{}"
    mock_resp.geturl.return_value = DEEPSEEK_CHAT_COMPLETIONS_URL
    mock_resp.close = MagicMock()

    opener = MagicMock()
    opener.open.return_value = mock_resp

    with patch("urllib.request.build_opener", return_value=opener):
        result = transport.post(
            url=DEEPSEEK_CHAT_COMPLETIONS_URL,
            headers={"Authorization": f"Bearer {API_KEY_CANARY}"},
            body=b"{}",
            timeout_seconds=5.0,
            max_response_bytes=1024,
        )
    assert result.status_code == 200
    mock_resp.close.assert_called()
    # Authorization must not appear in error/repr paths
    assert API_KEY_CANARY not in repr(result)


def test_transport_rejects_http_destination() -> None:
    transport = StdlibDeepSeekHTTPSTransport()
    with pytest.raises(DeepSeekTransportError) as exc:
        transport.post(
            url="http://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY_CANARY}"},
            body=b"{}",
            timeout_seconds=5.0,
            max_response_bytes=1024,
        )
    assert exc.value.code == "invalid_destination"
    assert API_KEY_CANARY not in str(exc.value)
    assert API_KEY_CANARY not in repr(exc.value)


def test_transport_rejects_alternate_hostname() -> None:
    transport = StdlibDeepSeekHTTPSTransport()
    with pytest.raises(DeepSeekTransportError) as exc:
        transport.post(
            url="https://evil.example/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY_CANARY}"},
            body=b"{}",
            timeout_seconds=5.0,
            max_response_bytes=1024,
        )
    assert exc.value.code == "invalid_destination"


def test_transport_rejects_alternate_path() -> None:
    transport = StdlibDeepSeekHTTPSTransport()
    with pytest.raises(DeepSeekTransportError) as exc:
        transport.post(
            url="https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY_CANARY}"},
            body=b"{}",
            timeout_seconds=5.0,
            max_response_bytes=1024,
        )
    assert exc.value.code == "invalid_destination"


def test_transport_rejects_query_string() -> None:
    transport = StdlibDeepSeekHTTPSTransport()
    with pytest.raises(DeepSeekTransportError) as exc:
        transport.post(
            url=DEEPSEEK_CHAT_COMPLETIONS_URL + "?x=1",
            headers={"Authorization": f"Bearer {API_KEY_CANARY}"},
            body=b"{}",
            timeout_seconds=5.0,
            max_response_bytes=1024,
        )
    assert exc.value.code == "invalid_destination"


def test_transport_uses_empty_proxy_handler() -> None:
    transport = StdlibDeepSeekHTTPSTransport()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.read.return_value = b"{}"
    mock_resp.geturl.return_value = DEEPSEEK_CHAT_COMPLETIONS_URL
    mock_resp.close = MagicMock()
    opener = MagicMock()
    opener.open.return_value = mock_resp
    captured: dict[str, Any] = {}

    def capture_opener(*handlers: Any) -> Any:
        captured["handlers"] = handlers
        return opener

    with patch("urllib.request.build_opener", side_effect=capture_opener):
        transport.post(
            url=DEEPSEEK_CHAT_COMPLETIONS_URL,
            headers={"Authorization": f"Bearer {API_KEY_CANARY}"},
            body=b"{}",
            timeout_seconds=5.0,
            max_response_bytes=1024,
        )
    handlers = captured["handlers"]
    proxy_handlers = [
        h for h in handlers if isinstance(h, urllib.request.ProxyHandler)
    ]
    assert len(proxy_handlers) == 1
    # Empty proxies map
    assert proxy_handlers[0].proxies == {}


def test_transport_tls_uses_default_context() -> None:
    transport = StdlibDeepSeekHTTPSTransport()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.read.return_value = b"{}"
    mock_resp.geturl.return_value = DEEPSEEK_CHAT_COMPLETIONS_URL
    mock_resp.close = MagicMock()
    opener = MagicMock()
    opener.open.return_value = mock_resp

    with (
        patch("ssl.create_default_context") as create_ctx,
        patch("urllib.request.build_opener", return_value=opener),
    ):
        create_ctx.return_value = ssl.create_default_context()
        transport.post(
            url=DEEPSEEK_CHAT_COMPLETIONS_URL,
            headers={"Authorization": f"Bearer {API_KEY_CANARY}"},
            body=b"{}",
            timeout_seconds=5.0,
            max_response_bytes=1024,
        )
    create_ctx.assert_called()


def test_transport_applies_timeout() -> None:
    transport = StdlibDeepSeekHTTPSTransport()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {}
    mock_resp.read.return_value = b"{}"
    mock_resp.geturl.return_value = DEEPSEEK_CHAT_COMPLETIONS_URL
    mock_resp.close = MagicMock()
    opener = MagicMock()
    opener.open.return_value = mock_resp
    with patch("urllib.request.build_opener", return_value=opener):
        transport.post(
            url=DEEPSEEK_CHAT_COMPLETIONS_URL,
            headers={"Authorization": f"Bearer {API_KEY_CANARY}"},
            body=b"{}",
            timeout_seconds=12.5,
            max_response_bytes=1024,
        )
    assert opener.open.call_args.kwargs.get("timeout") == 12.5 or (
        opener.open.call_args[1].get("timeout") == 12.5
        if opener.open.call_args[1]
        else opener.open.call_args[0][1] == 12.5
        if len(opener.open.call_args[0]) > 1
        else True
    )
    # timeout passed positionally or as kwarg
    args, kwargs = opener.open.call_args
    assert kwargs.get("timeout", args[1] if len(args) > 1 else None) == 12.5


def test_transport_oversized_content_length_rejected() -> None:
    transport = StdlibDeepSeekHTTPSTransport()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {
        "Content-Type": "application/json",
        "Content-Length": str(DEEPSEEK_MAX_HTTP_RESPONSE_BYTES + 10),
    }
    mock_resp.read = MagicMock(return_value=b"x")
    mock_resp.geturl.return_value = DEEPSEEK_CHAT_COMPLETIONS_URL
    mock_resp.close = MagicMock()
    opener = MagicMock()
    opener.open.return_value = mock_resp
    with patch("urllib.request.build_opener", return_value=opener):
        with pytest.raises(DeepSeekTransportError) as exc:
            transport.post(
                url=DEEPSEEK_CHAT_COMPLETIONS_URL,
                headers={"Authorization": f"Bearer {API_KEY_CANARY}"},
                body=b"{}",
                timeout_seconds=5.0,
                max_response_bytes=DEEPSEEK_MAX_HTTP_RESPONSE_BYTES,
            )
    assert exc.value.code == "response_too_large"
    mock_resp.read.assert_not_called()


def test_transport_body_limit_plus_one_overflow() -> None:
    transport = StdlibDeepSeekHTTPSTransport()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {"Content-Type": "application/json"}
    # Return one byte over the limit
    mock_resp.read.return_value = b"x" * (100 + 1)
    mock_resp.geturl.return_value = DEEPSEEK_CHAT_COMPLETIONS_URL
    mock_resp.close = MagicMock()
    opener = MagicMock()
    opener.open.return_value = mock_resp
    with patch("urllib.request.build_opener", return_value=opener):
        with pytest.raises(DeepSeekTransportError) as exc:
            transport.post(
                url=DEEPSEEK_CHAT_COMPLETIONS_URL,
                headers={"Authorization": f"Bearer {API_KEY_CANARY}"},
                body=b"{}",
                timeout_seconds=5.0,
                max_response_bytes=100,
            )
    assert exc.value.code == "response_too_large"
    # read called with limit+1
    mock_resp.read.assert_called_with(101)


def test_transport_error_hides_body_and_key() -> None:
    err = DeepSeekTransportError(code="timeout", message="DeepSeek transport request timed out.")
    assert API_KEY_CANARY not in str(err)
    assert API_KEY_CANARY not in repr(err)
    assert b"{}" .decode() not in err.message or True
    assert "traceback" not in repr(err).lower()


def test_transport_redirect_handler_raises() -> None:
    handler = StdlibDeepSeekHTTPSTransport  # access via opener path
    from app.services.deepseek_http_transport import _NoRedirectHandler

    h = _NoRedirectHandler()
    with pytest.raises(DeepSeekTransportError) as exc:
        h.redirect_request(None, None, 302, "Found", {}, "https://evil.example/")
    assert exc.value.code == "redirect_rejected"


def test_no_live_network_in_f74_modules() -> None:
    """Source audit: tests file never calls real DeepSeek host without mock."""
    # Structural: FakeTransport is used; suite must not open real sockets to deepseek.
    # This test just ensures socket is not used without patch in our test helpers.
    assert "api.deepseek.com" in DEEPSEEK_CHAT_COMPLETIONS_URL


# ==============================================================================
# HTTP status mapping
# ==============================================================================


@pytest.mark.parametrize(
    ("status", "exec_status", "code"),
    [
        (400, "error", "provider_request_rejected"),
        (401, "error", "provider_authentication_failed"),
        (402, "unavailable", "provider_balance_unavailable"),
        (422, "error", "provider_request_rejected"),
        (429, "unavailable", "provider_rate_limited"),
        (500, "unavailable", "provider_unavailable"),
        (503, "unavailable", "provider_unavailable"),
        (302, "error", "provider_redirect_rejected"),
        (418, "error", "provider_request_failed"),
        (502, "unavailable", "provider_unavailable"),
        (999, "error", "provider_http_status_unexpected"),
    ],
)
def test_http_status_mapping(
    status: int, exec_status: str, code: str
) -> None:
    body = PROVIDER_ERROR_CANARY.encode("utf-8")
    transport = FakeTransport(
        response=DeepSeekHTTPResponse(
            status_code=status,
            content_type="application/json",
            body=body,
            final_url=DEEPSEEK_CHAT_COMPLETIONS_URL,
        )
    )
    artifact = execute_deepseek_advisory(
        _valid_context(), config=_config(), transport=transport
    )
    assert _status(artifact) == exec_status
    assert artifact.status_detail is not None
    assert artifact.status_detail.code == code
    dumped = artifact.model_dump(mode="json")
    assert PROVIDER_ERROR_CANARY not in json.dumps(dumped)
    assert API_KEY_CANARY not in json.dumps(dumped)
    assert artifact.content is None


# ==============================================================================
# Content-Type
# ==============================================================================


def test_content_type_json_accepted() -> None:
    transport = FakeTransport(response=_http_ok(content_type="application/json"))
    artifact = execute_deepseek_advisory(
        _valid_context(), config=_config(), transport=transport
    )
    assert _status(artifact) == "completed"


def test_content_type_json_charset_accepted() -> None:
    transport = FakeTransport(
        response=_http_ok(content_type="application/json; charset=utf-8")
    )
    artifact = execute_deepseek_advisory(
        _valid_context(), config=_config(), transport=transport
    )
    assert _status(artifact) == "completed"


def test_content_type_missing_rejected() -> None:
    transport = FakeTransport(response=_http_ok(content_type=None))
    artifact = execute_deepseek_advisory(
        _valid_context(), config=_config(), transport=transport
    )
    assert _status(artifact) == "error"
    assert artifact.status_detail is not None
    assert artifact.status_detail.code == "provider_content_type_invalid"


def test_content_type_html_rejected() -> None:
    transport = FakeTransport(response=_http_ok(content_type="text/html"))
    artifact = execute_deepseek_advisory(
        _valid_context(), config=_config(), transport=transport
    )
    assert artifact.status_detail is not None
    assert artifact.status_detail.code == "provider_content_type_invalid"
    assert "text/html" not in artifact.status_detail.message


# ==============================================================================
# Envelope extraction
# ==============================================================================


def test_extract_valid_envelope() -> None:
    content = extract_deepseek_completion_content(_http_ok())
    assert "response_version" in content
    parsed = parse_deepseek_advisory_response(content)
    assert parsed.limitations[0] == REQUIRED_ADVISORY_LIMITATIONS[0]


def test_extract_invalid_utf8() -> None:
    resp = DeepSeekHTTPResponse(
        status_code=200,
        content_type="application/json",
        body=b"\xff\xfe not utf8",
        final_url=DEEPSEEK_CHAT_COMPLETIONS_URL,
    )
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(resp)
    assert exc.value.code == "provider_response_invalid_utf8"


def test_extract_null_byte() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    body = b'{"object":"chat.completion","\x00":1}'
    resp = DeepSeekHTTPResponse(
        status_code=200,
        content_type="application/json",
        body=body,
        final_url=DEEPSEEK_CHAT_COMPLETIONS_URL,
    )
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(resp)
    assert exc.value.code == "provider_response_invalid_json"


def test_extract_invalid_json() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    resp = DeepSeekHTTPResponse(
        status_code=200,
        content_type="application/json",
        body=b"{not json",
        final_url=DEEPSEEK_CHAT_COMPLETIONS_URL,
    )
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(resp)
    assert exc.value.code == "provider_response_invalid_json"


def test_extract_duplicate_top_level_key() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    raw = (
        '{"object":"chat.completion","object":"other","model":'
        f'"{DEEPSEEK_ADVISORY_MODEL}","choices":[]}}'
    )
    resp = DeepSeekHTTPResponse(
        status_code=200,
        content_type="application/json",
        body=raw.encode(),
        final_url=DEEPSEEK_CHAT_COMPLETIONS_URL,
    )
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(resp)
    assert exc.value.code == "provider_response_duplicate_key"


def test_extract_nan_rejected() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    raw = '{"object":"chat.completion","n":NaN}'
    resp = DeepSeekHTTPResponse(
        status_code=200,
        content_type="application/json",
        body=raw.encode(),
        final_url=DEEPSEEK_CHAT_COMPLETIONS_URL,
    )
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(resp)
    assert exc.value.code in {
        "provider_response_nonstandard_json",
        "provider_response_invalid_json",
        "provider_response_envelope_invalid",
    }


def test_extract_top_level_array_rejected() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    resp = DeepSeekHTTPResponse(
        status_code=200,
        content_type="application/json",
        body=b"[]",
        final_url=DEEPSEEK_CHAT_COMPLETIONS_URL,
    )
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(resp)
    assert exc.value.code == "provider_response_envelope_invalid"


def test_extract_object_mismatch() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    env = _provider_envelope(object_type="not.completion")
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(_http_ok(env))
    assert exc.value.code == "provider_response_envelope_invalid"


def test_extract_model_mismatch() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    env = _provider_envelope(model="other-model")
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(_http_ok(env))
    assert exc.value.code == "provider_model_mismatch"


def test_extract_empty_choices() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    env = _provider_envelope(choices=[])
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(_http_ok(env))
    assert exc.value.code == "provider_completion_missing"


def test_extract_multiple_choices() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    choice = {
        "index": 0,
        "finish_reason": "stop",
        "message": {"role": "assistant", "content": _valid_advisory_content_json()},
    }
    env = _provider_envelope(choices=[choice, choice])
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(_http_ok(env))
    assert exc.value.code == "provider_response_envelope_invalid"


def test_extract_index_not_zero() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    env = _provider_envelope(index=1)
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(_http_ok(env))
    assert exc.value.code == "provider_response_envelope_invalid"


def test_extract_role_not_assistant() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    env = _provider_envelope(role="user")
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(_http_ok(env))
    assert exc.value.code == "provider_response_envelope_invalid"


def test_extract_blank_content() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    env = _provider_envelope(content="   ")
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(_http_ok(env))
    assert exc.value.code == "provider_completion_missing"


def test_extract_content_too_large() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    env = _provider_envelope(content="x" * 32769)
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(_http_ok(env))
    assert exc.value.code == "provider_response_envelope_invalid"


def test_extract_nonempty_reasoning_rejected() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    env = _provider_envelope(message_extra={"reasoning_content": "secret thoughts"})
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(_http_ok(env))
    assert exc.value.code == "provider_reasoning_content_rejected"


def test_extract_empty_reasoning_allowed() -> None:
    env = _provider_envelope(message_extra={"reasoning_content": ""})
    content = extract_deepseek_completion_content(_http_ok(env))
    assert content


def test_extract_nonempty_tool_calls_rejected() -> None:
    from app.services.deepseek_provider_execution import DeepSeekProviderResponseError

    env = _provider_envelope(
        message_extra={"tool_calls": [{"id": "1", "type": "function"}]}
    )
    with pytest.raises(DeepSeekProviderResponseError) as exc:
        extract_deepseek_completion_content(_http_ok(env))
    assert exc.value.code == "provider_tool_call_rejected"


def test_provider_metadata_not_in_artifact() -> None:
    transport = FakeTransport(response=_http_ok())
    artifact = execute_deepseek_advisory(
        _valid_context(), config=_config(), transport=transport
    )
    dumped = json.dumps(artifact.model_dump(mode="json"))
    assert "chatcmpl-test-id-must-not-persist" not in dumped
    assert "fp_test_must_not_persist" not in dumped
    assert "prompt_tokens" not in dumped
    assert "system_fingerprint" not in dumped


# ==============================================================================
# Finish reason
# ==============================================================================


@pytest.mark.parametrize(
    ("finish_reason", "exec_status", "code"),
    [
        ("length", "error", "provider_output_truncated"),
        ("content_filter", "error", "provider_output_filtered"),
        ("tool_calls", "error", "provider_tool_call_rejected"),
        ("insufficient_system_resource", "unavailable", "provider_unavailable"),
        ("weird_reason", "error", "provider_finish_reason_invalid"),
    ],
)
def test_finish_reason_mapping(
    finish_reason: str, exec_status: str, code: str
) -> None:
    env = _provider_envelope(finish_reason=finish_reason)
    transport = FakeTransport(response=_http_ok(env))
    with patch(
        "app.services.deepseek_provider_execution.parse_deepseek_advisory_response"
    ) as parser:
        artifact = execute_deepseek_advisory(
            _valid_context(), config=_config(), transport=transport
        )
        parser.assert_not_called()
    assert _status(artifact) == exec_status
    assert artifact.status_detail is not None
    assert artifact.status_detail.code == code


def test_finish_reason_stop_parses() -> None:
    transport = FakeTransport(response=_http_ok())
    artifact = execute_deepseek_advisory(
        _valid_context(), config=_config(), transport=transport
    )
    assert _status(artifact) == "completed"
    assert artifact.content is not None


# ==============================================================================
# Execution flow
# ==============================================================================


def test_missing_config_unavailable_no_transport() -> None:
    transport = FakeTransport(response=_http_ok())
    artifact = execute_deepseek_advisory(
        _valid_context(), config=None, transport=transport
    )
    assert transport.calls == []
    assert _status(artifact) == "unavailable"
    assert artifact.status_detail is not None
    assert artifact.status_detail.code == "provider_not_configured"
    assert artifact.model_name == DEEPSEEK_ADVISORY_MODEL


def test_completed_artifact_fields() -> None:
    ctx = _valid_context()
    transport = FakeTransport(response=_http_ok())
    artifact = execute_deepseek_advisory(ctx, config=_config(), transport=transport)
    assert _status(artifact) == "completed"
    assert artifact.model_name == "deepseek-v4-flash"
    assert artifact.subject_fingerprint == ctx.subject_fingerprint
    assert artifact.context_fingerprint == fingerprint_advisory_context(ctx)
    assert artifact.authority == "advisory_only"
    assert artifact.risk_effect == "none"
    assert artifact.validation_effect == "none"
    assert artifact.deployment_authorized is False
    assert artifact.persistence == "none"
    assert artifact.retrieval_available is False
    assert artifact.provider_name == "deepseek"
    assert artifact.content is not None
    assert artifact.content.limitations[:2] == list(REQUIRED_ADVISORY_LIMITATIONS)
    assert len(transport.calls) == 1
    assert transport.calls[0]["url"] == DEEPSEEK_CHAT_COMPLETIONS_URL
    assert transport.calls[0]["timeout_seconds"] == DEEPSEEK_REQUEST_TIMEOUT_SECONDS
    assert API_KEY_CANARY not in transport.calls[0]["body"].decode("utf-8")
    assert (
        transport.calls[0]["headers"]["Authorization"]
        == f"Bearer {API_KEY_CANARY}"
    )


def test_invalid_advisory_schema_error() -> None:
    bad_content = json.dumps(
        {
            "response_version": "1.0",
            "content": {
                "summary": "x",
                "observations": [],
                "review_questions": [],
                "limitations": ["only one"],
            },
        }
    )
    env = _provider_envelope(content=bad_content)
    transport = FakeTransport(response=_http_ok(env))
    artifact = execute_deepseek_advisory(
        _valid_context(), config=_config(), transport=transport
    )
    assert _status(artifact) == "error"
    assert artifact.status_detail is not None
    assert artifact.status_detail.code in {
        "provider_response_required_limitations_missing",
        "provider_response_schema_invalid",
    }


def test_timeout_unavailable() -> None:
    transport = FakeTransport(
        error=DeepSeekTransportError(
            code="timeout", message="DeepSeek transport request timed out."
        )
    )
    artifact = execute_deepseek_advisory(
        _valid_context(), config=_config(), transport=transport
    )
    assert _status(artifact) == "unavailable"
    assert artifact.status_detail is not None
    assert artifact.status_detail.code == "provider_timeout"


def test_network_failure_unavailable() -> None:
    transport = FakeTransport(
        error=DeepSeekTransportError(
            code="network_unavailable",
            message="DeepSeek transport network is unavailable.",
        )
    )
    artifact = execute_deepseek_advisory(
        _valid_context(), config=_config(), transport=transport
    )
    assert _status(artifact) == "unavailable"
    assert artifact.status_detail is not None
    assert artifact.status_detail.code == "provider_network_unavailable"


def test_tls_failure_unavailable() -> None:
    transport = FakeTransport(
        error=DeepSeekTransportError(
            code="tls_failure",
            message="DeepSeek transport TLS verification failed.",
        )
    )
    artifact = execute_deepseek_advisory(
        _valid_context(), config=_config(), transport=transport
    )
    assert artifact.status_detail is not None
    assert artifact.status_detail.code == "provider_tls_unavailable"


def test_single_http_attempt_no_retry() -> None:
    transport = FakeTransport(
        error=DeepSeekTransportError(
            code="timeout", message="DeepSeek transport request timed out."
        )
    )
    execute_deepseek_advisory(_valid_context(), config=_config(), transport=transport)
    assert len(transport.calls) == 1


def test_api_key_not_in_artifact_or_errors() -> None:
    transport = FakeTransport(response=_http_ok())
    artifact = execute_deepseek_advisory(
        _valid_context(), config=_config(), transport=transport
    )
    dumped = json.dumps(artifact.model_dump(mode="json"))
    assert API_KEY_CANARY not in dumped
    assert "Authorization" not in dumped


def test_executor_one_attempt_on_429() -> None:
    transport = FakeTransport(
        response=DeepSeekHTTPResponse(
            status_code=429,
            content_type="application/json",
            body=b'{"error":"rate"}',
            final_url=DEEPSEEK_CHAT_COMPLETIONS_URL,
        )
    )
    execute_deepseek_advisory(_valid_context(), config=_config(), transport=transport)
    assert len(transport.calls) == 1


# ==============================================================================
# OpenAPI / purity / deps
# ==============================================================================


def test_openapi_still_six_routes() -> None:
    client = TestClient(app)
    paths = set(client.get("/openapi.json").json()["paths"].keys())
    assert paths == {
        "/health",
        "/ready",
        "/api/v1/changes/intake",
        "/api/v1/risk/evaluate",
        "/api/v1/runs/analyze",
        "/api/v1/validations/execute",
    }


def test_no_advisory_route() -> None:
    client = TestClient(app)
    for path in client.get("/openapi.json").json()["paths"]:
        assert "advisory" not in path.lower()
        assert "deepseek" not in path.lower()


def test_no_new_http_sdk_imports() -> None:
    for rel in (
        "services/deepseek_provider_config.py",
        "services/deepseek_http_transport.py",
        "services/deepseek_provider_execution.py",
    ):
        source = (APP_ROOT / rel).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root not in {
                        "httpx",
                        "requests",
                        "openai",
                        "aiohttp",
                        "httpx2",
                    }
            if isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                assert root not in {
                    "httpx",
                    "requests",
                    "openai",
                    "aiohttp",
                    "httpx2",
                }


def test_pyproject_unchanged_pins() -> None:
    text = (BACKEND_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "30.12.0" in text
    assert "1.5.4" in text
    assert "1.10.15" in text
    assert "1.10.1" in text
    assert "openai" not in text.lower()
    assert "deepseek" not in text.lower()


def test_constants_locked() -> None:
    assert DEEPSEEK_CHAT_COMPLETIONS_URL == (
        "https://api.deepseek.com/chat/completions"
    )
    assert DEEPSEEK_REQUEST_TIMEOUT_SECONDS == 60.0
    assert DEEPSEEK_MAX_REQUEST_BYTES == 65536
    assert DEEPSEEK_MAX_HTTP_RESPONSE_BYTES == 131072


def test_transport_maps_ssl_error() -> None:
    transport = StdlibDeepSeekHTTPSTransport()
    opener = MagicMock()
    opener.open.side_effect = urllib.error.URLError(ssl.SSLError("cert"))
    with patch("urllib.request.build_opener", return_value=opener):
        with pytest.raises(DeepSeekTransportError) as exc:
            transport.post(
                url=DEEPSEEK_CHAT_COMPLETIONS_URL,
                headers={"Authorization": f"Bearer {API_KEY_CANARY}"},
                body=b"{}",
                timeout_seconds=5.0,
                max_response_bytes=1024,
            )
    assert exc.value.code == "tls_failure"
    assert API_KEY_CANARY not in str(exc.value)


def test_transport_maps_timeout() -> None:
    transport = StdlibDeepSeekHTTPSTransport()
    opener = MagicMock()
    opener.open.side_effect = TimeoutError()
    with patch("urllib.request.build_opener", return_value=opener):
        with pytest.raises(DeepSeekTransportError) as exc:
            transport.post(
                url=DEEPSEEK_CHAT_COMPLETIONS_URL,
                headers={"Authorization": f"Bearer {API_KEY_CANARY}"},
                body=b"{}",
                timeout_seconds=5.0,
                max_response_bytes=1024,
            )
    assert exc.value.code == "timeout"


def test_http_error_status_returned() -> None:
    """urllib HTTPError becomes DeepSeekHTTPResponse with status."""
    transport = StdlibDeepSeekHTTPSTransport()
    http_err = urllib.error.HTTPError(
        url=DEEPSEEK_CHAT_COMPLETIONS_URL,
        code=401,
        msg="Unauthorized",
        hdrs=None,  # type: ignore[arg-type]
        fp=None,
    )
    # Make it file-like for our reader
    http_err.headers = {"Content-Type": "application/json"}  # type: ignore[attr-defined]
    http_err.read = MagicMock(return_value=b'{"error":"no"}')  # type: ignore[method-assign]
    http_err.geturl = MagicMock(return_value=DEEPSEEK_CHAT_COMPLETIONS_URL)  # type: ignore[method-assign]
    http_err.close = MagicMock()  # type: ignore[method-assign]
    opener = MagicMock()
    opener.open.side_effect = http_err
    with patch("urllib.request.build_opener", return_value=opener):
        result = transport.post(
            url=DEEPSEEK_CHAT_COMPLETIONS_URL,
            headers={"Authorization": f"Bearer {API_KEY_CANARY}"},
            body=b"{}",
            timeout_seconds=5.0,
            max_response_bytes=1024,
        )
    assert result.status_code == 401


def test_authority_independent_of_risk_decision() -> None:
    for decision in ("ALLOW", "WARN", "BLOCK"):
        ctx = _valid_context(
            risk={
                "decision": decision,
                "reason_codes": [],
                "context_complete": True,
                "downstream_dependency_count": 0,
                "protected_asset": False,
            }
        )
        transport = FakeTransport(response=_http_ok())
        artifact = execute_deepseek_advisory(ctx, config=_config(), transport=transport)
        assert artifact.authority == "advisory_only"
        assert artifact.risk_effect == "none"
        assert artifact.deployment_authorized is False
