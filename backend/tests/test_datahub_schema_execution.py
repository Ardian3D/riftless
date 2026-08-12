from __future__ import annotations

import hashlib
import inspect
import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.integrations.datahub.asset_resolution import DataHubAssetResolutionSubject, resolve_datahub_asset_candidate
from app.integrations.datahub.config import DATAHUB_MCP_PROTOCOL_VERSION, load_datahub_mcp_config
from app.integrations.datahub.entity_execution import (
    DataHubDatasetEntityMetadata,
    DataHubEntityMetadataExecutionResult,
)
from app.integrations.datahub.entity_schema_contract import (
    DataHubEntitySchemaContext,
    DataHubEntitySchemaToolDiscoveryBundle,
    DataHubListSchemaFieldsArgumentPlan,
    DataHubListSchemaFieldsSchemaContract,
    bind_datahub_entity_schema_context,
    build_datahub_list_schema_fields_argument_plan,
    build_datahub_list_schema_fields_tools_call_request,
    discover_datahub_entity_schema_tool_bundle,
    serialize_datahub_list_schema_fields_tools_call_request,
)
from app.integrations.datahub.initialization import DataHubMCPSession
from app.integrations.datahub.mcp_protocol import DataHubMCPProtocolError, serialize_jsonrpc
from app.integrations.datahub.schema_execution import (
    DataHubAffectedFieldObservation,
    DataHubDatasetSchemaSlice,
    DataHubSchemaFieldsExecutionError,
    DataHubSchemaFieldsExecutionResult,
    execute_datahub_list_schema_fields,
)
from app.integrations.datahub.search_contract import DataHubReadToolDiscoveryBundle
from app.integrations.datahub.search_execution import DataHubDatasetSearchRecord, DataHubSearchExecutionResult
from app.integrations.datahub.tool_discovery import CATALOG_VERSION, READ_TOOL_ORDER, DataHubReadToolCatalog
from app.integrations.datahub.transport import DataHubMCPHTTPResponse

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
        raise AssertionError("F8.3C3 must not send notifications")


class RaisingTransport:
    def __init__(self, error: DataHubMCPProtocolError):
        self.error = error
        self.calls = []

    def post_request(self, body: bytes, *, session_id: str | None, protocol_version: str | None):
        self.calls.append(1)
        raise self.error

    def post_notification(self, body: bytes, *, session_id: str | None, protocol_version: str):
        raise AssertionError("F8.3C3 must not send notifications")


def cfg_session() -> tuple[object, DataHubMCPSession]:
    config = load_datahub_mcp_config({"DATAHUB_MCP_URL": ENDPOINT, "DATAHUB_TOKEN": "test-token"})
    session = DataHubMCPSession(endpoint_url=ENDPOINT, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION, server_name="DataHub", server_version="1", tools_supported=True, session_id="session-1")
    return config, session


def discover():
    config, session = cfg_session()
    transport = FakeTransport([page(required_tools())])
    return discover_datahub_entity_schema_tool_bundle(config=config, session=session, transport=transport), transport


def subject(name: str = "orders", column: str = "customer_id") -> DataHubAssetResolutionSubject:
    return DataHubAssetResolutionSubject(platform="snowflake", database="analytics", schema_name="core", table_name=name, affected_column=column)


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


def entity_execution_result(context: DataHubEntitySchemaContext) -> DataHubEntityMetadataExecutionResult:
    return DataHubEntityMetadataExecutionResult(
        request_id=context.get_entities_request_id,
        next_request_id=context.list_schema_fields_request_id,
        entity_request_fingerprint="a" * 64,
        input_schema_fingerprint=context.discovery.get_entities_contract.input_schema_fingerprint,
        dataset_urn=context.dataset_urn,
        metadata=DataHubDatasetEntityMetadata(dataset_urn=context.dataset_urn),
    )


def c3_setup(*, urn: str = ORDERS_URN, name: str = "orders", column: str = "customer_id"):
    bundle, _ = discover()
    config, session = cfg_session()
    search_exec = search_execution(bundle, records=(record(urn, name),))
    subj = subject(name, column)
    resolution = resolve_datahub_asset_candidate(subject=subj, search_result=search_exec)
    context = bind_datahub_entity_schema_context(subject=subj, resolution=resolution, search_execution=search_exec, discovery=bundle)
    schema_plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=bundle.list_schema_fields_contract)
    entity_result = entity_execution_result(context)
    return config, session, bundle, search_exec, context, schema_plan, entity_result


def run(response: DataHubMCPHTTPResponse, *, config=None, session=None, discovery=None, binding=None, argument_plan=None, search_execution=None, entity_execution=None, transport=None):
    default_config, default_session, bundle, search_exec, context, schema_plan, entity_result = c3_setup()
    transport = transport or FakeTransport([response])
    result = execute_datahub_list_schema_fields(
        config=config if config is not None else default_config,
        session=session if session is not None else default_session,
        discovery=discovery if discovery is not None else bundle,
        binding=binding if binding is not None else context,
        argument_plan=argument_plan if argument_plan is not None else schema_plan,
        search_execution=search_execution if search_execution is not None else search_exec,
        entity_execution=entity_execution if entity_execution is not None else entity_result,
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


def bad_plan(plan: DataHubListSchemaFieldsArgumentPlan, **overrides) -> DataHubListSchemaFieldsArgumentPlan:
    values = {
        "dataset_urn": plan.dataset_urn,
        "affected_column": plan.affected_column,
        "arguments": dict(plan.arguments),
        "input_schema_fingerprint": plan.input_schema_fingerprint,
        "plan_version": "1.0",
    }
    values.update(overrides)
    return DataHubListSchemaFieldsArgumentPlan.model_construct(**values)


def bad_bundle(bundle: DataHubEntitySchemaToolDiscoveryBundle, **overrides) -> DataHubEntitySchemaToolDiscoveryBundle:
    values = {
        "read_discovery": bundle.read_discovery,
        "get_entities_contract": bundle.get_entities_contract,
        "list_schema_fields_contract": bundle.list_schema_fields_contract,
        "bundle_version": "1.0",
    }
    values.update(overrides)
    return DataHubEntitySchemaToolDiscoveryBundle.model_construct(**values)


def bad_entity_result(entity_result: DataHubEntityMetadataExecutionResult, **overrides) -> DataHubEntityMetadataExecutionResult:
    values = {
        "request_id": entity_result.request_id,
        "next_request_id": entity_result.next_request_id,
        "entity_request_fingerprint": entity_result.entity_request_fingerprint,
        "input_schema_fingerprint": entity_result.input_schema_fingerprint,
        "dataset_urn": entity_result.dataset_urn,
        "metadata": entity_result.metadata,
        "result_version": "1.0",
    }
    values.update(overrides)
    return DataHubEntityMetadataExecutionResult.model_construct(**values)


def provider_field(**overrides) -> dict:
    data = {
        "fieldPath": "customer_id",
        "nativeDataType": "string",
        "description": "customer identifier",
        "nullable": True,
        "isPartOfKey": False,
        "type": {"typeName": "string"},
        "globalTags": {"tags": [{"tag": {"urn": "urn:li:tag:golden", "name": "golden"}}]},
        "glossaryTerms": {"terms": [{"term": {"urn": "urn:li:glossaryTerm:pii", "name": "pii"}}]},
        "extraProp": "ignored",
    }
    data.update(overrides)
    return data


_UNSET = object()


def schema_payload(*, fields: list[dict] | None = None, urn: str = ORDERS_URN, total_fields: int | None = None, returned: int | None = None, remaining_count: int | None = None, matching_count: object = _UNSET, offset: int = 0) -> dict:
    fields = [provider_field()] if fields is None else fields
    total = len(fields) if total_fields is None else total_fields
    returned = len(fields) if returned is None else returned
    remaining = total - returned if remaining_count is None else remaining_count
    matching = len(fields) if matching_count is _UNSET else matching_count
    return {
        "urn": urn,
        "fields": fields,
        "totalFields": total,
        "returned": returned,
        "remainingCount": remaining,
        "matchingCount": matching,
        "offset": offset,
    }


def mcp_response(*, content: list[dict] | None = None, result_dict: dict | None = None, is_error: object = False, response_id: int = 5) -> DataHubMCPHTTPResponse:
    envelope: dict = {"content": content if content is not None else [{"type": "text", "text": "ignored"}]}
    if is_error is not None:
        envelope["isError"] = is_error
    if result_dict:
        envelope.update(result_dict)
    body = json.dumps({"jsonrpc": "2.0", "id": response_id, "result": envelope}).encode()
    return DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, body)


def structured_response(payload: dict | None = None, *, content: list[dict] | None = None, structured: object = None, is_error: object = False) -> DataHubMCPHTTPResponse:
    return mcp_response(content=content, result_dict={"structuredContent": structured if structured is not None else (schema_payload() if payload is None else payload)}, is_error=is_error)


def text_response(payload: dict | None = None, *, text: str | None = None, is_error: object = False) -> DataHubMCPHTTPResponse:
    return mcp_response(content=[{"type": "text", "text": text if text is not None else json.dumps(schema_payload() if payload is None else payload)}], is_error=is_error)


class TestPreflight:
    def test_valid_c3_context_accepted(self) -> None:
        result, transport = run(structured_response())
        assert isinstance(result, DataHubSchemaFieldsExecutionResult)
        assert len(transport.calls) == 1

    def test_endpoint_mismatch_zero_calls(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_copy(update={"endpoint_url": "https://other.example.com/mcp"})
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), session=bad_session, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_protocol_mismatch_zero_calls(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_construct(endpoint_url=ENDPOINT, protocol_version="2024-11-05", server_name="DataHub", server_version="1", tools_supported=True, session_id="session-1")
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), session=bad_session, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_tools_unsupported_zero_calls(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_copy(update={"tools_supported": False})
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), session=bad_session, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_catalog_unready_zero_calls(self) -> None:
        _, _, bundle, _, _, _, _ = c3_setup()
        bad_catalog = DataHubReadToolCatalog.model_construct(tools=bundle.read_discovery.catalog.tools, all_required_tools_available=False, annotation_verification_complete=False, catalog_version=CATALOG_VERSION)
        bad_read_discovery = DataHubReadToolDiscoveryBundle.model_construct(catalog=bad_catalog, search_contract=bundle.read_discovery.search_contract, next_request_id=bundle.read_discovery.next_request_id, bundle_version="1.0")
        unready = bad_bundle(bundle, read_discovery=bad_read_discovery)
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), discovery=unready, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_schema_capability_fingerprint_mismatch_zero_calls(self) -> None:
        _, _, bundle, _, _, _, _ = c3_setup()
        bad_contract = DataHubListSchemaFieldsSchemaContract.model_construct(input_schema_fingerprint="0" * 64, urn_supported=True, keywords_supported=True, limit_50_supported=True, offset_zero_supported=True, contract_version="1.0")
        mismatched = bad_bundle(bundle, list_schema_fields_contract=bad_contract)
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), discovery=mismatched, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_plan_fingerprint_mismatch_zero_calls(self) -> None:
        _, _, _, _, context, plan, _ = c3_setup()
        bad = bad_plan(plan, input_schema_fingerprint="0" * 64)
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), binding=context, argument_plan=bad, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_dataset_mismatch_zero_calls(self) -> None:
        _, _, _, _, context, plan, _ = c3_setup()
        bad = bad_plan(plan, dataset_urn=CUSTOMERS_URN, arguments={"urn": CUSTOMERS_URN, "keywords": ("customer_id",), "limit": 50, "offset": 0})
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), binding=context, argument_plan=bad, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_c2_dataset_mismatch_zero_calls(self) -> None:
        _, _, _, _, context, plan, entity_result = c3_setup()
        bad_entity = bad_entity_result(entity_result, dataset_urn=CUSTOMERS_URN)
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), binding=context, argument_plan=plan, entity_execution=bad_entity, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_affected_column_mismatch_zero_calls(self) -> None:
        _, _, _, _, context, plan, _ = c3_setup()
        bad = bad_plan(plan, affected_column="other_col", arguments={"urn": ORDERS_URN, "keywords": ("other_col",), "limit": 50, "offset": 0})
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), binding=context, argument_plan=bad, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_keyword_plan_mismatch_zero_calls(self) -> None:
        _, _, _, _, context, plan, _ = c3_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "keywords": ("other_col",), "limit": 50, "offset": 0})
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), binding=context, argument_plan=bad, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_limit_not_50_zero_calls(self) -> None:
        _, _, _, _, context, plan, _ = c3_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "keywords": ("customer_id",), "limit": 10, "offset": 0})
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), binding=context, argument_plan=bad, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_offset_not_zero_zero_calls(self) -> None:
        _, _, _, _, context, plan, _ = c3_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "keywords": ("customer_id",), "limit": 50, "offset": 50})
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), binding=context, argument_plan=bad, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_request_id_mismatch_zero_calls(self) -> None:
        _, _, _, _, context, plan, entity_result = c3_setup()
        bad_entity = bad_entity_result(entity_result, next_request_id=9)
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), binding=context, argument_plan=plan, entity_execution=bad_entity, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_platform_mismatch_zero_calls(self) -> None:
        _, _, _, _, context, plan, entity_result = c3_setup()
        postgres_subject = DataHubAssetResolutionSubject(platform="postgres", database="analytics", schema_name="core", table_name="orders", affected_column="customer_id")
        bad = bad_context(context, subject=postgres_subject)
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), binding=bad, argument_plan=plan, entity_execution=entity_result, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls

    def test_oversized_request_zero_calls(self) -> None:
        _, _, _, _, context, plan, _ = c3_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "keywords": ("x" * 70_000,), "limit": 50, "offset": 0})
        transport = FakeTransport([structured_response()])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(), binding=context, argument_plan=bad, transport=transport)
        assert exc.value.code == "schema_execution_context_mismatch" and not transport.calls


class TestExecution:
    def test_valid_execution_exactly_one_post_request(self) -> None:
        _, transport = run(structured_response())
        assert len(transport.calls) == 1

    def test_method_exact_tools_call(self) -> None:
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["method"] == "tools/call"

    def test_tool_exact_list_schema_fields(self) -> None:
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["params"]["name"] == "list_schema_fields"

    def test_exact_planned_urn(self) -> None:
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["params"]["arguments"]["urn"] == ORDERS_URN

    def test_exact_one_keyword(self) -> None:
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["params"]["arguments"]["keywords"] == ["customer_id"]

    def test_exact_limit_50(self) -> None:
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["params"]["arguments"]["limit"] == 50

    def test_exact_offset_zero(self) -> None:
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["params"]["arguments"]["offset"] == 0

    def test_exact_request_id(self) -> None:
        _, _, _, _, context, _, entity_result = c3_setup()
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["id"] == context.list_schema_fields_request_id == entity_result.next_request_id

    def test_canonical_bytes_sent(self) -> None:
        _, _, bundle, _, context, plan, _ = c3_setup()
        _, transport = run(structured_response())
        expected = serialize_datahub_list_schema_fields_tools_call_request(context=context, contract=bundle.list_schema_fields_contract, argument_plan=plan)
        assert transport.calls[0][0] == expected
        assert transport.calls[0][0] == serialize_jsonrpc(build_datahub_list_schema_fields_tools_call_request(context=context, contract=bundle.list_schema_fields_contract, argument_plan=plan))

    def test_protocol_session_auth_reused(self) -> None:
        _, transport = run(structured_response())
        assert transport.calls[0][1] == "session-1"
        assert transport.calls[0][2] == DATAHUB_MCP_PROTOCOL_VERSION
        assert b"test-token" not in transport.calls[0][0]

    def test_no_retry(self) -> None:
        _, transport = run(structured_response())
        assert len(transport.calls) == 1

    def test_no_second_call(self) -> None:
        _, transport = run(structured_response())
        assert len(transport.calls) == 1

    def test_no_get_entities(self) -> None:
        _, transport = run(structured_response())
        assert b"get_entities" not in transport.calls[0][0]

    def test_no_get_lineage(self) -> None:
        _, transport = run(structured_response())
        assert b"get_lineage" not in transport.calls[0][0]

    def test_no_search_execution(self) -> None:
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["params"]["name"] == "list_schema_fields"

    def test_no_tools_list(self) -> None:
        _, transport = run(structured_response())
        assert b"tools/list" not in transport.calls[0][0]

    def test_no_initialize(self) -> None:
        _, transport = run(structured_response())
        assert b"initialize" not in transport.calls[0][0]


class TestFingerprint:
    def test_deterministic_fingerprint(self) -> None:
        first, _ = run(structured_response())
        second, _ = run(structured_response())
        assert first.schema_request_fingerprint == second.schema_request_fingerprint

    def test_64_lowercase_hex(self) -> None:
        result, _ = run(structured_response())
        assert len(result.schema_request_fingerprint) == 64
        assert re.fullmatch(r"[0-9a-f]{64}", result.schema_request_fingerprint)

    def test_request_change_changes_fingerprint(self) -> None:
        first, _ = run(structured_response())
        config, session, bundle, search_exec, context, plan, entity_result = c3_setup(urn=CUSTOMERS_URN, name="customers")
        transport = FakeTransport([structured_response(schema_payload(urn=CUSTOMERS_URN, fields=[provider_field(fieldPath="customer_id")]))])
        second = execute_datahub_list_schema_fields(config=config, session=session, discovery=bundle, binding=context, argument_plan=plan, search_execution=search_exec, entity_execution=entity_result, transport=transport)
        assert first.schema_request_fingerprint != second.schema_request_fingerprint

    def test_endpoint_excluded(self) -> None:
        result, transport = run(structured_response())
        assert ENDPOINT.encode() not in transport.calls[0][0]
        assert "datahub.example.com" not in result.schema_request_fingerprint

    def test_token_excluded(self) -> None:
        result, transport = run(structured_response())
        assert b"test-token" not in transport.calls[0][0]
        assert "test-token" not in result.schema_request_fingerprint

    def test_session_excluded(self) -> None:
        result, transport = run(structured_response())
        assert b"session-1" not in transport.calls[0][0]
        assert "session-1" not in result.schema_request_fingerprint

    def test_response_excluded(self) -> None:
        result, transport = run(structured_response())
        assert result.schema_request_fingerprint == hashlib.sha256(transport.calls[0][0]).hexdigest()


class TestCallToolResult:
    def test_valid_result_accepted(self) -> None:
        result, _ = run(structured_response())
        assert result.schema_slice.dataset_urn == ORDERS_URN

    def test_is_error_absent_false(self) -> None:
        response = mcp_response(result_dict={"structuredContent": schema_payload()}, is_error=None)
        result, _ = run(response)
        assert result.dataset_urn == ORDERS_URN

    def test_is_error_false_accepted(self) -> None:
        result, _ = run(structured_response(is_error=False))
        assert result.dataset_urn == ORDERS_URN

    def test_is_error_true_safe_failure(self) -> None:
        transport = FakeTransport([structured_response(is_error=True)])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(is_error=True), transport=transport)
        assert exc.value.code == "schema_tool_execution_failed" and len(transport.calls) == 1

    def test_non_bool_is_error_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(is_error="true"))
        assert exc.value.code == "invalid_schema_tool_result"

    def test_content_required(self) -> None:
        response = DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, json.dumps({"jsonrpc": "2.0", "id": 5, "result": {"structuredContent": schema_payload()}}).encode())
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_schema_tool_result"

    def test_content_must_list(self) -> None:
        response = mcp_response(content={"not": "a list"}, result_dict={"structuredContent": schema_payload()})
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_schema_tool_result"

    def test_content_block_max(self) -> None:
        response = structured_response(content=[{"type": "text", "text": "x"} for _ in range(9)])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "unsupported_schema_content"

    def test_text_accepted(self) -> None:
        result, _ = run(text_response())
        assert result.dataset_urn == ORDERS_URN

    def test_unsupported_content_rejected(self) -> None:
        response = structured_response(content=[{"type": "image", "data": "x"}])
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "unsupported_schema_content"

    def test_utf8_enforced(self) -> None:
        response = text_response(text="\ud800")
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "unsupported_schema_content"

    def test_null_byte_rejected(self) -> None:
        response = text_response(text='{"urn": "x\x00"}')
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "schema_content_too_large"

    def test_individual_and_combined_bounds(self) -> None:
        big = "x" * 262_145
        response = mcp_response(content=[{"type": "text", "text": big}], result_dict={"structuredContent": schema_payload()})
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "schema_content_too_large"
        combined = mcp_response(content=[{"type": "text", "text": "x" * 200_000}, {"type": "text", "text": "y" * 200_000}], result_dict={"structuredContent": schema_payload()})
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(combined)
        assert exc.value.code == "schema_content_too_large"

    def test_meta_ignored(self) -> None:
        result, _ = run(mcp_response(result_dict={"structuredContent": schema_payload(), "_meta": {"progressToken": "t"}}))
        assert result.dataset_urn == ORDERS_URN

    def test_unknown_result_fields_ignored(self) -> None:
        result, _ = run(mcp_response(result_dict={"structuredContent": schema_payload(), "unknown": {"x": 1}}))
        assert result.dataset_urn == ORDERS_URN

    def test_raw_tool_result_absent_from_normalized_output(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        for token in ("structuredContent", "isError", "CallToolResult", "content"):
            assert token not in dumped


class TestPayloadSource:
    def test_direct_structured_content_object_accepted(self) -> None:
        result, _ = run(structured_response())
        assert result.schema_slice.provider_total_fields == 1

    def test_structured_content_priority(self) -> None:
        response = mcp_response(content=[{"type": "text", "text": "this is not json"}], result_dict={"structuredContent": schema_payload()})
        result, _ = run(response)
        assert result.dataset_urn == ORDERS_URN

    def test_text_not_reparsed_when_structured_exists(self) -> None:
        response = mcp_response(content=[{"type": "text", "text": "this is not json"}], result_dict={"structuredContent": schema_payload()})
        result, _ = run(response)
        assert result.schema_slice.fields[0].field_path == "customer_id"

    def test_structured_content_must_object(self) -> None:
        response = mcp_response(result_dict={"structuredContent": [1, 2]})
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_schema_result_payload"

    def test_structured_size_bound(self) -> None:
        payload = schema_payload()
        payload["blob"] = "x" * 524_300
        response = mcp_response(result_dict={"structuredContent": payload})
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "schema_content_too_large"

    def test_strict_json_object_fallback_accepted(self) -> None:
        result, _ = run(text_response())
        assert result.schema_slice.fields[0].field_path == "customer_id"

    def test_fallback_top_level_array_rejected(self) -> None:
        response = text_response(text=json.dumps([schema_payload()]))
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_schema_result_payload"

    def test_primitive_rejected(self) -> None:
        response = text_response(text='"just a string"')
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_schema_result_payload"

    def test_markdown_rejected(self) -> None:
        response = text_response(text="```json\n" + json.dumps(schema_payload()) + "\n```")
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_schema_result_payload"

    def test_prose_prefix_suffix_rejected(self) -> None:
        response = text_response(text="result " + json.dumps(schema_payload()))
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_schema_result_payload"
        response = text_response(text=json.dumps(schema_payload()) + " done")
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_schema_result_payload"

    def test_multiple_docs_rejected(self) -> None:
        response = text_response(text="{} {}")
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_schema_result_payload"

    def test_duplicate_keys_rejected(self) -> None:
        response = text_response(text='{"urn": "x", "urn": "y"}')
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_schema_result_payload"

    def test_nan_infinity_rejected(self) -> None:
        for text in ('{"urn": NaN}', '{"urn": Infinity}', '{"urn": -Infinity}'):
            with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
                run(text_response(text=text))
            assert exc.value.code == "invalid_schema_result_payload"

    def test_null_byte_rejected(self) -> None:
        response = text_response(text='{"urn": "x\x00"}')
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "schema_content_too_large"

    def test_malformed_json_rejected(self) -> None:
        response = text_response(text="{")
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_schema_result_payload"


class TestTopLevelAdapter:
    def test_valid_zero_field_result(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[])))
        assert result.schema_slice.fields == ()
        assert result.schema_slice.provider_returned == 0

    def test_valid_one_field_result(self) -> None:
        result, _ = run(structured_response())
        assert len(result.schema_slice.fields) == 1

    def test_valid_50_field_result(self) -> None:
        fields = [provider_field(fieldPath=f"col{i}") for i in range(50)]
        result, _ = run(structured_response(schema_payload(fields=fields)))
        assert len(result.schema_slice.fields) == 50

    def test_all_required_top_level_fields_required(self) -> None:
        payload = schema_payload()
        for key in ("urn", "fields", "totalFields", "returned", "remainingCount", "matchingCount", "offset"):
            bad = {k: v for k, v in payload.items() if k != key}
            with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
                run(structured_response(bad))
            assert exc.value.code == "missing_schema_result_payload"

    def test_returned_upper_bound(self) -> None:
        payload = schema_payload(returned=60)
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_schema_result_payload"

    def test_fields_upper_bound(self) -> None:
        fields = [provider_field(fieldPath=f"col{i}") for i in range(51)]
        payload = schema_payload(fields=fields, total_fields=51, returned=51, remaining_count=0)
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_schema_result_payload"

    def test_returned_equals_len_fields(self) -> None:
        payload = schema_payload(fields=[provider_field(), provider_field(fieldPath="other")], returned=1, total_fields=2)
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "schema_result_count_mismatch"

    def test_total_fields_gte_returned(self) -> None:
        payload = schema_payload(total_fields=0, returned=1, remaining_count=0)
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "schema_result_count_mismatch"

    def test_remaining_count_exact_invariant(self) -> None:
        payload = schema_payload(remaining_count=5)
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "schema_result_count_mismatch"

    def test_matching_count_le_total(self) -> None:
        payload = schema_payload(matching_count=5, total_fields=1)
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "schema_result_count_mismatch"

    def test_bool_as_int_rejected(self) -> None:
        payload = schema_payload()
        payload["returned"] = True
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_schema_result_payload"

    def test_negative_counts_rejected(self) -> None:
        payload = schema_payload(total_fields=-1)
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_schema_result_payload"

    def test_total_upper_bound(self) -> None:
        payload = schema_payload(total_fields=1_000_001)
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_schema_result_payload"

    def test_offset_must_zero(self) -> None:
        payload = schema_payload(offset=1)
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_schema_result_payload"

    def test_unknown_top_level_fields_ignored(self) -> None:
        payload = schema_payload()
        payload["unknownTopLevel"] = {"x": 1}
        result, _ = run(structured_response(payload))
        assert result.dataset_urn == ORDERS_URN
        assert "unknownTopLevel" not in json.dumps(result.model_dump())

    def test_raw_provider_object_discarded(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "totalFields" not in dumped and "matchingCount" not in dumped


class TestIdentity:
    def test_matching_returned_dataset_urn_accepted(self) -> None:
        result, _ = run(structured_response())
        assert result.dataset_urn == ORDERS_URN

    def test_missing_urn_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(urn=None)))
        assert exc.value.code == "schema_result_identity_mismatch"

    def test_malformed_urn_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(urn="not-a-urn")))
        assert exc.value.code == "schema_result_identity_mismatch"

    def test_non_dataset_urn_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(urn="urn:li:dashboard:dash")))
        assert exc.value.code == "schema_result_identity_mismatch"

    def test_different_urn_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(urn=CUSTOMERS_URN)))
        assert exc.value.code == "schema_result_identity_mismatch"

    def test_same_name_different_urn_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(urn=CUSTOMERS_URN)))
        assert exc.value.code == "schema_result_identity_mismatch"

    def test_wrong_platform_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(urn=BIGQUERY_ORDERS_URN)))
        assert exc.value.code == "schema_result_identity_mismatch"

    def test_identity_errors_hide_urns(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(urn=CUSTOMERS_URN)))
        assert "urn:li" not in str(exc.value) and ORDERS_URN not in str(exc.value)


class TestFieldNormalization:
    def test_valid_field_path(self) -> None:
        result, _ = run(structured_response())
        assert result.schema_slice.fields[0].field_path == "customer_id"

    def test_missing_field_path_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=[provider_field() | {"fieldPath": None}])))
        assert exc.value.code == "invalid_schema_field"

    def test_blank_field_path_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=[provider_field(fieldPath="   ")])))
        assert exc.value.code == "invalid_schema_field"

    def test_oversized_field_path_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=[provider_field(fieldPath="x" * 600)])))
        assert exc.value.code == "invalid_schema_field"

    def test_null_control_field_path_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=[provider_field(fieldPath="bad\x00name")])))
        assert exc.value.code == "invalid_schema_field"

    def test_duplicate_normalized_field_path_rejected(self) -> None:
        fields = [provider_field(fieldPath="customer_id"), provider_field(fieldPath="CUSTOMER_ID")]
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=fields, total_fields=2, returned=2)))
        assert exc.value.code == "duplicate_schema_field_path"

    def test_optional_native_datatype(self) -> None:
        result, _ = run(structured_response())
        assert result.schema_slice.fields[0].native_type == "string"

    def test_bounded_native_datatype(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=[provider_field(nativeDataType="x" * 200)])))
        assert exc.value.code == "invalid_schema_field"

    def test_optional_description(self) -> None:
        result, _ = run(structured_response())
        assert result.schema_slice.fields[0].description == "customer identifier"

    def test_bounded_control_safe_description(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=[provider_field(description="x" * 3000)])))
        assert exc.value.code == "invalid_schema_field"
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=[provider_field(description="bad\x00desc")])))
        assert exc.value.code == "invalid_schema_field"

    def test_nullable_real_bool(self) -> None:
        result, _ = run(structured_response())
        assert result.schema_slice.fields[0].nullable is True

    def test_nullable_non_bool_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=[provider_field(nullable="true")])))
        assert exc.value.code == "invalid_schema_field"

    def test_key_flag_real_bool(self) -> None:
        result, _ = run(structured_response())
        assert result.schema_slice.fields[0].field_path == "customer_id"

    def test_key_flag_non_bool_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=[provider_field(isPartOfKey="true")])))
        assert exc.value.code == "invalid_schema_field"

    def test_tags_normalized(self) -> None:
        result, _ = run(structured_response())
        assert result.schema_slice.fields[0].tags[0].urn == "urn:li:tag:golden"

    def test_terms_normalized(self) -> None:
        result, _ = run(structured_response())
        assert result.schema_slice.fields[0].glossary_terms[0].urn == "urn:li:glossaryTerm:pii"

    def test_malformed_normalized_metadata_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=[provider_field(globalTags={"tags": [{"tag": {"urn": 5}}]})])))
        assert exc.value.code == "invalid_schema_field"

    def test_unknown_field_properties_discarded(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "extraProp" not in dumped and "ignored" not in dumped

    def test_raw_type_object_discarded(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "typeName" not in dumped and '"type"' not in dumped

    def test_sql_like_provider_values_never_executed(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(nativeDataType="select * from x", description="delete from y")])))
        assert result.schema_slice.fields[0].native_type == "select * from x"
        assert result.schema_slice.fields[0].description == "delete from y"


class TestAffectedFieldObservation:
    def test_exact_field_path_observed(self) -> None:
        result, _ = run(structured_response())
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.OBSERVED_EXACT
        assert result.schema_slice.affected_field.field_path == "customer_id"

    def test_exact_match_may_appear_first(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(), provider_field(fieldPath="other")], total_fields=2, returned=2)))
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.OBSERVED_EXACT

    def test_exact_match_may_appear_last(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other"), provider_field()], total_fields=2, returned=2)))
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.OBSERVED_EXACT

    def test_provider_position_does_not_affect_observation(self) -> None:
        first = run(structured_response(schema_payload(fields=[provider_field(), provider_field(fieldPath="other")], total_fields=2, returned=2)))[0]
        last = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other"), provider_field()], total_fields=2, returned=2)))[0]
        assert first.schema_slice.affected_field_observation is last.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.OBSERVED_EXACT

    def test_substring_only_does_not_count_exact(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(fieldPath="customer")])))
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED

    def test_description_only_hit_does_not_count(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other", description="customer_id")])))
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED

    def test_tag_only_hit_does_not_count(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other", globalTags={"tags": [{"tag": {"urn": "urn:li:tag:customer_id", "name": "customer_id"}}]})])))
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED

    def test_term_only_hit_does_not_count(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other", glossaryTerms={"terms": [{"term": {"urn": "urn:li:glossaryTerm:customer_id", "name": "customer_id"}}]})])))
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED

    def test_case_normalization_per_locked_rule(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(fieldPath="CUSTOMER_ID")])))
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.OBSERVED_EXACT

    def test_no_exact_match_not_observed(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other_col")])))
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED
        assert result.schema_slice.affected_field is None

    def test_returned_greater_than_zero_does_not_imply_observed(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other")])))
        assert result.schema_slice.provider_returned == 1
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED

    def test_matching_count_greater_than_zero_does_not_imply_observed(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other")], matching_count=1)))
        assert result.schema_slice.provider_matching_count == 1
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED

    def test_first_provider_field_does_not_automatically_win(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other"), provider_field()], total_fields=2, returned=2)))
        assert result.schema_slice.affected_field.field_path == "customer_id"

    def test_reversed_fields_preserve_observation_state(self) -> None:
        forward = run(structured_response(schema_payload(fields=[provider_field(), provider_field(fieldPath="other")], total_fields=2, returned=2)))[0]
        reversed_result = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other"), provider_field()], total_fields=2, returned=2)))[0]
        assert forward.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.OBSERVED_EXACT
        assert reversed_result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.OBSERVED_EXACT

    def test_selected_affected_field_invariant_under_permutation(self) -> None:
        forward = run(structured_response(schema_payload(fields=[provider_field(), provider_field(fieldPath="other")], total_fields=2, returned=2)))[0]
        reversed_result = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other"), provider_field()], total_fields=2, returned=2)))[0]
        assert forward.schema_slice.affected_field.field_path == "customer_id"
        assert reversed_result.schema_slice.affected_field.field_path == "customer_id"


class TestAbsenceSemantics:
    def test_not_observed_has_null_affected_field(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other")])))
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED
        assert result.schema_slice.affected_field is None

    def test_not_observed_may_coexist_with_remaining_count(self) -> None:
        fields = [provider_field(fieldPath=f"col{i}") for i in range(20)]
        result, _ = run(structured_response(schema_payload(fields=fields, total_fields=120, returned=20, remaining_count=100, matching_count=20)))
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED
        assert result.schema_slice.provider_remaining_count == 100

    def test_not_observed_does_not_trigger_risk(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other")])))
        assert "risk" not in json.dumps(result.model_dump())

    def test_observed_exact_does_not_trigger_validation_success(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "pass" not in dumped and "valid" not in dumped and "safe" not in dumped

    def test_no_allow_warn_block_call(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "ALLOW" not in dumped and "WARN" not in dumped and "BLOCK" not in dumped


class TestResult:
    def test_exact_execution_result_fields(self) -> None:
        result, _ = run(structured_response())
        assert set(result.model_dump()) == {"request_id", "next_request_id", "schema_request_fingerprint", "input_schema_fingerprint", "dataset_urn", "schema_slice", "result_version"}

    def test_request_id_exact(self) -> None:
        _, _, _, _, context, _, entity_result = c3_setup()
        result, _ = run(structured_response())
        assert result.request_id == context.list_schema_fields_request_id == entity_result.next_request_id

    def test_next_id_equals_request_plus_one(self) -> None:
        result, _ = run(structured_response())
        assert result.next_request_id == result.request_id + 1

    def test_request_fingerprint_valid(self) -> None:
        result, _ = run(structured_response())
        assert re.fullmatch(r"[0-9a-f]{64}", result.schema_request_fingerprint)

    def test_input_schema_fingerprint_preserved(self) -> None:
        _, _, bundle, _, _, plan, _ = c3_setup()
        result, _ = run(structured_response())
        assert result.input_schema_fingerprint == plan.input_schema_fingerprint == bundle.list_schema_fields_contract.input_schema_fingerprint

    def test_dataset_urn_exact(self) -> None:
        result, _ = run(structured_response())
        assert result.dataset_urn == ORDERS_URN

    def test_schema_slice_immutable(self) -> None:
        result, _ = run(structured_response())
        assert result.schema_slice.model_config["frozen"] is True
        with pytest.raises(Exception):
            result.schema_slice.provider_returned = 0

    def test_fields_immutable(self) -> None:
        result, _ = run(structured_response())
        assert isinstance(result.schema_slice.fields, tuple)
        with pytest.raises(TypeError):
            result.schema_slice.fields[0] = result.schema_slice.fields[0]

    def test_result_immutable(self) -> None:
        result, _ = run(structured_response())
        assert result.model_config["frozen"] is True
        with pytest.raises(Exception):
            result.dataset_urn = "changed"

    def test_version_fixed(self) -> None:
        result, _ = run(structured_response())
        assert result.result_version == "1.0"
        assert result.schema_slice.schema_slice_version == "1.0"

    def test_provider_counts_preserved(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field()], total_fields=120, returned=1, remaining_count=119, matching_count=3)))
        assert result.schema_slice.provider_total_fields == 120
        assert result.schema_slice.provider_returned == 1
        assert result.schema_slice.provider_remaining_count == 119
        assert result.schema_slice.provider_matching_count == 3
        assert result.schema_slice.provider_offset == 0

    def test_no_raw_request(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "arguments" not in dumped and "keywords" not in dumped and '"urns"' not in dumped

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

    def test_no_endpoint_token_session(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        for token in ("datahub.example.com", "test-token", "session-1"):
            assert token not in dumped

    def test_no_risk_authority(self) -> None:
        result, _ = run(structured_response())
        assert "risk" not in json.dumps(result.model_dump())

    def test_no_validation_authority(self) -> None:
        result, _ = run(structured_response())
        assert "validation" not in json.dumps(result.model_dump())

    def test_no_deployment_writeback_authority(self) -> None:
        result, _ = run(structured_response())
        dumped = json.dumps(result.model_dump())
        assert "deployment" not in dumped and "writeback" not in dumped and "authority" not in dumped


class TestMatchingCountCompatibility:
    def test_zero_field_payload_with_null_matching_count_accepted(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[], matching_count=None)))
        assert result.schema_slice.provider_total_fields == 0
        assert result.schema_slice.provider_returned == 0

    def test_normalized_matching_count_remains_none(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[], matching_count=None)))
        assert result.schema_slice.provider_matching_count is None

    def test_zero_field_none_is_not_observed(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[], matching_count=None)))
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED

    def test_zero_field_none_affected_field_is_null(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[], matching_count=None)))
        assert result.schema_slice.affected_field is None

    def test_zero_field_payload_with_matching_count_zero_accepted(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[], matching_count=0)))
        assert result.schema_slice.provider_matching_count == 0
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED

    def test_total_fields_positive_with_null_matching_count_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=[provider_field()], matching_count=None)))
        assert exc.value.code == "invalid_schema_result_payload"

    def test_zero_total_with_true_matching_count_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=[], matching_count=True)))
        assert exc.value.code == "invalid_schema_result_payload"

    def test_zero_total_with_false_matching_count_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(fields=[], matching_count=False)))
        assert exc.value.code == "invalid_schema_result_payload"

    def test_integer_matching_count_above_total_rejected(self) -> None:
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(schema_payload(matching_count=5, total_fields=1)))
        assert exc.value.code == "schema_result_count_mismatch"

    def test_missing_matching_count_key_rejected(self) -> None:
        payload = schema_payload(fields=[])
        del payload["matchingCount"]
        with pytest.raises(DataHubSchemaFieldsExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "missing_schema_result_payload"

    def test_null_matching_count_not_converted_to_zero_internally(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[], matching_count=None)))
        assert result.schema_slice.provider_matching_count is None
        assert result.schema_slice.provider_matching_count != 0

    def test_positive_matching_count_without_exact_field_path_not_observed(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[provider_field(fieldPath="other")], matching_count=1)))
        assert result.schema_slice.provider_matching_count == 1
        assert result.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED

    def test_matching_count_never_changes_selected_affected_field(self) -> None:
        zero = run(structured_response(schema_payload(matching_count=0)))[0]
        positive = run(structured_response(schema_payload(matching_count=1)))[0]
        assert zero.schema_slice.affected_field.field_path == "customer_id"
        assert positive.schema_slice.affected_field.field_path == "customer_id"
        assert zero.schema_slice.affected_field_observation is positive.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.OBSERVED_EXACT

    def test_schema_result_immutable_with_optional_matching_count(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[], matching_count=None)))
        assert result.schema_slice.model_config["frozen"] is True
        assert result.model_config["frozen"] is True

    def test_no_risk_or_validation_behavior_introduced(self) -> None:
        result, _ = run(structured_response(schema_payload(fields=[], matching_count=None)))
        dumped = json.dumps(result.model_dump())
        assert "risk" not in dumped and "validation" not in dumped and "BLOCK" not in dumped

    def test_no_extra_mcp_call_introduced(self) -> None:
        _, transport = run(structured_response(schema_payload(fields=[], matching_count=None)))
        assert len(transport.calls) == 1
        assert json.loads(transport.calls[0][0])["params"]["name"] == "list_schema_fields"


class TestMatchingCountModelInvariant:
    def _slice(self, *, total_fields: int, matching_count: object) -> DataHubDatasetSchemaSlice:
        return DataHubDatasetSchemaSlice(
            dataset_urn=ORDERS_URN,
            fields=(),
            provider_total_fields=total_fields,
            provider_returned=0,
            provider_remaining_count=0,
            provider_matching_count=matching_count,
            provider_offset=0,
            affected_field_observation=DataHubAffectedFieldObservation.NOT_OBSERVED,
            affected_field=None,
        )

    def test_zero_total_null_accepted(self) -> None:
        schema_slice = self._slice(total_fields=0, matching_count=None)
        assert schema_slice.provider_matching_count is None

    def test_zero_total_integer_zero_accepted(self) -> None:
        schema_slice = self._slice(total_fields=0, matching_count=0)
        assert schema_slice.provider_matching_count == 0

    def test_null_preserved_as_null(self) -> None:
        assert self._slice(total_fields=0, matching_count=None).provider_matching_count is None

    def test_zero_preserved_as_integer_zero(self) -> None:
        assert self._slice(total_fields=0, matching_count=0).provider_matching_count == 0

    def test_positive_total_null_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._slice(total_fields=1, matching_count=None)

    def test_bool_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._slice(total_fields=0, matching_count=True)
        with pytest.raises(ValidationError):
            self._slice(total_fields=0, matching_count=False)

    def test_integer_above_total_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._slice(total_fields=1, matching_count=2)

    def test_matching_count_never_controls_observation(self) -> None:
        schema_slice = self._slice(total_fields=0, matching_count=None)
        assert schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED
        assert schema_slice.affected_field is None


class TestScopeRegression:
    def test_zero_get_entities_execution(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/schema_execution.py").read_text(encoding="utf-8")
        assert "get_entities" not in source

    def test_zero_get_lineage_execution(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/schema_execution.py").read_text(encoding="utf-8")
        assert "get_lineage" not in source

    def test_zero_search(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/schema_execution.py").read_text(encoding="utf-8")
        assert "execute_datahub_search" not in source

    def test_zero_tools_list(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/schema_execution.py").read_text(encoding="utf-8")
        assert "tools/list" not in source

    def test_zero_initialization(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/schema_execution.py").read_text(encoding="utf-8")
        assert "initialize" not in source

    def test_zero_mutation(self) -> None:
        _, transport = run(structured_response())
        assert json.loads(transport.calls[0][0])["params"]["name"] == "list_schema_fields"

    def test_zero_deepseek(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/schema_execution.py").read_text(encoding="utf-8")
        assert "DeepSeek" not in source

    def test_zero_persistence(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/schema_execution.py").read_text(encoding="utf-8")
        assert "persistence" not in source

    def test_zero_fastapi_integration(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/schema_execution.py").read_text(encoding="utf-8")
        assert "FastAPI" not in source and "APIRouter" not in source

    def test_zero_live_network(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/schema_execution.py").read_text(encoding="utf-8")
        for token in ("import requests", "import httpx", "import aiohttp", "urllib", "http.client", "os.environ", "json_repair", "except Exception", "logging", "print("):
            assert token not in source

    def test_protocol_unchanged(self) -> None:
        _, transport = run(structured_response())
        assert transport.calls[0][2] == "2025-11-25"

    def test_openapi_remains_six(self) -> None:
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

    def test_execution_signature_chain(self) -> None:
        params = set(inspect.signature(execute_datahub_list_schema_fields).parameters)
        assert params == {"config", "session", "discovery", "binding", "argument_plan", "search_execution", "entity_execution", "transport"}
