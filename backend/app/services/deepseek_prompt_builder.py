"""Server-owned DeepSeek advisory request builder (phase F7.3).

Pure function: AdvisoryContextPack → DeepSeekAdvisoryRequest.

Does **not**:
- call DeepSeek or any network endpoint
- read environment variables or API keys
- accept caller model / system / temperature / thinking_mode overrides
- implement F7.4 transport / HTTP payload assembly
- log prompts or write files
- mutate the input context pack

Always locks ``thinking_mode=disabled`` so temperature=0.0 is meaningful
under DeepSeek V4 (thinking mode would ignore temperature).
"""

from __future__ import annotations

from app.schemas.advisory import AdvisoryContextPack
from app.schemas.deepseek_advisory import (
    CONTEXT_JSON_END,
    CONTEXT_JSON_START,
    DEEPSEEK_ADVISORY_MAX_OUTPUT_TOKENS,
    DEEPSEEK_ADVISORY_MODEL,
    DEEPSEEK_ADVISORY_REQUEST_CONTRACT_VERSION,
    DEEPSEEK_ADVISORY_RESPONSE_FORMAT,
    DEEPSEEK_ADVISORY_STREAM,
    DEEPSEEK_ADVISORY_SYSTEM_INSTRUCTION,
    DEEPSEEK_ADVISORY_TEMPERATURE,
    DEEPSEEK_ADVISORY_THINKING_MODE,
    DEEPSEEK_ADVISORY_TOOLS_ENABLED,
    DeepSeekAdvisoryMessage,
    DeepSeekAdvisoryRequest,
)
from app.utils.fingerprint import canonical_json_bytes


def build_deepseek_advisory_request(
    context: AdvisoryContextPack,
) -> DeepSeekAdvisoryRequest:
    """Build the fixed internal DeepSeek advisory request from a context pack.

    The user message is only:

        CONTEXT_JSON_START
        <canonical JSON of the full AdvisoryContextPack>
        CONTEXT_JSON_END

    No caller natural-language instructions are accepted. The same context
    always yields an identical request (deterministic serialization).

    ``thinking_mode`` is always ``disabled`` (server-owned). Internal
    ``response_format`` remains the token ``json_object``; F7.4 must map it
    to ``{"type": "json_object"}`` and map ``thinking_mode`` to
    ``{"thinking": {"type": "disabled"}}`` on the wire.
    """
    if not isinstance(context, AdvisoryContextPack):
        raise TypeError("context must be an AdvisoryContextPack")

    payload = context.model_dump(mode="json")
    canonical = canonical_json_bytes(payload).decode("utf-8")
    user_content = f"{CONTEXT_JSON_START}\n{canonical}\n{CONTEXT_JSON_END}"

    return DeepSeekAdvisoryRequest(
        model=DEEPSEEK_ADVISORY_MODEL,
        messages=[
            DeepSeekAdvisoryMessage(
                role="system",
                content=DEEPSEEK_ADVISORY_SYSTEM_INSTRUCTION,
            ),
            DeepSeekAdvisoryMessage(
                role="user",
                content=user_content,
            ),
        ],
        response_format=DEEPSEEK_ADVISORY_RESPONSE_FORMAT,
        temperature=DEEPSEEK_ADVISORY_TEMPERATURE,
        max_output_tokens=DEEPSEEK_ADVISORY_MAX_OUTPUT_TOKENS,
        thinking_mode=DEEPSEEK_ADVISORY_THINKING_MODE,
        stream=DEEPSEEK_ADVISORY_STREAM,
        tools_enabled=DEEPSEEK_ADVISORY_TOOLS_ENABLED,
        request_contract_version=DEEPSEEK_ADVISORY_REQUEST_CONTRACT_VERSION,
    )
