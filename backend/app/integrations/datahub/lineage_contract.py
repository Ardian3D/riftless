"""F8.3D1 get_lineage schema attestation and downstream lineage call planning.

This module is planning-only. It attests the ephemeral provider ``get_lineage``
input schema, derives the lineage contract from the same single tools/list
discovery sequence as the search/entity/schema contracts, binds lineage
planning to the completed F8.3B3/F8.3C2/F8.3C3 identity chain, and constructs
two deterministic downstream-lineage request objects. It never executes
``get_lineage`` and never parses provider output.
"""

from __future__ import annotations

import json
from types import MappingProxyType
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from .asset_resolution import (
    DataHubAssetCandidateResolution,
    DataHubAssetResolutionStatus,
    DataHubAssetResolutionSubject,
    _dataset_urn_parts,
    _identity_text,
    _norm,
)
from .config import DATAHUB_MCP_MAX_REQUEST_BYTES, DataHubMCPConfig
from .entity_execution import DataHubEntityMetadataExecutionResult
from .entity_schema_contract import (
    DataHubEntitySchemaContext,
    DataHubEntitySchemaToolDiscoveryBundle,
    attest_datahub_get_entities_schema as _entity_schema_attest,
    attest_datahub_list_schema_fields_schema as _schema_fields_attest,
    _hex64,
    _integer_permits,
    _schema_required,
    _string_accepts_length,
    _type_member,
)
from .initialization import DataHubMCPSession
from .mcp_protocol import DataHubMCPProtocolError, MCPRequest, serialize_jsonrpc
from .schema_execution import DataHubSchemaFieldsExecutionResult
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

LINEAGE_CONTRACT_VERSION = "1.0"
LINEAGE_BUNDLE_VERSION = "1.0"
DATASET_LINEAGE_PLAN_VERSION = "1.0"
COLUMN_LINEAGE_PLAN_VERSION = "1.0"
LINEAGE_BINDING_VERSION = "1.0"

_MAX_URN_CHARS = 1024
_MAX_COLUMN_CHARS = 256
_MAX_HOPS = 1
_MAX_RESULTS = 30
_OFFSET = 0
_MIN_CHAIN_ID = 4
_MAX_CHAIN_ID = 15

_KNOWN_PROPERTIES = frozenset({"urn", "column", "upstream", "max_hops", "max_results", "offset"})


class DataHubLineageContractError(ValueError):
    """Safe, non-retryable lineage contract or planning error."""

    def __init__(self, code: str, message: str = "DataHub lineage contract is invalid.") -> None:
        self.code = code
        self.message = message
        self.retryable = False
        super().__init__(message)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _error(code: str) -> DataHubLineageContractError:
    return DataHubLineageContractError(code)


class DataHubGetLineageSchemaContract(_Strict):
    input_schema_fingerprint: str
    urn_supported: bool
    column_supported: bool
    downstream_false_supported: bool
    max_hops_one_supported: bool
    max_results_30_supported: bool
    offset_zero_supported: bool
    contract_version: str = LINEAGE_CONTRACT_VERSION

    @field_validator("input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        return _hex64(value)

    @model_validator(mode="after")
    def invariants(self) -> "DataHubGetLineageSchemaContract":
        required = (self.urn_supported and self.column_supported and self.downstream_false_supported and self.max_hops_one_supported and self.max_results_30_supported and self.offset_zero_supported)
        if not required or self.contract_version != LINEAGE_CONTRACT_VERSION:
            raise ValueError("invalid get_lineage schema contract")
        return self


class DataHubLineageToolDiscoveryBundle(_Strict):
    entity_schema_discovery: DataHubEntitySchemaToolDiscoveryBundle
    get_lineage_contract: DataHubGetLineageSchemaContract
    bundle_version: str = LINEAGE_BUNDLE_VERSION

    @model_validator(mode="after")
    def invariants(self) -> "DataHubLineageToolDiscoveryBundle":
        if self.bundle_version != LINEAGE_BUNDLE_VERSION:
            raise ValueError("invalid lineage discovery bundle version")
        capability = self._lineage_capability_fp()
        if capability is None or capability != self.get_lineage_contract.input_schema_fingerprint:
            raise ValueError("get_lineage fingerprint mismatch")
        return self

    def _lineage_capability_fp(self) -> str | None:
        for tool in self.entity_schema_discovery.read_discovery.catalog.tools:
            if tool.name.value == "get_lineage":
                return tool.input_schema_fingerprint
        return None


class DataHubLineageContext(_Strict):
    subject: DataHubAssetResolutionSubject
    resolution: DataHubAssetCandidateResolution
    search_execution: DataHubSearchExecutionResult
    entity_execution: DataHubEntityMetadataExecutionResult
    schema_execution: DataHubSchemaFieldsExecutionResult
    entity_schema_context: DataHubEntitySchemaContext
    discovery: DataHubLineageToolDiscoveryBundle
    dataset_urn: str
    affected_column: str
    dataset_lineage_request_id: StrictInt = Field(gt=0)
    column_lineage_request_id: StrictInt = Field(gt=0)
    post_lineage_next_request_id: StrictInt = Field(gt=0)
    binding_version: str = LINEAGE_BINDING_VERSION

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str:
        return _safe_urn(value)

    @field_validator("affected_column")
    @classmethod
    def column_ok(cls, value: str) -> str:
        return _identity_text(value, name="affected_column", max_len=_MAX_COLUMN_CHARS)

    @model_validator(mode="after")
    def invariants(self) -> "DataHubLineageContext":
        if self.binding_version != LINEAGE_BINDING_VERSION:
            raise ValueError("invalid lineage binding version")
        if self.resolution.status is not DataHubAssetResolutionStatus.RESOLVED or self.dataset_urn != self.resolution.selected_dataset_urn:
            raise ValueError("invalid lineage binding dataset")
        next_id = self.schema_execution.next_request_id
        if isinstance(next_id, bool) or not isinstance(next_id, int) or not _MIN_CHAIN_ID <= next_id <= _MAX_CHAIN_ID:
            raise ValueError("invalid lineage request id chain")
        if self.dataset_lineage_request_id != next_id or self.column_lineage_request_id != next_id + 1 or self.post_lineage_next_request_id != next_id + 2:
            raise ValueError("invalid lineage request id chain")
        return self


class DataHubDatasetLineageArgumentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    dataset_urn: str
    arguments: Mapping[str, Any]
    input_schema_fingerprint: str
    plan_version: str = DATASET_LINEAGE_PLAN_VERSION

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str:
        return _safe_urn(value)

    @field_validator("input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        return _hex64(value)

    @model_validator(mode="after")
    def freeze(self) -> "DataHubDatasetLineageArgumentPlan":
        expected = {"urn": self.dataset_urn, "upstream": False, "max_hops": _MAX_HOPS, "max_results": _MAX_RESULTS, "offset": _OFFSET}
        if dict(self.arguments) != expected:
            raise ValueError("invalid dataset lineage argument plan")
        object.__setattr__(self, "arguments", MappingProxyType(dict(self.arguments)))
        if self.plan_version != DATASET_LINEAGE_PLAN_VERSION:
            raise ValueError("invalid plan version")
        return self


class DataHubColumnLineageArgumentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    dataset_urn: str
    affected_column: str
    arguments: Mapping[str, Any]
    input_schema_fingerprint: str
    plan_version: str = COLUMN_LINEAGE_PLAN_VERSION

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str:
        return _safe_urn(value)

    @field_validator("affected_column")
    @classmethod
    def column_ok(cls, value: str) -> str:
        return _identity_text(value, name="affected_column", max_len=_MAX_COLUMN_CHARS)

    @field_validator("input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        return _hex64(value)

    @model_validator(mode="after")
    def freeze(self) -> "DataHubColumnLineageArgumentPlan":
        expected = {"urn": self.dataset_urn, "column": self.affected_column, "upstream": False, "max_hops": _MAX_HOPS, "max_results": _MAX_RESULTS, "offset": _OFFSET}
        if dict(self.arguments) != expected:
            raise ValueError("invalid column lineage argument plan")
        object.__setattr__(self, "arguments", MappingProxyType(dict(self.arguments)))
        if self.plan_version != COLUMN_LINEAGE_PLAN_VERSION:
            raise ValueError("invalid plan version")
        return self


def _boolean_permits(node: Any, value: bool) -> bool:
    if not _types(node, "boolean"):
        return False
    member = _type_member(node, "boolean")
    if member is None:
        return False
    if "enum" in member and (not isinstance(member["enum"], list) or value not in member["enum"]):
        return False
    if "const" in member and member["const"] != value:
        return False
    return True


def _cross_check_fp(schema: dict[str, Any], catalog_fingerprint: str) -> str:
    try:
        actual = _schema_fingerprint_hex(schema)
    except (DataHubToolDiscoveryError, ValueError):
        raise _error("lineage_schema_incompatible") from None
    if actual != catalog_fingerprint:
        raise _error("lineage_schema_fingerprint_mismatch")
    return catalog_fingerprint


def attest_datahub_get_lineage_schema(*, schema: dict[str, Any], catalog_fingerprint: str) -> DataHubGetLineageSchemaContract:
    """Attest an ephemeral get_lineage input schema against the bounded contract.

    Recognizes only ``urn``, ``column``, ``upstream``, ``max_hops``,
    ``max_results``, and ``offset``. Direct downstream lineage is expressed by
    exact server-owned values (``upstream=false``, ``max_hops=1``,
    ``max_results=30``, ``offset=0``) and each must be proven compatible.
    """
    required = _schema_required(schema)
    if required is None or "urn" not in required:
        raise _error("lineage_schema_incompatible")
    if any(item not in _KNOWN_PROPERTIES for item in required):
        raise _error("unsupported_required_lineage_argument")
    if "column" in required:
        raise _error("lineage_schema_incompatible")
    properties = schema.get("properties", {})
    if not _string_accepts_length(properties.get("urn"), min_len=_MAX_URN_CHARS):
        raise _error("lineage_schema_incompatible")
    if not _string_accepts_length(properties.get("column"), min_len=_MAX_COLUMN_CHARS):
        raise _error("lineage_schema_incompatible")
    if not _boolean_permits(properties.get("upstream"), False):
        raise _error("lineage_schema_incompatible")
    if not _integer_permits(properties.get("max_hops"), _MAX_HOPS):
        raise _error("lineage_schema_incompatible")
    if not _integer_permits(properties.get("max_results"), _MAX_RESULTS):
        raise _error("lineage_schema_incompatible")
    if not _integer_permits(properties.get("offset"), _OFFSET):
        raise _error("lineage_schema_incompatible")
    fingerprint = _cross_check_fp(schema, catalog_fingerprint)
    return DataHubGetLineageSchemaContract(input_schema_fingerprint=fingerprint, urn_supported=True, column_supported=True, downstream_false_supported=True, max_hops_one_supported=True, max_results_30_supported=True, offset_zero_supported=True)


def discover_datahub_lineage_tool_bundle(*, config: DataHubMCPConfig, session: DataHubMCPSession, transport: DataHubMCPTransport) -> DataHubLineageToolDiscoveryBundle:
    """Derive search, entity, schema, and get_lineage contracts from one tools/list sequence."""
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
        raise _error("lineage_schema_incompatible")
    get_entities_contract = _entity_schema_attest(schema=get_entities_schema, catalog_fingerprint=get_entities_capability.input_schema_fingerprint)
    list_schema_fields_schema = schemas.get("list_schema_fields")
    list_schema_fields_capability = next((tool for tool in catalog.tools if tool.name is DataHubReadToolName.LIST_SCHEMA_FIELDS), None)
    if list_schema_fields_schema is None or list_schema_fields_capability is None:
        raise _error("lineage_schema_incompatible")
    list_schema_fields_contract = _schema_fields_attest(schema=list_schema_fields_schema, catalog_fingerprint=list_schema_fields_capability.input_schema_fingerprint)
    entity_schema_discovery = DataHubEntitySchemaToolDiscoveryBundle(read_discovery=read_discovery, get_entities_contract=get_entities_contract, list_schema_fields_contract=list_schema_fields_contract)
    get_lineage_schema = schemas.get("get_lineage")
    get_lineage_capability = next((tool for tool in catalog.tools if tool.name is DataHubReadToolName.GET_LINEAGE), None)
    if get_lineage_schema is None or get_lineage_capability is None:
        raise _error("lineage_schema_missing")
    get_lineage_contract = attest_datahub_get_lineage_schema(schema=get_lineage_schema, catalog_fingerprint=get_lineage_capability.input_schema_fingerprint)
    return DataHubLineageToolDiscoveryBundle(entity_schema_discovery=entity_schema_discovery, get_lineage_contract=get_lineage_contract)


def _lineage_catalog_fp(discovery: DataHubLineageToolDiscoveryBundle) -> str | None:
    for tool in discovery.entity_schema_discovery.read_discovery.catalog.tools:
        if tool.name.value == "get_lineage":
            return tool.input_schema_fingerprint
    return None


def bind_datahub_lineage_context(*, subject: DataHubAssetResolutionSubject, resolution: DataHubAssetCandidateResolution, search_execution: DataHubSearchExecutionResult, entity_execution: DataHubEntityMetadataExecutionResult, schema_execution: DataHubSchemaFieldsExecutionResult, entity_schema_context: DataHubEntitySchemaContext, discovery: DataHubLineageToolDiscoveryBundle) -> DataHubLineageContext:
    """Bind the completed B3/C2/C3 identity chain to the lineage discovery.

    Schema observation state does not gate lineage planning: ``not_observed``
    means only that the exact fieldPath was not observed in the bounded schema
    response, so column lineage planning may still use the affected column.
    """
    if not isinstance(subject, DataHubAssetResolutionSubject) or not isinstance(resolution, DataHubAssetCandidateResolution):
        raise _error("invalid_lineage_binding")
    if not isinstance(search_execution, DataHubSearchExecutionResult) or not isinstance(entity_execution, DataHubEntityMetadataExecutionResult) or not isinstance(schema_execution, DataHubSchemaFieldsExecutionResult):
        raise _error("invalid_lineage_binding")
    if not isinstance(entity_schema_context, DataHubEntitySchemaContext) or not isinstance(discovery, DataHubLineageToolDiscoveryBundle):
        raise _error("invalid_lineage_binding")
    if subject.affected_column != entity_schema_context.affected_column:
        raise _error("invalid_lineage_binding")
    if resolution.status is not DataHubAssetResolutionStatus.RESOLVED or resolution.selected_dataset_urn is None:
        raise _error("invalid_lineage_binding")
    dataset_urn = resolution.selected_dataset_urn
    matches = [record for record in search_execution.records if record.dataset_urn == dataset_urn]
    if len(matches) != 1:
        raise _error("invalid_lineage_binding")
    if entity_execution.dataset_urn != dataset_urn or schema_execution.dataset_urn != dataset_urn:
        raise _error("invalid_lineage_binding")
    parts = _dataset_urn_parts(dataset_urn)
    if parts is None or _norm(parts[0]) != _norm(subject.platform):
        raise _error("invalid_lineage_binding")
    if entity_execution.next_request_id != entity_schema_context.list_schema_fields_request_id:
        raise _error("lineage_request_id_invalid")
    if schema_execution.request_id != entity_schema_context.list_schema_fields_request_id:
        raise _error("lineage_request_id_invalid")
    if discovery.entity_schema_discovery.get_entities_contract.input_schema_fingerprint != entity_schema_context.discovery.get_entities_contract.input_schema_fingerprint:
        raise _error("invalid_lineage_binding")
    if _lineage_catalog_fp(discovery) != discovery.get_lineage_contract.input_schema_fingerprint:
        raise _error("lineage_schema_fingerprint_mismatch")
    next_id = schema_execution.next_request_id
    if isinstance(next_id, bool) or not isinstance(next_id, int) or not _MIN_CHAIN_ID <= next_id <= _MAX_CHAIN_ID:
        raise _error("lineage_request_id_invalid")
    try:
        return DataHubLineageContext(
            subject=subject,
            resolution=resolution,
            search_execution=search_execution,
            entity_execution=entity_execution,
            schema_execution=schema_execution,
            entity_schema_context=entity_schema_context,
            discovery=discovery,
            dataset_urn=dataset_urn,
            affected_column=entity_schema_context.affected_column,
            dataset_lineage_request_id=next_id,
            column_lineage_request_id=next_id + 1,
            post_lineage_next_request_id=next_id + 2,
        )
    except ValueError:
        raise _error("invalid_lineage_binding") from None


def build_datahub_dataset_lineage_argument_plan(*, context: DataHubLineageContext, contract: DataHubGetLineageSchemaContract) -> DataHubDatasetLineageArgumentPlan:
    if not isinstance(context, DataHubLineageContext) or not isinstance(contract, DataHubGetLineageSchemaContract):
        raise _error("invalid_dataset_lineage_argument_plan")
    if contract.input_schema_fingerprint != context.discovery.get_lineage_contract.input_schema_fingerprint:
        raise _error("lineage_schema_fingerprint_mismatch")
    return DataHubDatasetLineageArgumentPlan(
        dataset_urn=context.dataset_urn,
        arguments={"urn": context.dataset_urn, "upstream": False, "max_hops": _MAX_HOPS, "max_results": _MAX_RESULTS, "offset": _OFFSET},
        input_schema_fingerprint=contract.input_schema_fingerprint,
    )


def build_datahub_column_lineage_argument_plan(*, context: DataHubLineageContext, contract: DataHubGetLineageSchemaContract) -> DataHubColumnLineageArgumentPlan:
    if not isinstance(context, DataHubLineageContext) or not isinstance(contract, DataHubGetLineageSchemaContract):
        raise _error("invalid_column_lineage_argument_plan")
    if contract.input_schema_fingerprint != context.discovery.get_lineage_contract.input_schema_fingerprint:
        raise _error("lineage_schema_fingerprint_mismatch")
    return DataHubColumnLineageArgumentPlan(
        dataset_urn=context.dataset_urn,
        affected_column=context.affected_column,
        arguments={"urn": context.dataset_urn, "column": context.affected_column, "upstream": False, "max_hops": _MAX_HOPS, "max_results": _MAX_RESULTS, "offset": _OFFSET},
        input_schema_fingerprint=contract.input_schema_fingerprint,
    )


def build_datahub_dataset_lineage_tools_call_request(*, context: DataHubLineageContext, contract: DataHubGetLineageSchemaContract, argument_plan: DataHubDatasetLineageArgumentPlan) -> MCPRequest:
    if not isinstance(context, DataHubLineageContext) or not isinstance(contract, DataHubGetLineageSchemaContract) or not isinstance(argument_plan, DataHubDatasetLineageArgumentPlan):
        raise _error("invalid_dataset_lineage_argument_plan")
    if contract.input_schema_fingerprint != context.discovery.get_lineage_contract.input_schema_fingerprint:
        raise _error("lineage_schema_fingerprint_mismatch")
    if argument_plan.input_schema_fingerprint != contract.input_schema_fingerprint:
        raise _error("lineage_schema_fingerprint_mismatch")
    if argument_plan.dataset_urn != context.dataset_urn:
        raise _error("invalid_lineage_binding")
    return MCPRequest(id=context.dataset_lineage_request_id, method="tools/call", params={"name": "get_lineage", "arguments": dict(argument_plan.arguments)})


def build_datahub_column_lineage_tools_call_request(*, context: DataHubLineageContext, contract: DataHubGetLineageSchemaContract, argument_plan: DataHubColumnLineageArgumentPlan) -> MCPRequest:
    if not isinstance(context, DataHubLineageContext) or not isinstance(contract, DataHubGetLineageSchemaContract) or not isinstance(argument_plan, DataHubColumnLineageArgumentPlan):
        raise _error("invalid_column_lineage_argument_plan")
    if contract.input_schema_fingerprint != context.discovery.get_lineage_contract.input_schema_fingerprint:
        raise _error("lineage_schema_fingerprint_mismatch")
    if argument_plan.input_schema_fingerprint != contract.input_schema_fingerprint:
        raise _error("lineage_schema_fingerprint_mismatch")
    if argument_plan.dataset_urn != context.dataset_urn:
        raise _error("invalid_lineage_binding")
    if argument_plan.affected_column != context.affected_column:
        raise _error("invalid_column_lineage_argument_plan")
    if context.column_lineage_request_id != context.dataset_lineage_request_id + 1:
        raise _error("lineage_request_id_invalid")
    return MCPRequest(id=context.column_lineage_request_id, method="tools/call", params={"name": "get_lineage", "arguments": dict(argument_plan.arguments)})


def _serialize_request(request: MCPRequest) -> bytes:
    try:
        body = serialize_jsonrpc(request)
    except DataHubMCPProtocolError:
        raise _error("lineage_request_invalid") from None
    if len(body) > DATAHUB_MCP_MAX_REQUEST_BYTES:
        raise _error("lineage_request_too_large")
    return body


def serialize_datahub_dataset_lineage_tools_call_request(*, context: DataHubLineageContext, contract: DataHubGetLineageSchemaContract, argument_plan: DataHubDatasetLineageArgumentPlan) -> bytes:
    request = build_datahub_dataset_lineage_tools_call_request(context=context, contract=contract, argument_plan=argument_plan)
    return _serialize_request(request)


def serialize_datahub_column_lineage_tools_call_request(*, context: DataHubLineageContext, contract: DataHubGetLineageSchemaContract, argument_plan: DataHubColumnLineageArgumentPlan) -> bytes:
    request = build_datahub_column_lineage_tools_call_request(context=context, contract=contract, argument_plan=argument_plan)
    return _serialize_request(request)


__all__ = [
    "COLUMN_LINEAGE_PLAN_VERSION",
    "DATASET_LINEAGE_PLAN_VERSION",
    "LINEAGE_BINDING_VERSION",
    "LINEAGE_BUNDLE_VERSION",
    "LINEAGE_CONTRACT_VERSION",
    "DataHubColumnLineageArgumentPlan",
    "DataHubDatasetLineageArgumentPlan",
    "DataHubGetLineageSchemaContract",
    "DataHubLineageContractError",
    "DataHubLineageContext",
    "DataHubLineageToolDiscoveryBundle",
    "attest_datahub_get_lineage_schema",
    "bind_datahub_lineage_context",
    "build_datahub_column_lineage_argument_plan",
    "build_datahub_column_lineage_tools_call_request",
    "build_datahub_dataset_lineage_argument_plan",
    "build_datahub_dataset_lineage_tools_call_request",
    "discover_datahub_lineage_tool_bundle",
    "serialize_datahub_column_lineage_tools_call_request",
    "serialize_datahub_dataset_lineage_tools_call_request",
]
