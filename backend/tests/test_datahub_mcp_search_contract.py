from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.integrations.datahub.config import DATAHUB_MCP_PROTOCOL_VERSION, load_datahub_mcp_config
from app.integrations.datahub.initialization import DataHubMCPSession
from app.integrations.datahub.mcp_protocol import serialize_jsonrpc
from app.integrations.datahub.search_contract import (
    DataHubSearchContractError,
    build_datahub_search_argument_plan,
    build_datahub_search_tools_call_request,
    discover_datahub_read_tool_bundle,
    serialize_datahub_search_tools_call_request,
)
from app.integrations.datahub.tool_discovery import DataHubToolDiscoveryError, READ_TOOL_ORDER, discover_datahub_read_tools
from app.integrations.datahub.transport import DataHubMCPHTTPResponse

ENDPOINT = "https://datahub.example.com/mcp"


class FakeTransport:
    def __init__(self, responses: list[DataHubMCPHTTPResponse]):
        self.responses = responses
        self.calls: list[tuple[bytes, str | None, str | None]] = []

    def post_request(self, body: bytes, *, session_id: str | None, protocol_version: str | None):
        self.calls.append((body, session_id, protocol_version))
        return self.responses[len(self.calls) - 1]

    def post_notification(self, body: bytes, *, session_id: str | None, protocol_version: str):
        raise AssertionError("search contract must not send notifications")


def cfg_session() -> tuple[object, DataHubMCPSession]:
    config = load_datahub_mcp_config({"DATAHUB_MCP_URL": ENDPOINT, "DATAHUB_TOKEN": "test-token"})
    session = DataHubMCPSession(endpoint_url=ENDPOINT, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION, server_name="DataHub", server_version="1", tools_supported=True, session_id="session-1")
    return config, session


def search_schema(**properties: dict) -> dict:
    return {"type": "object", "properties": {"query": {"type": "string", "minLength": 4, "maxLength": 512}, **properties}}


def tool(name: str, schema: dict | None = None) -> dict:
    return {"name": name, "inputSchema": search_schema() if name == "search" and schema is None else (schema or {"type": "object", "properties": {"value": {"type": "string"}}})}


def page(tools: list[dict], request_id: int = 2, next_cursor: str | None = None) -> DataHubMCPHTTPResponse:
    result = {"tools": tools}
    if next_cursor is not None:
        result["nextCursor"] = next_cursor
    body = json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}).encode()
    return DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, body)


def required_tools(schema: dict | None = None) -> list[dict]:
    return [tool(item.value, schema if item.value == "search" else None) for item in READ_TOOL_ORDER]


def discover(schema: dict | None = None, responses: list[DataHubMCPHTTPResponse] | None = None):
    config, session = cfg_session()
    transport = FakeTransport(responses or [page(required_tools(schema))])
    return discover_datahub_read_tool_bundle(config=config, session=session, transport=transport), transport


def test_minimal_attestation_and_bundle_request_id() -> None:
    bundle, transport = discover()
    assert bundle.next_request_id == 3
    assert bundle.search_contract.query_supported
    assert len(bundle.catalog.tools) == 4
    assert len(transport.calls) == 1


def test_optional_fields_are_attested_and_planned() -> None:
    schema = search_schema(
        filter={"type": "string"},
        num_results={"type": "integer", "minimum": 1, "maximum": 10},
        offset={"type": "integer", "minimum": 0},
        search_strategy={"type": "string", "enum": ["keyword"]},
        sort_by={"type": "string"},
        sort_order={"type": "string"},
    )
    bundle, _ = discover(schema)
    contract = bundle.search_contract
    assert contract.supports_dataset_filter and contract.supports_result_limit and contract.supports_offset
    assert contract.supports_keyword_strategy and contract.supports_sorting
    plan = build_datahub_search_argument_plan(search_contract=contract, query=" /q orders ")
    assert dict(plan.arguments) == {"query": "/q orders", "filter": "entity_type = dataset", "num_results": 10, "offset": 0, "search_strategy": "keyword"}


@pytest.mark.parametrize("schema", [
    {"type": "object", "properties": {}},
    {"type": "object", "properties": {"query": {"type": "integer"}}},
    {"type": "object", "properties": {"query": {"type": "string", "maxLength": 10}}},
    {"type": "object", "properties": {"query": {"type": "string", "minLength": 5}}},
    {"type": "object", "properties": {"query": {"$ref": "#/definitions/query"}}},
    {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query", "other"]},
])
def test_incompatible_search_schema_fails_closed(schema: dict) -> None:
    with pytest.raises((DataHubSearchContractError, DataHubToolDiscoveryError)) as exc:
        discover(schema)
    assert exc.value.code in {"search_schema_incompatible", "invalid_tool_schema"}


def test_unknown_optional_and_required_properties() -> None:
    optional = search_schema(unrecognized={"type": "string"})
    bundle, _ = discover(optional)
    assert bundle.search_contract.query_supported
    required = dict(optional, required=["query", "unrecognized"])
    with pytest.raises(DataHubSearchContractError):
        discover(required)


def test_fingerprint_cross_check_and_schema_order_stability() -> None:
    schema = search_schema(filter={"type": "string"})
    reordered = {"properties": {"filter": {"type": "string"}, "query": schema["properties"]["query"]}, "type": "object"}
    first, _ = discover(schema)
    second, _ = discover(reordered)
    assert first.search_contract.input_schema_fingerprint == second.search_contract.input_schema_fingerprint
    bad_plan = build_datahub_search_argument_plan(search_contract=first.search_contract, query="/q item")
    tampered = bad_plan.model_copy(update={"input_schema_fingerprint": "0" * 64})
    with pytest.raises(DataHubSearchContractError) as exc:
        build_datahub_search_tools_call_request(discovery=first, argument_plan=tampered)
    assert exc.value.code == "search_schema_fingerprint_mismatch"


def test_pagination_derives_next_request_id_and_preserves_cursor() -> None:
    config, session = cfg_session()
    first = required_tools()[:2]
    second = required_tools()[2:]
    transport = FakeTransport([page(first, 2, "opaque-cursor"), page(second, 3)])
    bundle = discover_datahub_read_tool_bundle(config=config, session=session, transport=transport)
    assert bundle.next_request_id == 4
    assert json.loads(transport.calls[1][0])["params"]["cursor"] == "opaque-cursor"


def test_existing_discovery_remains_catalog_only_and_single_pass() -> None:
    config, session = cfg_session()
    transport = FakeTransport([page(required_tools())])
    catalog = discover_datahub_read_tools(config=config, session=session, transport=transport)
    assert len(catalog.tools) == 4 and len(transport.calls) == 1
    assert "properties" not in repr(catalog).lower()


@pytest.mark.parametrize("query", ["table", " /q ", "/q ", "/q " + "x" * 513, "/q a\n", "/q a\x00b", "/q select * from table", "/q ```x```"])
def test_query_boundary(query: str) -> None:
    bundle, _ = discover()
    with pytest.raises((DataHubSearchContractError, ValueError)):
        build_datahub_search_argument_plan(search_contract=bundle.search_contract, query=query)


def test_argument_plan_and_tools_call_are_deterministic_and_do_not_transport() -> None:
    bundle, transport = discover()
    plan = build_datahub_search_argument_plan(search_contract=bundle.search_contract, query="/q customer_orders")
    request = build_datahub_search_tools_call_request(discovery=bundle, argument_plan=plan)
    assert request.model_dump(exclude_none=True) == {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search", "arguments": {"query": "/q customer_orders"}}}
    assert serialize_datahub_search_tools_call_request(discovery=bundle, argument_plan=plan) == serialize_jsonrpc(request)
    assert len(transport.calls) == 1
    body = serialize_datahub_search_tools_call_request(discovery=bundle, argument_plan=plan)
    assert b"sort_by" not in body
    assert b"token" not in body.lower()


def test_plan_mapping_is_defensively_immutable() -> None:
    bundle, _ = discover()
    plan = build_datahub_search_argument_plan(search_contract=bundle.search_contract, query="/q item")
    with pytest.raises(TypeError):
        plan.arguments["query"] = "/q changed"  # type: ignore[index]


def test_no_result_parser_or_transport_execution_was_added() -> None:
    source = Path(__file__).parents[1].joinpath("app/integrations/datahub/search_contract.py").read_text(encoding="utf-8")
    assert "structuredContent" not in source and "isError" not in source and "post_request" not in source
