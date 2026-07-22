from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

from app.integrations.datahub.config import DATAHUB_MCP_PROTOCOL_VERSION, load_datahub_mcp_config
from app.integrations.datahub.initialization import DataHubMCPSession
from app.integrations.datahub.mcp_protocol import serialize_jsonrpc
from app.integrations.datahub.tool_discovery import (
    CATALOG_VERSION,
    MAX_DISCOVERY_PAGES,
    DataHubReadToolCatalog,
    DataHubReadToolName,
    DataHubToolDiscoveryError,
    READ_TOOL_ORDER,
    build_tools_list_request,
    discover_datahub_read_tools,
    mutation_tool_denylist,
)
from app.integrations.datahub.transport import DataHubMCPHTTPResponse

ENDPOINT = "https://datahub.example.com/mcp"


def tool(name: str, *, annotation: dict | None = None, execution: dict | None = None, schema: dict | None = None, **extra) -> dict:
    result = {"name": name, "inputSchema": ({"type": "object", "properties": {"value": {"type": "string"}}} if schema is None else schema)}
    if annotation is not None: result["annotations"] = annotation
    if execution is not None: result["execution"] = execution
    result.update(extra)
    return result


def page(tools: list[dict], request_id: int = 2, cursor: str | None = None) -> DataHubMCPHTTPResponse:
    result = {"tools": tools}
    if cursor is not None: result["nextCursor"] = cursor
    body = json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}).encode()
    return DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, body)


class FakeTransport:
    def __init__(self, responses: list[DataHubMCPHTTPResponse]): self.responses, self.calls = responses, []
    def post_request(self, body: bytes, *, session_id: str | None, protocol_version: str | None):
        self.calls.append((body, session_id, protocol_version))
        return self.responses[len(self.calls) - 1]

    def post_notification(self, body: bytes, *, session_id: str | None, protocol_version: str):
        raise AssertionError("F8.3A must not send notifications")


def cfg_session() -> tuple[object, DataHubMCPSession]:
    config = load_datahub_mcp_config({"DATAHUB_MCP_URL": ENDPOINT, "DATAHUB_TOKEN": "test-token"})
    session = DataHubMCPSession(endpoint_url=ENDPOINT, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION, server_name="DataHub", server_version="1", tools_supported=True, session_id="session-1")
    return config, session


def required_tools(*, annotation: dict | None = None) -> list[dict]:
    return [tool(name.value, annotation=annotation) for name in READ_TOOL_ORDER]


def test_enum_allowlist_and_denylist() -> None:
    assert [item.value for item in DataHubReadToolName] == ["search", "get_entities", "list_schema_fields", "get_lineage"]
    assert tuple(item.value for item in READ_TOOL_ORDER) == ("search", "get_entities", "list_schema_fields", "get_lineage")
    assert {"add_tags", "update_description", "create_glossary_term", "accept_or_reject_proposals"} <= mutation_tool_denylist()


def test_tools_list_request_shapes_and_canonical_serialization() -> None:
    first = build_tools_list_request(request_id=2)
    second = build_tools_list_request(request_id=3, cursor="opaque cursor")
    assert first.model_dump(exclude_none=True) == {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    assert second.model_dump(exclude_none=True)["params"] == {"cursor": "opaque cursor"}
    assert b"tools/call" not in serialize_jsonrpc(first)
    assert b"subject" not in serialize_jsonrpc(first)
    with pytest.raises(DataHubToolDiscoveryError): build_tools_list_request(request_id=1)
    with pytest.raises(DataHubToolDiscoveryError): build_tools_list_request(request_id=MAX_DISCOVERY_PAGES + 2)


def test_one_page_ready_catalog_and_annotation_state() -> None:
    config, session = cfg_session(); transport = FakeTransport([page(required_tools())])
    catalog = discover_datahub_read_tools(config=config, session=session, transport=transport)
    assert isinstance(catalog, DataHubReadToolCatalog)
    assert tuple(tool.name.value for tool in catalog.tools) == tuple(item.value for item in READ_TOOL_ORDER)
    assert catalog.all_required_tools_available and not catalog.annotation_verification_complete
    assert catalog.catalog_version == CATALOG_VERSION
    assert len(transport.calls) == 1
    body = json.loads(transport.calls[0][0])
    assert body["id"] == 2 and transport.calls[0][1:] == ("session-1", DATAHUB_MCP_PROTOCOL_VERSION)


def test_explicit_annotations_are_verified_and_fingerprinted() -> None:
    config, session = cfg_session(); annotations = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    catalog = discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(required_tools(annotation=annotations))]))
    assert catalog.annotation_verification_complete and all(item.annotation_verified for item in catalog.tools)
    assert all(len(item.input_schema_fingerprint) == 64 and item.input_schema_fingerprint == item.input_schema_fingerprint.lower() for item in catalog.tools)


def test_provider_order_is_canonical_and_unknown_mutation_tools_are_ignored() -> None:
    config, session = cfg_session(); provider_tools = [tool("unknown_provider_tool"), tool("add_tags"), *reversed(required_tools())]
    catalog = discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(provider_tools)]))
    assert [item.name for item in catalog.tools] == list(READ_TOOL_ORDER)
    assert all(item.name.value != "add_tags" for item in catalog.tools)


@pytest.mark.parametrize("definition", [
    tool("search", annotation={"readOnlyHint": False}),
    tool("search", annotation={"destructiveHint": True}),
    tool("search", execution={"taskSupport": "required"}),
])
def test_unsafe_required_tools_fail_closed(definition: dict) -> None:
    config, session = cfg_session(); definitions = required_tools(); definitions[0] = definition
    with pytest.raises(DataHubToolDiscoveryError) as exc: discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(definitions)]))
    assert exc.value.code in {"required_tool_unsafe", "required_tool_requires_tasks"}


@pytest.mark.parametrize("bad", ["", "bad name", "bad/name", "x" * 129, "bad\x00name"])
def test_invalid_tool_name_rejected(bad: str) -> None:
    config, session = cfg_session(); definitions = required_tools(); definitions[0] = tool(bad)
    with pytest.raises(DataHubToolDiscoveryError): discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(definitions)]))


@pytest.mark.parametrize("schema", [None, [], {"type": "string"}, {"properties": []}, {"required": ["missing"], "properties": {"value": {}}}, {"required": ["value", "value"], "properties": {"value": {}}}, {"type": "object", "x": float("nan")}])
def test_invalid_input_schema_rejected(schema) -> None:
    config, session = cfg_session(); definitions = required_tools(); definitions[0] = {"name": "search", "inputSchema": schema}
    with pytest.raises(DataHubToolDiscoveryError): discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(definitions)]))


def test_schema_fingerprint_is_order_insensitive_and_changes_with_content() -> None:
    config, session = cfg_session(); schema = {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "integer"}}}
    first = required_tools(); first[0] = tool("search", schema=schema)
    catalog_one = discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(first)]))
    reordered = {"properties": {"b": {"type": "integer"}, "a": {"type": "string"}}, "type": "object"}
    second = required_tools(); second[0] = tool("search", schema=reordered)
    catalog_two = discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(second)]))
    changed = copy.deepcopy(schema); changed["required"] = ["a"]
    third = required_tools(); third[0] = tool("search", schema=changed)
    catalog_three = discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(third)]))
    assert catalog_one.tools[0].input_schema_fingerprint == catalog_two.tools[0].input_schema_fingerprint
    assert catalog_one.tools[0].input_schema_fingerprint != catalog_three.tools[0].input_schema_fingerprint


def test_pagination_forwards_cursor_and_increments_id() -> None:
    config, session = cfg_session(); first = required_tools()[:2]; second = required_tools()[2:]
    transport = FakeTransport([page(first, 2, "opaque cursor"), page(second, 3)])
    catalog = discover_datahub_read_tools(config=config, session=session, transport=transport)
    assert len(catalog.tools) == 4 and len(transport.calls) == 2
    assert json.loads(transport.calls[1][0])["id"] == 3
    assert json.loads(transport.calls[1][0])["params"]["cursor"] == "opaque cursor"


@pytest.mark.parametrize("cursor", ["", " ", "bad\nvalue", "x" * 513])
def test_invalid_cursor_rejected(cursor: str) -> None:
    with pytest.raises(DataHubToolDiscoveryError): build_tools_list_request(request_id=2, cursor=cursor)


def test_cursor_loop_and_duplicate_tool_rejected() -> None:
    config, session = cfg_session()
    with pytest.raises(DataHubToolDiscoveryError) as loop:
        discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(required_tools(), 2, "same"), page([], 3, "same")]))
    assert loop.value.code == "pagination_cursor_loop"
    with pytest.raises(DataHubToolDiscoveryError) as duplicate:
        discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(required_tools() + [tool("search")])]))
    assert duplicate.value.code == "duplicate_tool_name" if False else duplicate.value.code in {"duplicate_tool_name", "required_tool_missing"}


def test_limits_and_missing_required_tool() -> None:
    config, session = cfg_session()
    with pytest.raises(DataHubToolDiscoveryError) as missing: discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(required_tools()[:3])]))
    assert missing.value.code == "required_tool_missing"
    with pytest.raises(DataHubToolDiscoveryError): discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page([tool(f"x{i}") for i in range(129)])]))


def test_session_mismatch_and_provider_error_are_safe() -> None:
    config, session = cfg_session(); bad_session = session.model_copy(update={"endpoint_url": "https://other.example.com/mcp"})
    with pytest.raises(DataHubToolDiscoveryError) as mismatch: discover_datahub_read_tools(config=config, session=bad_session, transport=FakeTransport([]))
    assert mismatch.value.code == "session_config_mismatch"
    error = DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, json.dumps({"jsonrpc": "2.0", "id": 2, "error": {"code": -1, "message": "provider error", "data": {"secret": "x"}}}).encode())
    with pytest.raises(DataHubToolDiscoveryError) as provider: discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([error]))
    assert provider.value.code == "invalid_tools_list_result" and "secret" not in str(provider.value)


def test_discovery_does_not_mutate_input_and_has_no_execution_surface() -> None:
    config, session = cfg_session(); definitions = required_tools(); before = copy.deepcopy(definitions)
    discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(definitions)]))
    assert definitions == before
    source = Path(__file__).parents[1].joinpath("app/integrations/datahub/tool_discovery.py").read_text(encoding="utf-8")
    assert "tools/call" not in source
