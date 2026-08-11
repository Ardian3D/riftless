from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.integrations.datahub.config import DATAHUB_MCP_PROTOCOL_VERSION, load_datahub_mcp_config
from app.integrations.datahub.initialization import DataHubMCPSession
from app.integrations.datahub.search_contract import (
    DataHubReadToolDiscoveryBundle,
    DataHubSearchArgumentPlan,
    DataHubSearchSchemaContract,
    build_datahub_search_argument_plan,
    discover_datahub_read_tool_bundle,
    serialize_datahub_search_tools_call_request,
)
from app.integrations.datahub.search_execution import DataHubSearchExecutionError, DataHubSearchExecutionResult, execute_datahub_search
from app.integrations.datahub.tool_discovery import READ_TOOL_ORDER
from app.integrations.datahub.transport import DataHubMCPHTTPResponse

ENDPOINT = "https://datahub.example.com/mcp"


class FakeTransport:
    def __init__(self, response: DataHubMCPHTTPResponse):
        self.response = response
        self.calls: list[tuple[bytes, str | None, str | None]] = []

    def post_request(self, body: bytes, *, session_id: str | None, protocol_version: str | None):
        self.calls.append((body, session_id, protocol_version))
        return self.response

    def post_notification(self, body: bytes, *, session_id: str | None, protocol_version: str):
        raise AssertionError("search execution must not send notifications")


def config_session() -> tuple[object, DataHubMCPSession]:
    config = load_datahub_mcp_config({"DATAHUB_MCP_URL": ENDPOINT, "DATAHUB_TOKEN": "test-token"})
    session = DataHubMCPSession(endpoint_url=ENDPOINT, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION, server_name="DataHub", server_version="1", tools_supported=True, session_id="session-1")
    return config, session


def tool(name: str) -> dict:
    if name == "search":
        schema = {"type": "object", "properties": {"query": {"type": "string", "minLength": 4, "maxLength": 512}}}
    else:
        schema = {"type": "object", "properties": {"value": {"type": "string"}}}
    return {"name": name, "inputSchema": schema}


def discovery_bundle():
    config, session = config_session()
    responses = [DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"tools": [tool(item.value) for item in READ_TOOL_ORDER]}}).encode())]
    discovery_transport = FakeTransport(responses[0])
    discovery = discover_datahub_read_tool_bundle(config=config, session=session, transport=discovery_transport)
    plan = build_datahub_search_argument_plan(search_contract=discovery.search_contract, query="/q orders")
    return config, session, discovery, plan


def page(*, result: dict, content: list[dict] | None = None, is_error: object = False, structured: bool = True, response_id: int = 3) -> DataHubMCPHTTPResponse:
    envelope_result: dict = {"content": ([{"type": "text", "text": "ignored"}] if content is None else content), "isError": is_error}
    if structured:
        envelope_result["structuredContent"] = result
    elif content is None:
        envelope_result["content"] = [{"type": "text", "text": json.dumps(result, separators=(",", ":"))}]
    body = json.dumps({"jsonrpc": "2.0", "id": response_id, "result": envelope_result}).encode()
    return DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, body)


def payload(entries: list[dict], total: int | None = None) -> dict:
    return {"start": 0, "count": len(entries), "total": len(entries) if total is None else total, "searchResults": entries, "facets": [{"ignored": True}]}


def entry(urn: str = "urn:li:dataset:(platform,orders,PROD)", name: object = "orders") -> dict:
    return {"entity": {"urn": urn, "properties": {"name": name}, "unknown": "ignored"}}


def execute(response: DataHubMCPHTTPResponse, *, session: DataHubMCPSession | None = None):
    config, original_session, discovery, plan = discovery_bundle()
    transport = FakeTransport(response)
    result = execute_datahub_search(config=config, session=session or original_session, discovery=discovery, argument_plan=plan, transport=transport)
    return result, transport, config, original_session, discovery, plan


def test_valid_structured_result_is_normalized_with_exact_one_call() -> None:
    result, transport, _, _, discovery, plan = execute(page(result=payload([entry()])))
    assert isinstance(result, DataHubSearchExecutionResult)
    assert result.request_id == discovery.next_request_id == 3
    assert result.next_request_id == 4
    assert result.records[0].dataset_urn == "urn:li:dataset:(platform,orders,PROD)"
    assert result.records[0].display_name == "orders"
    assert result.records[0].source_position == 0
    assert result.input_schema_fingerprint == plan.input_schema_fingerprint
    assert len(transport.calls) == 1
    sent = json.loads(transport.calls[0][0])
    assert sent["method"] == "tools/call" and sent["params"]["name"] == "search" and sent["id"] == 3
    assert transport.calls[0][1:] == ("session-1", DATAHUB_MCP_PROTOCOL_VERSION)


def test_text_json_fallback_and_empty_page() -> None:
    empty, transport, *_ = execute(page(result=payload([], total=25), structured=False))
    assert empty.records == () and empty.provider_count == 0 and empty.provider_total == 25 and len(transport.calls) == 1


def test_request_fingerprint_is_deterministic_and_excludes_secret_endpoint() -> None:
    first, _, *_ = execute(page(result=payload([entry()])))
    second, _, *_ = execute(page(result=payload([entry()])))
    assert first.search_request_fingerprint == second.search_request_fingerprint
    assert len(first.search_request_fingerprint) == 64 and first.search_request_fingerprint == first.search_request_fingerprint.lower()
    assert "test-token" not in first.search_request_fingerprint and "datahub.example.com" not in first.search_request_fingerprint


@pytest.mark.parametrize("field,value", [("start", True), ("count", True), ("total", True), ("start", -1), ("start", 1), ("count", 11), ("total", 1_000_001)])
def test_page_integer_boundaries_rejected(field: str, value: object) -> None:
    data = payload([])
    data[field] = value
    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute(page(result=data))
    assert exc.value.code == "invalid_search_result_payload"


def test_count_mismatch_total_below_count_and_missing_fields_rejected() -> None:
    bad = payload([entry()]); bad["count"] = 0
    with pytest.raises(DataHubSearchExecutionError) as exc: execute(page(result=bad))
    assert exc.value.code == "search_result_count_mismatch"
    bad = payload([entry()]); bad["total"] = 0
    with pytest.raises(DataHubSearchExecutionError): execute(page(result=bad))
    with pytest.raises(DataHubSearchExecutionError): execute(page(result={"start": 0, "count": 0, "total": 0}))


def test_non_dataset_is_ignored_and_counted_but_malformed_urn_rejected() -> None:
    data = payload([entry("urn:li:dashboard:dash"), entry()])
    result, *_ = execute(page(result=data))
    assert len(result.records) == 1 and result.non_dataset_result_count == 1
    with pytest.raises(DataHubSearchExecutionError): execute(page(result=payload([entry("not-a-urn")])))


def test_duplicate_urn_is_rejected_without_leaking_urn() -> None:
    duplicate = payload([entry(), entry(name="other")])
    with pytest.raises(DataHubSearchExecutionError) as exc: execute(page(result=duplicate))
    assert exc.value.code == "duplicate_search_result_urn" and "urn:li" not in str(exc.value)


@pytest.mark.parametrize("content", [
    [{"type": "image", "data": "x"}],
    [{"type": "audio", "data": "x"}],
    [{"type": "resource", "resource": {}}],
    [{"type": "text"}],
    [{"type": "text", "text": "x\x00"}],
])
def test_content_blocks_are_strictly_bounded(content: list[dict]) -> None:
    with pytest.raises(DataHubSearchExecutionError): execute(page(result=payload([]), content=content))


def test_content_and_payload_limits_are_enforced() -> None:
    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute(page(result=payload([]), content=[{"type": "text", "text": "x" * 262145}], structured=False))
    assert exc.value.code == "search_content_too_large"
    huge = {"start": 0, "count": 0, "total": 0, "searchResults": [], "large": "x" * 524_289}
    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute(page(result=huge))
    assert exc.value.code == "search_content_too_large"


def test_is_error_is_safe_and_malformed_is_error_rejected() -> None:
    with pytest.raises(DataHubSearchExecutionError) as exc: execute(page(result=payload([]), is_error=True))
    assert exc.value.code == "search_tool_execution_failed" and "provider" not in str(exc.value)
    with pytest.raises(DataHubSearchExecutionError): execute(page(result=payload([]), is_error="true"))


@pytest.mark.parametrize("text", ["", "```{} ```", "prefix {}", "{} suffix", "{} {}", "[]", '{"start":0,"start":0}'])
def test_strict_text_fallback_rejects_invalid_payloads(text: str) -> None:
    response = DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, json.dumps({"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": text}]}}).encode())
    with pytest.raises(DataHubSearchExecutionError): execute(response)


def test_structured_content_has_priority_and_text_is_not_reparsed() -> None:
    response = page(result=payload([]), content=[{"type": "text", "text": "not JSON and must be ignored"}], structured=True)
    result, *_ = execute(response)
    assert result.records == ()


def test_context_mismatch_fails_before_transport() -> None:
    config, session, discovery, plan = discovery_bundle()
    transport = FakeTransport(page(result=payload([])))
    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute_datahub_search(config=config, session=session.model_copy(update={"endpoint_url": "https://other.example.com/mcp"}), discovery=discovery, argument_plan=plan, transport=transport)
    assert exc.value.code == "search_execution_context_mismatch" and not transport.calls


def test_response_id_mismatch_propagates_safe_protocol_error_without_second_call() -> None:
    response = page(result=payload([]), response_id=4)
    _, _, discovery, _ = discovery_bundle()
    config, session = config_session()
    transport = FakeTransport(response)
    plan = build_datahub_search_argument_plan(search_contract=discovery.search_contract, query="/q orders")
    with pytest.raises(Exception) as exc:
        execute_datahub_search(config=config, session=session, discovery=discovery, argument_plan=plan, transport=transport)
    assert len(transport.calls) == 1 and "urn:li" not in str(exc.value)


def test_result_contains_no_raw_payload_or_authority_fields() -> None:
    result, *_ = execute(page(result=payload([entry()])))
    dumped = result.model_dump()
    assert set(dumped) == {"request_id", "next_request_id", "search_request_fingerprint", "input_schema_fingerprint", "records", "provider_start", "provider_count", "provider_total", "non_dataset_result_count", "result_version"}
    assert "query" not in repr(result) and "facets" not in repr(result) and "authority" not in repr(result)


def test_no_additional_tool_execution_surface() -> None:
    source = Path(__file__).parents[1].joinpath("app/integrations/datahub/search_execution.py").read_text(encoding="utf-8")
    assert "get_entities" not in source and "list_schema_fields" not in source and "get_lineage" not in source and "tasks/" not in source


def test_request_bytes_are_canonical_and_fingerprint_changes_with_query() -> None:
    first, transport, config, session, discovery, plan = execute(page(result=payload([])))
    assert transport.calls[0][0] == serialize_datahub_search_tools_call_request(discovery=discovery, argument_plan=plan)
    other_plan = build_datahub_search_argument_plan(search_contract=discovery.search_contract, query="/q products")
    second_transport = FakeTransport(page(result=payload([])))
    second = execute_datahub_search(config=config, session=session, discovery=discovery, argument_plan=other_plan, transport=second_transport)
    assert first.search_request_fingerprint != second.search_request_fingerprint


def test_preflight_context_failures_make_zero_transport_calls() -> None:
    config, session, discovery, plan = discovery_bundle()
    bad_sessions = (
        session.model_construct(endpoint_url=ENDPOINT, protocol_version="2024-11-05", server_name="DataHub", server_version="1", tools_supported=True, session_id="session-1"),
        session.model_copy(update={"tools_supported": False}),
    )
    for bad_session in bad_sessions:
        transport = FakeTransport(page(result=payload([])))
        with pytest.raises(DataHubSearchExecutionError) as exc:
            execute_datahub_search(config=config, session=bad_session, discovery=discovery, argument_plan=plan, transport=transport)
        assert exc.value.code == "search_execution_context_mismatch" and not transport.calls

    bad_contract = DataHubSearchSchemaContract.model_construct(
        input_schema_fingerprint="0" * 64,
        query_supported=True,
        supports_dataset_filter=False,
        supports_result_limit=False,
        supports_offset=False,
        supports_keyword_strategy=False,
        supports_sorting=False,
        contract_version="1.0",
    )
    bad_discovery = DataHubReadToolDiscoveryBundle.model_construct(
        catalog=discovery.catalog, search_contract=bad_contract, next_request_id=3, bundle_version="1.0"
    )
    bad_plan = DataHubSearchArgumentPlan.model_construct(
        query=plan.query, arguments=plan.arguments, input_schema_fingerprint="1" * 64, plan_version="1.0"
    )
    for current_discovery, current_plan in ((bad_discovery, plan), (discovery, bad_plan)):
        transport = FakeTransport(page(result=payload([])))
        with pytest.raises(DataHubSearchExecutionError) as exc:
            execute_datahub_search(config=config, session=session, discovery=current_discovery, argument_plan=current_plan, transport=transport)
        assert exc.value.code == "search_execution_context_mismatch" and not transport.calls


def test_invalid_request_id_and_oversized_request_fail_before_transport() -> None:
    config, session, discovery, plan = discovery_bundle()
    bad_discovery = DataHubReadToolDiscoveryBundle.model_construct(
        catalog=discovery.catalog, search_contract=discovery.search_contract, next_request_id=2, bundle_version="1.0"
    )
    transport = FakeTransport(page(result=payload([])))
    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute_datahub_search(config=config, session=session, discovery=bad_discovery, argument_plan=plan, transport=transport)
    assert exc.value.code == "search_execution_context_mismatch" and not transport.calls

    oversized_plan = DataHubSearchArgumentPlan.model_construct(
        query=plan.query,
        arguments={"query": plan.query, "filter": "x" * 70_000},
        input_schema_fingerprint=plan.input_schema_fingerprint,
        plan_version="1.0",
    )
    transport = FakeTransport(page(result=payload([])))
    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute_datahub_search(config=config, session=session, discovery=discovery, argument_plan=oversized_plan, transport=transport)
    assert exc.value.code == "search_request_too_large" and not transport.calls


def test_call_tool_result_shape_and_content_limits() -> None:
    missing_content = DataHubMCPHTTPResponse(
        200,
        {"Content-Type": "application/json"},
        json.dumps({"jsonrpc": "2.0", "id": 3, "result": {"structuredContent": payload([])}}).encode(),
    )
    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute(missing_content)
    assert exc.value.code == "invalid_search_tool_result"

    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute(page(result=payload([]), content=[{"type": "text", "text": "x"} for _ in range(9)]))
    assert exc.value.code == "unsupported_search_content"

    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute(page(result=payload([]), content=[{"type": "text", "text": "x" * 200_000}, {"type": "text", "text": "y" * 200_000}]))
    assert exc.value.code == "search_content_too_large"


def test_meta_and_unknown_call_tool_fields_are_ignored() -> None:
    envelope = {
        "content": [{"type": "text", "text": "ignored"}],
        "structuredContent": payload([entry()]),
        "isError": False,
        "_meta": {"provider": "ignored"},
        "unknown": {"raw": "ignored"},
    }
    response = DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, json.dumps({"jsonrpc": "2.0", "id": 3, "result": envelope}).encode())
    result, *_ = execute(response)
    assert len(result.records) == 1


def test_structured_content_and_fallback_payload_boundaries() -> None:
    response = DataHubMCPHTTPResponse(
        200,
        {"Content-Type": "application/json"},
        json.dumps({"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "ignored"}], "structuredContent": []}}).encode(),
    )
    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute(response)
    assert exc.value.code == "missing_search_result_payload"

    content = [{"type": "text", "text": json.dumps(payload([]))}, {"type": "text", "text": "second"}]
    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute(page(result=payload([]), content=content, structured=False))
    assert exc.value.code == "missing_search_result_payload"


@pytest.mark.parametrize("text", ["NaN", "Infinity", '{"start":0,"count":0,"total":0,"searchResults":[],"x":NaN}'])
def test_non_standard_json_numbers_are_rejected(text: str) -> None:
    response = DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, json.dumps({"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": text}]}}).encode())
    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute(response)
    assert exc.value.code == "invalid_search_result_payload"


def test_ten_results_and_unknown_page_fields_are_supported() -> None:
    entries = [entry(f"urn:li:dataset:(platform,table-{index},PROD)", name=f"table-{index}") for index in range(10)]
    data = payload(entries)
    data["unknownTopLevel"] = {"ignored": True}
    result, *_ = execute(page(result=data))
    assert result.provider_count == 10 and len(result.records) == 10


def test_oversized_result_list_is_rejected() -> None:
    entries = [entry(f"urn:li:dataset:(platform,table-{index},PROD)") for index in range(11)]
    data = payload(entries, total=11)
    data["count"] = 10
    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute(page(result=data))
    assert exc.value.code == "search_result_too_large"


def test_entity_shape_and_optional_metadata() -> None:
    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute(page(result=payload([{}])))
    assert exc.value.code == "invalid_search_result_entity"

    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute(page(result=payload([{"entity": {"properties": {"name": "missing urn"}}}])))
    assert exc.value.code == "invalid_search_result_entity"

    data = payload([
        {"entity": {"urn": "urn:li:dataset:(platform,one,PROD)"}},
        {"entity": {"urn": "urn:li:dataset:(platform,two,PROD)", "properties": None}},
        {"entity": {"urn": "urn:li:dataset:(platform,three,PROD)", "properties": {"name": None}}},
    ])
    result, *_ = execute(page(result=data))
    assert [record.display_name for record in result.records] == [None, None, None]


def test_names_are_trimmed_bounded_and_control_safe() -> None:
    result, *_ = execute(page(result=payload([entry(name="   ")])))
    assert result.records[0].display_name is None
    for name in ("x" * 513, "bad\x00name", "bad\nname"):
        with pytest.raises(DataHubSearchExecutionError) as exc:
            execute(page(result=payload([entry(name=name)])))
        assert exc.value.code == "invalid_search_result_entity"


def test_duplicate_non_dataset_urn_is_rejected() -> None:
    duplicate = payload([entry("urn:li:dashboard:dash"), entry("urn:li:dashboard:dash", name="different")])
    with pytest.raises(DataHubSearchExecutionError) as exc:
        execute(page(result=duplicate))
    assert exc.value.code == "duplicate_search_result_urn" and "urn:li" not in str(exc.value)


def test_provider_order_source_positions_and_result_version_are_fixed() -> None:
    data = payload([
        entry("urn:li:dataset:(platform,first,PROD)"),
        entry("urn:li:dataset:(platform,second,PROD)"),
        entry("urn:li:dataset:(platform,third,PROD)"),
    ])
    result, *_ = execute(page(result=data))
    assert [record.dataset_urn for record in result.records] == [
        "urn:li:dataset:(platform,first,PROD)",
        "urn:li:dataset:(platform,second,PROD)",
        "urn:li:dataset:(platform,third,PROD)",
    ]
    assert [record.source_position for record in result.records] == [0, 1, 2]
    assert result.result_version == "1.0"


def test_scope_regression_source_audit() -> None:
    source = Path(__file__).parents[1].joinpath("app/integrations/datahub/search_execution.py").read_text(encoding="utf-8")
    forbidden = (
        "load_datahub_mcp_config", "initialize_datahub_mcp", "tools/list", "resources/", "prompts/", "sampling/",
        "logging", "print(", "subprocess", "import requests", "import httpx", "import aiohttp", "DataHubResolvedSubject",
        "DataHubContextPack", "DataHubContextArtifact", "except Exception", "score", "urllib", "http.client",
    )
    assert all(token not in source for token in forbidden)
