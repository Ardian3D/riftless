from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.integrations.datahub.config import DATAHUB_MCP_PROTOCOL_VERSION, load_datahub_mcp_config
from app.integrations.datahub.initialization import DataHubMCPSession
from app.integrations.datahub.search_contract import build_datahub_search_argument_plan, discover_datahub_read_tool_bundle
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
