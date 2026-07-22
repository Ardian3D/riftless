"""DeepSeek advisory provider execution boundary (phase F7.4).

Orchestrates: F7.3 request → wire payload → one HTTPS attempt → envelope
extraction → F7.3 parser → F7.1 AdvisoryArtifact builders.

Does **not**:
- expose an HTTP endpoint or change /runs/analyze
- retry, stream, or tool-call
- log API keys, raw bodies, or provider error text
- persist or retrieve artifacts
- use third-party HTTP / provider SDKs
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from app.schemas.advisory import (
    AdvisoryArtifact,
    AdvisoryContextPack,
    AdvisoryExecutionStatus,
    AdvisoryStatusDetail,
)
from app.schemas.deepseek_advisory import (
    DEEPSEEK_ADVISORY_MAX_OUTPUT_TOKENS,
    DEEPSEEK_ADVISORY_MAX_RAW_RESPONSE_CHARS,
    DEEPSEEK_ADVISORY_MODEL,
    DEEPSEEK_ADVISORY_STREAM,
    DEEPSEEK_ADVISORY_TEMPERATURE,
    DEEPSEEK_ADVISORY_TRANSPORT_RESPONSE_FORMAT,
    DEEPSEEK_ADVISORY_TRANSPORT_THINKING,
    DeepSeekAdvisoryRequest,
)
from app.services.advisory_artifacts import (
    build_completed_advisory_artifact,
    build_noncompleted_advisory_artifact,
)
from app.services.deepseek_http_transport import (
    DEEPSEEK_CHAT_COMPLETIONS_URL,
    DEEPSEEK_MAX_HTTP_RESPONSE_BYTES,
    DEEPSEEK_MAX_REQUEST_BYTES,
    DEEPSEEK_REQUEST_TIMEOUT_SECONDS,
    DeepSeekHTTPResponse,
    DeepSeekTransport,
    DeepSeekTransportError,
)
from app.services.deepseek_prompt_builder import build_deepseek_advisory_request
from app.services.deepseek_provider_config import DeepSeekProviderConfig
from app.services.deepseek_response_parser import (
    DeepSeekAdvisoryResponseError,
    parse_deepseek_advisory_response,
)

# ---- Safe provider envelope error --------------------------------------------


class DeepSeekProviderResponseError(Exception):
    """Bounded failure extracting/validating the provider chat envelope."""

    def __init__(self, *, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

    def __repr__(self) -> str:
        return f"DeepSeekProviderResponseError(code={self.code!r})"


def _envelope_fail(code: str, message: str) -> None:
    raise DeepSeekProviderResponseError(code=code, message=message)


# ---- Wire payload ------------------------------------------------------------


def build_deepseek_wire_payload(
    request: DeepSeekAdvisoryRequest,
) -> dict[str, object]:
    """Map F7.3 internal request to the exact DeepSeek wire JSON object.

    Translates internal tokens; never includes API key, tools, or
    internal-only field names.
    """
    if not isinstance(request, DeepSeekAdvisoryRequest):
        raise TypeError("request must be a DeepSeekAdvisoryRequest")

    messages: list[dict[str, str]] = [
        {"role": msg.role, "content": msg.content} for msg in request.messages
    ]
    return {
        "model": DEEPSEEK_ADVISORY_MODEL,
        "messages": messages,
        "response_format": dict(DEEPSEEK_ADVISORY_TRANSPORT_RESPONSE_FORMAT),
        "temperature": DEEPSEEK_ADVISORY_TEMPERATURE,
        "max_tokens": DEEPSEEK_ADVISORY_MAX_OUTPUT_TOKENS,
        "thinking": dict(DEEPSEEK_ADVISORY_TRANSPORT_THINKING["thinking"]),
        "stream": DEEPSEEK_ADVISORY_STREAM,
    }


def serialize_deepseek_wire_payload(payload: Mapping[str, object]) -> bytes:
    """Canonical UTF-8 JSON for the wire body. Rejects NaN/Infinity."""
    try:
        text = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("wire payload is not JSON-serializable") from exc
    return text.encode("utf-8")


# ---- Strict JSON helpers (envelope) ------------------------------------------


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _envelope_fail(
                "provider_response_duplicate_key",
                "Provider response JSON contains duplicate object keys.",
            )
        result[key] = value
    return result


def _reject_nonstandard_constant(_value: str) -> None:
    _envelope_fail(
        "provider_response_nonstandard_json",
        "Provider response JSON contains a non-standard numeric constant.",
    )


def _strict_json_loads(text: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonstandard_constant,
        )
    except DeepSeekProviderResponseError:
        raise
    except json.JSONDecodeError:
        _envelope_fail(
            "provider_response_invalid_json",
            "Provider response is not valid JSON.",
        )
    except (ValueError, TypeError):
        _envelope_fail(
            "provider_response_invalid_json",
            "Provider response is not valid JSON.",
        )


# ---- Content-Type ------------------------------------------------------------


def _normalized_media_type(content_type: str | None) -> str | None:
    if content_type is None:
        return None
    if not isinstance(content_type, str):
        return None
    cleaned = content_type.strip()
    if not cleaned:
        return None
    # media-type is before the first ';'
    return cleaned.split(";", 1)[0].strip().lower()


# ---- HTTP status → artifact codes --------------------------------------------


def _map_http_status(status_code: int) -> tuple[AdvisoryExecutionStatus, str, str]:
    """Return (execution_status, code, message) for non-200 responses."""
    if status_code == 400:
        return (
            AdvisoryExecutionStatus.ERROR,
            "provider_request_rejected",
            "The advisory provider rejected the request.",
        )
    if status_code == 401:
        return (
            AdvisoryExecutionStatus.ERROR,
            "provider_authentication_failed",
            "The advisory provider rejected authentication.",
        )
    if status_code == 402:
        return (
            AdvisoryExecutionStatus.UNAVAILABLE,
            "provider_balance_unavailable",
            "The advisory provider reported insufficient balance.",
        )
    if status_code == 422:
        return (
            AdvisoryExecutionStatus.ERROR,
            "provider_request_rejected",
            "The advisory provider rejected the request.",
        )
    if status_code == 429:
        return (
            AdvisoryExecutionStatus.UNAVAILABLE,
            "provider_rate_limited",
            "The advisory provider rate-limited the request.",
        )
    if status_code in (500, 503):
        return (
            AdvisoryExecutionStatus.UNAVAILABLE,
            "provider_unavailable",
            "The advisory provider is unavailable.",
        )
    if 300 <= status_code <= 399:
        return (
            AdvisoryExecutionStatus.ERROR,
            "provider_redirect_rejected",
            "The advisory provider returned a disallowed redirect.",
        )
    if 400 <= status_code <= 499:
        return (
            AdvisoryExecutionStatus.ERROR,
            "provider_request_failed",
            "The advisory provider rejected the request.",
        )
    if 500 <= status_code <= 599:
        return (
            AdvisoryExecutionStatus.UNAVAILABLE,
            "provider_unavailable",
            "The advisory provider is unavailable.",
        )
    return (
        AdvisoryExecutionStatus.ERROR,
        "provider_http_status_unexpected",
        "The advisory provider returned an unexpected HTTP status.",
    )


def _map_transport_error(
    err: DeepSeekTransportError,
) -> tuple[AdvisoryExecutionStatus, str, str]:
    code = err.code
    if code == "timeout":
        return (
            AdvisoryExecutionStatus.UNAVAILABLE,
            "provider_timeout",
            "The advisory provider request timed out.",
        )
    if code == "network_unavailable":
        return (
            AdvisoryExecutionStatus.UNAVAILABLE,
            "provider_network_unavailable",
            "The advisory provider network is unavailable.",
        )
    if code == "tls_failure":
        return (
            AdvisoryExecutionStatus.UNAVAILABLE,
            "provider_tls_unavailable",
            "The advisory provider TLS connection failed.",
        )
    if code == "redirect_rejected":
        return (
            AdvisoryExecutionStatus.ERROR,
            "provider_redirect_rejected",
            "The advisory provider returned a disallowed redirect.",
        )
    if code == "response_too_large":
        return (
            AdvisoryExecutionStatus.ERROR,
            "provider_http_response_too_large",
            "The advisory provider response exceeds the size limit.",
        )
    if code == "invalid_destination":
        return (
            AdvisoryExecutionStatus.ERROR,
            "provider_destination_invalid",
            "The advisory provider destination is invalid.",
        )
    return (
        AdvisoryExecutionStatus.ERROR,
        "provider_request_failed",
        "The advisory provider request failed.",
    )


_PARSER_CODE_MAP: dict[str, str] = {
    "response_empty": "provider_response_empty",
    "response_too_large": "provider_response_too_large",
    "response_invalid_json": "provider_response_invalid_json",
    "response_duplicate_key": "provider_response_duplicate_key",
    "response_nonstandard_json": "provider_response_nonstandard_json",
    "response_schema_invalid": "provider_response_schema_invalid",
    "response_version_unsupported": "provider_response_version_unsupported",
    "response_required_limitations_missing": (
        "provider_response_required_limitations_missing"
    ),
}


def _map_parser_code(parser_code: str) -> str:
    return _PARSER_CODE_MAP.get(parser_code, "provider_response_schema_invalid")


def _status_detail(code: str, message: str) -> AdvisoryStatusDetail:
    return AdvisoryStatusDetail(code=code, message=message)


def _noncompleted(
    *,
    context: AdvisoryContextPack,
    execution_status: AdvisoryExecutionStatus,
    code: str,
    message: str,
) -> AdvisoryArtifact:
    return build_noncompleted_advisory_artifact(
        context=context,
        execution_status=execution_status,
        status_detail=_status_detail(code, message),
        model_name=DEEPSEEK_ADVISORY_MODEL,
    )


# ---- Envelope extraction -----------------------------------------------------


def extract_deepseek_completion_content(
    response: DeepSeekHTTPResponse,
) -> str:
    """Extract final assistant message content from a chat.completion body.

    Validates envelope invariants. Does not store the parsed envelope.
    Raises ``DeepSeekProviderResponseError`` with safe codes only.
    """
    if not isinstance(response, DeepSeekHTTPResponse):
        raise TypeError("response must be a DeepSeekHTTPResponse")

    if len(response.body) > DEEPSEEK_MAX_HTTP_RESPONSE_BYTES:
        _envelope_fail(
            "provider_response_envelope_invalid",
            "Provider response exceeds the allowed size.",
        )

    if b"\x00" in response.body:
        _envelope_fail(
            "provider_response_invalid_json",
            "Provider response contains invalid characters.",
        )

    try:
        text = response.body.decode("utf-8")
    except UnicodeDecodeError:
        _envelope_fail(
            "provider_response_invalid_utf8",
            "Provider response is not valid UTF-8.",
        )

    if not text.strip():
        _envelope_fail(
            "provider_response_invalid_json",
            "Provider response is not valid JSON.",
        )

    parsed = _strict_json_loads(text)
    if not isinstance(parsed, dict):
        _envelope_fail(
            "provider_response_envelope_invalid",
            "Provider response envelope is invalid.",
        )

    if parsed.get("object") != "chat.completion":
        _envelope_fail(
            "provider_response_envelope_invalid",
            "Provider response envelope is invalid.",
        )

    if parsed.get("model") != DEEPSEEK_ADVISORY_MODEL:
        _envelope_fail(
            "provider_model_mismatch",
            "Provider response model does not match the expected model.",
        )

    choices = parsed.get("choices")
    if not isinstance(choices, list) or len(choices) == 0:
        _envelope_fail(
            "provider_completion_missing",
            "Provider response is missing a completion choice.",
        )
    if len(choices) != 1:
        _envelope_fail(
            "provider_response_envelope_invalid",
            "Provider response envelope is invalid.",
        )

    choice = choices[0]
    if not isinstance(choice, dict):
        _envelope_fail(
            "provider_response_envelope_invalid",
            "Provider response envelope is invalid.",
        )

    if choice.get("index") != 0:
        _envelope_fail(
            "provider_response_envelope_invalid",
            "Provider response envelope is invalid.",
        )

    finish_reason = choice.get("finish_reason")
    if finish_reason is None or not isinstance(finish_reason, str) or not finish_reason:
        _envelope_fail(
            "provider_finish_reason_invalid",
            "Provider response finish reason is invalid.",
        )

    # Map finish reasons before reading content when not stop.
    if finish_reason == "length":
        _envelope_fail(
            "provider_output_truncated",
            "Provider output was truncated.",
        )
    if finish_reason == "content_filter":
        _envelope_fail(
            "provider_output_filtered",
            "Provider output was filtered.",
        )
    if finish_reason == "tool_calls":
        _envelope_fail(
            "provider_tool_call_rejected",
            "Provider tool calls are not allowed for advisory.",
        )
    if finish_reason == "insufficient_system_resource":
        _envelope_fail(
            "provider_unavailable",
            "The advisory provider is unavailable.",
        )
    if finish_reason != "stop":
        _envelope_fail(
            "provider_finish_reason_invalid",
            "Provider response finish reason is invalid.",
        )

    message = choice.get("message")
    if not isinstance(message, dict):
        _envelope_fail(
            "provider_completion_missing",
            "Provider response is missing a completion message.",
        )

    if message.get("role") != "assistant":
        _envelope_fail(
            "provider_response_envelope_invalid",
            "Provider response envelope is invalid.",
        )

    # reasoning_content: missing / null / empty string OK; any nonempty value rejected.
    if "reasoning_content" in message:
        reasoning = message["reasoning_content"]
        if reasoning is not None and not (
            isinstance(reasoning, str) and reasoning == ""
        ):
            _envelope_fail(
                "provider_reasoning_content_rejected",
                "Provider reasoning content is not allowed for advisory.",
            )

    # tool_calls: missing / null / empty list OK; nonempty rejected.
    if "tool_calls" in message:
        tool_calls = message["tool_calls"]
        if tool_calls is not None and not (
            isinstance(tool_calls, list) and len(tool_calls) == 0
        ):
            _envelope_fail(
                "provider_tool_call_rejected",
                "Provider tool calls are not allowed for advisory.",
            )

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        _envelope_fail(
            "provider_completion_missing",
            "Provider response is missing completion content.",
        )
    if len(content) > DEEPSEEK_ADVISORY_MAX_RAW_RESPONSE_CHARS:
        _envelope_fail(
            "provider_response_envelope_invalid",
            "Provider completion content exceeds the allowed size.",
        )

    return content


def _map_envelope_error(
    err: DeepSeekProviderResponseError,
) -> tuple[AdvisoryExecutionStatus, str, str]:
    code = err.code
    # provider_unavailable from finish_reason insufficient_system_resource
    if code == "provider_unavailable":
        return (
            AdvisoryExecutionStatus.UNAVAILABLE,
            "provider_unavailable",
            "The advisory provider is unavailable.",
        )
    # All other envelope codes → error with the same code.
    messages = {
        "provider_response_invalid_utf8": "Provider response is not valid UTF-8.",
        "provider_response_invalid_json": "Provider response is not valid JSON.",
        "provider_response_duplicate_key": (
            "Provider response JSON contains duplicate object keys."
        ),
        "provider_response_nonstandard_json": (
            "Provider response JSON contains a non-standard numeric constant."
        ),
        "provider_response_envelope_invalid": (
            "Provider response envelope is invalid."
        ),
        "provider_model_mismatch": (
            "Provider response model does not match the expected model."
        ),
        "provider_completion_missing": (
            "Provider response is missing a completion choice."
        ),
        "provider_reasoning_content_rejected": (
            "Provider reasoning content is not allowed for advisory."
        ),
        "provider_tool_call_rejected": (
            "Provider tool calls are not allowed for advisory."
        ),
        "provider_output_truncated": "Provider output was truncated.",
        "provider_output_filtered": "Provider output was filtered.",
        "provider_finish_reason_invalid": (
            "Provider response finish reason is invalid."
        ),
    }
    return (
        AdvisoryExecutionStatus.ERROR,
        code,
        messages.get(code, "Provider response is invalid."),
    )


# ---- Main executor -----------------------------------------------------------


def execute_deepseek_advisory(
    context: AdvisoryContextPack,
    *,
    config: DeepSeekProviderConfig | None,
    transport: DeepSeekTransport,
) -> AdvisoryArtifact:
    """Execute one DeepSeek advisory attempt and return an AdvisoryArtifact.

    At most one transport ``post`` call. Missing config yields unavailable
    without network. Expected provider/transport/parser failures become
    noncompleted artifacts; unexpected programming errors propagate.
    """
    if not isinstance(context, AdvisoryContextPack):
        raise TypeError("context must be an AdvisoryContextPack")
    if config is not None and not isinstance(config, DeepSeekProviderConfig):
        raise TypeError("config must be DeepSeekProviderConfig or None")
    if transport is None:
        raise TypeError("transport is required")

    if config is None:
        return _noncompleted(
            context=context,
            execution_status=AdvisoryExecutionStatus.UNAVAILABLE,
            code="provider_not_configured",
            message="The advisory provider is not configured.",
        )

    # 1. Build F7.3 internal request (pure).
    request = build_deepseek_advisory_request(context)

    # 2. Wire payload + size gate (no network yet).
    wire = build_deepseek_wire_payload(request)
    try:
        body = serialize_deepseek_wire_payload(wire)
    except ValueError:
        return _noncompleted(
            context=context,
            execution_status=AdvisoryExecutionStatus.ERROR,
            code="provider_request_failed",
            message="The advisory provider request could not be prepared.",
        )

    if len(body) > DEEPSEEK_MAX_REQUEST_BYTES:
        return _noncompleted(
            context=context,
            execution_status=AdvisoryExecutionStatus.ERROR,
            code="provider_request_too_large",
            message="The advisory provider request exceeds the size limit.",
        )

    # 3. Single transport attempt.
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {config.api_key}",
    }
    try:
        http_response = transport.post(
            url=DEEPSEEK_CHAT_COMPLETIONS_URL,
            headers=headers,
            body=body,
            timeout_seconds=DEEPSEEK_REQUEST_TIMEOUT_SECONDS,
            max_response_bytes=DEEPSEEK_MAX_HTTP_RESPONSE_BYTES,
        )
    except DeepSeekTransportError as err:
        status, code, message = _map_transport_error(err)
        return _noncompleted(
            context=context,
            execution_status=status,
            code=code,
            message=message,
        )

    if not isinstance(http_response, DeepSeekHTTPResponse):
        raise TypeError("transport.post must return DeepSeekHTTPResponse")

    # 4. HTTP status mapping (body ignored for non-200 — not stored).
    if http_response.status_code != 200:
        status, code, message = _map_http_status(http_response.status_code)
        return _noncompleted(
            context=context,
            execution_status=status,
            code=code,
            message=message,
        )

    # 5. Content-Type for 200.
    media = _normalized_media_type(http_response.content_type)
    if media != "application/json":
        return _noncompleted(
            context=context,
            execution_status=AdvisoryExecutionStatus.ERROR,
            code="provider_content_type_invalid",
            message="The advisory provider returned an invalid content type.",
        )

    # 6. Envelope extraction (finish_reason + content).
    try:
        completion_text = extract_deepseek_completion_content(http_response)
    except DeepSeekProviderResponseError as err:
        status, code, message = _map_envelope_error(err)
        return _noncompleted(
            context=context,
            execution_status=status,
            code=code,
            message=message,
        )

    # 7. F7.3 strict advisory content parser.
    try:
        content = parse_deepseek_advisory_response(completion_text)
    except DeepSeekAdvisoryResponseError as err:
        mapped = _map_parser_code(err.code)
        return _noncompleted(
            context=context,
            execution_status=AdvisoryExecutionStatus.ERROR,
            code=mapped,
            message="The advisory provider response content is invalid.",
        )

    # 8. Completed artifact via F7.1 builder.
    return build_completed_advisory_artifact(
        context=context,
        content=content,
        model_name=DEEPSEEK_ADVISORY_MODEL,
    )
