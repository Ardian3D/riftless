"""F8.3C1 get_entities / list_schema_fields schema attestation and call planning.

This module is planning-only. It attests ephemeral provider input schemas for
``get_entities`` and ``list_schema_fields``, binds them to a deterministically
resolved F8.3B3 dataset, builds immutable argument plans, and constructs
canonical ``tools/call`` request objects and bytes. It never executes a tool,
never calls the transport, and parses no provider output.
"""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from app.schemas.datahub_context import DataHubEntityKind

from .asset_resolution import (
    DataHubAssetCandidateResolution,
    DataHubAssetResolutionStatus,
    DataHubAssetResolutionSubject,
    _dataset_urn_parts,
    _identity_text,
    _norm,
)
from .config import DATAHUB_MCP_MAX_REQUEST_BYTES, DataHubMCPConfig
from .initialization import DataHubMCPSession
from .mcp_protocol import DataHubMCPProtocolError, MCPRequest, serialize_jsonrpc
from .search_contract import (
    DataHubReadToolDiscoveryBundle,
    DataHubSearchContractError,
    _make_search_contract,
    _types,
)
from .search_execution import DataHubSearchExecutionResult, _safe_urn
from .tool_discovery import (
    DataHubReadToolName,
    DataHubToolDiscoveryError,
    _discover_tool_details,
    fingerprint_datahub_tool_input_schema as _schema_fingerprint_hex,
)
from .transport import DataHubMCPTransport

ENTITY_SCHEMA_BUNDLE_VERSION = "1.0"
GET_ENTITIES_CONTRACT_VERSION = "1.0"
LIST_SCHEMA_FIELDS_CONTRACT_VERSION = "1.0"
GET_ENTITIES_PLAN_VERSION = "1.0"
LIST_SCHEMA_FIELDS_PLAN_VERSION = "1.0"
BINDING_VERSION = "1.0"

_MAX_URN_CHARS = 1024
_MAX_KEYWORD_CHARS = 256
_MAX_COLUMN = 256
_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")

_GET_ENTITIES_KNOWN = frozenset({"urns"})
_SCHEMA_KNOWN = frozenset({"urn", "keywords", "limit", "offset"})


class DataHubEntitySchemaContractError(ValueError):
    """Safe, non-retryable entity/schema contract or planning error."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        self.retryable = False
        super().__init__(message)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _error(code: str) -> DataHubEntitySchemaContractError:
    return DataHubEntitySchemaContractError(code, "DataHub entity/schema contract is invalid.")


def _hex64(value: Any) -> str:
    if not isinstance(value, str) or not _FINGERPRINT.fullmatch(value):
        raise ValueError("invalid fingerprint")
    return value


class DataHubGetEntitiesSchemaContract(_Strict):
    input_schema_fingerprint: str
    supports_single_item_urn_array: bool
    contract_version: str = GET_ENTITIES_CONTRACT_VERSION

    @field_validator("input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        return _hex64(value)

    @model_validator(mode="after")
    def invariants(self) -> "DataHubGetEntitiesSchemaContract":
        if not self.supports_single_item_urn_array or self.contract_version != GET_ENTITIES_CONTRACT_VERSION:
            raise ValueError("invalid get_entities schema contract")
        return self


class DataHubListSchemaFieldsSchemaContract(_Strict):
    input_schema_fingerprint: str
    urn_supported: bool
    keywords_supported: bool
    limit_50_supported: bool
    offset_zero_supported: bool
    contract_version: str = LIST_SCHEMA_FIELDS_CONTRACT_VERSION

    @field_validator("input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        return _hex64(value)

    @model_validator(mode="after")
    def invariants(self) -> "DataHubListSchemaFieldsSchemaContract":
        required = (self.urn_supported and self.keywords_supported and self.limit_50_supported and self.offset_zero_supported)
        if not required or self.contract_version != LIST_SCHEMA_FIELDS_CONTRACT_VERSION:
            raise ValueError("invalid list_schema_fields schema contract")
        return self


class DataHubEntitySchemaToolDiscoveryBundle(_Strict):
    read_discovery: DataHubReadToolDiscoveryBundle
    get_entities_contract: DataHubGetEntitiesSchemaContract
    list_schema_fields_contract: DataHubListSchemaFieldsSchemaContract
    bundle_version: str = ENTITY_SCHEMA_BUNDLE_VERSION

    @model_validator(mode="after")
    def invariants(self) -> "DataHubEntitySchemaToolDiscoveryBundle":
        if self.bundle_version != ENTITY_SCHEMA_BUNDLE_VERSION:
            raise ValueError("invalid entity/schema discovery bundle version")
        if self._capability_fp(DataHubReadToolName.GET_ENTITIES.value) != self.get_entities_contract.input_schema_fingerprint:
            raise ValueError("get_entities fingerprint mismatch")
        if self._capability_fp(DataHubReadToolName.LIST_SCHEMA_FIELDS.value) != self.list_schema_fields_contract.input_schema_fingerprint:
            raise ValueError("list_schema_fields fingerprint mismatch")
        return self

    def _capability_fp(self, tool_name: str) -> str | None:
        for tool in self.read_discovery.catalog.tools:
            if tool.name.value == tool_name:
                return tool.input_schema_fingerprint
        return None


class DataHubEntitySchemaContext(_Strict):
    subject: DataHubAssetResolutionSubject
    resolution: DataHubAssetCandidateResolution
    search_execution: DataHubSearchExecutionResult
    discovery: DataHubEntitySchemaToolDiscoveryBundle
    dataset_urn: str
    affected_column: str
    get_entities_request_id: StrictInt = Field(gt=0)
    list_schema_fields_request_id: StrictInt = Field(gt=0)
    post_metadata_next_request_id: StrictInt = Field(gt=0)
    binding_version: str = BINDING_VERSION

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str:
        return _safe_urn(value)

    @field_validator("affected_column")
    @classmethod
    def column_ok(cls, value: str) -> str:
        return _identity_text(value, name="affected_column", max_len=_MAX_COLUMN)

    @model_validator(mode="after")
    def invariants(self) -> "DataHubEntitySchemaContext":
        if self.binding_version != BINDING_VERSION:
            raise ValueError("invalid binding version")
        if self.resolution.status is not DataHubAssetResolutionStatus.RESOLVED:
            raise ValueError("unresolved resolution cannot bind")
        if self.dataset_urn != self.resolution.selected_dataset_urn:
            raise ValueError("dataset urn mismatch")
        next_id = self.search_execution.next_request_id
        if isinstance(next_id, bool) or not isinstance(next_id, int) or not 4 <= next_id <= 13:
            raise ValueError("invalid request id chain")
        if self.get_entities_request_id != next_id or self.list_schema_fields_request_id != next_id + 1 or self.post_metadata_next_request_id != next_id + 2:
            raise ValueError("invalid request id chain")
        return self


class DataHubGetEntitiesArgumentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    dataset_urn: str
    arguments: Mapping[str, Any]
    input_schema_fingerprint: str
    plan_version: str = GET_ENTITIES_PLAN_VERSION

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str:
        return _safe_urn(value)

    @field_validator("input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        return _hex64(value)

    @model_validator(mode="after")
    def freeze(self) -> "DataHubGetEntitiesArgumentPlan":
        if dict(self.arguments) != {"urns": (self.dataset_urn,)}:
            raise ValueError("invalid get_entities argument plan")
        object.__setattr__(self, "arguments", MappingProxyType(dict(self.arguments)))
        if self.plan_version != GET_ENTITIES_PLAN_VERSION:
            raise ValueError("invalid plan version")
        return self


class DataHubListSchemaFieldsArgumentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    dataset_urn: str
    affected_column: str
    arguments: Mapping[str, Any]
    input_schema_fingerprint: str
    plan_version: str = LIST_SCHEMA_FIELDS_PLAN_VERSION

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str:
        return _safe_urn(value)

    @field_validator("affected_column")
    @classmethod
    def column_ok(cls, value: str) -> str:
        return _identity_text(value, name="affected_column", max_len=_MAX_COLUMN)

    @field_validator("input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        return _hex64(value)

    @model_validator(mode="after")
    def freeze(self) -> "DataHubListSchemaFieldsArgumentPlan":
        expected = {"urn": self.dataset_urn, "keywords": (self.affected_column,), "limit": 50, "offset": 0}
        if dict(self.arguments) != expected:
            raise ValueError("invalid list_schema_fields argument plan")
        object.__setattr__(self, "arguments", MappingProxyType(dict(self.arguments)))
        if self.plan_version != LIST_SCHEMA_FIELDS_PLAN_VERSION:
            raise ValueError("invalid plan version")
        return self


def _type_member(node: Any, expected: str) -> dict[str, Any] | None:
    """Return the effective subnode of ``expected`` type across narrow nullable unions."""
    if not isinstance(node, dict):
        return None
    node_type = node.get("type")
    if isinstance(node_type, str):
        return node if node_type == expected else None
    if isinstance(node_type, list):
        if expected in node_type and all(item in {expected, "null"} for item in node_type):
            return node
        return None
    for key in ("anyOf", "oneOf"):
        members = node.get(key)
        if isinstance(members, list) and 1 <= len(members) <= 2:
            non_null = [member for member in members if isinstance(member, dict) and member.get("type") != "null"]
            if len(non_null) == 1:
                nested = _type_member(non_null[0], expected)
                if nested is not None:
                    return nested
    return None


def _string_accepts_length(node: Any, *, min_len: int) -> bool:
    if not _types(node, "string"):
        return False
    member = _type_member(node, "string")
    if member is None or "pattern" in member:
        return False
    if "maxLength" in member:
        value = member["maxLength"]
        if not isinstance(value, int) or isinstance(value, bool) or value < min_len:
            return False
    return True


def _integer_permits(node: Any, value: int) -> bool:
    if not _types(node, "integer"):
        return False
    member = _type_member(node, "integer")
    if member is None:
        return False
    if "minimum" in member and (not isinstance(member["minimum"], (int, float)) or isinstance(member["minimum"], bool) or member["minimum"] > value):
        return False
    if "maximum" in member and (not isinstance(member["maximum"], (int, float)) or isinstance(member["maximum"], bool) or member["maximum"] < value):
        return False
    if "enum" in member and (not isinstance(member["enum"], list) or value not in member["enum"]):
        return False
    if "const" in member and member["const"] != value:
        return False
    return True


def _array_permits_single_string_item(node: Any, *, item_min_len: int) -> bool:
    if not _types(node, "array"):
        return False
    array = _type_member(node, "array")
    if array is None:
        return False
    items = array.get("items")
    if not isinstance(items, dict) or not _string_accepts_length(items, min_len=item_min_len):
        return False
    if "maxItems" in array:
        value = array["maxItems"]
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            return False
    if "minItems" in array:
        value = array["minItems"]
        if not isinstance(value, int) or isinstance(value, bool) or value > 1:
            return False
    return True


def _schema_required(schema: Any) -> list[str] | None:
    if not isinstance(schema, dict) or schema.get("type") != "object":
        return None
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return None
    required = schema.get("required", [])
    if not isinstance(required, list) or not all(isinstance(item, str) and item for item in required) or len(set(required)) != len(required):
        return None
    return required


def _cross_check_fp(schema: dict[str, Any], catalog_fingerprint: str) -> str:
    try:
        actual = _schema_fingerprint_hex(schema)
    except (DataHubToolDiscoveryError, ValueError):
        raise _error("entity_schema_schema_incompatible") from None
    if actual != catalog_fingerprint:
        raise _error("entity_schema_fingerprint_mismatch")
    return catalog_fingerprint


def attest_datahub_get_entities_schema(*, schema: dict[str, Any], catalog_fingerprint: str) -> DataHubGetEntitiesSchemaContract:
    """Attest an ephemeral get_entities input schema against the bounded contract.

    Only the ``urns`` property is recognized. Array support with string items
    that safely accept one bounded dataset URN is required; anything else
    fails closed.
    """
    required = _schema_required(schema)
    if required is None or "urns" not in required:
        raise _error("entity_schema_schema_incompatible")
    if any(item not in _GET_ENTITIES_KNOWN for item in required):
        raise _error("unsupported_required_entity_argument")
    urns_node = schema.get("properties", {}).get("urns")
    if not isinstance(urns_node, dict) or not _array_permits_single_string_item(urns_node, item_min_len=_MAX_URN_CHARS):
        raise _error("entity_schema_schema_incompatible")
    fingerprint = _cross_check_fp(schema, catalog_fingerprint)
    return DataHubGetEntitiesSchemaContract(input_schema_fingerprint=fingerprint, supports_single_item_urn_array=True)


def attest_datahub_list_schema_fields_schema(*, schema: dict[str, Any], catalog_fingerprint: str) -> DataHubListSchemaFieldsSchemaContract:
    """Attest an ephemeral list_schema_fields input schema against the bounded contract.

    Recognizes only ``urn``, ``keywords``, ``limit``, and ``offset``. All four
    must be structurally compatible with the exact RIFTLESS call strategy;
    otherwise the schema is incompatible and rejected.
    """
    required = _schema_required(schema)
    if required is None or "urn" not in required:
        raise _error("entity_schema_schema_incompatible")
    if any(item not in _SCHEMA_KNOWN for item in required):
        raise _error("unsupported_required_schema_argument")
    properties = schema.get("properties", {})
    if not _string_accepts_length(properties.get("urn"), min_len=_MAX_URN_CHARS):
        raise _error("entity_schema_schema_incompatible")
    if not _array_permits_single_string_item(properties.get("keywords"), item_min_len=_MAX_KEYWORD_CHARS):
        raise _error("entity_schema_schema_incompatible")
    if not _integer_permits(properties.get("limit"), 50):
        raise _error("entity_schema_schema_incompatible")
    if not _integer_permits(properties.get("offset"), 0):
        raise _error("entity_schema_schema_incompatible")
    fingerprint = _cross_check_fp(schema, catalog_fingerprint)
    return DataHubListSchemaFieldsSchemaContract(input_schema_fingerprint=fingerprint, urn_supported=True, keywords_supported=True, limit_50_supported=True, offset_zero_supported=True)


def discover_datahub_entity_schema_tool_bundle(*, config: DataHubMCPConfig, session: DataHubMCPSession, transport: DataHubMCPTransport) -> DataHubEntitySchemaToolDiscoveryBundle:
    """Derive search, get_entities, and list_schema_fields contracts from one tools/list sequence."""
    catalog, schemas, next_request_id = _discover_tool_details(config=config, session=session, transport=transport)
    search_schema = schemas.get("search")
    if search_schema is None:
        raise DataHubSearchContractError("search_schema_missing", "DataHub search schema is missing.")
    search_tool = next((tool for tool in catalog.tools if tool.name is DataHubReadToolName.SEARCH), None)
    if search_tool is None:
        raise DataHubToolDiscoveryError("required_tool_missing", "Required DataHub MCP read capability is missing.")
    search_contract = _make_search_contract(search_schema, search_tool.input_schema_fingerprint)
    read_discovery = DataHubReadToolDiscoveryBundle(catalog=catalog, search_contract=search_contract, next_request_id=next_request_id)
    get_entities_schema = schemas.get("get_entities")
    get_entities_capability = next((tool for tool in catalog.tools if tool.name is DataHubReadToolName.GET_ENTITIES), None)
    if get_entities_schema is None or get_entities_capability is None:
        raise _error("entity_schema_schema_missing")
    get_entities_contract = attest_datahub_get_entities_schema(schema=get_entities_schema, catalog_fingerprint=get_entities_capability.input_schema_fingerprint)
    list_schema_fields_schema = schemas.get("list_schema_fields")
    list_schema_fields_capability = next((tool for tool in catalog.tools if tool.name is DataHubReadToolName.LIST_SCHEMA_FIELDS), None)
    if list_schema_fields_schema is None or list_schema_fields_capability is None:
        raise _error("entity_schema_schema_missing")
    list_schema_fields_contract = attest_datahub_list_schema_fields_schema(schema=list_schema_fields_schema, catalog_fingerprint=list_schema_fields_capability.input_schema_fingerprint)
    return DataHubEntitySchemaToolDiscoveryBundle(read_discovery=read_discovery, get_entities_contract=get_entities_contract, list_schema_fields_contract=list_schema_fields_contract)


def _catalog_fp(discovery: DataHubEntitySchemaToolDiscoveryBundle, tool_name: str) -> str | None:
    for tool in discovery.read_discovery.catalog.tools:
        if tool.name.value == tool_name:
            return tool.input_schema_fingerprint
    return None


def bind_datahub_entity_schema_context(*, subject: DataHubAssetResolutionSubject, resolution: DataHubAssetCandidateResolution, search_execution: DataHubSearchExecutionResult, discovery: DataHubEntitySchemaToolDiscoveryBundle) -> DataHubEntitySchemaContext:
    """Bind a resolved dataset and executed search result to the F8.3C1 discovery bundle.

    Ambiguous or unresolved resolutions fail before any planning. Mixed or
    inconsistent inputs are rejected with safe errors.
    """
    if not isinstance(subject, DataHubAssetResolutionSubject) or not isinstance(resolution, DataHubAssetCandidateResolution):
        raise _error("invalid_entity_schema_binding")
    if not isinstance(search_execution, DataHubSearchExecutionResult) or not isinstance(discovery, DataHubEntitySchemaToolDiscoveryBundle):
        raise _error("invalid_entity_schema_binding")
    if resolution.status is not DataHubAssetResolutionStatus.RESOLVED or resolution.selected_dataset_urn is None or resolution.selected_source_position is None:
        raise _error("invalid_entity_schema_binding")
    dataset_urn = resolution.selected_dataset_urn
    affected_column = subject.affected_column
    if affected_column is None:
        raise _error("invalid_entity_schema_binding")
    records = search_execution.records
    if resolution.candidate_count != len(records):
        raise _error("invalid_entity_schema_binding")
    matches = [record for record in records if record.dataset_urn == dataset_urn]
    if len(matches) != 1 or matches[0].source_position != resolution.selected_source_position:
        raise _error("invalid_entity_schema_binding")
    parts = _dataset_urn_parts(dataset_urn)
    if parts is None or _norm(parts[0]) != _norm(subject.platform):
        raise _error("invalid_entity_schema_binding")
    if search_execution.input_schema_fingerprint != discovery.read_discovery.search_contract.input_schema_fingerprint:
        raise _error("entity_schema_fingerprint_mismatch")
    if _catalog_fp(discovery, DataHubReadToolName.GET_ENTITIES.value) != discovery.get_entities_contract.input_schema_fingerprint:
        raise _error("entity_schema_fingerprint_mismatch")
    if _catalog_fp(discovery, DataHubReadToolName.LIST_SCHEMA_FIELDS.value) != discovery.list_schema_fields_contract.input_schema_fingerprint:
        raise _error("entity_schema_fingerprint_mismatch")
    next_id = search_execution.next_request_id
    if isinstance(next_id, bool) or not isinstance(next_id, int) or not 4 <= next_id <= 13:
        raise _error("entity_schema_request_id_invalid")
    try:
        return DataHubEntitySchemaContext(
            subject=subject,
            resolution=resolution,
            search_execution=search_execution,
            discovery=discovery,
            dataset_urn=dataset_urn,
            affected_column=affected_column,
            get_entities_request_id=next_id,
            list_schema_fields_request_id=next_id + 1,
            post_metadata_next_request_id=next_id + 2,
        )
    except ValueError:
        raise _error("invalid_entity_schema_binding") from None


def build_datahub_get_entities_argument_plan(*, context: DataHubEntitySchemaContext, contract: DataHubGetEntitiesSchemaContract) -> DataHubGetEntitiesArgumentPlan:
    if not isinstance(context, DataHubEntitySchemaContext) or not isinstance(contract, DataHubGetEntitiesSchemaContract):
        raise _error("invalid_entity_metadata_argument_plan")
    if contract.input_schema_fingerprint != context.discovery.get_entities_contract.input_schema_fingerprint:
        raise _error("entity_schema_fingerprint_mismatch")
    return DataHubGetEntitiesArgumentPlan(dataset_urn=context.dataset_urn, arguments={"urns": (context.dataset_urn,)}, input_schema_fingerprint=contract.input_schema_fingerprint)


def build_datahub_list_schema_fields_argument_plan(*, context: DataHubEntitySchemaContext, contract: DataHubListSchemaFieldsSchemaContract) -> DataHubListSchemaFieldsArgumentPlan:
    if not isinstance(context, DataHubEntitySchemaContext) or not isinstance(contract, DataHubListSchemaFieldsSchemaContract):
        raise _error("invalid_schema_fields_argument_plan")
    if contract.input_schema_fingerprint != context.discovery.list_schema_fields_contract.input_schema_fingerprint:
        raise _error("entity_schema_fingerprint_mismatch")
    return DataHubListSchemaFieldsArgumentPlan(
        dataset_urn=context.dataset_urn,
        affected_column=context.affected_column,
        arguments={"urn": context.dataset_urn, "keywords": (context.affected_column,), "limit": 50, "offset": 0},
        input_schema_fingerprint=contract.input_schema_fingerprint,
    )


def build_datahub_get_entities_tools_call_request(*, context: DataHubEntitySchemaContext, contract: DataHubGetEntitiesSchemaContract, argument_plan: DataHubGetEntitiesArgumentPlan) -> MCPRequest:
    if not isinstance(context, DataHubEntitySchemaContext) or not isinstance(contract, DataHubGetEntitiesSchemaContract) or not isinstance(argument_plan, DataHubGetEntitiesArgumentPlan):
        raise _error("invalid_entity_metadata_argument_plan")
    if contract.input_schema_fingerprint != context.discovery.get_entities_contract.input_schema_fingerprint:
        raise _error("entity_schema_fingerprint_mismatch")
    if argument_plan.input_schema_fingerprint != contract.input_schema_fingerprint:
        raise _error("entity_schema_fingerprint_mismatch")
    if argument_plan.dataset_urn != context.dataset_urn:
        raise _error("invalid_entity_schema_binding")
    return MCPRequest(id=context.get_entities_request_id, method="tools/call", params={"name": "get_entities", "arguments": dict(argument_plan.arguments)})


def build_datahub_list_schema_fields_tools_call_request(*, context: DataHubEntitySchemaContext, contract: DataHubListSchemaFieldsSchemaContract, argument_plan: DataHubListSchemaFieldsArgumentPlan) -> MCPRequest:
    if not isinstance(context, DataHubEntitySchemaContext) or not isinstance(contract, DataHubListSchemaFieldsSchemaContract) or not isinstance(argument_plan, DataHubListSchemaFieldsArgumentPlan):
        raise _error("invalid_schema_fields_argument_plan")
    if contract.input_schema_fingerprint != context.discovery.list_schema_fields_contract.input_schema_fingerprint:
        raise _error("entity_schema_fingerprint_mismatch")
    if argument_plan.input_schema_fingerprint != contract.input_schema_fingerprint:
        raise _error("entity_schema_fingerprint_mismatch")
    if argument_plan.dataset_urn != context.dataset_urn:
        raise _error("invalid_entity_schema_binding")
    if argument_plan.affected_column != context.affected_column:
        raise _error("invalid_schema_fields_argument_plan")
    if context.list_schema_fields_request_id != context.get_entities_request_id + 1:
        raise _error("entity_schema_request_id_invalid")
    return MCPRequest(id=context.list_schema_fields_request_id, method="tools/call", params={"name": "list_schema_fields", "arguments": dict(argument_plan.arguments)})


def _serialize_request(request: MCPRequest) -> bytes:
    try:
        body = serialize_jsonrpc(request)
    except DataHubMCPProtocolError:
        raise _error("entity_schema_request_invalid") from None
    if len(body) > DATAHUB_MCP_MAX_REQUEST_BYTES:
        raise _error("entity_schema_request_too_large")
    return body


def serialize_datahub_get_entities_tools_call_request(*, context: DataHubEntitySchemaContext, contract: DataHubGetEntitiesSchemaContract, argument_plan: DataHubGetEntitiesArgumentPlan) -> bytes:
    request = build_datahub_get_entities_tools_call_request(context=context, contract=contract, argument_plan=argument_plan)
    return _serialize_request(request)


def serialize_datahub_list_schema_fields_tools_call_request(*, context: DataHubEntitySchemaContext, contract: DataHubListSchemaFieldsSchemaContract, argument_plan: DataHubListSchemaFieldsArgumentPlan) -> bytes:
    request = build_datahub_list_schema_fields_tools_call_request(context=context, contract=contract, argument_plan=argument_plan)
    return _serialize_request(request)


__all__ = [
    "BINDING_VERSION",
    "ENTITY_SCHEMA_BUNDLE_VERSION",
    "GET_ENTITIES_CONTRACT_VERSION",
    "GET_ENTITIES_PLAN_VERSION",
    "LIST_SCHEMA_FIELDS_CONTRACT_VERSION",
    "LIST_SCHEMA_FIELDS_PLAN_VERSION",
    "DataHubEntitySchemaContractError",
    "DataHubEntitySchemaContext",
    "DataHubEntitySchemaToolDiscoveryBundle",
    "DataHubGetEntitiesArgumentPlan",
    "DataHubGetEntitiesSchemaContract",
    "DataHubListSchemaFieldsArgumentPlan",
    "DataHubListSchemaFieldsSchemaContract",
    "attest_datahub_get_entities_schema",
    "attest_datahub_list_schema_fields_schema",
    "bind_datahub_entity_schema_context",
    "build_datahub_get_entities_argument_plan",
    "build_datahub_get_entities_tools_call_request",
    "build_datahub_list_schema_fields_argument_plan",
    "build_datahub_list_schema_fields_tools_call_request",
    "discover_datahub_entity_schema_tool_bundle",
    "serialize_datahub_get_entities_tools_call_request",
    "serialize_datahub_list_schema_fields_tools_call_request",
]
