"""F8.3C3 bounded list_schema_fields execution and schema-field normalization.

This module executes exactly one ``list_schema_fields`` ``tools/call`` per
valid invocation, continuing the request-ID chain after F8.3C2. It validates
the MCP envelope, normalizes at most fifty returned schema fields, derives a
deterministic exact affected-field observation, and discards the raw provider
response. Provider keyword ranking is never treated as field-identity
authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from app.schemas.datahub_context import DataHubFieldMetadata

from .asset_resolution import _dataset_urn_parts, _norm
from .config import DATAHUB_MCP_PROTOCOL_VERSION, DataHubMCPConfig
from .entity_execution import DataHubEntityMetadataExecutionResult, _normalize_named_refs
from .entity_schema_contract import (
    DataHubEntitySchemaContractError,
    DataHubEntitySchemaContext,
    DataHubEntitySchemaToolDiscoveryBundle,
    DataHubListSchemaFieldsArgumentPlan,
    build_datahub_list_schema_fields_tools_call_request,
    serialize_datahub_list_schema_fields_tools_call_request,
)
from .initialization import DataHubMCPSession
from .mcp_protocol import DataHubMCPProtocolError, parse_http_response, parse_strict_json_object
from .search_execution import (
    MAX_STRUCTURED_BYTES,
    DataHubSearchExecutionError,
    DataHubSearchExecutionResult,
    _canonical_size,
    _safe_urn,
    _validate_content,
)
from .transport import DataHubMCPTransport

SCHEMA_SLICE_VERSION = "1.0"
RESULT_VERSION = "1.0"
MAX_FIELDS = 50
MAX_TOTAL_FIELDS = 1_000_000
_DATASET_PREFIX = "urn:li:dataset:"
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")


class DataHubSchemaFieldsExecutionError(ValueError):
    """Safe, non-retryable schema-fields execution error."""

    def __init__(self, code: str, message: str = "DataHub schema fields execution failed.", *, retryable: bool = False) -> None:
        self.code = code
        self.message = message
        self.retryable = retryable
        super().__init__(message)


class _StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class DataHubAffectedFieldObservation(_StrEnum):
    OBSERVED_EXACT = "observed_exact"
    NOT_OBSERVED = "not_observed"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _error(code: str) -> DataHubSchemaFieldsExecutionError:
    return DataHubSchemaFieldsExecutionError(code)


def _hex64(value: Any) -> str:
    if not isinstance(value, str) or not _FINGERPRINT.fullmatch(value):
        raise ValueError("invalid fingerprint")
    return value


class DataHubDatasetSchemaSlice(_Strict):
    """Bounded normalized schema slice for one dataset.

    Provider counts are external unverified observations. The affected-field
    observation records only whether the exact normalized fieldPath appeared
    in this returned bounded slice.
    """

    dataset_urn: str
    fields: tuple[DataHubFieldMetadata, ...] = Field(default_factory=tuple, max_length=MAX_FIELDS)
    provider_total_fields: StrictInt = Field(ge=0, le=MAX_TOTAL_FIELDS)
    provider_returned: StrictInt = Field(ge=0, le=MAX_FIELDS)
    provider_remaining_count: StrictInt = Field(ge=0, le=MAX_TOTAL_FIELDS)
    provider_matching_count: StrictInt | None = Field(default=None, ge=0, le=MAX_TOTAL_FIELDS)
    provider_offset: StrictInt = Field(ge=0, le=0)
    affected_field_observation: DataHubAffectedFieldObservation
    affected_field: DataHubFieldMetadata | None = None
    schema_slice_version: str = SCHEMA_SLICE_VERSION

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str:
        value = _safe_urn(value)
        if not value.startswith(_DATASET_PREFIX):
            raise ValueError("invalid dataset URN")
        return value

    @model_validator(mode="after")
    def invariants(self) -> "DataHubDatasetSchemaSlice":
        if self.schema_slice_version != SCHEMA_SLICE_VERSION:
            raise ValueError("invalid schema slice version")
        paths = [_norm(field.field_path) for field in self.fields]
        if len(set(paths)) != len(paths):
            raise ValueError("duplicate normalized field path")
        if self.provider_returned != len(self.fields) or self.provider_offset != 0:
            raise ValueError("invalid provider counts")
        if self.provider_total_fields < self.provider_returned or self.provider_remaining_count > self.provider_total_fields:
            raise ValueError("invalid provider count relationship")
        if self.provider_matching_count is None:
            if self.provider_total_fields != 0:
                raise ValueError("matching count requires zero total fields")
        elif self.provider_matching_count > self.provider_total_fields:
            raise ValueError("matching count exceeds total fields")
        if self.provider_remaining_count != self.provider_total_fields - self.provider_returned:
            raise ValueError("invalid remaining count relationship")
        if self.affected_field_observation is DataHubAffectedFieldObservation.OBSERVED_EXACT:
            if self.affected_field is None or self.affected_field not in self.fields:
                raise ValueError("invalid affected field observation")
        else:
            if self.affected_field is not None:
                raise ValueError("invalid affected field observation")
        return self


class DataHubSchemaFieldsExecutionResult(_Strict):
    request_id: StrictInt = Field(gt=0)
    next_request_id: StrictInt = Field(gt=0)
    schema_request_fingerprint: str
    input_schema_fingerprint: str
    dataset_urn: str
    schema_slice: DataHubDatasetSchemaSlice
    result_version: str = RESULT_VERSION

    @field_validator("schema_request_fingerprint", "input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        return _hex64(value)

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str:
        return _safe_urn(value)

    @model_validator(mode="after")
    def invariants(self) -> "DataHubSchemaFieldsExecutionResult":
        if self.next_request_id != self.request_id + 1 or self.result_version != RESULT_VERSION:
            raise ValueError("invalid schema fields execution result")
        return self


def _validate_schema_content(result: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        return _validate_content(result)
    except DataHubSearchExecutionError as exc:
        mapping = {
            "invalid_search_tool_result": "invalid_schema_tool_result",
            "unsupported_search_content": "unsupported_schema_content",
            "search_content_too_large": "schema_content_too_large",
        }
        code = mapping.get(exc.code)
        if code is None:
            raise _error("invalid_schema_tool_result") from None
        raise _error(code) from None


def _schema_canonical_size(value: dict[str, Any]) -> int:
    try:
        return _canonical_size(value)
    except DataHubSearchExecutionError:
        raise _error("invalid_schema_result_payload") from None


def _select_schema_payload(result: dict[str, Any], text_blocks: list[dict[str, Any]]) -> dict[str, Any]:
    if "structuredContent" in result:
        payload = result["structuredContent"]
        if not isinstance(payload, dict):
            raise _error("invalid_schema_result_payload")
        if _schema_canonical_size(payload) > MAX_STRUCTURED_BYTES:
            raise _error("schema_content_too_large")
        return payload
    if len(text_blocks) != 1:
        raise _error("missing_schema_result_payload")
    try:
        return parse_strict_json_object(text_blocks[0]["text"])
    except DataHubMCPProtocolError:
        raise _error("invalid_schema_result_payload") from None


def _require_int(payload: dict[str, Any], key: str, *, lo: int, hi: int) -> int:
    if key not in payload:
        raise _error("missing_schema_result_payload")
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise _error("invalid_schema_result_payload")
    if not lo <= value <= hi:
        raise _error("invalid_schema_result_payload")
    return value


def _parse_matching_count(payload: dict[str, Any], *, total_fields: int) -> int | None:
    """Parse the provider matchingCount; null is valid only for a zero-field result."""
    if "matchingCount" not in payload:
        raise _error("missing_schema_result_payload")
    value = payload["matchingCount"]
    if value is None:
        if total_fields != 0:
            raise _error("invalid_schema_result_payload")
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise _error("invalid_schema_result_payload")
    if not 0 <= value <= MAX_TOTAL_FIELDS:
        raise _error("invalid_schema_result_payload")
    return value


def _normalize_field(raw: Any) -> DataHubFieldMetadata:
    if not isinstance(raw, dict):
        raise ValueError("invalid field")
    raw_path = raw.get("fieldPath")
    if not isinstance(raw_path, str):
        raise ValueError("invalid field path")
    if "nullable" in raw and not isinstance(raw["nullable"], bool):
        raise ValueError("invalid nullable")
    if "isPartOfKey" in raw and not isinstance(raw["isPartOfKey"], bool):
        raise ValueError("invalid key flag")
    if "nativeDataType" in raw and not isinstance(raw["nativeDataType"], str):
        raise ValueError("invalid native datatype")
    if "description" in raw and not isinstance(raw["description"], str):
        raise ValueError("invalid description")
    tags = _normalize_named_refs(raw.get("globalTags"), wrapper_key="tags", inner_key="tag")
    glossary_terms = _normalize_named_refs(raw.get("glossaryTerms"), wrapper_key="terms", inner_key="term")
    try:
        return DataHubFieldMetadata(
            field_path=raw_path,
            native_type=raw.get("nativeDataType"),
            nullable=raw.get("nullable"),
            description=raw.get("description"),
            tags=list(tags),
            glossary_terms=list(glossary_terms),
        )
    except ValueError:
        raise ValueError("invalid field") from None


def execute_datahub_list_schema_fields(*, config: DataHubMCPConfig, session: DataHubMCPSession, discovery: DataHubEntitySchemaToolDiscoveryBundle, binding: DataHubEntitySchemaContext, argument_plan: DataHubListSchemaFieldsArgumentPlan, search_execution: DataHubSearchExecutionResult, entity_execution: DataHubEntityMetadataExecutionResult, transport: DataHubMCPTransport) -> DataHubSchemaFieldsExecutionResult:
    """Execute exactly one bounded list_schema_fields call and normalize the slice.

    All preflight failures happen before any transport call. Exactly one
    ``tools/call`` for ``list_schema_fields`` is sent on success; there is
    never a retry, a second attempt, or pagination.
    """
    if not isinstance(config, DataHubMCPConfig) or not isinstance(session, DataHubMCPSession):
        raise _error("schema_execution_context_mismatch")
    if session.endpoint_url != config.endpoint_url or session.protocol_version != DATAHUB_MCP_PROTOCOL_VERSION or not session.tools_supported:
        raise _error("schema_execution_context_mismatch")
    if not isinstance(discovery, DataHubEntitySchemaToolDiscoveryBundle) or not isinstance(binding, DataHubEntitySchemaContext) or not isinstance(argument_plan, DataHubListSchemaFieldsArgumentPlan) or not isinstance(search_execution, DataHubSearchExecutionResult) or not isinstance(entity_execution, DataHubEntityMetadataExecutionResult):
        raise _error("schema_execution_context_mismatch")
    if binding.discovery.list_schema_fields_contract.input_schema_fingerprint != discovery.list_schema_fields_contract.input_schema_fingerprint:
        raise _error("schema_execution_context_mismatch")
    if binding.search_execution.next_request_id != search_execution.next_request_id or binding.search_execution.input_schema_fingerprint != search_execution.input_schema_fingerprint:
        raise _error("schema_execution_context_mismatch")
    if not discovery.read_discovery.catalog.all_required_tools_available:
        raise _error("schema_execution_context_mismatch")
    capability = next((tool for tool in discovery.read_discovery.catalog.tools if tool.name.value == "list_schema_fields"), None)
    if capability is None or capability.input_schema_fingerprint != discovery.list_schema_fields_contract.input_schema_fingerprint:
        raise _error("schema_execution_context_mismatch")
    if argument_plan.input_schema_fingerprint != discovery.list_schema_fields_contract.input_schema_fingerprint:
        raise _error("schema_execution_context_mismatch")
    plan_args = dict(argument_plan.arguments)
    expected_args = {"urn": argument_plan.dataset_urn, "keywords": (argument_plan.affected_column,), "limit": 50, "offset": 0}
    if plan_args != expected_args:
        raise _error("schema_execution_context_mismatch")
    if argument_plan.dataset_urn != binding.dataset_urn:
        raise _error("schema_execution_context_mismatch")
    if argument_plan.affected_column != binding.affected_column:
        raise _error("schema_execution_context_mismatch")
    if entity_execution.dataset_urn != binding.dataset_urn:
        raise _error("schema_execution_context_mismatch")
    if entity_execution.next_request_id != binding.list_schema_fields_request_id:
        raise _error("schema_execution_context_mismatch")
    dataset_urn = binding.dataset_urn
    try:
        _safe_urn(dataset_urn)
    except ValueError:
        raise _error("schema_execution_context_mismatch") from None
    parts = _dataset_urn_parts(dataset_urn)
    if parts is None or _norm(parts[0]) != _norm(binding.subject.platform):
        raise _error("schema_execution_context_mismatch")
    try:
        request = build_datahub_list_schema_fields_tools_call_request(context=binding, contract=discovery.list_schema_fields_contract, argument_plan=argument_plan)
        body = serialize_datahub_list_schema_fields_tools_call_request(context=binding, contract=discovery.list_schema_fields_contract, argument_plan=argument_plan)
    except DataHubEntitySchemaContractError:
        raise _error("schema_execution_context_mismatch") from None
    if request.id != binding.list_schema_fields_request_id:
        raise _error("schema_execution_context_mismatch")
    request_fingerprint = hashlib.sha256(body).hexdigest()
    if not _FINGERPRINT.fullmatch(request_fingerprint):
        raise _error("schema_request_fingerprint_invalid")
    try:
        response = transport.post_request(body, session_id=session.session_id, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION)
        parsed = parse_http_response(response, expected_id=request.id)
    except DataHubMCPProtocolError:
        raise
    if parsed.request_id != request.id:
        raise _error("schema_result_request_mismatch")
    if parsed.error is not None or parsed.result is None:
        raise _error("schema_tool_execution_failed")
    result = parsed.result
    is_error = result.get("isError", False)
    if not isinstance(is_error, bool):
        raise _error("invalid_schema_tool_result")
    if is_error:
        raise _error("schema_tool_execution_failed")
    text_blocks = _validate_schema_content(result)
    payload = _select_schema_payload(result, text_blocks)
    offset = _require_int(payload, "offset", lo=0, hi=0)
    returned = _require_int(payload, "returned", lo=0, hi=MAX_FIELDS)
    total_fields = _require_int(payload, "totalFields", lo=0, hi=MAX_TOTAL_FIELDS)
    remaining_count = _require_int(payload, "remainingCount", lo=0, hi=MAX_TOTAL_FIELDS)
    matching_count = _parse_matching_count(payload, total_fields=total_fields)
    if "urn" not in payload:
        raise _error("missing_schema_result_payload")
    if "fields" not in payload:
        raise _error("missing_schema_result_payload")
    fields_value = payload["fields"]
    if not isinstance(fields_value, list) or len(fields_value) > MAX_FIELDS:
        raise _error("invalid_schema_result_payload")
    if returned != len(fields_value):
        raise _error("schema_result_count_mismatch")
    if total_fields < returned or remaining_count > total_fields or remaining_count != total_fields - returned:
        raise _error("schema_result_count_mismatch")
    if matching_count is not None and matching_count > total_fields:
        raise _error("schema_result_count_mismatch")
    returned_urn = payload["urn"]
    try:
        returned_urn = _safe_urn(returned_urn)
    except ValueError:
        raise _error("schema_result_identity_mismatch") from None
    if not returned_urn.startswith(_DATASET_PREFIX) or returned_urn != dataset_urn:
        raise _error("schema_result_identity_mismatch")
    parts = _dataset_urn_parts(returned_urn)
    if parts is None or _norm(parts[0]) != _norm(binding.subject.platform):
        raise _error("schema_result_identity_mismatch")
    normalized_fields: list[DataHubFieldMetadata] = []
    seen_paths: set[str] = set()
    for raw in fields_value:
        try:
            field = _normalize_field(raw)
        except ValueError:
            raise _error("invalid_schema_field") from None
        norm_path = _norm(field.field_path)
        if norm_path in seen_paths:
            raise _error("duplicate_schema_field_path")
        seen_paths.add(norm_path)
        normalized_fields.append(field)
    fields_tuple = tuple(normalized_fields)
    target = _norm(binding.affected_column)
    matched = [field for field in fields_tuple if _norm(field.field_path) == target]
    if len(matched) == 1:
        observation = DataHubAffectedFieldObservation.OBSERVED_EXACT
        affected_field = matched[0]
    else:
        observation = DataHubAffectedFieldObservation.NOT_OBSERVED
        affected_field = None
    schema_slice = DataHubDatasetSchemaSlice(
        dataset_urn=returned_urn,
        fields=fields_tuple,
        provider_total_fields=total_fields,
        provider_returned=returned,
        provider_remaining_count=remaining_count,
        provider_matching_count=matching_count,
        provider_offset=offset,
        affected_field_observation=observation,
        affected_field=affected_field,
    )
    return DataHubSchemaFieldsExecutionResult(
        request_id=request.id,
        next_request_id=request.id + 1,
        schema_request_fingerprint=request_fingerprint,
        input_schema_fingerprint=argument_plan.input_schema_fingerprint,
        dataset_urn=returned_urn,
        schema_slice=schema_slice,
    )


__all__ = [
    "MAX_FIELDS",
    "RESULT_VERSION",
    "SCHEMA_SLICE_VERSION",
    "DataHubAffectedFieldObservation",
    "DataHubDatasetSchemaSlice",
    "DataHubSchemaFieldsExecutionError",
    "DataHubSchemaFieldsExecutionResult",
    "execute_datahub_list_schema_fields",
]
