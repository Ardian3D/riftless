"""F8.3D3 bounded column-level downstream lineage execution and normalization.

This module executes exactly one column-level ``get_lineage`` request from
the locked F8.3D1 plan, continues the request-ID chain after F8.3D2, validates
the MCP envelope and downstream-direction payload, normalizes at most thirty
downstream dataset targets with bounded compact ``lineageColumns`` endpoint
observations, and discards the raw provider response. It never executes the
dataset-level plan again, never calls a path-between capability, and never
treats missing columns as proof of no impact.
"""

from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator

from app.schemas.datahub_context import DataHubLineageRelation

from .asset_resolution import DataHubAssetResolutionStatus, _dataset_urn_parts, _identity_text, _norm
from .config import DATAHUB_MCP_PROTOCOL_VERSION, DataHubMCPConfig
from .dataset_lineage_execution import DataHubDatasetLineageExecutionResult, DataHubDownstreamObservation
from .initialization import DataHubMCPSession
from .lineage_contract import (
    DataHubColumnLineageArgumentPlan,
    DataHubLineageContext,
    DataHubLineageContractError,
    build_datahub_column_lineage_tools_call_request,
    serialize_datahub_column_lineage_tools_call_request,
)
from .mcp_protocol import DataHubMCPProtocolError, parse_http_response, parse_strict_json_object
from .schema_execution import DataHubSchemaFieldsExecutionResult
from .search_execution import (
    MAX_STRUCTURED_BYTES,
    DataHubSearchExecutionError,
    _canonical_size,
    _safe_name,
    _safe_urn,
    _validate_content,
)
from .transport import DataHubMCPTransport

RESULT_VERSION = "1.0"
SLICE_VERSION = "1.0"
MAX_TARGETS = 30
MAX_PROVIDER_TOTAL = 1_000_000
MAX_LINEAGE_COLUMNS_PER_TARGET = 64
MAX_TOTAL_LINEAGE_COLUMNS = 256
MAX_LINEAGE_COLUMN_CHARS = 512
_DATASET_PREFIX = "urn:li:dataset:"
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")


class DataHubColumnLineageExecutionError(ValueError):
    """Safe, non-retryable column-lineage execution error."""

    def __init__(self, code: str, message: str = "DataHub column lineage execution failed.", *, retryable: bool = False) -> None:
        self.code = code
        self.message = message
        self.retryable = retryable
        super().__init__(message)


class _StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class DataHubColumnLineageObservation(_StrEnum):
    OBSERVED = "observed"
    NOT_OBSERVED = "not_observed"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _InvalidLineageColumn(ValueError):
    pass


class _DuplicateLineageColumn(ValueError):
    pass


def _error(code: str) -> DataHubColumnLineageExecutionError:
    return DataHubColumnLineageExecutionError(code)


def _hex64(value: Any) -> str:
    if not isinstance(value, str) or not _FINGERPRINT.fullmatch(value):
        raise ValueError("invalid fingerprint")
    return value


class DataHubColumnDownstreamTarget(_Strict):
    """Frozen normalized downstream dataset target with compact column endpoints."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    dataset_urn: str
    display_name: str | None = None
    relation: DataHubLineageRelation
    depth: StrictInt
    lineage_columns: tuple[str, ...] = Field(default_factory=tuple, max_length=MAX_LINEAGE_COLUMNS_PER_TARGET)

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: Any) -> str:
        value = _safe_urn(value)
        if not value.startswith(_DATASET_PREFIX):
            raise ValueError("invalid target dataset URN")
        return value

    @field_validator("display_name")
    @classmethod
    def display_ok(cls, value: Any) -> str | None:
        return _safe_name(value)

    @field_validator("lineage_columns")
    @classmethod
    def columns_ok(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_lineage_column_text(item) for item in value)

    @model_validator(mode="after")
    def invariants(self) -> "DataHubColumnDownstreamTarget":
        if self.relation is not DataHubLineageRelation.DOWNSTREAM or self.depth != 1:
            raise ValueError("invalid downstream target relation or depth")
        return self


class DataHubColumnLineageSlice(_Strict):
    """Bounded normalized column-level downstream observation for one source."""

    source_dataset_urn: str
    source_column: str
    targets: tuple[DataHubColumnDownstreamTarget, ...] = Field(default_factory=tuple, max_length=MAX_TARGETS)
    column_lineage_observation: DataHubColumnLineageObservation
    provider_total: StrictInt | None = Field(default=None, ge=0, le=MAX_PROVIDER_TOTAL)
    provider_offset: StrictInt | None = Field(default=None, ge=0, le=0)
    provider_returned: StrictInt | None = Field(default=None, ge=0, le=MAX_TARGETS)
    provider_has_more: StrictBool | None = None
    provider_truncated_due_to_token_budget: StrictBool | None = None
    slice_version: str = SLICE_VERSION

    @field_validator("source_dataset_urn")
    @classmethod
    def source_ok(cls, value: Any) -> str:
        value = _safe_urn(value)
        if not value.startswith(_DATASET_PREFIX):
            raise ValueError("invalid source dataset URN")
        return value

    @field_validator("source_column")
    @classmethod
    def column_ok(cls, value: Any) -> str:
        return _identity_text(value, name="source_column", max_len=256)

    @model_validator(mode="after")
    def invariants(self) -> "DataHubColumnLineageSlice":
        if self.slice_version != SLICE_VERSION:
            raise ValueError("invalid column lineage slice version")
        if self.provider_returned is not None and self.provider_returned != len(self.targets):
            raise ValueError("invalid provider returned count")
        if self.provider_total is not None and self.provider_total < len(self.targets):
            raise ValueError("invalid provider total")
        urns = [target.dataset_urn for target in self.targets]
        if len(set(urns)) != len(urns):
            raise ValueError("duplicate downstream target")
        total_columns = sum(len(target.lineage_columns) for target in self.targets)
        if total_columns > MAX_TOTAL_LINEAGE_COLUMNS:
            raise ValueError("total lineage column bound exceeded")
        has_columns = any(len(target.lineage_columns) > 0 for target in self.targets)
        if self.column_lineage_observation is DataHubColumnLineageObservation.OBSERVED and not has_columns:
            raise ValueError("observed requires at least one lineage column")
        if self.column_lineage_observation is DataHubColumnLineageObservation.NOT_OBSERVED and has_columns:
            raise ValueError("not_observed requires no lineage columns")
        return self


class DataHubColumnLineageExecutionResult(_Strict):
    request_id: StrictInt = Field(gt=0)
    next_request_id: StrictInt = Field(gt=0)
    column_lineage_request_fingerprint: str
    input_schema_fingerprint: str
    source_dataset_urn: str
    source_column: str
    column_lineage_slice: DataHubColumnLineageSlice
    result_version: str = RESULT_VERSION

    @field_validator("column_lineage_request_fingerprint", "input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        return _hex64(value)

    @field_validator("source_dataset_urn")
    @classmethod
    def source_ok(cls, value: Any) -> str:
        value = _safe_urn(value)
        if not value.startswith(_DATASET_PREFIX):
            raise ValueError("invalid source dataset URN")
        return value

    @field_validator("source_column")
    @classmethod
    def column_ok(cls, value: Any) -> str:
        return _identity_text(value, name="source_column", max_len=256)

    @model_validator(mode="after")
    def invariants(self) -> "DataHubColumnLineageExecutionResult":
        if self.next_request_id != self.request_id + 1 or self.result_version != RESULT_VERSION:
            raise ValueError("invalid column lineage execution result")
        return self


def _lineage_column_text(value: Any) -> str:
    if not isinstance(value, str):
        raise _InvalidLineageColumn("invalid lineage column")
    if "\x00" in value or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise _InvalidLineageColumn("invalid lineage column")
    result = value.strip()
    if not result:
        raise _InvalidLineageColumn("invalid lineage column")
    if len(result) > MAX_LINEAGE_COLUMN_CHARS:
        raise _InvalidLineageColumn("invalid lineage column")
    return result


def _validate_column_content(result: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        return _validate_content(result)
    except DataHubSearchExecutionError as exc:
        mapping = {
            "invalid_search_tool_result": "invalid_column_lineage_tool_result",
            "unsupported_search_content": "unsupported_column_lineage_content",
            "search_content_too_large": "column_lineage_content_too_large",
        }
        code = mapping.get(exc.code)
        if code is None:
            raise _error("invalid_column_lineage_tool_result") from None
        raise _error(code) from None


def _column_canonical_size(value: dict[str, Any]) -> int:
    try:
        return _canonical_size(value)
    except DataHubSearchExecutionError:
        raise _error("invalid_column_lineage_payload") from None


def _select_column_payload(result: dict[str, Any], text_blocks: list[dict[str, Any]]) -> dict[str, Any]:
    if "structuredContent" in result:
        payload = result["structuredContent"]
        if not isinstance(payload, dict):
            raise _error("invalid_column_lineage_payload")
        if _column_canonical_size(payload) > MAX_STRUCTURED_BYTES:
            raise _error("column_lineage_content_too_large")
        return payload
    if len(text_blocks) != 1:
        raise _error("missing_column_lineage_payload")
    try:
        return parse_strict_json_object(text_blocks[0]["text"])
    except DataHubMCPProtocolError:
        raise _error("invalid_column_lineage_payload") from None


def _optional_int(payload: dict[str, Any], key: str, *, lo: int, hi: int) -> int | None:
    if key not in payload:
        return None
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise _error("invalid_column_lineage_payload")
    if not lo <= value <= hi:
        raise _error("invalid_column_lineage_payload")
    return value


def _optional_bool(payload: dict[str, Any], key: str) -> bool | None:
    if key not in payload:
        return None
    value = payload[key]
    if not isinstance(value, bool):
        raise _error("invalid_column_lineage_payload")
    return value


def _upstream_has_data(obj: dict[str, Any]) -> bool:
    search_results = obj.get("searchResults")
    if isinstance(search_results, list) and len(search_results) > 0:
        return True
    total = obj.get("total")
    if isinstance(total, int) and not isinstance(total, bool) and total > 0:
        return True
    return False


def _extract_lineage_columns(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list):
        raise _InvalidLineageColumn("invalid lineage column")
    result: list[str] = []
    seen: set[str] = set()
    for item in raw:
        column = _lineage_column_text(item)
        normalized = _norm(column)
        if normalized in seen:
            raise _DuplicateLineageColumn("duplicate lineage column")
        seen.add(normalized)
        result.append(column)
    return tuple(result)


def _normalize_column_target(item: Any) -> DataHubColumnDownstreamTarget:
    if not isinstance(item, dict):
        raise _error("invalid_column_lineage_target")
    entity = item.get("entity")
    if not isinstance(entity, dict):
        raise _error("invalid_column_lineage_target")
    urn = entity.get("urn")
    try:
        urn = _safe_urn(urn)
        if not urn.startswith(_DATASET_PREFIX):
            raise ValueError("non-dataset URN")
    except ValueError:
        raise _error("invalid_column_lineage_target") from None
    raw_type = entity.get("type")
    if raw_type is not None:
        if not isinstance(raw_type, str):
            raise _error("invalid_column_lineage_target")
        if raw_type.strip().lower() != "dataset":
            raise _error("invalid_column_lineage_target")
    if "degree" not in item:
        raise _error("invalid_column_lineage_target")
    degree = item["degree"]
    if isinstance(degree, bool) or not isinstance(degree, int) or degree != 1:
        raise _error("invalid_column_lineage_target")
    try:
        display_name = _safe_name(entity.get("name"))
    except ValueError:
        raise _error("invalid_column_lineage_target") from None
    try:
        if "lineageColumns" in item:
            lineage_columns = _extract_lineage_columns(item["lineageColumns"])
        else:
            lineage_columns = ()
    except _InvalidLineageColumn:
        raise _error("invalid_lineage_column")
    except _DuplicateLineageColumn:
        raise _error("duplicate_lineage_column")
    try:
        return DataHubColumnDownstreamTarget(dataset_urn=urn, display_name=display_name, relation=DataHubLineageRelation.DOWNSTREAM, depth=1, lineage_columns=lineage_columns)
    except ValueError:
        raise _error("invalid_column_lineage_target") from None


def _parse_column_downstreams(payload: dict[str, Any]) -> tuple[tuple[DataHubColumnDownstreamTarget, ...], int | None, int | None, int | None, bool | None, bool | None]:
    if "downstreams" not in payload:
        raise _error("column_lineage_direction_mismatch")
    downstreams = payload["downstreams"]
    if not isinstance(downstreams, dict):
        raise _error("invalid_column_lineage_payload")
    if "upstreams" in payload:
        upstreams = payload["upstreams"]
        if upstreams is not None and not isinstance(upstreams, dict):
            raise _error("invalid_column_lineage_payload")
        if isinstance(upstreams, dict) and _upstream_has_data(upstreams):
            raise _error("column_lineage_direction_mismatch")
    results: list[Any] = []
    if "searchResults" in downstreams:
        value = downstreams["searchResults"]
        if not isinstance(value, list):
            raise _error("invalid_column_lineage_payload")
        if len(value) > MAX_TARGETS:
            raise _error("column_lineage_count_mismatch")
        results = value
    nonempty = len(results) > 0
    if nonempty and ("offset" not in downstreams or "returned" not in downstreams or "hasMore" not in downstreams):
        raise _error("invalid_column_lineage_payload")
    offset = _optional_int(downstreams, "offset", lo=0, hi=0)
    returned = _optional_int(downstreams, "returned", lo=0, hi=MAX_TARGETS)
    has_more = _optional_bool(downstreams, "hasMore")
    truncated = _optional_bool(downstreams, "truncatedDueToTokenBudget")
    total = _optional_int(downstreams, "total", lo=0, hi=MAX_PROVIDER_TOTAL)
    if returned is not None and returned != len(results):
        raise _error("column_lineage_count_mismatch")
    if total is not None and total < len(results):
        raise _error("column_lineage_count_mismatch")
    targets: list[DataHubColumnDownstreamTarget] = []
    seen_urns: set[str] = set()
    total_columns = 0
    for item in results:
        target = _normalize_column_target(item)
        if target.dataset_urn in seen_urns:
            raise _error("duplicate_column_lineage_target")
        seen_urns.add(target.dataset_urn)
        total_columns += len(target.lineage_columns)
        if total_columns > MAX_TOTAL_LINEAGE_COLUMNS:
            raise _error("column_lineage_count_mismatch")
        targets.append(target)
    return tuple(targets), total, offset, returned, has_more, truncated


def execute_datahub_column_lineage(*, config: DataHubMCPConfig, session: DataHubMCPSession, lineage_context: DataHubLineageContext, column_plan: DataHubColumnLineageArgumentPlan, dataset_lineage_execution: DataHubDatasetLineageExecutionResult, schema_execution: DataHubSchemaFieldsExecutionResult, transport: DataHubMCPTransport) -> DataHubColumnLineageExecutionResult:
    """Execute exactly one bounded column-level get_lineage call and normalize the slice.

    All preflight failures happen before any transport call. Exactly one
    downstream column ``get_lineage`` request is sent on success; there is
    never a retry, a second call, pagination, or a path-between capability.
    """
    if not isinstance(config, DataHubMCPConfig) or not isinstance(session, DataHubMCPSession):
        raise _error("column_lineage_execution_context_mismatch")
    if session.endpoint_url != config.endpoint_url or session.protocol_version != DATAHUB_MCP_PROTOCOL_VERSION or not session.tools_supported:
        raise _error("column_lineage_execution_context_mismatch")
    if not isinstance(lineage_context, DataHubLineageContext) or not isinstance(column_plan, DataHubColumnLineageArgumentPlan) or not isinstance(dataset_lineage_execution, DataHubDatasetLineageExecutionResult) or not isinstance(schema_execution, DataHubSchemaFieldsExecutionResult):
        raise _error("column_lineage_execution_context_mismatch")
    if not lineage_context.discovery.entity_schema_discovery.read_discovery.catalog.all_required_tools_available:
        raise _error("column_lineage_execution_context_mismatch")
    capability = next((tool for tool in lineage_context.discovery.entity_schema_discovery.read_discovery.catalog.tools if tool.name.value == "get_lineage"), None)
    if capability is None or capability.input_schema_fingerprint != lineage_context.discovery.get_lineage_contract.input_schema_fingerprint:
        raise _error("column_lineage_execution_context_mismatch")
    if column_plan.input_schema_fingerprint != lineage_context.discovery.get_lineage_contract.input_schema_fingerprint:
        raise _error("column_lineage_execution_context_mismatch")
    if lineage_context.resolution.status is not DataHubAssetResolutionStatus.RESOLVED or lineage_context.resolution.selected_dataset_urn is None:
        raise _error("column_lineage_execution_context_mismatch")
    if lineage_context.resolution.selected_dataset_urn != lineage_context.dataset_urn:
        raise _error("column_lineage_execution_context_mismatch")
    source_urn = lineage_context.dataset_urn
    if lineage_context.entity_execution.dataset_urn != source_urn:
        raise _error("column_lineage_execution_context_mismatch")
    if schema_execution.dataset_urn != source_urn:
        raise _error("column_lineage_execution_context_mismatch")
    if dataset_lineage_execution.source_dataset_urn != source_urn:
        raise _error("column_lineage_execution_context_mismatch")
    if column_plan.dataset_urn != source_urn:
        raise _error("column_lineage_execution_context_mismatch")
    if column_plan.affected_column != lineage_context.affected_column:
        raise _error("column_lineage_execution_context_mismatch")
    expected_args = {"urn": source_urn, "column": lineage_context.affected_column, "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0}
    if dict(column_plan.arguments) != expected_args:
        raise _error("column_lineage_execution_context_mismatch")
    try:
        _safe_urn(source_urn)
        if not source_urn.startswith(_DATASET_PREFIX):
            raise ValueError("invalid source URN")
    except ValueError:
        raise _error("column_lineage_execution_context_mismatch") from None
    parts = _dataset_urn_parts(source_urn)
    if parts is None or _norm(parts[0]) != _norm(lineage_context.subject.platform):
        raise _error("column_lineage_execution_context_mismatch")
    if dataset_lineage_execution.request_id != lineage_context.dataset_lineage_request_id:
        raise _error("column_lineage_execution_context_mismatch")
    if dataset_lineage_execution.next_request_id != lineage_context.column_lineage_request_id:
        raise _error("column_lineage_execution_context_mismatch")
    try:
        request = build_datahub_column_lineage_tools_call_request(context=lineage_context, contract=lineage_context.discovery.get_lineage_contract, argument_plan=column_plan)
        body = serialize_datahub_column_lineage_tools_call_request(context=lineage_context, contract=lineage_context.discovery.get_lineage_contract, argument_plan=column_plan)
    except DataHubLineageContractError:
        raise _error("column_lineage_execution_context_mismatch") from None
    if request.id != lineage_context.column_lineage_request_id:
        raise _error("column_lineage_execution_context_mismatch")
    request_fingerprint = hashlib.sha256(body).hexdigest()
    if not _FINGERPRINT.fullmatch(request_fingerprint):
        raise _error("column_lineage_request_fingerprint_invalid")
    try:
        response = transport.post_request(body, session_id=session.session_id, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION)
        parsed = parse_http_response(response, expected_id=request.id)
    except DataHubMCPProtocolError:
        raise
    if parsed.request_id != request.id:
        raise _error("column_lineage_result_request_mismatch")
    if parsed.error is not None or parsed.result is None:
        raise _error("column_lineage_tool_execution_failed")
    result = parsed.result
    is_error = result.get("isError", False)
    if not isinstance(is_error, bool):
        raise _error("invalid_column_lineage_tool_result")
    if is_error:
        raise _error("column_lineage_tool_execution_failed")
    text_blocks = _validate_column_content(result)
    payload = _select_column_payload(result, text_blocks)
    targets, total, offset, returned, has_more, truncated = _parse_column_downstreams(payload)
    has_columns = any(len(target.lineage_columns) > 0 for target in targets)
    observation = DataHubColumnLineageObservation.OBSERVED if has_columns else DataHubColumnLineageObservation.NOT_OBSERVED
    column_lineage_slice = DataHubColumnLineageSlice(
        source_dataset_urn=source_urn,
        source_column=lineage_context.affected_column,
        targets=targets,
        column_lineage_observation=observation,
        provider_total=total,
        provider_offset=offset,
        provider_returned=returned,
        provider_has_more=has_more,
        provider_truncated_due_to_token_budget=truncated,
    )
    return DataHubColumnLineageExecutionResult(
        request_id=request.id,
        next_request_id=request.id + 1,
        column_lineage_request_fingerprint=request_fingerprint,
        input_schema_fingerprint=column_plan.input_schema_fingerprint,
        source_dataset_urn=source_urn,
        source_column=lineage_context.affected_column,
        column_lineage_slice=column_lineage_slice,
    )


__all__ = [
    "MAX_LINEAGE_COLUMNS_PER_TARGET",
    "MAX_LINEAGE_COLUMN_CHARS",
    "MAX_TARGETS",
    "MAX_TOTAL_LINEAGE_COLUMNS",
    "RESULT_VERSION",
    "SLICE_VERSION",
    "DataHubColumnDownstreamTarget",
    "DataHubColumnLineageExecutionError",
    "DataHubColumnLineageExecutionResult",
    "DataHubColumnLineageObservation",
    "DataHubColumnLineageSlice",
    "execute_datahub_column_lineage",
]
