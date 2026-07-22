"""One-call, bounded DataHub search execution and result normalization."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from .config import DATAHUB_MCP_PROTOCOL_VERSION, DataHubMCPConfig
from .initialization import DataHubMCPSession
from .mcp_protocol import DataHubMCPProtocolError, parse_http_response, parse_strict_json_object
from .search_contract import (
    DataHubReadToolDiscoveryBundle,
    DataHubSearchArgumentPlan,
    DataHubSearchContractError,
    build_datahub_search_tools_call_request,
    serialize_datahub_search_tools_call_request,
)
from .transport import DataHubMCPTransport

MAX_CONTENT_BLOCKS = 8
MAX_TEXT_CHARS = 262_144
MAX_STRUCTURED_BYTES = 524_288
MAX_RESULTS = 10
MAX_TOTAL = 1_000_000
RESULT_VERSION = "1.0"
_URN_PREFIX = "urn:li:"
_DATASET_PREFIX = "urn:li:dataset:"
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")


class DataHubSearchExecutionError(ValueError):
    """Safe execution error with no provider-controlled detail."""

    def __init__(self, code: str, message: str = "DataHub search execution failed.", *, retryable: bool = False) -> None:
        self.code = code
        self.message = message
        self.retryable = retryable
        super().__init__(message)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _safe_urn(value: Any) -> str:
    if not isinstance(value, str) or not 8 <= len(value) <= 1024 or not value.startswith(_URN_PREFIX):
        raise ValueError("invalid structural URN")
    if value != value.strip() or "\x00" in value or any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ValueError("invalid structural URN")
    return value


def _safe_name(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or "\x00" in value or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ValueError("invalid display name")
    value = value.strip()
    if len(value) > 512:
        raise ValueError("display name is too large")
    return value or None


class DataHubDatasetSearchRecord(_Strict):
    dataset_urn: str
    display_name: str | None = None
    source_position: StrictInt = Field(ge=0, le=9)

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str:
        return _safe_urn(value)


class DataHubSearchExecutionResult(_Strict):
    request_id: StrictInt = Field(ge=3, le=12)
    next_request_id: StrictInt = Field(ge=4, le=13)
    search_request_fingerprint: str
    input_schema_fingerprint: str
    records: tuple[DataHubDatasetSearchRecord, ...]
    provider_start: StrictInt = Field(ge=0, le=0)
    provider_count: StrictInt = Field(ge=0, le=10)
    provider_total: StrictInt = Field(ge=0, le=MAX_TOTAL)
    non_dataset_result_count: StrictInt = Field(ge=0, le=10)
    result_version: str = RESULT_VERSION

    @field_validator("search_request_fingerprint", "input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        if not isinstance(value, str) or not _FINGERPRINT.fullmatch(value):
            raise ValueError("invalid fingerprint")
        return value

    @model_validator(mode="after")
    def invariants(self) -> "DataHubSearchExecutionResult":
        if self.next_request_id != self.request_id + 1 or self.provider_count != len(self.records) + self.non_dataset_result_count or self.provider_total < self.provider_count or self.result_version != RESULT_VERSION:
            raise ValueError("invalid search execution result")
        if len({record.dataset_urn for record in self.records}) != len(self.records):
            raise ValueError("duplicate normalized record")
        return self


def _error(code: str) -> DataHubSearchExecutionError:
    return DataHubSearchExecutionError(code)


def _canonical_size(value: dict[str, Any]) -> int:
    try:
        return len(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))
    except (TypeError, ValueError, OverflowError):
        raise _error("invalid_search_tool_result") from None


def _validate_content(result: dict[str, Any]) -> list[dict[str, Any]]:
    if "content" not in result or not isinstance(result["content"], list):
        raise _error("invalid_search_tool_result")
    blocks = result["content"]
    if len(blocks) > MAX_CONTENT_BLOCKS:
        raise _error("unsupported_search_content")
    text_blocks: list[dict[str, Any]] = []
    total_chars = 0
    for block in blocks:
        if not isinstance(block, dict) or block.get("type") != "text" or not isinstance(block.get("text"), str):
            raise _error("unsupported_search_content")
        text = block["text"]
        if "\x00" in text or len(text) > MAX_TEXT_CHARS:
            raise _error("search_content_too_large")
        total_chars += len(text)
        if total_chars > MAX_TEXT_CHARS:
            raise _error("search_content_too_large")
        text_blocks.append(block)
    return text_blocks


def _select_payload(result: dict[str, Any], text_blocks: list[dict[str, Any]]) -> dict[str, Any]:
    if "structuredContent" in result:
        payload = result["structuredContent"]
        if not isinstance(payload, dict):
            raise _error("missing_search_result_payload")
        if _canonical_size(payload) > MAX_STRUCTURED_BYTES:
            raise _error("search_content_too_large")
        return payload
    if len(text_blocks) != 1:
        raise _error("missing_search_result_payload")
    try:
        return parse_strict_json_object(text_blocks[0]["text"])
    except DataHubMCPProtocolError:
        raise _error("invalid_search_result_payload") from None


def _parse_payload(payload: dict[str, Any]) -> tuple[tuple[DataHubDatasetSearchRecord, ...], int, int, int, int]:
    if any(key not in payload for key in ("start", "count", "total", "searchResults")):
        raise _error("invalid_search_result_payload")
    start, count, total, entries = (payload["start"], payload["count"], payload["total"], payload["searchResults"])
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (start, count, total)):
        raise _error("invalid_search_result_payload")
    if start != 0 or not 0 <= count <= MAX_RESULTS or not 0 <= total <= MAX_TOTAL or total < count or not isinstance(entries, list) or len(entries) > MAX_RESULTS:
        raise _error("invalid_search_result_payload")
    if count != len(entries):
        raise _error("search_result_count_mismatch")
    records: list[DataHubDatasetSearchRecord] = []
    seen: set[str] = set()
    non_dataset = 0
    for position, item in enumerate(entries):
        if not isinstance(item, dict) or not isinstance(item.get("entity"), dict):
            raise _error("invalid_search_result_entity")
        entity = item["entity"]
        urn = entity.get("urn")
        try:
            urn = _safe_urn(urn)
        except ValueError:
            raise _error("invalid_search_result_entity") from None
        if urn in seen:
            raise _error("duplicate_search_result_urn")
        seen.add(urn)
        properties = entity.get("properties")
        if properties is not None and not isinstance(properties, dict):
            raise _error("invalid_search_result_entity")
        name = _safe_name(properties.get("name") if isinstance(properties, dict) else None)
        if not urn.startswith(_DATASET_PREFIX):
            non_dataset += 1
            continue
        try:
            records.append(DataHubDatasetSearchRecord(dataset_urn=urn, display_name=name, source_position=position))
        except ValueError:
            raise _error("invalid_search_result_entity") from None
    return tuple(records), start, count, total, non_dataset


def execute_datahub_search(*, config: DataHubMCPConfig, session: DataHubMCPSession, discovery: DataHubReadToolDiscoveryBundle, argument_plan: DataHubSearchArgumentPlan, transport: DataHubMCPTransport) -> DataHubSearchExecutionResult:
    if not isinstance(config, DataHubMCPConfig) or not isinstance(session, DataHubMCPSession) or session.endpoint_url != config.endpoint_url or session.protocol_version != DATAHUB_MCP_PROTOCOL_VERSION or not session.tools_supported:
        raise _error("search_execution_context_mismatch")
    if not isinstance(discovery, DataHubReadToolDiscoveryBundle) or not isinstance(argument_plan, DataHubSearchArgumentPlan):
        raise _error("search_execution_context_mismatch")
    search = next((tool for tool in discovery.catalog.tools if tool.name.value == "search"), None)
    if search is None or search.input_schema_fingerprint != discovery.search_contract.input_schema_fingerprint or argument_plan.input_schema_fingerprint != discovery.search_contract.input_schema_fingerprint:
        raise _error("search_execution_context_mismatch")
    try:
        request = build_datahub_search_tools_call_request(discovery=discovery, argument_plan=argument_plan)
        body = serialize_datahub_search_tools_call_request(discovery=discovery, argument_plan=argument_plan)
    except DataHubSearchContractError as exc:
        raise _error("search_execution_context_mismatch" if exc.code == "search_schema_fingerprint_mismatch" else exc.code) from None
    request_fingerprint = hashlib.sha256(body).hexdigest()
    try:
        response = transport.post_request(body, session_id=session.session_id, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION)
        parsed = parse_http_response(response, expected_id=request.id)
    except DataHubMCPProtocolError:
        raise
    if parsed.error is not None or parsed.result is None:
        raise _error("search_tool_execution_failed")
    result = parsed.result
    is_error = result.get("isError", False)
    if not isinstance(is_error, bool):
        raise _error("invalid_search_tool_result")
    text_blocks = _validate_content(result)
    if is_error:
        raise _error("search_tool_execution_failed")
    payload = _select_payload(result, text_blocks)
    records, start, count, total, non_dataset = _parse_payload(payload)
    return DataHubSearchExecutionResult(request_id=request.id, next_request_id=request.id + 1, search_request_fingerprint=request_fingerprint, input_schema_fingerprint=argument_plan.input_schema_fingerprint, records=records, provider_start=start, provider_count=count, provider_total=total, non_dataset_result_count=non_dataset)
