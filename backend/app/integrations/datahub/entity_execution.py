"""F8.3C2 bounded get_entities execution and dataset metadata normalization.

This module executes exactly one ``get_entities`` ``tools/call`` per valid
invocation, reusing the F8.3C1 request plan and the F8.2 transport. It
validates the MCP envelope, normalizes a bounded set of dataset entity
metadata, and discards the raw provider response. It never executes the
schema tool, never retrieves lineage, never retries, and normalizes no schema
fields in this phase.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from app.schemas.datahub_context import DataHubNamedReference, DataHubOwnerKind, DataHubOwnerReference

from .asset_resolution import _dataset_urn_parts, _norm
from .config import DATAHUB_MCP_PROTOCOL_VERSION, DataHubMCPConfig
from .entity_schema_contract import (
    DataHubEntitySchemaContractError,
    DataHubEntitySchemaContext,
    DataHubEntitySchemaToolDiscoveryBundle,
    DataHubGetEntitiesArgumentPlan,
    build_datahub_get_entities_tools_call_request,
    serialize_datahub_get_entities_tools_call_request,
)
from .initialization import DataHubMCPSession
from .mcp_protocol import DataHubMCPProtocolError, _duplicate_key, _reject_constant, parse_http_response
from .search_execution import (
    MAX_CONTENT_BLOCKS,
    MAX_STRUCTURED_BYTES,
    MAX_TEXT_CHARS,
    DataHubSearchExecutionError,
    DataHubSearchExecutionResult,
    _canonical_size,
    _safe_name,
    _safe_urn,
    _validate_content,
)
from .transport import DataHubMCPTransport

RESULT_VERSION = "1.0"
METADATA_VERSION = "1.0"
MAX_DESCRIPTION_CHARS = 4000
MAX_NAME_CHARS = 512
_DATASET_PREFIX = "urn:li:dataset:"
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")
_OWNER_KIND_VALUES = frozenset(kind.value for kind in DataHubOwnerKind)


class DataHubEntityMetadataExecutionError(ValueError):
    """Safe, non-retryable entity metadata execution error."""

    def __init__(self, code: str, message: str = "DataHub entity metadata execution failed.", *, retryable: bool = False) -> None:
        self.code = code
        self.message = message
        self.retryable = retryable
        super().__init__(message)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _error(code: str) -> DataHubEntityMetadataExecutionError:
    return DataHubEntityMetadataExecutionError(code)


def _hex64(value: Any) -> str:
    if not isinstance(value, str) or not _FINGERPRINT.fullmatch(value):
        raise ValueError("invalid fingerprint")
    return value


class DataHubDatasetEntityMetadata(_Strict):
    """Bounded normalized dataset entity metadata.

    Reuses locked F8.1 reference subtypes. Metadata is external unverified
    context only and carries no authority.
    """

    dataset_urn: str
    dataset_name: str | None = None
    system_description: str | None = None
    editable_description: str | None = None
    owners: tuple[DataHubOwnerReference, ...] = Field(default_factory=tuple, max_length=50)
    tags: tuple[DataHubNamedReference, ...] = Field(default_factory=tuple, max_length=100)
    glossary_terms: tuple[DataHubNamedReference, ...] = Field(default_factory=tuple, max_length=100)
    domain: DataHubNamedReference | None = None
    metadata_version: str = METADATA_VERSION

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str:
        value = _safe_urn(value)
        if not value.startswith(_DATASET_PREFIX):
            raise ValueError("invalid dataset URN")
        return value

    @field_validator("dataset_name")
    @classmethod
    def name_ok(cls, value: str | None) -> str | None:
        return _safe_name(value)

    @field_validator("system_description", "editable_description")
    @classmethod
    def description_ok(cls, value: str | None) -> str | None:
        return _description_text(value)

    @model_validator(mode="after")
    def invariants(self) -> "DataHubDatasetEntityMetadata":
        if self.metadata_version != METADATA_VERSION:
            raise ValueError("invalid metadata version")
        return self


class DataHubEntityMetadataExecutionResult(_Strict):
    request_id: StrictInt = Field(gt=0)
    next_request_id: StrictInt = Field(gt=0)
    entity_request_fingerprint: str
    input_schema_fingerprint: str
    dataset_urn: str
    metadata: DataHubDatasetEntityMetadata
    result_version: str = RESULT_VERSION

    @field_validator("entity_request_fingerprint", "input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        return _hex64(value)

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str:
        return _safe_urn(value)

    @model_validator(mode="after")
    def invariants(self) -> "DataHubEntityMetadataExecutionResult":
        if self.next_request_id != self.request_id + 1 or self.result_version != RESULT_VERSION:
            raise ValueError("invalid entity metadata execution result")
        return self


def _description_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("invalid description")
    if "\x00" in value or any(ord(ch) < 32 and ch not in "\t\n\r" for ch in value):
        raise ValueError("invalid description")
    result = value.strip()
    if len(result) > MAX_DESCRIPTION_CHARS:
        raise ValueError("description is too large")
    return result or None


def _normalize_owners(wrapper: Any) -> tuple[DataHubOwnerReference, ...]:
    if wrapper is None:
        return ()
    if not isinstance(wrapper, dict):
        raise ValueError("invalid ownership")
    if "owners" not in wrapper:
        return ()
    items = wrapper["owners"]
    if not isinstance(items, list):
        raise ValueError("invalid ownership")
    result: list[DataHubOwnerReference] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("invalid owner")
        owner_ref = item.get("owner")
        if isinstance(owner_ref, dict):
            owner_urn = owner_ref.get("urn")
        elif isinstance(owner_ref, str):
            owner_urn = owner_ref
        else:
            raise ValueError("invalid owner")
        if not isinstance(owner_urn, str):
            raise ValueError("invalid owner")
        kind = DataHubOwnerKind.UNKNOWN
        raw_type = item.get("type")
        if raw_type is not None:
            if not isinstance(raw_type, str):
                raise ValueError("invalid ownership type")
            lowered = raw_type.strip().lower()
            if lowered in _OWNER_KIND_VALUES:
                kind = DataHubOwnerKind(lowered)
        try:
            result.append(DataHubOwnerReference(owner_urn=owner_urn, owner_kind=kind))
        except ValueError:
            raise ValueError("invalid owner") from None
    return tuple(result)


def _normalize_named_refs(wrapper: Any, *, wrapper_key: str, inner_key: str) -> tuple[DataHubNamedReference, ...]:
    if wrapper is None:
        return ()
    if not isinstance(wrapper, dict):
        raise ValueError("invalid reference collection")
    if wrapper_key not in wrapper:
        return ()
    items = wrapper[wrapper_key]
    if not isinstance(items, list):
        raise ValueError("invalid reference collection")
    result: list[DataHubNamedReference] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("invalid reference")
        ref = item.get(inner_key)
        if not isinstance(ref, dict):
            raise ValueError("invalid reference")
        urn = ref.get("urn")
        name = ref.get("name")
        if not isinstance(urn, str) or not isinstance(name, str):
            raise ValueError("invalid reference")
        try:
            result.append(DataHubNamedReference(urn=urn, name=name))
        except ValueError:
            raise ValueError("invalid reference") from None
    return tuple(result)


def _normalize_domain(wrapper: Any) -> DataHubNamedReference | None:
    if wrapper is None:
        return None
    if not isinstance(wrapper, dict):
        raise ValueError("invalid domain")
    if "domain" not in wrapper:
        return None
    ref = wrapper["domain"]
    if not isinstance(ref, dict):
        raise ValueError("invalid domain")
    urn = ref.get("urn")
    name = ref.get("name")
    if not isinstance(urn, str) or not isinstance(name, str):
        raise ValueError("invalid domain")
    return DataHubNamedReference(urn=urn, name=name)


def _normalize_metadata(*, dataset_urn: str, entity: dict[str, Any]) -> DataHubDatasetEntityMetadata:
    try:
        dataset_name: str | None = None
        system_description: str | None = None
        editable_description: str | None = None
        properties = entity.get("properties")
        if properties is not None:
            if not isinstance(properties, dict):
                raise ValueError("invalid properties")
            dataset_name = _safe_name(properties.get("name"))
            system_description = _description_text(properties.get("description"))
        editable = entity.get("editableProperties")
        if editable is not None:
            if not isinstance(editable, dict):
                raise ValueError("invalid editable properties")
            editable_description = _description_text(editable.get("description"))
        owners = _normalize_owners(entity.get("ownership"))
        tags = _normalize_named_refs(entity.get("globalTags"), wrapper_key="tags", inner_key="tag")
        glossary_terms = _normalize_named_refs(entity.get("glossaryTerms"), wrapper_key="terms", inner_key="term")
        domain = _normalize_domain(entity.get("domain"))
        return DataHubDatasetEntityMetadata(
            dataset_urn=dataset_urn,
            dataset_name=dataset_name,
            system_description=system_description,
            editable_description=editable_description,
            owners=owners,
            tags=tags,
            glossary_terms=glossary_terms,
            domain=domain,
        )
    except ValueError:
        raise _error("invalid_entity_metadata") from None


def _validate_entity_content(result: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        return _validate_content(result)
    except DataHubSearchExecutionError as exc:
        mapping = {
            "invalid_search_tool_result": "invalid_entity_tool_result",
            "unsupported_search_content": "unsupported_entity_content",
            "search_content_too_large": "entity_content_too_large",
        }
        code = mapping.get(exc.code)
        if code is None:
            raise _error("invalid_entity_tool_result") from None
        raise _error(code) from None


def _entity_canonical_size(value: dict[str, Any]) -> int:
    try:
        return _canonical_size(value)
    except DataHubSearchExecutionError:
        raise _error("invalid_entity_result_payload") from None


def parse_strict_json_array(payload: bytes | str) -> list[Any]:
    """Decode exactly one strict UTF-8 JSON array without retaining raw text."""
    if isinstance(payload, bytes):
        try:
            text = payload.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise _error("invalid_entity_result_payload") from None
    elif isinstance(payload, str):
        text = payload
    else:
        raise _error("invalid_entity_result_payload")
    if not text.strip() or "\x00" in text:
        raise _error("invalid_entity_result_payload")
    try:
        value = json.loads(text, object_pairs_hook=_duplicate_key, parse_constant=_reject_constant)
    except (json.JSONDecodeError, ValueError, TypeError):
        raise _error("invalid_entity_result_payload") from None
    if not isinstance(value, list):
        raise _error("invalid_entity_result_payload")
    return value


def _select_entity_items(result: dict[str, Any], text_blocks: list[dict[str, Any]]) -> list[Any]:
    if "structuredContent" in result:
        payload = result["structuredContent"]
        if not isinstance(payload, dict):
            raise _error("invalid_entity_result_payload")
        if _entity_canonical_size(payload) > MAX_STRUCTURED_BYTES:
            raise _error("entity_content_too_large")
        if "result" not in payload:
            raise _error("missing_entity_result_payload")
        items = payload["result"]
        if not isinstance(items, list):
            raise _error("invalid_entity_result_payload")
        return items
    if len(text_blocks) != 1:
        raise _error("missing_entity_result_payload")
    return parse_strict_json_array(text_blocks[0]["text"])


def execute_datahub_get_entities(*, config: DataHubMCPConfig, session: DataHubMCPSession, discovery: DataHubEntitySchemaToolDiscoveryBundle, binding: DataHubEntitySchemaContext, argument_plan: DataHubGetEntitiesArgumentPlan, search_execution: DataHubSearchExecutionResult, transport: DataHubMCPTransport) -> DataHubEntityMetadataExecutionResult:
    """Execute exactly one bounded get_entities call and normalize dataset metadata.

    All preflight failures happen before any transport call. Exactly one
    ``tools/call`` for ``get_entities`` is sent on success; there is never a
    retry or a second attempt.
    """
    if not isinstance(config, DataHubMCPConfig) or not isinstance(session, DataHubMCPSession):
        raise _error("entity_execution_context_mismatch")
    if session.endpoint_url != config.endpoint_url or session.protocol_version != DATAHUB_MCP_PROTOCOL_VERSION or not session.tools_supported:
        raise _error("entity_execution_context_mismatch")
    if not isinstance(discovery, DataHubEntitySchemaToolDiscoveryBundle) or not isinstance(binding, DataHubEntitySchemaContext) or not isinstance(argument_plan, DataHubGetEntitiesArgumentPlan) or not isinstance(search_execution, DataHubSearchExecutionResult):
        raise _error("entity_execution_context_mismatch")
    if binding.discovery.get_entities_contract.input_schema_fingerprint != discovery.get_entities_contract.input_schema_fingerprint:
        raise _error("entity_execution_context_mismatch")
    if binding.search_execution.next_request_id != search_execution.next_request_id or binding.search_execution.input_schema_fingerprint != search_execution.input_schema_fingerprint:
        raise _error("entity_execution_context_mismatch")
    if not discovery.read_discovery.catalog.all_required_tools_available:
        raise _error("entity_execution_context_mismatch")
    capability = next((tool for tool in discovery.read_discovery.catalog.tools if tool.name.value == "get_entities"), None)
    if capability is None or capability.input_schema_fingerprint != discovery.get_entities_contract.input_schema_fingerprint:
        raise _error("entity_execution_context_mismatch")
    if argument_plan.input_schema_fingerprint != discovery.get_entities_contract.input_schema_fingerprint:
        raise _error("entity_execution_context_mismatch")
    plan_args = dict(argument_plan.arguments)
    if plan_args != {"urns": (argument_plan.dataset_urn,)} or len(plan_args["urns"]) != 1:
        raise _error("entity_execution_context_mismatch")
    if argument_plan.dataset_urn != binding.dataset_urn:
        raise _error("entity_execution_context_mismatch")
    dataset_urn = binding.dataset_urn
    try:
        _safe_urn(dataset_urn)
    except ValueError:
        raise _error("entity_execution_context_mismatch") from None
    parts = _dataset_urn_parts(dataset_urn)
    if parts is None or _norm(parts[0]) != _norm(binding.subject.platform):
        raise _error("entity_execution_context_mismatch")
    if binding.get_entities_request_id != search_execution.next_request_id:
        raise _error("entity_execution_context_mismatch")
    try:
        request = build_datahub_get_entities_tools_call_request(context=binding, contract=discovery.get_entities_contract, argument_plan=argument_plan)
        body = serialize_datahub_get_entities_tools_call_request(context=binding, contract=discovery.get_entities_contract, argument_plan=argument_plan)
    except DataHubEntitySchemaContractError:
        raise _error("entity_execution_context_mismatch") from None
    if request.id != binding.get_entities_request_id:
        raise _error("entity_execution_context_mismatch")
    request_fingerprint = hashlib.sha256(body).hexdigest()
    if not _FINGERPRINT.fullmatch(request_fingerprint):
        raise _error("entity_request_fingerprint_invalid")
    try:
        response = transport.post_request(body, session_id=session.session_id, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION)
        parsed = parse_http_response(response, expected_id=request.id)
    except DataHubMCPProtocolError:
        raise
    if parsed.request_id != request.id:
        raise _error("entity_result_request_mismatch")
    if parsed.error is not None or parsed.result is None:
        raise _error("entity_tool_execution_failed")
    result = parsed.result
    is_error = result.get("isError", False)
    if not isinstance(is_error, bool):
        raise _error("invalid_entity_tool_result")
    if is_error:
        raise _error("entity_tool_execution_failed")
    text_blocks = _validate_entity_content(result)
    items = _select_entity_items(result, text_blocks)
    if len(items) != 1:
        raise _error("entity_result_cardinality_mismatch")
    entity = items[0]
    if not isinstance(entity, dict):
        raise _error("invalid_entity_result_payload")
    if "error" in entity and entity["error"] not in (None, False):
        raise _error("entity_provider_item_failed")
    returned_urn = entity.get("urn")
    try:
        returned_urn = _safe_urn(returned_urn)
    except ValueError:
        raise _error("entity_result_identity_mismatch") from None
    if not returned_urn.startswith(_DATASET_PREFIX) or returned_urn != dataset_urn:
        raise _error("entity_result_identity_mismatch")
    parts = _dataset_urn_parts(returned_urn)
    if parts is None or _norm(parts[0]) != _norm(binding.subject.platform):
        raise _error("entity_result_identity_mismatch")
    metadata = _normalize_metadata(dataset_urn=returned_urn, entity=entity)
    return DataHubEntityMetadataExecutionResult(
        request_id=request.id,
        next_request_id=request.id + 1,
        entity_request_fingerprint=request_fingerprint,
        input_schema_fingerprint=argument_plan.input_schema_fingerprint,
        dataset_urn=returned_urn,
        metadata=metadata,
    )


__all__ = [
    "METADATA_VERSION",
    "RESULT_VERSION",
    "DataHubDatasetEntityMetadata",
    "DataHubEntityMetadataExecutionError",
    "DataHubEntityMetadataExecutionResult",
    "execute_datahub_get_entities",
]
