from __future__ import annotations

import hashlib
import inspect
import json
import re
from pathlib import Path

import pytest

from app.integrations.datahub.asset_resolution import DataHubAssetResolutionSubject, resolve_datahub_asset_candidate
from app.integrations.datahub.config import DATAHUB_MCP_PROTOCOL_VERSION, load_datahub_mcp_config
from app.integrations.datahub.entity_execution import (
    DataHubDatasetEntityMetadata,
    DataHubEntityMetadataExecutionError,
    DataHubEntityMetadataExecutionResult,
    execute_datahub_get_entities,
)
from app.integrations.datahub.entity_schema_contract import (
    DataHubEntitySchemaContext,
    DataHubEntitySchemaToolDiscoveryBundle,
    DataHubGetEntitiesArgumentPlan,
    DataHubGetEntitiesSchemaContract,
    bind_datahub_entity_schema_context,
    build_datahub_get_entities_argument_plan,
    build_datahub_get_entities_tools_call_request,
    discover_datahub_entity_schema_tool_bundle,
    serialize_datahub_get_entities_tools_call_request,
)
from app.integrations.datahub.initialization import DataHubMCPSession
from app.integrations.datahub.mcp_protocol import DataHubMCPProtocolError, serialize_jsonrpc
from app.integrations.datahub.search_contract import DataHubReadToolDiscoveryBundle
from app.integrations.datahub.search_execution import DataHubDatasetSearchRecord, DataHubSearchExecutionResult
from app.integrations.datahub.tool_discovery import CATALOG_VERSION, READ_TOOL_ORDER, DataHubReadToolCatalog
from app.integrations.datahub.transport import DataHubMCPHTTPResponse
from app.schemas.datahub_context import DataHubOwnerKind

ENDPOINT = "https://datahub.example.com/mcp"
ORDERS_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.orders,PROD)"
CUSTOMERS_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.customers,PROD)"
BIGQUERY_ORDERS_URN = "urn:li:dataset:(urn:li:dataPlatform:bigquery,analytics.core.orders,PROD)"

GET_ENTITIES_SCHEMA = {
    "type": "object",
    "properties": {"urns": {"type": "array", "items": {"type": "string", "maxLength": 1024}}},
    "required": ["urns"],
}

LIST_SCHEMA_FIELDS_SCHEMA = {
    "type": "object",
    "properties": {
        "urn": {"type": "string", "maxLength": 1024},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100},
        "offset": {"type": "integer", "minimum": 0},
    },
    "required": ["urn"],
}


def search_schema(**properties: dict) -> dict:
    return {"type": "object", "properties": {"query": {"type": "string", "minLength": 4, "maxLength": 512}, **properties}}


def tool(name: str, schema: dict | None = None) -> dict:
    if name == "search":
        default = search_schema()
    elif name == "get_entities":
        default = GET_ENTITIES_SCHEMA
    elif name == "list_schema_fields":
        default = LIST_SCHEMA_FIELDS_SCHEMA
    else:
        default = {"type": "object", "properties": {"value": {"type": "string"}}}
    return {"name": name, "inputSchema": default if schema is None else schema}


def required_tools() -> list[dict]:
    return [tool(item.value) for item in READ_TOOL_ORDER]


def page(tools: list[dict], request_id: int = 2) -> DataHubMCPHTTPResponse:
    body = json.dumps({"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}).encode()
    return DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, body)


class FakeTransport:
    def __init__(self, responses: list[DataHubMCPHTTPResponse]):
        self.responses = responses
        self.calls: list[tuple[bytes, str | None, str | None]] = []

    def post_request(self, body: bytes, *, session_id: str | None, protocol_version: str | None):
        self.calls.append((body, session_id, protocol_version))
        return self.responses[len(self.calls) - 1]

    def post_notification(self, body: bytes, *, session_id: str | None, protocol_version: str):
        raise AssertionError("F8.3C2 must not send notifications")


class RaisingTransport:
    def __init__(self, error: DataHubMCPProtocolError):
        self.error = error
        self.calls = []

    def post_request(self, body: bytes, *, session_id: str | None, protocol_version: str | None):
        self.calls.append(1)
        raise self.error

    def post_notification(self, body: bytes, *, session_id: str | None, protocol_version: str):
        raise AssertionError("F8.3C2 must not send notifications")


def cfg_session() -> tuple[object, DataHubMCPSession]:
    config = load_datahub_mcp_config({"DATAHUB_MCP_URL": ENDPOINT, "DATAHUB_TOKEN": "test-token"})
    session = DataHubMCPSession(endpoint_url=ENDPOINT, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION, server_name="DataHub", server_version="1", tools_supported=True, session_id="session-1")
    return config, session


def discover():
    config, session = cfg_session()
    transport = FakeTransport([page(required_tools())])
    return discover_datahub_entity_schema_tool_bundle(config=config, session=session, transport=transport), transport


def subject(name: str = "orders") -> DataHubAssetResolutionSubject:
    return DataHubAssetResolutionSubject(platform="snowflake", database="analytics", schema_name="core", table_name=name, affected_column="customer_id")


def record(urn: str = ORDERS_URN, name: str = "orders", position: int = 0) -> DataHubDatasetSearchRecord:
    return DataHubDatasetSearchRecord(dataset_urn=urn, display_name=name, source_position=position)


def search_execution(bundle: DataHubEntitySchemaToolDiscoveryBundle, *, records: tuple[DataHubDatasetSearchRecord, ...] | None = None) -> DataHubSearchExecutionResult:
    records = (record(),) if records is None else records
    next_id = bundle.read_discovery.next_request_id + 1
    return DataHubSearchExecutionResult(
        request_id=next_id - 1,
        next_request_id=next_id,
        search_request_fingerprint="a" * 64,
        input_schema_fingerprint=bundle.read_discovery.search_contract.input_schema_fingerprint,
        records=records,
        provider_start=0,
        provider_count=len(records),
        provider_total=len(records),
        non_dataset_result_count=0,
        result_version="1.0",
    )


def c2_setup(*, urn: str = ORDERS_URN, name: str = "orders") -> tuple[object, DataHubMCPSession, DataHubEntitySchemaToolDiscoveryBundle, DataHubSearchExecutionResult, DataHubEntitySchemaContext, DataHubGetEntitiesArgumentPlan]:
    bundle, _ = discover()
    config, session = cfg_session()
    search_exec = search_execution(bundle, records=(record(urn, name),))
    subj = subject(name)
    resolution = resolve_datahub_asset_candidate(subject=subj, search_result=search_exec)
    context = bind_datahub_entity_schema_context(subject=subj, resolution=resolution, search_execution=search_exec, discovery=bundle)
    plan = build_datahub_get_entities_argument_plan(context=context, contract=bundle.get_entities_contract)
    return config, session, bundle, search_exec, context, plan


def run(response: DataHubMCPHTTPResponse, *, config=None, session=None, discovery=None, binding=None, argument_plan=None, search_execution=None, transport=None):
    default_config, default_session, bundle, search_exec, context, plan = c2_setup()
    transport = transport or FakeTransport([response])
    result = execute_datahub_get_entities(
        config=config if config is not None else default_config,
        session=session if session is not None else default_session,
        discovery=discovery if discovery is not None else bundle,
        binding=binding if binding is not None else context,
        argument_plan=argument_plan if argument_plan is not None else plan,
        search_execution=search_execution if search_execution is not None else search_exec,
        transport=transport,
    )
    return result, transport


def bad_context(context: DataHubEntitySchemaContext, **overrides) -> DataHubEntitySchemaContext:
    values = {
        "subject": context.subject,
        "resolution": context.resolution,
        "search_execution": context.search_execution,
        "discovery": context.discovery,
        "dataset_urn": context.dataset_urn,
        "affected_column": context.affected_column,
        "get_entities_request_id": context.get_entities_request_id,
        "list_schema_fields_request_id": context.list_schema_fields_request_id,
        "post_metadata_next_request_id": context.post_metadata_next_request_id,
        "binding_version": "1.0",
    }
    values.update(overrides)
    return DataHubEntitySchemaContext.model_construct(**values)


def bad_plan(plan: DataHubGetEntitiesArgumentPlan, **overrides) -> DataHubGetEntitiesArgumentPlan:
    values = {
        "dataset_urn": plan.dataset_urn,
        "arguments": dict(plan.arguments),
        "input_schema_fingerprint": plan.input_schema_fingerprint,
        "plan_version": "1.0",
    }
    values.update(overrides)
    return DataHubGetEntitiesArgumentPlan.model_construct(**values)


def bad_bundle(bundle: DataHubEntitySchemaToolDiscoveryBundle, **overrides) -> DataHubEntitySchemaToolDiscoveryBundle:
    values = {
        "read_discovery": bundle.read_discovery,
        "get_entities_contract": bundle.get_entities_contract,
        "list_schema_fields_contract": bundle.list_schema_fields_contract,
        "bundle_version": "1.0",
    }
    values.update(overrides)
    return DataHubEntitySchemaToolDiscoveryBundle.model_construct(**values)


def entity(**overrides) -> dict:
    data = {
        "urn": ORDERS_URN,
        "properties": {"name": "orders", "description": "system description", "customProperties": {"env": "prod"}},
        "editableProperties": {"description": "editable description"},
        "ownership": {"owners": [{"owner": {"urn": "urn:li:corpuser:alice"}, "type": "TECHNICAL_OWNER"}]},
        "globalTags": {"tags": [{"tag": {"urn": "urn:li:tag:golden", "name": "golden"}}]},
        "glossaryTerms": {"terms": [{"term": {"urn": "urn:li:glossaryTerm:pii", "name": "pii"}}]},
        "domain": {"domain": {"urn": "urn:li:domain:finance", "name": "finance"}},
        "schemaMetadata": {"fields": [{"fieldPath": "id"}]},
        "viewProperties": {"logic": "select * from orders"},
        "relatedDocuments": [{"url": "https://example.com/orders"}],
        "status": {"removed": False},
    }
    data.update(overrides)
    return data


def mcp_response(*, content: list[dict] | None = None, result_dict: dict | None = None, is_error: object = False) -> DataHubMCPHTTPResponse:
    envelope: dict = {"content": content if content is not None else [{"type": "text", "text": "ignored"}]}
    if is_error is not None:
        envelope["isError"] = is_error
    if result_dict:
        envelope.update(result_dict)
    body = json.dumps({"jsonrpc": "2.0", "id": 4, "result": envelope}).encode()
    return DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, body)


def structured_response(entity_obj: dict | None = None, *, content: list[dict] | None = None, structured: object = None, is_error: object = False) -> DataHubMCPHTTPResponse:
    return mcp_response(content=content, result_dict={"structuredContent": structured if structured is not None else {"result": [entity_obj if entity_obj is not None else entity()]}}, is_error=is_error)


def text_response(entity_obj: dict | None = None, *, text: str | None = None, is_error: object = False) -> DataHubMCPHTTPResponse:
    return mcp_response(content=[{"type": "text", "text": text if text is not None else json.dumps([entity_obj if entity_obj is not None else entity()])}], is_error=is_error)


class TestPreflight:
    def test_valid_execution_context_accepted(self) -> None:
        result, transport = run(structured_response())
        assert isinstance(result, DataHubEntityMetadataExecutionResult)
        assert len(transport.calls) == 1

    def test_endpoint_mismatch_zero_calls(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_copy(update={"endpoint_url": "https://other.example.com/mcp"})
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), session=bad_session, transport=transport)
        assert exc.value.code == "entity_execution_context_mismatch" and not transport.calls

    def test_protocol_mismatch_zero_calls(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_construct(endpoint_url=ENDPOINT, protocol_version="2024-11-05", server_name="DataHub", server_version="1", tools_supported=True, session_id="session-1")
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), session=bad_session, transport=transport)
        assert exc.value.code == "entity_execution_context_mismatch" and not transport.calls

    def test_tools_unsupported_zero_calls(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_copy(update={"tools_supported": False})
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), session=bad_session, transport=transport)
        assert exc.value.code == "entity_execution_context_mismatch" and not transport.calls

    def test_unready_catalog_zero_calls(self) -> None:
        _, _, bundle, _, _, _ = c2_setup()
        bad_catalog = DataHubReadToolCatalog.model_construct(tools=bundle.read_discovery.catalog.tools, all_required_tools_available=False, annotation_verification_complete=False, catalog_version=CATALOG_VERSION)
        bad_read_discovery = DataHubReadToolDiscoveryBundle.model_construct(catalog=bad_catalog, search_contract=bundle.read_discovery.search_contract, next_request_id=bundle.read_discovery.next_request_id, bundle_version="1.0")
        unready = bad_bundle(bundle, read_discovery=bad_read_discovery)
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), discovery=unready, transport=transport)
        assert exc.value.code == "entity_execution_context_mismatch" and not transport.calls

    def test_get_entities_fingerprint_mismatch_zero_calls(self) -> None:
        _, _, bundle, _, _, _ = c2_setup()
        bad_contract = DataHubGetEntitiesSchemaContract.model_construct(input_schema_fingerprint="0" * 64, supports_single_item_urn_array=True, contract_version="1.0")
        mismatched = bad_bundle(bundle, get_entities_contract=bad_contract)
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), discovery=mismatched, transport=transport)
        assert exc.value.code == "entity_execution_context_mismatch" and not transport.calls

    def test_plan_fingerprint_mismatch_zero_calls(self) -> None:
        _, _, _, _, context, plan = c2_setup()
        bad = bad_plan(plan, input_schema_fingerprint="0" * 64)
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), binding=context, argument_plan=bad, transport=transport)
        assert exc.value.code == "entity_execution_context_mismatch" and not transport.calls

    def test_dataset_target_mismatch_zero_calls(self) -> None:
        _, _, _, _, context, plan = c2_setup()
        bad = bad_plan(plan, dataset_urn=CUSTOMERS_URN, arguments={"urns": (CUSTOMERS_URN,)})
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), binding=context, argument_plan=bad, transport=transport)
        assert exc.value.code == "entity_execution_context_mismatch" and not transport.calls

    def test_platform_mismatch_zero_calls(self) -> None:
        _, _, _, _, context, plan = c2_setup()
        postgres_subject = DataHubAssetResolutionSubject(platform="postgres", database="analytics", schema_name="core", table_name="orders", affected_column="customer_id")
        bad = bad_context(context, subject=postgres_subject)
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), binding=bad, argument_plan=plan, transport=transport)
        assert exc.value.code == "entity_execution_context_mismatch" and not transport.calls

    def test_request_id_mismatch_zero_calls(self) -> None:
        _, _, _, _, context, plan = c2_setup()
        bad = bad_context(context, get_entities_request_id=9, list_schema_fields_request_id=10, post_metadata_next_request_id=11)
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), binding=bad, argument_plan=plan, transport=transport)
        assert exc.value.code == "entity_execution_context_mismatch" and not transport.calls

    def test_oversized_request_zero_calls(self) -> None:
        _, _, _, _, context, plan = c2_setup()
        bad = bad_plan(plan, arguments={"urns": ("x" * 70_000,)})
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), binding=context, argument_plan=bad, transport=transport)
        assert exc.value.code == "entity_execution_context_mismatch" and not transport.calls

    def test_arbitrary_multi_urn_plan_rejected(self) -> None:
        _, _, _, _, context, plan = c2_setup()
        bad = bad_plan(plan, arguments={"urns": (ORDERS_URN, CUSTOMERS_URN)})
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), binding=context, argument_plan=bad, transport=transport)
        assert exc.value.code == "entity_execution_context_mismatch" and not transport.calls


class TestOneCallTransport:
    def test_valid_execution_makes_exactly_one_post_request(self) -> None:
        _, transport = run(structured_response())
        assert len(transport.calls) == 1

    def test_method_exact_tools_call(self) -> None:
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["method"] == "tools/call"

    def test_tool_exact_get_entities(self) -> None:
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["params"]["name"] == "get_entities"

    def test_arguments_exact_one_item_urns_array(self) -> None:
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["params"]["arguments"] == {"urns": [ORDERS_URN]}

    def test_exact_request_id(self) -> None:
        _, _, _, search_exec, context, _ = c2_setup()
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["id"] == context.get_entities_request_id == search_exec.next_request_id

    def test_canonical_request_bytes(self) -> None:
        _, _, bundle, _, context, plan = c2_setup()
        _, transport = run(structured_response())
        expected = serialize_datahub_get_entities_tools_call_request(context=context, contract=bundle.get_entities_contract, argument_plan=plan)
        assert transport.calls[0][0] == expected
        assert transport.calls[0][0] == serialize_jsonrpc(build_datahub_get_entities_tools_call_request(context=context, contract=bundle.get_entities_contract, argument_plan=plan))

    def test_endpoint_reused(self) -> None:
        _, transport = run(structured_response())
        assert transport.calls[0][1] == "session-1"

    def test_auth_behavior_reused(self) -> None:
        _, transport = run(structured_response())
        body = transport.calls[0][0]
        assert b"test-token" not in body

    def test_protocol_header_reused(self) -> None:
        _, transport = run(structured_response())
        assert transport.calls[0][2] == DATAHUB_MCP_PROTOCOL_VERSION == "2025-11-25"

    def test_session_header_reused(self) -> None:
        _, transport = run(structured_response())
        assert transport.calls[0][1] == "session-1"

    def test_no_retry(self) -> None:
        _, transport = run(structured_response())
        assert len(transport.calls) == 1

    def test_no_second_call(self) -> None:
        _, transport = run(structured_response())
        assert len(transport.calls) == 1

    def test_no_list_schema_fields(self) -> None:
        _, transport = run(structured_response())
        assert b"list_schema_fields" not in transport.calls[0][0]

    def test_no_get_lineage(self) -> None:
        _, transport = run(structured_response())
        assert b"get_lineage" not in transport.calls[0][0]

    def test_no_tools_list_init_search(self) -> None:
        _, transport = run(structured_response())
        body = transport.calls[0][0]
        assert b"tools/list" not in body and b"initialize" not in body
        assert json.loads(body)["params"]["name"] == "get_entities"


class TestRequestFingerprint:
    def test_deterministic_fingerprint(self) -> None:
        first, _ = run(structured_response())
        second, _ = run(structured_response())
        assert first.entity_request_fingerprint == second.entity_request_fingerprint

    def test_64_lowercase_hex(self) -> None:
        result, _ = run(structured_response())
        assert len(result.entity_request_fingerprint) == 64
        assert re.fullmatch(r"[0-9a-f]{64}", result.entity_request_fingerprint)

    def test_request_change_changes_fingerprint(self) -> None:
        first, _ = run(structured_response())
        config, session, bundle, search_exec, context, plan = c2_setup(urn=CUSTOMERS_URN, name="customers")
        transport = FakeTransport([structured_response(entity(urn=CUSTOMERS_URN))])
        second = execute_datahub_get_entities(config=config, session=session, discovery=bundle, binding=context, argument_plan=plan, search_execution=search_exec, transport=transport)
        assert first.entity_request_fingerprint != second.entity_request_fingerprint

    def test_token_excluded(self) -> None:
        result, transport = run(structured_response())
        assert b"test-token" not in transport.calls[0][0]
        assert "test-token" not in result.entity_request_fingerprint

    def test_endpoint_excluded(self) -> None:
        result, transport = run(structured_response())
        assert ENDPOINT.encode() not in transport.calls[0][0]
        assert "datahub.example.com" not in result.entity_request_fingerprint

    def test_session_excluded(self) -> None:
        result, transport = run(structured_response())
        assert b"session-1" not in transport.calls[0][0]
        assert "session-1" not in result.entity_request_fingerprint

    def test_response_excluded(self) -> None:
        result, transport = run(structured_response())
        assert result.entity_request_fingerprint == hashlib.sha256(transport.calls[0][0]).hexdigest()


class TestMcpToolResult:
    def test_valid_call_tool_result_accepted(self) -> None:
        result, _ = run(structured_response())
        assert result.metadata.dataset_urn == ORDERS_URN

    def test_is_error_absent_false(self) -> None:
        response = mcp_response(result_dict={"structuredContent": {"result": [entity()]}}, is_error=None)
        result, _ = run(response)
        assert result.dataset_urn == ORDERS_URN

    def test_is_error_false_accepted(self) -> None:
        result, _ = run(structured_response(is_error=False))
        assert result.dataset_urn == ORDERS_URN

    def test_is_error_true_safe_failure(self) -> None:
        transport = FakeTransport([structured_response(is_error=True)])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(is_error=True), transport=transport)
        assert exc.value.code == "entity_tool_execution_failed" and len(transport.calls) == 1

    def test_malformed_is_error_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(is_error="true"))
        assert exc.value.code == "invalid_entity_tool_result"

    def test_content_required(self) -> None:
        response = DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, json.dumps({"jsonrpc": "2.0", "id": 4, "result": {"structuredContent": {"result": [entity()]}}}).encode())
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_tool_result"

    def test_content_list_required(self) -> None:
        response = mcp_response(content={"not": "a list"}, result_dict={"structuredContent": {"result": [entity()]}})
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_tool_result"

    def test_max_content_blocks_enforced(self) -> None:
        response = structured_response(content=[{"type": "text", "text": "x"} for _ in range(9)])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "unsupported_entity_content"

    def test_text_content_accepted(self) -> None:
        result, _ = run(text_response())
        assert result.dataset_urn == ORDERS_URN

    def test_unsupported_content_types_rejected(self) -> None:
        response = structured_response(content=[{"type": "image", "data": "x"}])
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "unsupported_entity_content"

    def test_text_utf8_enforced(self) -> None:
        response = text_response(text="\ud800")
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "unsupported_entity_content"

    def test_null_byte_rejected(self) -> None:
        response = text_response(text='[{"urn": "x\x00"}]')
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "entity_content_too_large"

    def test_text_size_bound(self) -> None:
        response = text_response(text="[" + json.dumps({"urn": ORDERS_URN}) + "x" * 262_145 + "]")
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "entity_content_too_large"

    def test_combined_text_bound(self) -> None:
        big = "x" * 200_000
        response = text_response(text=json.dumps([entity()]))
        response = mcp_response(content=[{"type": "text", "text": big}, {"type": "text", "text": big}], result_dict={"structuredContent": {"result": [entity()]}})
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "entity_content_too_large"

    def test_meta_ignored(self) -> None:
        result, _ = run(mcp_response(result_dict={"structuredContent": {"result": [entity()]}, "_meta": {"progressToken": "t"}}))
        assert result.dataset_urn == ORDERS_URN

    def test_unknown_result_fields_ignored(self) -> None:
        result, _ = run(mcp_response(result_dict={"structuredContent": {"result": [entity()]}, "unknown": {"x": 1}}))
        assert result.dataset_urn == ORDERS_URN

    def test_raw_result_not_retained(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        for token in ("structuredContent", "isError", "CallToolResult", "content"):
            assert token not in dumped


class TestStructuredPayload:
    def test_structured_result_one_item_accepted(self) -> None:
        result, _ = run(structured_response())
        assert result.metadata.dataset_urn == ORDERS_URN

    def test_structured_content_priority_over_text(self) -> None:
        response = mcp_response(content=[{"type": "text", "text": "this is not json"}], result_dict={"structuredContent": {"result": [entity()]}})
        result, _ = run(response)
        assert result.dataset_urn == ORDERS_URN

    def test_text_not_reparsed_when_structured_exists(self) -> None:
        response = mcp_response(content=[{"type": "text", "text": "this is not json"}], result_dict={"structuredContent": {"result": [entity()]}})
        result, _ = run(response)
        assert result.metadata.dataset_name == "orders"

    def test_structured_content_must_be_object(self) -> None:
        response = mcp_response(result_dict={"structuredContent": [1, 2]})
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_result_key_required(self) -> None:
        response = mcp_response(result_dict={"structuredContent": {}})
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "missing_entity_result_payload"

    def test_result_must_be_list(self) -> None:
        response = mcp_response(result_dict={"structuredContent": {"result": {}}})
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_structured_size_bound(self) -> None:
        response = mcp_response(result_dict={"structuredContent": {"result": [entity()], "blob": "x" * 524_300}})
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "entity_content_too_large"

    def test_empty_result_array_rejected(self) -> None:
        response = structured_response(structured={"result": []})
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "entity_result_cardinality_mismatch"

    def test_more_than_one_result_rejected(self) -> None:
        response = structured_response(structured={"result": [entity(), entity()]})
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "entity_result_cardinality_mismatch"

    def test_non_object_entity_item_rejected(self) -> None:
        response = structured_response(structured={"result": ["not-an-object"]})
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_unknown_wrapper_fields_ignored_not_stored(self) -> None:
        result, _ = run(structured_response(structured={"result": [entity()], "unknownWrapper": {"x": 1}}))
        assert result.dataset_urn == ORDERS_URN
        assert "unknownWrapper" not in json.dumps(result.model_dump())


class TestTextArrayFallback:
    def test_exact_one_item_json_array_accepted(self) -> None:
        result, _ = run(text_response())
        assert result.metadata.dataset_urn == ORDERS_URN

    def test_top_level_object_rejected(self) -> None:
        response = text_response(text=json.dumps(entity()))
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_top_level_scalar_rejected(self) -> None:
        response = text_response(text="42")
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_empty_array_rejected(self) -> None:
        response = text_response(text="[]")
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "entity_result_cardinality_mismatch"

    def test_two_item_array_rejected(self) -> None:
        response = text_response(text=json.dumps([entity(), entity()]))
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "entity_result_cardinality_mismatch"

    def test_markdown_fence_rejected(self) -> None:
        response = text_response(text="```json\n" + json.dumps([entity()]) + "\n```")
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_prose_prefix_rejected(self) -> None:
        response = text_response(text="result " + json.dumps([entity()]))
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_prose_suffix_rejected(self) -> None:
        response = text_response(text=json.dumps([entity()]) + " done")
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_multiple_json_documents_rejected(self) -> None:
        response = text_response(text="[] []")
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_duplicate_keys_rejected(self) -> None:
        response = text_response(text='[{"urn": "' + ORDERS_URN + '", "urn": "x"}]')
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_nan_rejected(self) -> None:
        response = text_response(text='[{"urn": NaN}]')
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_infinity_rejected(self) -> None:
        response = text_response(text='[{"urn": Infinity}]')
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_negative_infinity_rejected(self) -> None:
        response = text_response(text='[{"urn": -Infinity}]')
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_null_byte_rejected(self) -> None:
        response = text_response(text='[{"urn": "x\x00"}]')
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "entity_content_too_large"

    def test_malformed_json_rejected(self) -> None:
        response = text_response(text="[")
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_entity_result_payload"

    def test_raw_fallback_text_not_stored(self) -> None:
        result, _ = run(text_response())
        dumped = json.dumps(result.model_dump())
        assert json.dumps([entity()]) not in dumped


class TestProviderItemError:
    def test_provider_error_object_rejected(self) -> None:
        item = {"error": {"message": "entity not found"}}
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(item))
        assert exc.value.code == "entity_provider_item_failed"

    def test_provider_error_text_absent_from_safe_exception(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response({"error": {"message": "entity not found"}}))
        assert "entity not found" not in str(exc.value)

    def test_provider_error_urn_absent_from_safe_exception(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response({"error": {"urn": ORDERS_URN}}))
        assert "urn:li" not in str(exc.value)

    def test_error_plus_partial_metadata_still_rejected(self) -> None:
        item = {"error": {"message": "x"}, "urn": ORDERS_URN, "properties": {"name": "orders"}}
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(item))
        assert exc.value.code == "entity_provider_item_failed"

    def test_provider_item_error_does_not_retry(self) -> None:
        transport = FakeTransport([structured_response({"error": {"message": "x"}})])
        with pytest.raises(DataHubEntityMetadataExecutionError):
            run(structured_response({"error": {"message": "x"}}), transport=transport)
        assert len(transport.calls) == 1

    def test_provider_item_error_returns_no_partial_metadata(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError):
            run(structured_response({"error": {"message": "x"}}))


class TestIdentity:
    def test_exact_requested_returned_urn_accepted(self) -> None:
        result, _ = run(structured_response())
        assert result.dataset_urn == ORDERS_URN

    def test_missing_returned_urn_rejected(self) -> None:
        without_urn = {key: value for key, value in entity().items() if key != "urn"}
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(without_urn))
        assert exc.value.code == "entity_result_identity_mismatch"

    def test_null_returned_urn_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(urn=None)))
        assert exc.value.code == "entity_result_identity_mismatch"

    def test_non_string_urn_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(urn=123)))
        assert exc.value.code == "entity_result_identity_mismatch"

    def test_malformed_urn_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(urn="not-a-urn")))
        assert exc.value.code == "entity_result_identity_mismatch"

    def test_non_dataset_urn_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(urn="urn:li:dashboard:dash")))
        assert exc.value.code == "entity_result_identity_mismatch"

    def test_different_dataset_urn_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(urn=CUSTOMERS_URN)))
        assert exc.value.code == "entity_result_identity_mismatch"

    def test_same_name_different_urn_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(urn=CUSTOMERS_URN, properties={"name": "orders"})))
        assert exc.value.code == "entity_result_identity_mismatch"

    def test_wrong_platform_returned_urn_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(urn=BIGQUERY_ORDERS_URN)))
        assert exc.value.code == "entity_result_identity_mismatch"

    def test_identity_error_hides_urns(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(urn=CUSTOMERS_URN)))
        assert "urn:li" not in str(exc.value)
        assert ORDERS_URN not in str(exc.value)

    def test_no_provider_redirection(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError):
            run(structured_response(entity(urn=BIGQUERY_ORDERS_URN)))


class TestMetadataNormalization:
    def test_bounded_dataset_name(self) -> None:
        result, _ = run(structured_response())
        assert result.metadata.dataset_name == "orders"

    def test_blank_optional_name_handling(self) -> None:
        result, _ = run(structured_response(entity(properties={"name": "   "})))
        assert result.metadata.dataset_name is None

    def test_oversized_name_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(properties={"name": "x" * 600})))
        assert exc.value.code == "invalid_entity_metadata"

    def test_control_null_name_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(properties={"name": "bad\x00name"})))
        assert exc.value.code == "invalid_entity_metadata"

    def test_system_description_bounded(self) -> None:
        result, _ = run(structured_response())
        assert result.metadata.system_description == "system description"

    def test_editable_description_bounded(self) -> None:
        result, _ = run(structured_response())
        assert result.metadata.editable_description == "editable description"

    def test_description_source_distinction_preserved(self) -> None:
        result, _ = run(structured_response())
        assert result.metadata.system_description == "system description"
        assert result.metadata.editable_description == "editable description"
        assert result.metadata.system_description != result.metadata.editable_description

    def test_absent_owners_valid(self) -> None:
        result, _ = run(structured_response(entity() | {"ownership": None}))
        assert result.metadata.owners == ()

    def test_valid_bounded_owners(self) -> None:
        result, _ = run(structured_response())
        assert result.metadata.owners[0].owner_urn == "urn:li:corpuser:alice"
        assert result.metadata.owners[0].owner_kind is DataHubOwnerKind.TECHNICAL_OWNER

    def test_malformed_owners_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(ownership={"owners": [{"owner": 123}]})))
        assert exc.value.code == "invalid_entity_metadata"

    def test_owner_collection_bound(self) -> None:
        owners = [{"owner": {"urn": f"urn:li:corpuser:user{i}"}} for i in range(51)]
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(ownership={"owners": owners})))
        assert exc.value.code == "invalid_entity_metadata"

    def test_absent_tags_valid(self) -> None:
        result, _ = run(structured_response(entity() | {"globalTags": None}))
        assert result.metadata.tags == ()

    def test_valid_bounded_tags(self) -> None:
        result, _ = run(structured_response())
        assert result.metadata.tags[0].urn == "urn:li:tag:golden"
        assert result.metadata.tags[0].name == "golden"

    def test_malformed_tags_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(globalTags={"tags": [{"tag": {"urn": 5}}]})))
        assert exc.value.code == "invalid_entity_metadata"

    def test_tag_collection_bound(self) -> None:
        tags = [{"tag": {"urn": f"urn:li:tag:t{i}", "name": f"t{i}"}} for i in range(101)]
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(globalTags={"tags": tags})))
        assert exc.value.code == "invalid_entity_metadata"

    def test_absent_glossary_terms_valid(self) -> None:
        result, _ = run(structured_response(entity() | {"glossaryTerms": None}))
        assert result.metadata.glossary_terms == ()

    def test_valid_bounded_terms(self) -> None:
        result, _ = run(structured_response())
        assert result.metadata.glossary_terms[0].urn == "urn:li:glossaryTerm:pii"
        assert result.metadata.glossary_terms[0].name == "pii"

    def test_malformed_terms_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(glossaryTerms={"terms": [{"term": {"name": "pii"}}]})))
        assert exc.value.code == "invalid_entity_metadata"

    def test_term_collection_bound(self) -> None:
        terms = [{"term": {"urn": f"urn:li:glossaryTerm:t{i}", "name": f"t{i}"}} for i in range(101)]
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(glossaryTerms={"terms": terms})))
        assert exc.value.code == "invalid_entity_metadata"

    def test_absent_domain_valid(self) -> None:
        result, _ = run(structured_response(entity() | {"domain": None}))
        assert result.metadata.domain is None

    def test_valid_bounded_domain(self) -> None:
        result, _ = run(structured_response())
        assert result.metadata.domain is not None
        assert result.metadata.domain.urn == "urn:li:domain:finance"
        assert result.metadata.domain.name == "finance"

    def test_malformed_domain_rejected(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(domain={"domain": "not-a-dict"})))
        assert exc.value.code == "invalid_entity_metadata"

    def test_unknown_provider_fields_ignored(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "status" not in dumped and "removed" not in dumped

    def test_arbitrary_custom_properties_discarded(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "customProperties" not in dumped and "env" not in dumped

    def test_related_documents_discarded(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "relatedDocuments" not in dumped and "example.com" not in dumped

    def test_schema_metadata_discarded(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "schemaMetadata" not in dumped and "fieldPath" not in dumped

    def test_sql_view_logic_discarded(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "viewProperties" not in dumped and "logic" not in dumped and "select * from orders" not in dumped


class TestExecutionResult:
    def test_exact_execution_result_fields(self) -> None:
        result, _ = run(structured_response())
        assert set(result.model_dump()) == {"request_id", "next_request_id", "entity_request_fingerprint", "input_schema_fingerprint", "dataset_urn", "metadata", "result_version"}

    def test_request_id_preserved(self) -> None:
        _, _, _, search_exec, context, _ = c2_setup()
        result, _ = run(structured_response())
        assert result.request_id == context.get_entities_request_id == search_exec.next_request_id

    def test_next_id_equals_request_plus_one(self) -> None:
        result, _ = run(structured_response())
        assert result.next_request_id == result.request_id + 1

    def test_next_id_equals_planned_schema_request_id(self) -> None:
        _, _, _, _, context, _ = c2_setup()
        result, _ = run(structured_response())
        assert result.next_request_id == context.list_schema_fields_request_id

    def test_request_fingerprint_valid(self) -> None:
        result, _ = run(structured_response())
        assert re.fullmatch(r"[0-9a-f]{64}", result.entity_request_fingerprint)

    def test_schema_fingerprint_preserved(self) -> None:
        _, _, bundle, _, _, plan = c2_setup()
        result, _ = run(structured_response())
        assert result.input_schema_fingerprint == plan.input_schema_fingerprint == bundle.get_entities_contract.input_schema_fingerprint

    def test_dataset_urn_exact(self) -> None:
        result, _ = run(structured_response())
        assert result.dataset_urn == ORDERS_URN

    def test_normalized_metadata_immutable(self) -> None:
        result, _ = run(structured_response())
        metadata = result.metadata
        assert metadata.model_config["frozen"] is True
        with pytest.raises(Exception):
            metadata.dataset_name = "changed"

    def test_result_immutable(self) -> None:
        result, _ = run(structured_response())
        assert result.model_config["frozen"] is True
        with pytest.raises(Exception):
            result.dataset_urn = "changed"

    def test_result_version_fixed(self) -> None:
        result, _ = run(structured_response())
        assert result.result_version == "1.0"

    def test_no_request_arguments(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "arguments" not in dumped and '"urns"' not in dumped

    def test_no_raw_call_tool_result(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "CallToolResult" not in dumped and "structuredContent" not in dumped and "isError" not in dumped

    def test_no_content(self) -> None:
        result, _ = run(structured_response())
        assert "content" not in json.dumps(result.model_dump())

    def test_no_structured_content(self) -> None:
        result, _ = run(structured_response())
        assert "structuredContent" not in json.dumps(result.model_dump())

    def test_no_schema_metadata(self) -> None:
        result, _ = run(structured_response())
        assert "schemaMetadata" not in json.dumps(result.model_dump())

    def test_no_related_documents(self) -> None:
        result, _ = run(structured_response())
        assert "relatedDocuments" not in json.dumps(result.model_dump())

    def test_no_endpoint_token_session(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        for token in ("datahub.example.com", "test-token", "session-1"):
            assert token not in dumped

    def test_no_authority_fields(self) -> None:
        result, _ = run(structured_response())
        dumped = result.model_dump()
        for key in ("decision", "risk_score", "outcome", "deployment_authorized", "writeback_authorized", "authority"):
            assert key not in dumped


class TestErrorSafety:
    def test_provider_description_absent_from_error(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(properties={"name": "x" * 600, "description": "secret provider text"})))
        assert "secret provider text" not in str(exc.value)

    def test_owner_data_absent_from_error(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(ownership={"owners": [{"owner": 123}]})))
        assert "corpuser" not in str(exc.value)

    def test_tag_data_absent_from_error(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(globalTags={"tags": [{"tag": {"urn": 5}}]})))
        assert "golden" not in str(exc.value)

    def test_glossary_data_absent_from_error(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(glossaryTerms={"terms": [{"term": {"name": "pii"}}]})))
        assert "pii" not in str(exc.value)

    def test_domain_data_absent_from_error(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(entity(domain={"domain": "not-a-dict"})))
        assert "finance" not in str(exc.value)

    def test_request_body_absent_from_error(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_copy(update={"endpoint_url": "https://other.example.com/mcp"})
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), session=bad_session)
        assert "tools/call" not in str(exc.value) and ORDERS_URN not in str(exc.value)

    def test_endpoint_absent_from_error(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_copy(update={"endpoint_url": "https://other.example.com/mcp"})
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), session=bad_session)
        assert "other.example.com" not in str(exc.value)

    def test_token_absent_from_error(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_copy(update={"endpoint_url": "https://other.example.com/mcp"})
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), session=bad_session)
        assert "test-token" not in str(exc.value)

    def test_session_absent_from_error(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_copy(update={"endpoint_url": "https://other.example.com/mcp"})
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(), session=bad_session)
        assert "session-1" not in str(exc.value)

    def test_exception_repr_absent(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(structured={"result": []}))
        assert "Traceback" not in str(exc.value) and "0x" not in str(exc.value)

    def test_parser_errors_non_retryable(self) -> None:
        with pytest.raises(DataHubEntityMetadataExecutionError) as exc:
            run(structured_response(structured={"result": []}))
        assert exc.value.retryable is False

    def test_transient_transport_classification_preserved(self) -> None:
        transport = RaisingTransport(DataHubMCPProtocolError("timeout", "DataHub MCP request timed out.", retryable=True))
        with pytest.raises(DataHubMCPProtocolError) as exc:
            run(structured_response(), transport=transport)
        assert exc.value.retryable is True and transport.calls == [1]

    def test_no_broad_exception_swallowing(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_execution.py").read_text(encoding="utf-8")
        assert "except Exception" not in source


class TestScopeRegression:
    def test_no_list_schema_fields_execution(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_execution.py").read_text(encoding="utf-8")
        assert "list_schema_fields" not in source
        _, transport = run(structured_response())
        assert b"list_schema_fields" not in transport.calls[0][0]

    def test_no_get_lineage(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_execution.py").read_text(encoding="utf-8")
        assert "get_lineage" not in source

    def test_no_search_execution(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_execution.py").read_text(encoding="utf-8")
        assert "execute_datahub_search" not in source

    def test_no_tools_list(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_execution.py").read_text(encoding="utf-8")
        assert "tools/list" not in source

    def test_no_initialize(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_execution.py").read_text(encoding="utf-8")
        assert "initialize" not in source

    def test_no_mutation_tool(self) -> None:
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["params"]["name"] == "get_entities"

    def test_no_tasks(self) -> None:
        _, transport = run(structured_response())
        assert b"task" not in transport.calls[0][0]

    def test_no_persistence(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_execution.py").read_text(encoding="utf-8")
        assert "persistence" not in source

    def test_no_deepseek(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_execution.py").read_text(encoding="utf-8")
        assert "DeepSeek" not in source

    def test_no_risk(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_execution.py").read_text(encoding="utf-8")
        assert "risk" not in source

    def test_no_validation(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_execution.py").read_text(encoding="utf-8")
        assert "validation" not in source

    def test_no_fastapi_integration(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_execution.py").read_text(encoding="utf-8")
        assert "FastAPI" not in source and "APIRouter" not in source

    def test_no_live_network(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_execution.py").read_text(encoding="utf-8")
        for token in ("import requests", "import httpx", "import aiohttp", "urllib", "http.client", "os.environ", "json_repair"):
            assert token not in source

    def test_protocol_remains_2025_11_25(self) -> None:
        _, transport = run(structured_response())
        assert transport.calls[0][2] == "2025-11-25"

    def test_openapi_route_count_remains_exactly_six(self) -> None:
        routes_dir = Path(__file__).parents[1].joinpath("app/api/routes")
        paths: set[tuple[str, str]] = set()
        for path in sorted(routes_dir.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            for match in re.finditer(r"@router\.(get|post)\(\s*\n\s*\"([^\"]+)\"", source):
                paths.add((match.group(1), match.group(2)))
        assert len(paths) == 6
        assert paths == {
            ("get", "/health"),
            ("get", "/ready"),
            ("post", "/changes/intake"),
            ("post", "/risk/evaluate"),
            ("post", "/runs/analyze"),
            ("post", "/validations/execute"),
        }

    def test_execution_signature_has_no_transport_override(self) -> None:
        params = set(inspect.signature(execute_datahub_get_entities).parameters)
        assert params == {"config", "session", "discovery", "binding", "argument_plan", "search_execution", "transport"}
