"""Bounded, read-only DataHub MCP tools/list discovery for F8.3A."""

from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.utils.fingerprint import canonical_json_bytes

from .config import DATAHUB_MCP_PROTOCOL_VERSION, DataHubMCPConfig
from .initialization import DataHubMCPSession
from .mcp_protocol import DataHubMCPProtocolError, MCPRequest, parse_http_response, serialize_jsonrpc
from .transport import DataHubMCPTransport

MAX_DISCOVERY_PAGES = 10
MAX_PROVIDER_TOOLS = 256
MAX_PAGE_TOOLS = 128
MAX_CURSOR_LENGTH = 512
MAX_SCHEMA_BYTES = 32_768
CATALOG_VERSION = "1.0"
_TOOL_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
_MUTATION_DENYLIST = frozenset({
    "add_tags", "remove_tags", "add_terms", "remove_terms", "add_owners", "remove_owners",
    "set_domains", "remove_domains", "update_description", "add_structured_properties",
    "remove_structured_properties", "set_lifecycle_stage", "save_document", "create_glossary_term",
    "create_glossary_term_version", "add_related_terms", "propose_create_glossary_term",
    "propose_lifecycle_stage", "accept_or_reject_proposals",
})


class DataHubReadToolName(str, Enum):
    SEARCH = "search"
    GET_ENTITIES = "get_entities"
    LIST_SCHEMA_FIELDS = "list_schema_fields"
    GET_LINEAGE = "get_lineage"


READ_TOOL_ORDER: tuple[DataHubReadToolName, ...] = (
    DataHubReadToolName.SEARCH, DataHubReadToolName.GET_ENTITIES,
    DataHubReadToolName.LIST_SCHEMA_FIELDS, DataHubReadToolName.GET_LINEAGE,
)


class DataHubToolDiscoveryError(ValueError):
    """Safe discovery error without provider metadata or secrets."""

    _CONTRACT_CODES = frozenset({
        "invalid_tools_list_result", "invalid_tool_definition", "duplicate_tool_name",
        "tool_catalog_too_large", "tool_page_too_large", "pagination_limit_exceeded",
        "invalid_cursor", "pagination_cursor_loop", "required_tool_missing",
        "required_tool_unsafe", "required_tool_requires_tasks", "invalid_tool_schema",
        "session_config_mismatch",
    })

    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        self.code = code
        self.message = message
        self.retryable = False if code in self._CONTRACT_CODES else retryable
        super().__init__(message)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DataHubReadToolCapability(_Strict):
    name: DataHubReadToolName
    input_schema_fingerprint: str
    annotation_verified: bool
    read_only_hint: bool | None
    idempotent_hint: bool | None
    open_world_hint: bool | None
    task_support: str = "unspecified"

    @field_validator("input_schema_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        if not re.fullmatch(r"[0-9a-f]{64}", value): raise ValueError("invalid input schema fingerprint")
        return value

    @field_validator("task_support")
    @classmethod
    def task_ok(cls, value: str) -> str:
        if value not in {"forbidden", "optional", "unspecified"}: raise ValueError("invalid task support")
        return value


class DataHubReadToolCatalog(_Strict):
    tools: tuple[DataHubReadToolCapability, ...]
    all_required_tools_available: bool
    annotation_verification_complete: bool
    catalog_version: str = CATALOG_VERSION

    @model_validator(mode="after")
    def catalog_invariants(self) -> "DataHubReadToolCatalog":
        if tuple(tool.name for tool in self.tools) != READ_TOOL_ORDER: raise ValueError("catalog order is invalid")
        if not self.all_required_tools_available or self.catalog_version != CATALOG_VERSION: raise ValueError("catalog constants are invalid")
        if self.annotation_verification_complete != all(tool.annotation_verified for tool in self.tools): raise ValueError("annotation state is not derived")
        return self


def mutation_tool_denylist() -> frozenset[str]:
    return _MUTATION_DENYLIST


def build_tools_list_request(*, request_id: int, cursor: str | None = None) -> MCPRequest:
    if isinstance(request_id, bool) or not isinstance(request_id, int) or not 2 <= request_id <= MAX_DISCOVERY_PAGES + 1:
        raise DataHubToolDiscoveryError("invalid_tools_list_result", "DataHub MCP discovery request is invalid.")
    if cursor is not None: _validate_cursor(cursor)
    return MCPRequest(id=request_id, method="tools/list", params={} if cursor is None else {"cursor": cursor})


def _validate_cursor(cursor: str) -> str:
    if not isinstance(cursor, str) or not 1 <= len(cursor) <= MAX_CURSOR_LENGTH or not cursor.strip() or any(ord(c) < 32 or ord(c) == 127 for c in cursor):
        raise DataHubToolDiscoveryError("invalid_cursor", "DataHub MCP pagination cursor is invalid.")
    return cursor


def _schema_fingerprint(schema: dict[str, Any]) -> str:
    try:
        json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(canonical_json_bytes(schema)).hexdigest()
    except (TypeError, ValueError, OverflowError):
        raise DataHubToolDiscoveryError("invalid_tool_schema", "DataHub MCP input schema is invalid.") from None


def _validate_schema(schema: Any) -> dict[str, Any]:
    if not isinstance(schema, dict): raise DataHubToolDiscoveryError("invalid_tool_schema", "DataHub MCP input schema is invalid.")
    try:
        size = len(json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))
    except (TypeError, ValueError, OverflowError):
        raise DataHubToolDiscoveryError("invalid_tool_schema", "DataHub MCP input schema is invalid.") from None
    if size > MAX_SCHEMA_BYTES or ("type" in schema and schema["type"] != "object"):
        raise DataHubToolDiscoveryError("invalid_tool_schema", "DataHub MCP input schema is invalid.")
    properties = schema.get("properties")
    if properties is not None and not isinstance(properties, dict): raise DataHubToolDiscoveryError("invalid_tool_schema", "DataHub MCP input schema is invalid.")
    required = schema.get("required")
    if required is not None:
        if not isinstance(required, list) or any(not isinstance(item, str) or not item for item in required) or len(set(required)) != len(required): raise DataHubToolDiscoveryError("invalid_tool_schema", "DataHub MCP input schema is invalid.")
        if properties is not None and any(item not in properties for item in required): raise DataHubToolDiscoveryError("invalid_tool_schema", "DataHub MCP input schema is invalid.")
    _schema_fingerprint(schema)
    return schema


def _parse_tool_definition(raw: Any) -> DataHubReadToolCapability | None:
    if not isinstance(raw, dict) or not isinstance(raw.get("name"), str): raise DataHubToolDiscoveryError("invalid_tool_definition", "DataHub MCP tool definition is invalid.")
    name = raw["name"]
    if not _TOOL_NAME.fullmatch(name): raise DataHubToolDiscoveryError("invalid_tool_definition", "DataHub MCP tool definition is invalid.")
    if "inputSchema" not in raw: raise DataHubToolDiscoveryError("invalid_tool_definition", "DataHub MCP tool definition is invalid.")
    schema = _validate_schema(raw["inputSchema"])
    annotations = raw.get("annotations", {})
    if annotations is None: annotations = {}
    if not isinstance(annotations, dict): raise DataHubToolDiscoveryError("invalid_tool_definition", "DataHub MCP tool definition is invalid.")
    hints: dict[str, bool | None] = {}
    for key in ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"):
        if key in annotations and not isinstance(annotations[key], bool): raise DataHubToolDiscoveryError("invalid_tool_definition", "DataHub MCP tool definition is invalid.")
        hints[key] = annotations.get(key)
    execution = raw.get("execution", {})
    if execution is None: execution = {}
    if not isinstance(execution, dict): raise DataHubToolDiscoveryError("invalid_tool_definition", "DataHub MCP tool definition is invalid.")
    task_support = execution.get("taskSupport", "unspecified")
    if task_support not in {"forbidden", "optional", "required", "unspecified"}: raise DataHubToolDiscoveryError("invalid_tool_definition", "DataHub MCP tool definition is invalid.")
    try: enum_name = DataHubReadToolName(name)
    except ValueError: return None
    if hints["readOnlyHint"] is False or hints["destructiveHint"] is True: raise DataHubToolDiscoveryError("required_tool_unsafe", "Required DataHub MCP read capability is unsafe.")
    if task_support == "required": raise DataHubToolDiscoveryError("required_tool_requires_tasks", "Required DataHub MCP capability requires unsupported tasks.")
    return DataHubReadToolCapability(name=enum_name, input_schema_fingerprint=_schema_fingerprint(schema), annotation_verified=hints["readOnlyHint"] is True and hints["destructiveHint"] is not True, read_only_hint=hints["readOnlyHint"], idempotent_hint=hints["idempotentHint"], open_world_hint=hints["openWorldHint"], task_support=task_support)


def discover_datahub_read_tools(*, config: DataHubMCPConfig, session: DataHubMCPSession, transport: DataHubMCPTransport) -> DataHubReadToolCatalog:
    if not isinstance(config, DataHubMCPConfig) or not isinstance(session, DataHubMCPSession) or session.endpoint_url != config.endpoint_url or session.protocol_version != DATAHUB_MCP_PROTOCOL_VERSION or not session.tools_supported:
        raise DataHubToolDiscoveryError("session_config_mismatch", "DataHub MCP session and configuration are incompatible.")
    seen_cursors: set[str] = set(); seen_tools: set[str] = set(); capabilities: dict[DataHubReadToolName, DataHubReadToolCapability] = {}
    cursor: str | None = None; pages = 0; total_tools = 0
    while True:
        if pages >= MAX_DISCOVERY_PAGES: raise DataHubToolDiscoveryError("pagination_limit_exceeded", "DataHub MCP tool discovery failed.")
        request_id = pages + 2
        request = build_tools_list_request(request_id=request_id, cursor=cursor)
        response = transport.post_request(serialize_jsonrpc(request), session_id=session.session_id, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION)
        try: parsed = parse_http_response(response, expected_id=request_id)
        except DataHubMCPProtocolError as exc: raise DataHubToolDiscoveryError(exc.code, "DataHub MCP tool discovery failed.", retryable=exc.retryable) from None
        if parsed.error is not None or parsed.result is None: raise DataHubToolDiscoveryError("invalid_tools_list_result", "DataHub MCP tool discovery failed.")
        result = parsed.result; tools = result.get("tools")
        if not isinstance(tools, list): raise DataHubToolDiscoveryError("invalid_tools_list_result", "DataHub MCP tool discovery failed.")
        if len(tools) > MAX_PAGE_TOOLS: raise DataHubToolDiscoveryError("tool_page_too_large", "DataHub MCP tool discovery failed.")
        total_tools += len(tools)
        if total_tools > MAX_PROVIDER_TOOLS: raise DataHubToolDiscoveryError("tool_catalog_too_large", "DataHub MCP tool discovery failed.")
        for raw in tools:
            capability = _parse_tool_definition(raw)
            if not isinstance(raw, dict) or not isinstance(raw.get("name"), str): raise DataHubToolDiscoveryError("invalid_tool_definition", "DataHub MCP tool definition is invalid.")
            raw_name = raw["name"]
            if raw_name in seen_tools: raise DataHubToolDiscoveryError("duplicate_tool_name", "DataHub MCP tool discovery failed.")
            seen_tools.add(raw_name)
            if capability is not None: capabilities[capability.name] = capability
        if "nextCursor" not in result: break
        next_cursor = result["nextCursor"]
        _validate_cursor(next_cursor)
        if next_cursor in seen_cursors: raise DataHubToolDiscoveryError("pagination_cursor_loop", "DataHub MCP pagination cursor loop detected.")
        seen_cursors.add(next_cursor); cursor = next_cursor; pages += 1
    if set(capabilities) != set(READ_TOOL_ORDER): raise DataHubToolDiscoveryError("required_tool_missing", "Required DataHub MCP read capability is missing.")
    ordered = tuple(capabilities[name] for name in READ_TOOL_ORDER)
    return DataHubReadToolCatalog(tools=ordered, all_required_tools_available=True, annotation_verification_complete=all(tool.annotation_verified for tool in ordered), catalog_version=CATALOG_VERSION)
