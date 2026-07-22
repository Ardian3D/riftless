"""F8.3B1 search-schema attestation and call-plan contracts.

This module only builds immutable internal objects and JSON-RPC request bytes;
it never sends ``tools/call`` or parses a tool result.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .config import DATAHUB_MCP_MAX_REQUEST_BYTES, DATAHUB_MCP_PROTOCOL_VERSION, DataHubMCPConfig
from .initialization import DataHubMCPSession
from .mcp_protocol import MCPRequest, serialize_jsonrpc
from .tool_discovery import (
    CATALOG_VERSION,
    DataHubReadToolCatalog,
    DataHubReadToolName,
    DataHubToolDiscoveryError,
    _discover_tool_details,
)
from .transport import DataHubMCPTransport

CONTRACT_VERSION = "1.0"
PLAN_VERSION = "1.0"
_SAFE_PROPERTIES = frozenset({"query", "filter", "num_results", "offset", "search_strategy", "sort_by", "sort_order"})
_SQLISH = re.compile(r"^(select|insert|update|delete|drop|alter|create|with)\b", re.IGNORECASE)


class DataHubSearchContractError(ValueError):
    """Safe, non-retryable search-contract error."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        self.retryable = False
        super().__init__(message)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DataHubSearchSchemaContract(_Strict):
    input_schema_fingerprint: str
    query_supported: bool
    supports_dataset_filter: bool
    supports_result_limit: bool
    supports_offset: bool
    supports_keyword_strategy: bool
    supports_sorting: bool
    contract_version: str = CONTRACT_VERSION

    @field_validator("input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        if not re.fullmatch(r"[0-9a-f]{64}", value): raise ValueError("invalid search schema fingerprint")
        return value

    @model_validator(mode="after")
    def invariants(self) -> "DataHubSearchSchemaContract":
        if not self.query_supported or self.contract_version != CONTRACT_VERSION: raise ValueError("invalid search schema contract")
        return self


class DataHubReadToolDiscoveryBundle(_Strict):
    catalog: DataHubReadToolCatalog
    search_contract: DataHubSearchSchemaContract
    next_request_id: int = Field(ge=3, le=12)
    bundle_version: str = CONTRACT_VERSION

    @model_validator(mode="after")
    def bundle_invariants(self) -> "DataHubReadToolDiscoveryBundle":
        search = next((tool for tool in self.catalog.tools if tool.name == DataHubReadToolName.SEARCH), None)
        if search is None or search.input_schema_fingerprint != self.search_contract.input_schema_fingerprint: raise ValueError("search fingerprint mismatch")
        if self.bundle_version != CONTRACT_VERSION: raise ValueError("invalid discovery bundle version")
        return self


class DataHubSearchArgumentPlan(_Strict):
    query: str
    arguments: Mapping[str, Any]
    input_schema_fingerprint: str
    plan_version: str = PLAN_VERSION

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    @field_validator("query")
    @classmethod
    def query_ok(cls, value: str) -> str:
        return _validate_query(value)

    @field_validator("input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        if not re.fullmatch(r"[0-9a-f]{64}", value): raise ValueError("invalid plan fingerprint")
        return value

    @model_validator(mode="after")
    def freeze_arguments(self) -> "DataHubSearchArgumentPlan":
        expected = {"query", "filter", "num_results", "offset", "search_strategy"}
        if set(self.arguments) - expected or self.arguments.get("query") != self.query: raise ValueError("invalid search argument plan")
        object.__setattr__(self, "arguments", MappingProxyType(dict(self.arguments)))
        if self.plan_version != PLAN_VERSION: raise ValueError("invalid plan version")
        return self


def _fail(code: str) -> DataHubSearchContractError:
    return DataHubSearchContractError(code, "DataHub search contract is invalid.")


def _types(node: Any, expected: str) -> bool:
    if not isinstance(node, dict): return False
    if "$ref" in node or any(key in node for key in ("if", "then", "else", "dynamicRef", "unevaluatedProperties", "contentSchema")): return False
    if isinstance(node.get("type"), str): return node["type"] == expected
    if isinstance(node.get("type"), list): return set(node["type"]) <= {expected, "null"} and expected in node["type"]
    for key in ("anyOf", "oneOf"):
        if key in node and isinstance(node[key], list) and len(node[key]) in {1, 2}:
            return all(_types(member, expected) or (isinstance(member, dict) and member.get("type") == "null") for member in node[key]) and any(_types(member, expected) for member in node[key])
    return False


def _permits_integer(node: dict[str, Any], value: int) -> bool:
    if not _types(node, "integer"): return False
    if "minimum" in node and (not isinstance(node["minimum"], (int, float)) or node["minimum"] > value): return False
    if "maximum" in node and (not isinstance(node["maximum"], (int, float)) or node["maximum"] < value): return False
    if "enum" in node and (not isinstance(node["enum"], list) or value not in node["enum"]): return False
    if "const" in node and node["const"] != value: return False
    return True


def _permits_string(node: dict[str, Any], value: str | None = None, *, query: bool = False) -> bool:
    if not _types(node, "string"): return False
    if "pattern" in node: return False
    if query:
        if "maxLength" in node and (not isinstance(node["maxLength"], int) or node["maxLength"] < 512): return False
        if "minLength" in node and (not isinstance(node["minLength"], int) or node["minLength"] > 4): return False
    if value is not None:
        if "enum" in node and (not isinstance(node["enum"], list) or value not in node["enum"]): return False
        if "const" in node and node["const"] != value: return False
    return True


def _validate_query(query: str) -> str:
    if not isinstance(query, str): raise DataHubSearchContractError("invalid_search_query", "DataHub search query is invalid.")
    if any(ord(char) < 32 or ord(char) == 127 for char in query): raise DataHubSearchContractError("invalid_search_query", "DataHub search query is invalid.")
    value = query.strip()
    if not 4 <= len(value) <= 512 or not value.startswith("/q ") or not value[3:].strip() or "\x00" in value or "```" in value or _SQLISH.match(value[3:].lstrip()):
        raise DataHubSearchContractError("invalid_search_query", "DataHub search query is invalid.")
    return value


def _make_search_contract(schema: dict[str, Any], fingerprint: str) -> DataHubSearchSchemaContract:
    properties = schema.get("properties")
    required = schema.get("required", [])
    if not isinstance(properties, dict) or not isinstance(required, list): raise _fail("search_schema_incompatible")
    if "query" not in properties or not _permits_string(properties["query"], query=True): raise _fail("search_schema_incompatible")
    if any(item not in _SAFE_PROPERTIES for item in required): raise _fail("unsupported_required_search_argument")
    if "query" not in required and required: raise _fail("search_schema_incompatible")
    filter_ok = "filter" in properties and _permits_string(properties["filter"], "entity_type = dataset")
    limit_ok = "num_results" in properties and _permits_integer(properties["num_results"], 10)
    offset_ok = "offset" in properties and _permits_integer(properties["offset"], 0)
    strategy_ok = "search_strategy" in properties and _permits_string(properties["search_strategy"], "keyword")
    sorting = any(name in properties and _types(properties[name], "string") for name in ("sort_by", "sort_order"))
    return DataHubSearchSchemaContract(input_schema_fingerprint=fingerprint, query_supported=True, supports_dataset_filter=filter_ok, supports_result_limit=limit_ok, supports_offset=offset_ok, supports_keyword_strategy=strategy_ok, supports_sorting=sorting)


def discover_datahub_read_tool_bundle(*, config: DataHubMCPConfig, session: DataHubMCPSession, transport: DataHubMCPTransport) -> DataHubReadToolDiscoveryBundle:
    catalog, schemas, next_request_id = _discover_tool_details(config=config, session=session, transport=transport)
    schema = schemas.get("search")
    if schema is None: raise _fail("search_schema_missing")
    search = next(tool for tool in catalog.tools if tool.name == DataHubReadToolName.SEARCH)
    contract = _make_search_contract(schema, search.input_schema_fingerprint)
    return DataHubReadToolDiscoveryBundle(catalog=catalog, search_contract=contract, next_request_id=next_request_id)


def build_datahub_search_argument_plan(*, search_contract: DataHubSearchSchemaContract, query: str) -> DataHubSearchArgumentPlan:
    if not isinstance(search_contract, DataHubSearchSchemaContract): raise _fail("invalid_search_argument_plan")
    value = _validate_query(query)
    args: dict[str, Any] = {"query": value}
    if search_contract.supports_dataset_filter: args["filter"] = "entity_type = dataset"
    if search_contract.supports_result_limit: args["num_results"] = 10
    if search_contract.supports_offset: args["offset"] = 0
    if search_contract.supports_keyword_strategy: args["search_strategy"] = "keyword"
    return DataHubSearchArgumentPlan(query=value, arguments=args, input_schema_fingerprint=search_contract.input_schema_fingerprint)


def build_datahub_search_tools_call_request(*, discovery: DataHubReadToolDiscoveryBundle, argument_plan: DataHubSearchArgumentPlan) -> MCPRequest:
    if not isinstance(discovery, DataHubReadToolDiscoveryBundle) or not isinstance(argument_plan, DataHubSearchArgumentPlan): raise _fail("invalid_search_argument_plan")
    if argument_plan.input_schema_fingerprint != discovery.search_contract.input_schema_fingerprint: raise _fail("search_schema_fingerprint_mismatch")
    return MCPRequest(id=discovery.next_request_id, method="tools/call", params={"name": "search", "arguments": dict(argument_plan.arguments)})


def serialize_datahub_search_tools_call_request(*, discovery: DataHubReadToolDiscoveryBundle, argument_plan: DataHubSearchArgumentPlan) -> bytes:
    try: body = serialize_jsonrpc(build_datahub_search_tools_call_request(discovery=discovery, argument_plan=argument_plan))
    except DataHubSearchContractError: raise
    if len(body) > DATAHUB_MCP_MAX_REQUEST_BYTES: raise DataHubSearchContractError("search_request_too_large", "DataHub search request is too large.")
    return body
