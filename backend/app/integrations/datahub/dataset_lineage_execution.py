"""F8.3D2 bounded dataset-level downstream lineage execution and normalization.

This module executes exactly one dataset-level ``get_lineage`` request from
the locked F8.3D1 plan, continues the request-ID chain after F8.3C3, validates
the MCP envelope and downstream-direction payload, normalizes at most thirty
downstream target observations, preserves bounded provider pagination
observations, and discards the raw provider response. It never executes the
column-lineage plan and never makes completeness or consumer claims.
"""

from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator

from app.schemas.datahub_context import DataHubEntityKind, DataHubLineageRelation

from .asset_resolution import DataHubAssetResolutionStatus, _dataset_urn_parts, _norm
from .config import DATAHUB_MCP_PROTOCOL_VERSION, DataHubMCPConfig
from .initialization import DataHubMCPSession
from .lineage_contract import (
    DataHubDatasetLineageArgumentPlan,
    DataHubLineageContext,
    DataHubLineageContractError,
    build_datahub_dataset_lineage_tools_call_request,
    serialize_datahub_dataset_lineage_tools_call_request,
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
_DATASET_PREFIX = "urn:li:dataset:"
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")
_ENTITY_KIND_VALUES = frozenset(kind.value for kind in DataHubEntityKind)


class DataHubDatasetLineageExecutionError(ValueError):
    """Safe, non-retryable dataset-lineage execution error."""

    def __init__(self, code: str, message: str = "DataHub dataset lineage execution failed.", *, retryable: bool = False) -> None:
        self.code = code
        self.message = message
        self.retryable = retryable
        super().__init__(message)


class _StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class DataHubDownstreamObservation(_StrEnum):
    OBSERVED = "observed"
    NOT_OBSERVED = "not_observed"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _error(code: str) -> DataHubDatasetLineageExecutionError:
    return DataHubDatasetLineageExecutionError(code)


def _hex64(value: Any) -> str:
    if not isinstance(value, str) or not _FINGERPRINT.fullmatch(value):
        raise ValueError("invalid fingerprint")
    return value


class DataHubDatasetDownstreamTarget(_Strict):
    """Frozen normalized downstream target evidence.

    Reuses F8.1 enums and bounds but stores only the bounded D2 evidence,
    deeply immutable. The raw provider entity object is never retained.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    urn: str
    entity_kind: DataHubEntityKind
    display_name: str | None = None
    relation: DataHubLineageRelation
    depth: StrictInt

    @field_validator("urn")
    @classmethod
    def urn_ok(cls, value: Any) -> str:
        return _safe_urn(value)

    @field_validator("display_name")
    @classmethod
    def display_ok(cls, value: Any) -> str | None:
        return _safe_name(value)

    @model_validator(mode="after")
    def invariants(self) -> "DataHubDatasetDownstreamTarget":
        if self.relation is not DataHubLineageRelation.DOWNSTREAM or self.depth != 1:
            raise ValueError("invalid downstream target relation or depth")
        return self


class DataHubDatasetDownstreamSlice(_Strict):
    """Bounded normalized downstream observation for one source dataset.

    Provider pagination fields are external unverified observations. Zero
    observed targets never mean zero consumers, and provider ``hasMore``
    never proves graph completeness.
    """

    source_dataset_urn: str
    targets: tuple[DataHubDatasetDownstreamTarget, ...] = Field(default_factory=tuple, max_length=MAX_TARGETS)
    downstream_observation: DataHubDownstreamObservation
    provider_total: StrictInt | None = Field(default=None, ge=0, le=MAX_PROVIDER_TOTAL)
    provider_offset: StrictInt | None = Field(default=None, ge=0, le=0)
    provider_returned: StrictInt | None = Field(default=None, ge=0, le=MAX_TARGETS)
    provider_has_more: StrictBool | None = None
    provider_truncated_due_to_token_budget: StrictBool | None = None
    slice_version: str = SLICE_VERSION

    @field_validator("source_dataset_urn")
    @classmethod
    def source_ok(cls, value: str) -> str:
        value = _safe_urn(value)
        if not value.startswith(_DATASET_PREFIX):
            raise ValueError("invalid source dataset URN")
        return value

    @model_validator(mode="after")
    def invariants(self) -> "DataHubDatasetDownstreamSlice":
        if self.slice_version != SLICE_VERSION:
            raise ValueError("invalid downstream slice version")
        if self.provider_returned is not None and self.provider_returned != len(self.targets):
            raise ValueError("invalid provider returned count")
        if self.provider_total is not None and self.provider_total < len(self.targets):
            raise ValueError("invalid provider total")
        urns = [target.urn for target in self.targets]
        if len(set(urns)) != len(urns):
            raise ValueError("duplicate downstream target")
        if any(target.relation is not DataHubLineageRelation.DOWNSTREAM or target.depth != 1 for target in self.targets):
            raise ValueError("invalid downstream target relation or depth")
        if self.downstream_observation is DataHubDownstreamObservation.OBSERVED:
            if len(self.targets) == 0:
                raise ValueError("observed requires at least one target")
        elif len(self.targets) > 0:
            raise ValueError("not_observed requires zero targets")
        return self


class DataHubDatasetLineageExecutionResult(_Strict):
    request_id: StrictInt = Field(gt=0)
    next_request_id: StrictInt = Field(gt=0)
    dataset_lineage_request_fingerprint: str
    input_schema_fingerprint: str
    source_dataset_urn: str
    downstream_slice: DataHubDatasetDownstreamSlice
    result_version: str = RESULT_VERSION

    @field_validator("dataset_lineage_request_fingerprint", "input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        return _hex64(value)

    @field_validator("source_dataset_urn")
    @classmethod
    def source_ok(cls, value: str) -> str:
        value = _safe_urn(value)
        if not value.startswith(_DATASET_PREFIX):
            raise ValueError("invalid source dataset URN")
        return value

    @model_validator(mode="after")
    def invariants(self) -> "DataHubDatasetLineageExecutionResult":
        if self.next_request_id != self.request_id + 1 or self.result_version != RESULT_VERSION:
            raise ValueError("invalid dataset lineage execution result")
        return self


def _validate_lineage_content(result: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        return _validate_content(result)
    except DataHubSearchExecutionError as exc:
        mapping = {
            "invalid_search_tool_result": "invalid_dataset_lineage_tool_result",
            "unsupported_search_content": "unsupported_dataset_lineage_content",
            "search_content_too_large": "dataset_lineage_content_too_large",
        }
        code = mapping.get(exc.code)
        if code is None:
            raise _error("invalid_dataset_lineage_tool_result") from None
        raise _error(code) from None


def _lineage_canonical_size(value: dict[str, Any]) -> int:
    try:
        return _canonical_size(value)
    except DataHubSearchExecutionError:
        raise _error("invalid_dataset_lineage_payload") from None


def _select_lineage_payload(result: dict[str, Any], text_blocks: list[dict[str, Any]]) -> dict[str, Any]:
    if "structuredContent" in result:
        payload = result["structuredContent"]
        if not isinstance(payload, dict):
            raise _error("invalid_dataset_lineage_payload")
        if _lineage_canonical_size(payload) > MAX_STRUCTURED_BYTES:
            raise _error("dataset_lineage_content_too_large")
        return payload
    if len(text_blocks) != 1:
        raise _error("missing_dataset_lineage_payload")
    try:
        return parse_strict_json_object(text_blocks[0]["text"])
    except DataHubMCPProtocolError:
        raise _error("invalid_dataset_lineage_payload") from None


def _optional_int(payload: dict[str, Any], key: str, *, lo: int, hi: int) -> int | None:
    if key not in payload:
        return None
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise _error("invalid_dataset_lineage_payload")
    if not lo <= value <= hi:
        raise _error("invalid_dataset_lineage_payload")
    return value


def _optional_bool(payload: dict[str, Any], key: str) -> bool | None:
    if key not in payload:
        return None
    value = payload[key]
    if not isinstance(value, bool):
        raise _error("invalid_dataset_lineage_payload")
    return value


def _upstream_has_data(obj: dict[str, Any]) -> bool:
    search_results = obj.get("searchResults")
    if isinstance(search_results, list) and len(search_results) > 0:
        return True
    total = obj.get("total")
    if isinstance(total, int) and not isinstance(total, bool) and total > 0:
        return True
    return False


def _normalize_target(item: Any) -> DataHubDatasetDownstreamTarget:
    if not isinstance(item, dict):
        raise ValueError("invalid target")
    entity = item.get("entity")
    if not isinstance(entity, dict):
        raise ValueError("invalid target")
    urn = entity.get("urn")
    try:
        urn = _safe_urn(urn)
    except ValueError:
        raise ValueError("invalid target") from None
    if "degree" not in item:
        raise ValueError("invalid target")
    degree = item["degree"]
    if isinstance(degree, bool) or not isinstance(degree, int) or degree != 1:
        raise ValueError("invalid target")
    kind = DataHubEntityKind.OTHER
    raw_type = entity.get("type")
    if raw_type is not None:
        if not isinstance(raw_type, str):
            raise ValueError("invalid target")
        lowered = raw_type.strip().lower()
        if lowered in _ENTITY_KIND_VALUES:
            kind = DataHubEntityKind(lowered)
    try:
        display_name = _safe_name(entity.get("name"))
    except ValueError:
        raise ValueError("invalid target") from None
    try:
        return DataHubDatasetDownstreamTarget(urn=urn, entity_kind=kind, display_name=display_name, relation=DataHubLineageRelation.DOWNSTREAM, depth=1)
    except ValueError:
        raise ValueError("invalid target") from None


def _parse_downstreams(payload: dict[str, Any]) -> tuple[tuple[DataHubDatasetDownstreamTarget, ...], int | None, int | None, int | None, bool | None, bool | None]:
    if "downstreams" not in payload:
        raise _error("dataset_lineage_direction_mismatch")
    downstreams = payload["downstreams"]
    if not isinstance(downstreams, dict):
        raise _error("invalid_dataset_lineage_payload")
    if "upstreams" in payload:
        upstreams = payload["upstreams"]
        if upstreams is not None and not isinstance(upstreams, dict):
            raise _error("invalid_dataset_lineage_payload")
        if isinstance(upstreams, dict) and _upstream_has_data(upstreams):
            raise _error("dataset_lineage_direction_mismatch")
    results: list[Any] = []
    if "searchResults" in downstreams:
        value = downstreams["searchResults"]
        if not isinstance(value, list):
            raise _error("invalid_dataset_lineage_payload")
        if len(value) > MAX_TARGETS:
            raise _error("dataset_lineage_count_mismatch")
        results = value
    nonempty = len(results) > 0
    if nonempty and ("offset" not in downstreams or "returned" not in downstreams or "hasMore" not in downstreams):
        raise _error("invalid_dataset_lineage_payload")
    offset = _optional_int(downstreams, "offset", lo=0, hi=0)
    returned = _optional_int(downstreams, "returned", lo=0, hi=MAX_TARGETS)
    has_more = _optional_bool(downstreams, "hasMore")
    truncated = _optional_bool(downstreams, "truncatedDueToTokenBudget")
    total = _optional_int(downstreams, "total", lo=0, hi=MAX_PROVIDER_TOTAL)
    if returned is not None and returned != len(results):
        raise _error("dataset_lineage_count_mismatch")
    if total is not None and total < len(results):
        raise _error("dataset_lineage_count_mismatch")
    targets: list[DataHubDatasetDownstreamTarget] = []
    seen: set[str] = set()
    for item in results:
        try:
            target = _normalize_target(item)
        except ValueError:
            raise _error("invalid_dataset_lineage_target") from None
        if target.urn in seen:
            raise _error("duplicate_dataset_lineage_target")
        seen.add(target.urn)
        targets.append(target)
    return tuple(targets), total, offset, returned, has_more, truncated


def execute_datahub_dataset_lineage(*, config: DataHubMCPConfig, session: DataHubMCPSession, lineage_context: DataHubLineageContext, dataset_plan: DataHubDatasetLineageArgumentPlan, schema_execution: DataHubSchemaFieldsExecutionResult, transport: DataHubMCPTransport) -> DataHubDatasetLineageExecutionResult:
    """Execute exactly one bounded dataset-level get_lineage call and normalize the slice.

    All preflight failures happen before any transport call. Exactly one
    downstream ``get_lineage`` request is sent on success; there is never a
    retry, a second call, or pagination.
    """
    if not isinstance(config, DataHubMCPConfig) or not isinstance(session, DataHubMCPSession):
        raise _error("dataset_lineage_execution_context_mismatch")
    if session.endpoint_url != config.endpoint_url or session.protocol_version != DATAHUB_MCP_PROTOCOL_VERSION or not session.tools_supported:
        raise _error("dataset_lineage_execution_context_mismatch")
    if not isinstance(lineage_context, DataHubLineageContext) or not isinstance(dataset_plan, DataHubDatasetLineageArgumentPlan) or not isinstance(schema_execution, DataHubSchemaFieldsExecutionResult):
        raise _error("dataset_lineage_execution_context_mismatch")
    if not lineage_context.discovery.entity_schema_discovery.read_discovery.catalog.all_required_tools_available:
        raise _error("dataset_lineage_execution_context_mismatch")
    capability = next((tool for tool in lineage_context.discovery.entity_schema_discovery.read_discovery.catalog.tools if tool.name.value == "get_lineage"), None)
    if capability is None or capability.input_schema_fingerprint != lineage_context.discovery.get_lineage_contract.input_schema_fingerprint:
        raise _error("dataset_lineage_execution_context_mismatch")
    if dataset_plan.input_schema_fingerprint != lineage_context.discovery.get_lineage_contract.input_schema_fingerprint:
        raise _error("dataset_lineage_execution_context_mismatch")
    if lineage_context.resolution.status is not DataHubAssetResolutionStatus.RESOLVED or lineage_context.resolution.selected_dataset_urn is None:
        raise _error("dataset_lineage_execution_context_mismatch")
    if lineage_context.resolution.selected_dataset_urn != lineage_context.dataset_urn:
        raise _error("dataset_lineage_execution_context_mismatch")
    if lineage_context.entity_execution.dataset_urn != lineage_context.dataset_urn:
        raise _error("dataset_lineage_execution_context_mismatch")
    if schema_execution.dataset_urn != lineage_context.dataset_urn:
        raise _error("dataset_lineage_execution_context_mismatch")
    if dataset_plan.dataset_urn != lineage_context.dataset_urn:
        raise _error("dataset_lineage_execution_context_mismatch")
    expected_args = {"urn": lineage_context.dataset_urn, "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0}
    if dict(dataset_plan.arguments) != expected_args:
        raise _error("dataset_lineage_execution_context_mismatch")
    source_urn = lineage_context.dataset_urn
    try:
        _safe_urn(source_urn)
        if not source_urn.startswith(_DATASET_PREFIX):
            raise ValueError("invalid source URN")
    except ValueError:
        raise _error("dataset_lineage_execution_context_mismatch") from None
    parts = _dataset_urn_parts(source_urn)
    if parts is None or _norm(parts[0]) != _norm(lineage_context.subject.platform):
        raise _error("dataset_lineage_execution_context_mismatch")
    if lineage_context.dataset_lineage_request_id != schema_execution.next_request_id:
        raise _error("dataset_lineage_execution_context_mismatch")
    try:
        request = build_datahub_dataset_lineage_tools_call_request(context=lineage_context, contract=lineage_context.discovery.get_lineage_contract, argument_plan=dataset_plan)
        body = serialize_datahub_dataset_lineage_tools_call_request(context=lineage_context, contract=lineage_context.discovery.get_lineage_contract, argument_plan=dataset_plan)
    except DataHubLineageContractError:
        raise _error("dataset_lineage_execution_context_mismatch") from None
    if request.id != lineage_context.dataset_lineage_request_id:
        raise _error("dataset_lineage_execution_context_mismatch")
    request_fingerprint = hashlib.sha256(body).hexdigest()
    if not _FINGERPRINT.fullmatch(request_fingerprint):
        raise _error("dataset_lineage_request_fingerprint_invalid")
    try:
        response = transport.post_request(body, session_id=session.session_id, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION)
        parsed = parse_http_response(response, expected_id=request.id)
    except DataHubMCPProtocolError:
        raise
    if parsed.request_id != request.id:
        raise _error("dataset_lineage_result_request_mismatch")
    if parsed.error is not None or parsed.result is None:
        raise _error("dataset_lineage_tool_execution_failed")
    result = parsed.result
    is_error = result.get("isError", False)
    if not isinstance(is_error, bool):
        raise _error("invalid_dataset_lineage_tool_result")
    if is_error:
        raise _error("dataset_lineage_tool_execution_failed")
    text_blocks = _validate_lineage_content(result)
    payload = _select_lineage_payload(result, text_blocks)
    targets, total, offset, returned, has_more, truncated = _parse_downstreams(payload)
    observation = DataHubDownstreamObservation.OBSERVED if len(targets) > 0 else DataHubDownstreamObservation.NOT_OBSERVED
    downstream_slice = DataHubDatasetDownstreamSlice(
        source_dataset_urn=source_urn,
        targets=targets,
        downstream_observation=observation,
        provider_total=total,
        provider_offset=offset,
        provider_returned=returned,
        provider_has_more=has_more,
        provider_truncated_due_to_token_budget=truncated,
    )
    return DataHubDatasetLineageExecutionResult(
        request_id=request.id,
        next_request_id=request.id + 1,
        dataset_lineage_request_fingerprint=request_fingerprint,
        input_schema_fingerprint=dataset_plan.input_schema_fingerprint,
        source_dataset_urn=source_urn,
        downstream_slice=downstream_slice,
    )


__all__ = [
    "MAX_TARGETS",
    "RESULT_VERSION",
    "SLICE_VERSION",
    "DataHubDatasetDownstreamSlice",
    "DataHubDatasetDownstreamTarget",
    "DataHubDatasetLineageExecutionError",
    "DataHubDatasetLineageExecutionResult",
    "DataHubDownstreamObservation",
    "execute_datahub_dataset_lineage",
]
