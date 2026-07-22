"""Strict DeepSeek advisory response parser (phase F7.3).

Parses untrusted raw provider text into F7.1 ``AdvisoryContent``.

Does **not**:
- call DeepSeek or any network endpoint
- retry or repair invalid JSON / Markdown fences
- log or return the raw response on error
- write files or read environment variables
- map parse failures to non-completed artifacts (F7.4+)
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.schemas.advisory import AdvisoryContent
from app.schemas.deepseek_advisory import (
    DEEPSEEK_ADVISORY_MAX_RAW_RESPONSE_CHARS,
    DEEPSEEK_ADVISORY_RESPONSE_VERSION,
    REQUIRED_ADVISORY_LIMITATIONS,
    DeepSeekAdvisoryResponse,
)

# ---- Safe error --------------------------------------------------------------


class DeepSeekAdvisoryResponseError(Exception):
    """Bounded, safe failure while parsing a DeepSeek advisory response.

    Stores only ``code`` and a generic ``message``. Never stores raw response
    text, excerpts, parser line/column content, prompts, or API keys.
    """

    def __init__(self, *, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def _fail(code: str, message: str) -> None:
    raise DeepSeekAdvisoryResponseError(code=code, message=message)


# ---- Strict JSON helpers -----------------------------------------------------


def _reject_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    """object_pairs_hook: reject duplicate keys at every object level."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(
                "response_duplicate_key",
                "Provider response JSON contains duplicate object keys.",
            )
        result[key] = value
    return result


def _reject_nonstandard_constant(_value: str) -> None:
    """parse_constant: reject NaN / Infinity / -Infinity."""
    _fail(
        "response_nonstandard_json",
        "Provider response JSON contains a non-standard numeric constant.",
    )


def _strict_json_loads(text: str) -> Any:
    """Parse JSON with duplicate-key and non-standard-constant rejection."""
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonstandard_constant,
        )
    except DeepSeekAdvisoryResponseError:
        raise
    except json.JSONDecodeError:
        _fail(
            "response_invalid_json",
            "Provider response is not valid JSON.",
        )
    except (ValueError, TypeError):
        _fail(
            "response_invalid_json",
            "Provider response is not valid JSON.",
        )


# ---- Required limitations ----------------------------------------------------


def _validate_required_limitations(content: AdvisoryContent) -> None:
    required = list(REQUIRED_ADVISORY_LIMITATIONS)
    limitations = content.limitations
    if len(limitations) < 2:
        _fail(
            "response_required_limitations_missing",
            "Provider response is missing required authority limitations.",
        )
    if limitations[0] != required[0] or limitations[1] != required[1]:
        _fail(
            "response_required_limitations_missing",
            "Provider response is missing required authority limitations.",
        )
    if limitations.count(required[0]) != 1 or limitations.count(required[1]) != 1:
        _fail(
            "response_required_limitations_missing",
            "Provider response is missing required authority limitations.",
        )


# ---- Public parser -----------------------------------------------------------


def parse_deepseek_advisory_response(raw_response: str) -> AdvisoryContent:
    """Parse raw provider text into validated ``AdvisoryContent``.

    Strict rules:
    - non-empty, size-bounded, no null bytes
    - exact JSON object (no Markdown fence repair, no prose extraction)
    - duplicate keys rejected
    - NaN / Infinity rejected
    - response_version must be 1.0
    - content must satisfy AdvisoryContent + required limitations
    - returns only AdvisoryContent (never raw text or provider metadata)
    """
    if not isinstance(raw_response, str):
        _fail(
            "response_schema_invalid",
            "Provider response must be a string.",
        )

    if "\x00" in raw_response:
        _fail(
            "response_invalid_json",
            "Provider response contains invalid characters.",
        )

    if not raw_response or not raw_response.strip():
        _fail(
            "response_empty",
            "Provider response is empty.",
        )

    if len(raw_response) > DEEPSEEK_ADVISORY_MAX_RAW_RESPONSE_CHARS:
        _fail(
            "response_too_large",
            "Provider response exceeds the maximum allowed size.",
        )

    stripped = raw_response.strip()
    # Reject Markdown code fences without attempting repair.
    if stripped.startswith("```") or stripped.startswith("`"):
        _fail(
            "response_invalid_json",
            "Provider response is not valid JSON.",
        )
    if not stripped.startswith("{"):
        _fail(
            "response_schema_invalid",
            "Provider response must be a JSON object.",
        )

    parsed = _strict_json_loads(raw_response)

    if not isinstance(parsed, dict):
        _fail(
            "response_schema_invalid",
            "Provider response must be a JSON object.",
        )

    version = parsed.get("response_version")
    if version is None:
        _fail(
            "response_schema_invalid",
            "Provider response does not match the required schema.",
        )
    if version != DEEPSEEK_ADVISORY_RESPONSE_VERSION:
        _fail(
            "response_version_unsupported",
            "Provider response version is not supported.",
        )

    # Validate content first so required-limitation failures get a dedicated code.
    content_raw = parsed.get("content")
    if not isinstance(content_raw, dict):
        _fail(
            "response_schema_invalid",
            "Provider response does not match the required schema.",
        )

    try:
        content = AdvisoryContent.model_validate(content_raw)
    except ValidationError:
        _fail(
            "response_schema_invalid",
            "Provider response does not match the required schema.",
        )

    _validate_required_limitations(content)

    # Full envelope validation (extra="forbid", banned fields, frozen contract).
    try:
        envelope = DeepSeekAdvisoryResponse.model_validate(parsed)
    except ValidationError:
        _fail(
            "response_schema_invalid",
            "Provider response does not match the required schema.",
        )
    except ValueError:
        _fail(
            "response_schema_invalid",
            "Provider response does not match the required schema.",
        )

    return envelope.content
