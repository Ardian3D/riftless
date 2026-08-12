from __future__ import annotations

import hashlib
import inspect
import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.integrations.datahub.asset_resolution import DataHubAssetResolutionSubject, resolve_datahub_asset_candidate
from app.integrations.datahub.column_lineage_execution import (
    DataHubColumnDownstreamTarget,
    DataHubColumnLineageExecutionError,
    DataHubColumnLineageExecutionResult,
    DataHubColumnLineageObservation,
    DataHubColumnLineageSlice,
    execute_datahub_column_lineage,
)
from app.integrations.datahub.config import DATAHUB_MCP_PROTOCOL_VERSION, load_datahub_mcp_config
from app.integrations.datahub.dataset_lineage_execution import (
    DataHubDatasetDownstreamSlice,
    DataHubDatasetLineageExecutionResult,
    DataHubDownstreamObservation,
)
from app.integrations.datahub.entity_execution import DataHubDatasetEntityMetadata, DataHubEntityMetadataExecutionResult
from app.integrations.datahub.entity_schema_contract import (
    DataHubEntitySchemaContext,
    DataHubEntitySchemaToolDiscoveryBundle,
    bind_datahub_entity_schema_context,
)
from app.integrations.datahub.initialization import DataHubMCPSession
from app.integrations.datahub.lineage_contract import (
    DataHubColumnLineageArgumentPlan,
    DataHubGetLineageSchemaContract,
    DataHubLineageContext,
    DataHubLineageToolDiscoveryBundle,
    bind_datahub_lineage_context,
    build_datahub_column_lineage_argument_plan,
    build_datahub_column_lineage_tools_call_request,
    discover_datahub_lineage_tool_bundle,
    serialize_datahub_column_lineage_tools_call_request,
)
from app.integrations.datahub.mcp_protocol import serialize_jsonrpc
from app.integrations.datahub.schema_execution import DataHubAffectedFieldObservation, DataHubDatasetSchemaSlice, DataHubSchemaFieldsExecutionResult
from app.integrations.datahub.search_contract import DataHubReadToolDiscoveryBundle
from app.integrations.datahub.search_execution import DataHubDatasetSearchRecord, DataHubSearchExecutionResult
from app.integrations.datahub.tool_discovery import CATALOG_VERSION, READ_TOOL_ORDER, DataHubReadToolCatalog
from app.integrations.datahub.transport import DataHubMCPHTTPResponse
from app.schemas.datahub_context import DataHubLineageRelation

ENDPOINT = "https://datahub.example.com/mcp"
ORDERS_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.orders,PROD)"
CUSTOMERS_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.customers,PROD)"
TARGET_DATASET_URN = "urn:li:dataset:(urn:li:dataPlatform:postgres,analytics.orders_usage,PROD)"
CROSS_PLATFORM_URN = "urn:li:dataset:(urn:li:dataPlatform:bigquery,analytics.orders_usage,PROD)"

GET_LINEAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "urn": {"type": "string", "maxLength": 1024},
        "column": {"type": "string", "maxLength": 256},
        "upstream": {"type": "boolean"},
        "max_hops": {"type": "integer", "minimum": 1, "maximum": 10},
        "max_results": {"type": "integer", "minimum": 1, "maximum": 100},
        "offset": {"type": "integer", "minimum": 0},
    },
    "required": ["urn"],
}

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


def required_tools() -> list[dict]:
    schemas = {"search": search_schema(), "get_entities": GET_ENTITIES_SCHEMA, "list_schema_fields": LIST_SCHEMA_FIELDS_SCHEMA, "get_lineage": GET_LINEAGE_SCHEMA}
    return [{"name": item.value, "inputSchema": schemas[item.value]} for item in READ_TOOL_ORDER]


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
        raise AssertionError("F8.3D3 must not send notifications")


def cfg_session() -> tuple[object, DataHubMCPSession]:
    config = load_datahub_mcp_config({"DATAHUB_MCP_URL": ENDPOINT, "DATAHUB_TOKEN": "test-token"})
    session = DataHubMCPSession(endpoint_url=ENDPOINT, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION, server_name="DataHub", server_version="1", tools_supported=True, session_id="session-1")
    return config, session


def lineage_discover():
    config, session = cfg_session()
    transport = FakeTransport([page(required_tools())])
    return discover_datahub_lineage_tool_bundle(config=config, session=session, transport=transport), transport


def subject(name: str = "orders", column: str = "customer_id") -> DataHubAssetResolutionSubject:
    return DataHubAssetResolutionSubject(platform="snowflake", database="analytics", schema_name="core", table_name=name, affected_column=column)


def record(urn: str = ORDERS_URN, name: str = "orders", position: int = 0) -> DataHubDatasetSearchRecord:
    return DataHubDatasetSearchRecord(dataset_urn=urn, display_name=name, source_position=position)


def search_execution(bundle, *, records: tuple[DataHubDatasetSearchRecord, ...] | None = None) -> DataHubSearchExecutionResult:
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


def schema_execution_result(context: DataHubEntitySchemaContext, *, observation: DataHubAffectedFieldObservation = DataHubAffectedFieldObservation.NOT_OBSERVED) -> DataHubSchemaFieldsExecutionResult:
    return DataHubSchemaFieldsExecutionResult.model_construct(
        request_id=context.list_schema_fields_request_id,
        next_request_id=context.list_schema_fields_request_id + 1,
        schema_request_fingerprint="b" * 64,
        input_schema_fingerprint=context.discovery.list_schema_fields_contract.input_schema_fingerprint,
        dataset_urn=context.dataset_urn,
        schema_slice=DataHubDatasetSchemaSlice.model_construct(
            dataset_urn=context.dataset_urn, fields=(), provider_total_fields=0, provider_returned=0,
            provider_remaining_count=0, provider_matching_count=None, provider_offset=0,
            affected_field_observation=observation, affected_field=None, schema_slice_version="1.0",
        ),
    )


def dataset_execution_result(ctx: DataHubLineageContext) -> DataHubDatasetLineageExecutionResult:
    return DataHubDatasetLineageExecutionResult.model_construct(
        request_id=ctx.dataset_lineage_request_id,
        next_request_id=ctx.column_lineage_request_id,
        dataset_lineage_request_fingerprint="c" * 64,
        input_schema_fingerprint=ctx.discovery.get_lineage_contract.input_schema_fingerprint,
        source_dataset_urn=ctx.dataset_urn,
        downstream_slice=DataHubDatasetDownstreamSlice.model_construct(
            source_dataset_urn=ctx.dataset_urn, targets=(), downstream_observation=DataHubDownstreamObservation.NOT_OBSERVED,
            provider_total=None, provider_offset=None, provider_returned=None, provider_has_more=None,
            provider_truncated_due_to_token_budget=None, slice_version="1.0",
        ),
    )


def full_setup(*, observation: DataHubAffectedFieldObservation = DataHubAffectedFieldObservation.NOT_OBSERVED, urn: str = ORDERS_URN, name: str = "orders", column: str = "customer_id"):
    lineage_bundle, _ = lineage_discover()
    c1_bundle = lineage_bundle.entity_schema_discovery
    config, session = cfg_session()
    search_exec = search_execution(c1_bundle, records=(record(urn, name),))
    subj = subject(name, column)
    resolution = resolve_datahub_asset_candidate(subject=subj, search_result=search_exec)
    esc = bind_datahub_entity_schema_context(subject=subj, resolution=resolution, search_execution=search_exec, discovery=c1_bundle)
    entity_exec = entity_execution_result(esc)
    schema_exec = schema_execution_result(esc, observation=observation)
    ctx = bind_datahub_lineage_context(subject=subj, resolution=resolution, search_execution=search_exec, entity_execution=entity_exec, schema_execution=schema_exec, entity_schema_context=esc, discovery=lineage_bundle)
    column_plan = build_datahub_column_lineage_argument_plan(context=ctx, contract=lineage_bundle.get_lineage_contract)
    dataset_exec = dataset_execution_result(ctx)
    return config, session, lineage_bundle, ctx, column_plan, dataset_exec, schema_exec


def run(response: DataHubMCPHTTPResponse, *, config=None, session=None, lineage_context=None, column_plan=None, dataset_lineage_execution=None, schema_execution=None, transport=None):
    default_config, default_session, _, ctx, plan, dataset_exec, schema_exec = full_setup()
    transport = transport or FakeTransport([response])
    result = execute_datahub_column_lineage(
        config=config if config is not None else default_config,
        session=session if session is not None else default_session,
        lineage_context=lineage_context if lineage_context is not None else ctx,
        column_plan=column_plan if column_plan is not None else plan,
        dataset_lineage_execution=dataset_lineage_execution if dataset_lineage_execution is not None else dataset_exec,
        schema_execution=schema_execution if schema_execution is not None else schema_exec,
        transport=transport,
    )
    return result, transport


def construct_lineage_ctx(ctx: DataHubLineageContext, **overrides) -> DataHubLineageContext:
    values = {
        "subject": ctx.subject,
        "resolution": ctx.resolution,
        "search_execution": ctx.search_execution,
        "entity_execution": ctx.entity_execution,
        "schema_execution": ctx.schema_execution,
        "entity_schema_context": ctx.entity_schema_context,
        "discovery": ctx.discovery,
        "dataset_urn": ctx.dataset_urn,
        "affected_column": ctx.affected_column,
        "dataset_lineage_request_id": ctx.dataset_lineage_request_id,
        "column_lineage_request_id": ctx.column_lineage_request_id,
        "post_lineage_next_request_id": ctx.post_lineage_next_request_id,
        "binding_version": "1.0",
    }
    values.update(overrides)
    return DataHubLineageContext.model_construct(**values)


def bad_plan(plan: DataHubColumnLineageArgumentPlan, **overrides) -> DataHubColumnLineageArgumentPlan:
    values = {
        "dataset_urn": plan.dataset_urn,
        "affected_column": plan.affected_column,
        "arguments": dict(plan.arguments),
        "input_schema_fingerprint": plan.input_schema_fingerprint,
        "plan_version": "1.0",
    }
    values.update(overrides)
    return DataHubColumnLineageArgumentPlan.model_construct(**values)


def bad_dataset_exec(dataset_exec: DataHubDatasetLineageExecutionResult, *, source_dataset_urn: str | None = None, request_id: int | None = None, next_request_id: int | None = None) -> DataHubDatasetLineageExecutionResult:
    return DataHubDatasetLineageExecutionResult.model_construct(
        request_id=request_id if request_id is not None else dataset_exec.request_id,
        next_request_id=next_request_id if next_request_id is not None else dataset_exec.next_request_id,
        dataset_lineage_request_fingerprint=dataset_exec.dataset_lineage_request_fingerprint,
        input_schema_fingerprint=dataset_exec.input_schema_fingerprint,
        source_dataset_urn=source_dataset_urn if source_dataset_urn is not None else dataset_exec.source_dataset_urn,
        downstream_slice=dataset_exec.downstream_slice,
    )


def bad_schema_exec(schema_exec: DataHubSchemaFieldsExecutionResult, *, dataset_urn: str | None = None) -> DataHubSchemaFieldsExecutionResult:
    return DataHubSchemaFieldsExecutionResult.model_construct(
        request_id=schema_exec.request_id,
        next_request_id=schema_exec.next_request_id,
        schema_request_fingerprint=schema_exec.schema_request_fingerprint,
        input_schema_fingerprint=schema_exec.input_schema_fingerprint,
        dataset_urn=dataset_urn if dataset_urn is not None else schema_exec.dataset_urn,
        schema_slice=schema_exec.schema_slice,
    )


def unready_lineage_bundle(lineage_bundle: DataHubLineageToolDiscoveryBundle) -> DataHubLineageToolDiscoveryBundle:
    esd = lineage_bundle.entity_schema_discovery
    bad_catalog = DataHubReadToolCatalog.model_construct(tools=esd.read_discovery.catalog.tools, all_required_tools_available=False, annotation_verification_complete=False, catalog_version=CATALOG_VERSION)
    bad_read = DataHubReadToolDiscoveryBundle.model_construct(catalog=bad_catalog, search_contract=esd.read_discovery.search_contract, next_request_id=esd.read_discovery.next_request_id, bundle_version="1.0")
    bad_esd = DataHubEntitySchemaToolDiscoveryBundle.model_construct(read_discovery=bad_read, get_entities_contract=esd.get_entities_contract, list_schema_fields_contract=esd.list_schema_fields_contract, bundle_version="1.0")
    return DataHubLineageToolDiscoveryBundle.model_construct(entity_schema_discovery=bad_esd, get_lineage_contract=lineage_bundle.get_lineage_contract, bundle_version="1.0")


def fingerprint_mismatch_lineage_bundle(lineage_bundle: DataHubLineageToolDiscoveryBundle) -> DataHubLineageToolDiscoveryBundle:
    bad_contract = DataHubGetLineageSchemaContract.model_construct(input_schema_fingerprint="0" * 64, urn_supported=True, column_supported=True, downstream_false_supported=True, max_hops_one_supported=True, max_results_30_supported=True, offset_zero_supported=True, contract_version="1.0")
    return DataHubLineageToolDiscoveryBundle.model_construct(entity_schema_discovery=lineage_bundle.entity_schema_discovery, get_lineage_contract=bad_contract, bundle_version="1.0")


_ABSENT = object()


def column_item(*, urn: str = TARGET_DATASET_URN, entity_type: object = "DATASET", name: str = "orders_usage", degree: object = 1, lineage_columns: object = ("customer_id",), **extra) -> dict:
    entity: dict = {"urn": urn, "name": name}
    if entity_type is not _ABSENT:
        entity["type"] = entity_type
    entity.update(extra)
    item: dict = {"entity": entity, "degree": degree}
    if lineage_columns is not _ABSENT:
        item["lineageColumns"] = list(lineage_columns)
    return item


def downstreams_payload(search_results: object = _ABSENT, *, total: object = _ABSENT, offset: object = _ABSENT, returned: object = _ABSENT, has_more: object = _ABSENT, truncated: object = _ABSENT, upstreams: object = _ABSENT, metadata: object = _ABSENT) -> dict:
    data: dict = {}
    if search_results is not _ABSENT:
        data["searchResults"] = search_results
    if total is not _ABSENT:
        data["total"] = total
    if offset is not _ABSENT:
        data["offset"] = offset
    if returned is not _ABSENT:
        data["returned"] = returned
    if has_more is not _ABSENT:
        data["hasMore"] = has_more
    if truncated is not _ABSENT:
        data["truncatedDueToTokenBudget"] = truncated
    payload: dict = {"downstreams": data}
    if upstreams is not _ABSENT:
        payload["upstreams"] = upstreams
    if metadata is not _ABSENT:
        payload["metadata"] = metadata
    return payload


def nonempty_payload(items: list[dict] | None = None, *, total: object = _ABSENT, offset: int = 0, returned: object = _ABSENT, has_more: bool = False, truncated: object = _ABSENT) -> dict:
    items = [column_item()] if items is None else items
    return downstreams_payload(items, total=total, offset=offset, returned=len(items) if returned is _ABSENT else returned, has_more=has_more, truncated=truncated)


def mcp_response(*, content: list[dict] | None = None, result_dict: dict | None = None, is_error: object = False, response_id: int = 7) -> DataHubMCPHTTPResponse:
    envelope: dict = {"content": content if content is not None else [{"type": "text", "text": "ignored"}]}
    if is_error is not None:
        envelope["isError"] = is_error
    if result_dict:
        envelope.update(result_dict)
    body = json.dumps({"jsonrpc": "2.0", "id": response_id, "result": envelope}).encode()
    return DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, body)


def structured_response(payload: dict, *, content: list[dict] | None = None, structured: object = None, is_error: object = False) -> DataHubMCPHTTPResponse:
    return mcp_response(content=content, result_dict={"structuredContent": structured if structured is not None else payload}, is_error=is_error)


def text_response(payload: dict, *, text: str | None = None, is_error: object = False) -> DataHubMCPHTTPResponse:
    return mcp_response(content=[{"type": "text", "text": text if text is not None else json.dumps(payload)}], is_error=is_error)


class TestPreflight:
    def test_valid_d3_context_accepted(self) -> None:
        result, transport = run(structured_response(nonempty_payload()))
        assert isinstance(result, DataHubColumnLineageExecutionResult)
        assert len(transport.calls) == 1

    def test_endpoint_mismatch_zero_calls(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_copy(update={"endpoint_url": "https://other.example.com/mcp"})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), session=bad_session, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_protocol_mismatch_zero_calls(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_construct(endpoint_url=ENDPOINT, protocol_version="2024-11-05", server_name="DataHub", server_version="1", tools_supported=True, session_id="session-1")
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), session=bad_session, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_tools_unsupported_zero_calls(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_copy(update={"tools_supported": False})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), session=bad_session, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_catalog_unready_zero_calls(self) -> None:
        _, _, lineage_bundle, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad_ctx = construct_lineage_ctx(ctx, discovery=unready_lineage_bundle(lineage_bundle))
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=bad_ctx, column_plan=plan, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_lineage_fingerprint_mismatch_zero_calls(self) -> None:
        _, _, lineage_bundle, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad_ctx = construct_lineage_ctx(ctx, discovery=fingerprint_mismatch_lineage_bundle(lineage_bundle))
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=bad_ctx, column_plan=plan, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_plan_fingerprint_mismatch_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_plan(plan, input_schema_fingerprint="0" * 64)
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=bad, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_source_dataset_mismatch_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_plan(plan, dataset_urn=CUSTOMERS_URN, arguments={"urn": CUSTOMERS_URN, "column": "customer_id", "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=bad, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_d2_source_mismatch_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_dataset_exec(dataset_exec, source_dataset_urn=CUSTOMERS_URN)
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=plan, dataset_lineage_execution=bad, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_schema_source_mismatch_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_schema_exec(schema_exec, dataset_urn=CUSTOMERS_URN)
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=plan, dataset_lineage_execution=dataset_exec, schema_execution=bad, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_source_platform_mismatch_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        postgres_subject = subject(column="customer_id").model_copy(update={"platform": "postgres"})
        bad_ctx = construct_lineage_ctx(ctx, subject=postgres_subject)
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=bad_ctx, column_plan=plan, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_affected_column_mismatch_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_plan(plan, affected_column="other_col", arguments={"urn": ORDERS_URN, "column": "other_col", "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=bad, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_missing_column_argument_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=bad, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_wrong_column_argument_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "column": "wrong_col", "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=bad, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_upstream_not_false_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "column": "customer_id", "upstream": True, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=bad, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_max_hops_not_one_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "column": "customer_id", "upstream": False, "max_hops": 2, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=bad, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_max_results_not_30_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "column": "customer_id", "upstream": False, "max_hops": 1, "max_results": 50, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=bad, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_offset_not_zero_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "column": "customer_id", "upstream": False, "max_hops": 1, "max_results": 30, "offset": 30})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=bad, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_query_present_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "column": "customer_id", "query": "x", "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=bad, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_filter_present_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "column": "customer_id", "filter": "x", "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=bad, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_d2_next_request_id_mismatch_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_dataset_exec(dataset_exec, next_request_id=9)
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=plan, dataset_lineage_execution=bad, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_d1_column_id_mismatch_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad_ctx = construct_lineage_ctx(ctx, column_lineage_request_id=9, post_lineage_next_request_id=10)
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=bad_ctx, column_plan=plan, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls

    def test_oversized_request_zero_calls(self) -> None:
        _, _, _, ctx, plan, dataset_exec, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "column": "x" * 70_000, "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, column_plan=bad, dataset_lineage_execution=dataset_exec, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "column_lineage_execution_context_mismatch" and not transport.calls


class TestExecution:
    def test_valid_execution_exactly_one_post_request(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert len(transport.calls) == 1

    def test_method_exact_tools_call(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert json.loads(transport.calls[0][0])["method"] == "tools/call"

    def test_tool_exact_get_lineage(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert json.loads(transport.calls[0][0])["params"]["name"] == "get_lineage"

    def test_exact_source_dataset(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert json.loads(transport.calls[0][0])["params"]["arguments"]["urn"] == ORDERS_URN

    def test_exact_affected_column(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert json.loads(transport.calls[0][0])["params"]["arguments"]["column"] == "customer_id"

    def test_upstream_exact_false(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert json.loads(transport.calls[0][0])["params"]["arguments"]["upstream"] is False

    def test_max_hops_exact_one(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert json.loads(transport.calls[0][0])["params"]["arguments"]["max_hops"] == 1

    def test_max_results_exact_30(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert json.loads(transport.calls[0][0])["params"]["arguments"]["max_results"] == 30

    def test_offset_exact_zero(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert json.loads(transport.calls[0][0])["params"]["arguments"]["offset"] == 0

    def test_query_absent(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert "query" not in json.loads(transport.calls[0][0])["params"]["arguments"]

    def test_filter_absent(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert "filter" not in json.loads(transport.calls[0][0])["params"]["arguments"]

    def test_exact_request_id(self) -> None:
        _, _, _, ctx, _, dataset_exec, _ = full_setup()
        _, transport = run(structured_response(nonempty_payload()))
        assert json.loads(transport.calls[0][0])["id"] == ctx.column_lineage_request_id == dataset_exec.next_request_id

    def test_canonical_bytes_exact(self) -> None:
        _, _, lineage_bundle, ctx, plan, _, _ = full_setup()
        _, transport = run(structured_response(nonempty_payload()))
        expected = serialize_datahub_column_lineage_tools_call_request(context=ctx, contract=lineage_bundle.get_lineage_contract, argument_plan=plan)
        assert transport.calls[0][0] == expected
        assert transport.calls[0][0] == serialize_jsonrpc(build_datahub_column_lineage_tools_call_request(context=ctx, contract=lineage_bundle.get_lineage_contract, argument_plan=plan))

    def test_protocol_reused(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert transport.calls[0][2] == DATAHUB_MCP_PROTOCOL_VERSION == "2025-11-25"

    def test_session_reused(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert transport.calls[0][1] == "session-1"

    def test_auth_reused(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert b"test-token" not in transport.calls[0][0]

    def test_no_retry(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert len(transport.calls) == 1

    def test_no_second_call(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert len(transport.calls) == 1

    def test_no_dataset_lineage_reexecution(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        body = transport.calls[0][0].decode("utf-8")
        assert '"column":"customer_id"' in body

    def test_no_pagination(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert len(transport.calls) == 1


class TestFingerprint:
    def test_deterministic_fingerprint(self) -> None:
        first, _ = run(structured_response(nonempty_payload()))
        second, _ = run(structured_response(nonempty_payload()))
        assert first.column_lineage_request_fingerprint == second.column_lineage_request_fingerprint

    def test_64_lowercase_hex(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert len(result.column_lineage_request_fingerprint) == 64
        assert re.fullmatch(r"[0-9a-f]{64}", result.column_lineage_request_fingerprint)

    def test_request_mutation_changes_fingerprint(self) -> None:
        first, _ = run(structured_response(nonempty_payload()))
        _, _, bundle2, ctx2, plan2, _, _ = full_setup(urn=CUSTOMERS_URN, name="customers")
        body_a = serialize_datahub_column_lineage_tools_call_request(context=ctx2 if False else ctx2, contract=bundle2.get_lineage_contract, argument_plan=plan2)
        _ = body_a
        _, _, lineage_bundle, ctx, plan, _, _ = full_setup()
        body_default = serialize_datahub_column_lineage_tools_call_request(context=ctx, contract=lineage_bundle.get_lineage_contract, argument_plan=plan)
        body_changed = serialize_datahub_column_lineage_tools_call_request(context=ctx2, contract=bundle2.get_lineage_contract, argument_plan=plan2)
        assert body_default != body_changed
        assert first.column_lineage_request_fingerprint == hashlib.sha256(body_default).hexdigest()

    def test_endpoint_excluded(self) -> None:
        result, transport = run(structured_response(nonempty_payload()))
        assert ENDPOINT.encode() not in transport.calls[0][0]
        assert "datahub.example.com" not in result.column_lineage_request_fingerprint

    def test_token_excluded(self) -> None:
        result, transport = run(structured_response(nonempty_payload()))
        assert b"test-token" not in transport.calls[0][0]
        assert "test-token" not in result.column_lineage_request_fingerprint

    def test_session_excluded(self) -> None:
        result, transport = run(structured_response(nonempty_payload()))
        assert b"session-1" not in transport.calls[0][0]
        assert "session-1" not in result.column_lineage_request_fingerprint

    def test_response_excluded(self) -> None:
        result, transport = run(structured_response(nonempty_payload()))
        assert result.column_lineage_request_fingerprint == hashlib.sha256(transport.calls[0][0]).hexdigest()


class TestCallToolResult:
    def test_valid_result(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.column_lineage_slice.source_dataset_urn == ORDERS_URN

    def test_is_error_absent(self) -> None:
        response = mcp_response(result_dict={"structuredContent": nonempty_payload()}, is_error=None)
        result, _ = run(response)
        assert result.source_dataset_urn == ORDERS_URN

    def test_is_error_false(self) -> None:
        result, _ = run(structured_response(nonempty_payload(), is_error=False))
        assert result.source_dataset_urn == ORDERS_URN

    def test_is_error_true_safe_failure(self) -> None:
        transport = FakeTransport([structured_response(nonempty_payload(), is_error=True)])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload(), is_error=True), transport=transport)
        assert exc.value.code == "column_lineage_tool_execution_failed" and len(transport.calls) == 1

    def test_non_bool_is_error_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload(), is_error="true"))
        assert exc.value.code == "invalid_column_lineage_tool_result"

    def test_content_required(self) -> None:
        response = DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, json.dumps({"jsonrpc": "2.0", "id": 7, "result": {"structuredContent": nonempty_payload()}}).encode())
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_column_lineage_tool_result"

    def test_content_list_required(self) -> None:
        response = mcp_response(content={"not": "a list"}, result_dict={"structuredContent": nonempty_payload()})
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_column_lineage_tool_result"

    def test_block_count_bounded(self) -> None:
        response = structured_response(nonempty_payload(), content=[{"type": "text", "text": "x"} for _ in range(9)])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "unsupported_column_lineage_content"

    def test_valid_text_accepted(self) -> None:
        result, _ = run(text_response(nonempty_payload()))
        assert result.source_dataset_urn == ORDERS_URN

    def test_unsupported_content_rejected(self) -> None:
        response = structured_response(nonempty_payload(), content=[{"type": "image", "data": "x"}])
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "unsupported_column_lineage_content"

    def test_utf8_enforced(self) -> None:
        response = text_response(nonempty_payload(), text="\ud800")
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "unsupported_column_lineage_content"

    def test_null_byte_rejected(self) -> None:
        response = text_response(nonempty_payload(), text='{"downstreams": {"x": "y\u0000"}}')
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "column_lineage_content_too_large"

    def test_text_size_bounds(self) -> None:
        big = "x" * 262_145
        response = mcp_response(content=[{"type": "text", "text": big}], result_dict={"structuredContent": nonempty_payload()})
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "column_lineage_content_too_large"

    def test_structured_size_bound(self) -> None:
        payload = nonempty_payload()
        payload["blob"] = "x" * 524_300
        response = mcp_response(result_dict={"structuredContent": payload})
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "column_lineage_content_too_large"

    def test_meta_ignored(self) -> None:
        result, _ = run(mcp_response(result_dict={"structuredContent": nonempty_payload(), "_meta": {"progressToken": "t"}}))
        assert result.source_dataset_urn == ORDERS_URN

    def test_unknown_result_fields_ignored(self) -> None:
        result, _ = run(mcp_response(result_dict={"structuredContent": nonempty_payload(), "unknown": {"x": 1}}))
        assert result.source_dataset_urn == ORDERS_URN

    def test_raw_result_discarded(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        for token in ("structuredContent", "isError", "CallToolResult", "content"):
            assert token not in dumped


class TestPayload:
    def test_direct_structured_content_object(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.OBSERVED

    def test_structured_priority(self) -> None:
        response = mcp_response(content=[{"type": "text", "text": "this is not json"}], result_dict={"structuredContent": nonempty_payload()})
        result, _ = run(response)
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.OBSERVED

    def test_text_not_reparsed_with_structured(self) -> None:
        response = mcp_response(content=[{"type": "text", "text": "this is not json"}], result_dict={"structuredContent": nonempty_payload()})
        result, _ = run(response)
        assert result.column_lineage_slice.targets[0].dataset_urn == TARGET_DATASET_URN

    def test_non_object_structured_rejected(self) -> None:
        response = mcp_response(result_dict={"structuredContent": [1, 2]})
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_column_lineage_payload"

    def test_strict_object_fallback(self) -> None:
        result, _ = run(text_response(nonempty_payload()))
        assert result.column_lineage_slice.targets[0].dataset_urn == TARGET_DATASET_URN

    def test_array_fallback_rejected(self) -> None:
        response = text_response(nonempty_payload(), text=json.dumps([nonempty_payload()]))
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_column_lineage_payload"

    def test_primitive_rejected(self) -> None:
        response = text_response(nonempty_payload(), text='"x"')
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_column_lineage_payload"

    def test_fences_rejected(self) -> None:
        response = text_response(nonempty_payload(), text="```json\n" + json.dumps(nonempty_payload()) + "\n```")
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_column_lineage_payload"

    def test_prose_rejected(self) -> None:
        response = text_response(nonempty_payload(), text="result " + json.dumps(nonempty_payload()))
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_column_lineage_payload"
        response = text_response(nonempty_payload(), text=json.dumps(nonempty_payload()) + " done")
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_column_lineage_payload"

    def test_duplicate_keys_rejected(self) -> None:
        response = text_response(nonempty_payload(), text='{"downstreams": {"x": 1, "x": 2}}')
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_column_lineage_payload"

    def test_nan_infinity_rejected(self) -> None:
        for text in ('{"downstreams": {"x": NaN}}', '{"downstreams": {"x": Infinity}}'):
            with pytest.raises(DataHubColumnLineageExecutionError) as exc:
                run(text_response(nonempty_payload(), text=text))
            assert exc.value.code == "invalid_column_lineage_payload"

    def test_multiple_documents_rejected(self) -> None:
        response = text_response(nonempty_payload(), text="{} {}")
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_column_lineage_payload"

    def test_null_byte_rejected(self) -> None:
        response = text_response(nonempty_payload(), text='{"downstreams": {"x": "y\u0000"}}')
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "column_lineage_content_too_large"

    def test_malformed_json_rejected(self) -> None:
        response = text_response(nonempty_payload(), text="{")
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_column_lineage_payload"


class TestDirection:
    def test_downstreams_object_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.OBSERVED

    def test_missing_downstreams_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response({"other": {}}))
        assert exc.value.code == "column_lineage_direction_mismatch"

    def test_non_object_downstreams_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response({"downstreams": []}))
        assert exc.value.code == "invalid_column_lineage_payload"

    def test_absent_upstreams_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.source_dataset_urn == ORDERS_URN

    def test_semantically_empty_upstreams_ignored(self) -> None:
        payload = downstreams_payload([column_item()], offset=0, returned=1, has_more=False, upstreams={"total": 0})
        result, _ = run(structured_response(payload))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.OBSERVED

    def test_nonempty_upstream_lineage_rejected(self) -> None:
        payload = downstreams_payload([column_item()], offset=0, returned=1, has_more=False, upstreams={"searchResults": [column_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,raw.orders,PROD)")]})
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "column_lineage_direction_mismatch"

    def test_upstream_content_never_normalized(self) -> None:
        payload = downstreams_payload([column_item()], offset=0, returned=1, has_more=False, upstreams={"searchResults": [column_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,raw.orders,PROD)")]})
        with pytest.raises(DataHubColumnLineageExecutionError):
            run(structured_response(payload))


class TestEmptyResults:
    def test_empty_downstreams_accepted(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.NOT_OBSERVED
        assert result.column_lineage_slice.targets == ()

    def test_missing_search_results_accepted(self) -> None:
        result, _ = run(structured_response(downstreams_payload(total=0)))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.NOT_OBSERVED

    def test_empty_search_results_accepted(self) -> None:
        result, _ = run(structured_response(downstreams_payload([], offset=0, returned=0, has_more=False)))
        assert result.column_lineage_slice.targets == ()

    def test_zero_result_not_observed(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.NOT_OBSERVED

    def test_zero_result_does_not_claim_no_impact(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        dumped = json.dumps(result.model_dump())
        assert "no_impact" not in dumped and "no_consumers" not in dumped

    def test_absent_total_stays_none(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.column_lineage_slice.provider_total is None

    def test_absent_offset_stays_none(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.column_lineage_slice.provider_offset is None

    def test_absent_returned_stays_none(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.column_lineage_slice.provider_returned is None

    def test_absent_has_more_stays_none(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.column_lineage_slice.provider_has_more is None

    def test_absent_truncation_stays_none(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.column_lineage_slice.provider_truncated_due_to_token_budget is None

    def test_present_zero_metadata_structurally_validated(self) -> None:
        result, _ = run(structured_response(downstreams_payload([], offset=0, returned=0, has_more=False)))
        assert result.column_lineage_slice.provider_offset == 0
        assert result.column_lineage_slice.provider_returned == 0
        assert result.column_lineage_slice.provider_has_more is False


class TestNonemptyResults:
    def test_one_dataset_target_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert len(result.column_lineage_slice.targets) == 1

    def test_thirty_target_datasets_accepted(self) -> None:
        items = [column_item(urn=f"urn:li:dataset:(urn:li:dataPlatform:postgres,db.t{i},PROD)") for i in range(30)]
        result, _ = run(structured_response(nonempty_payload(items)))
        assert len(result.column_lineage_slice.targets) == 30

    def test_over_30_rejected(self) -> None:
        items = [column_item(urn=f"urn:li:dataset:(urn:li:dataPlatform:postgres,db.t{i},PROD)") for i in range(31)]
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload(items)))
        assert exc.value.code == "column_lineage_count_mismatch"

    def test_returned_required(self) -> None:
        payload = downstreams_payload([column_item()], offset=0, has_more=False)
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_column_lineage_payload"

    def test_returned_equals_result_length(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.column_lineage_slice.provider_returned == 1 == len(result.column_lineage_slice.targets)

    def test_returned_mismatch_rejected(self) -> None:
        payload = downstreams_payload([column_item()], offset=0, returned=2, has_more=False)
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "column_lineage_count_mismatch"

    def test_offset_required_exact_zero(self) -> None:
        payload = downstreams_payload([column_item()], offset=1, returned=1, has_more=False)
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_column_lineage_payload"

    def test_has_more_required_bool(self) -> None:
        result, _ = run(structured_response(nonempty_payload(has_more=False)))
        assert result.column_lineage_slice.provider_has_more is False

    def test_integer_has_more_rejected(self) -> None:
        payload = downstreams_payload([column_item()], offset=0, returned=1, has_more=1)
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_column_lineage_payload"

    def test_optional_truncation_bool(self) -> None:
        result, _ = run(structured_response(nonempty_payload(truncated=True)))
        assert result.column_lineage_slice.provider_truncated_due_to_token_budget is True

    def test_malformed_truncation_rejected(self) -> None:
        payload = downstreams_payload([column_item()], offset=0, returned=1, has_more=False, truncated="yes")
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_column_lineage_payload"

    def test_optional_total(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.column_lineage_slice.provider_total is None
        result, _ = run(structured_response(nonempty_payload(total=5)))
        assert result.column_lineage_slice.provider_total == 5

    def test_total_gte_returned(self) -> None:
        payload = nonempty_payload([column_item(), column_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,db.t2,PROD)")], total=1, returned=2)
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "column_lineage_count_mismatch"

    def test_bool_total_rejected(self) -> None:
        payload = downstreams_payload([column_item()], total=True, offset=0, returned=1, has_more=False)
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_column_lineage_payload"

    def test_total_bounds(self) -> None:
        payload = downstreams_payload([column_item()], total=1_000_001, offset=0, returned=1, has_more=False)
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_column_lineage_payload"


class TestTargetDataset:
    def test_valid_dataset_urn_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.column_lineage_slice.targets[0].dataset_urn == TARGET_DATASET_URN

    def test_missing_urn_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(urn=None)])))
        assert exc.value.code == "invalid_column_lineage_target"

    def test_malformed_urn_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(urn="not-a-urn")])))
        assert exc.value.code == "invalid_column_lineage_target"

    def test_non_dataset_urn_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(urn="urn:li:dashboard:dash")])))
        assert exc.value.code == "invalid_column_lineage_target"

    def test_blank_urn_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(urn="   ")])))
        assert exc.value.code == "invalid_column_lineage_target"

    def test_oversized_urn_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(urn="urn:li:" + "x" * 1100)])))
        assert exc.value.code == "invalid_column_lineage_target"

    def test_cross_platform_dataset_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(urn=CROSS_PLATFORM_URN)])))
        assert result.column_lineage_slice.targets[0].dataset_urn == CROSS_PLATFORM_URN

    def test_source_platform_gate_not_applied(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(urn="urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.orders_usage,PROD)")])))
        assert len(result.column_lineage_slice.targets) == 1

    def test_type_dataset_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.column_lineage_slice.targets[0].dataset_urn == TARGET_DATASET_URN

    def test_incompatible_non_dataset_type_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(entity_type="DataJob")])))
        assert exc.value.code == "invalid_column_lineage_target"

    def test_missing_type_allowed_when_urn_proves_dataset(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(entity_type=_ABSENT)])))
        assert result.column_lineage_slice.targets[0].dataset_urn == TARGET_DATASET_URN

    def test_bounded_display_name(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.column_lineage_slice.targets[0].display_name == "orders_usage"

    def test_missing_display_name_allowed(self) -> None:
        item = {"entity": {"urn": TARGET_DATASET_URN, "type": "DATASET"}, "degree": 1, "lineageColumns": ["customer_id"]}
        result, _ = run(structured_response(nonempty_payload([item])))
        assert result.column_lineage_slice.targets[0].display_name is None

    def test_descriptions_discarded(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(description="a provider description")])))
        assert "a provider description" not in json.dumps(result.model_dump())

    def test_urls_discarded(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(url="https://example.com")])))
        assert "example.com" not in json.dumps(result.model_dump())

    def test_provider_arbitrary_metadata_discarded(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(extra_prop={"x": 1})])))
        assert "extra_prop" not in json.dumps(result.model_dump())


class TestDuplicateTargets:
    def test_duplicate_target_urn_rejected(self) -> None:
        items = [column_item(), column_item(name="orders_usage_2")]
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload(items, returned=2)))
        assert exc.value.code == "duplicate_column_lineage_target"

    def test_duplicate_target_not_merged(self) -> None:
        items = [column_item(), column_item(name="orders_usage_2")]
        with pytest.raises(DataHubColumnLineageExecutionError):
            run(structured_response(nonempty_payload(items, returned=2)))

    def test_duplicate_columns_not_merged_across_duplicate_entities(self) -> None:
        items = [column_item(), column_item(name="orders_usage_2")]
        with pytest.raises(DataHubColumnLineageExecutionError):
            run(structured_response(nonempty_payload(items, returned=2)))

    def test_provider_order_not_dedup_tiebreak(self) -> None:
        items = [column_item(), column_item(name="orders_usage_2")]
        with pytest.raises(DataHubColumnLineageExecutionError):
            run(structured_response(nonempty_payload(items, returned=2)))


class TestDegree:
    def test_degree_one_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.column_lineage_slice.targets[0].depth == 1

    def test_degree_zero_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(degree=0)])))
        assert exc.value.code == "invalid_column_lineage_target"

    def test_degree_two_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(degree=2)])))
        assert exc.value.code == "invalid_column_lineage_target"

    def test_bool_degree_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(degree=True)])))
        assert exc.value.code == "invalid_column_lineage_target"

    def test_string_degree_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(degree="1")])))
        assert exc.value.code == "invalid_column_lineage_target"

    def test_missing_degree_rejected(self) -> None:
        item = {"entity": {"urn": TARGET_DATASET_URN, "type": "DATASET"}, "lineageColumns": ["customer_id"]}
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([item])))
        assert exc.value.code == "invalid_column_lineage_target"

    def test_degree_never_risk_or_priority(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        assert "risk" not in dumped and "priority" not in dumped and "severity" not in dumped


class TestLineageColumns:
    def test_lineage_columns_absent_accepted(self) -> None:
        item = {"entity": {"urn": TARGET_DATASET_URN, "type": "DATASET"}, "degree": 1}
        result, _ = run(structured_response(nonempty_payload([item])))
        assert result.column_lineage_slice.targets[0].lineage_columns == ()
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.NOT_OBSERVED

    def test_empty_lineage_columns_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(lineage_columns=[])])))
        assert result.column_lineage_slice.targets[0].lineage_columns == ()

    def test_one_target_column_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.column_lineage_slice.targets[0].lineage_columns == ("customer_id",)

    def test_multiple_target_columns_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(lineage_columns=["customer_id", "account_id"])])))
        assert result.column_lineage_slice.targets[0].lineage_columns == ("customer_id", "account_id")

    def test_target_column_may_differ_from_source(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(lineage_columns=["account_id"])])))
        assert result.column_lineage_slice.targets[0].lineage_columns == ("account_id",)

    def test_exact_same_name_target_column_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(lineage_columns=["customer_id"])])))
        assert result.column_lineage_slice.targets[0].lineage_columns == ("customer_id",)

    def test_target_column_string_required(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(lineage_columns=[123])])))
        assert exc.value.code == "invalid_lineage_column"

    def test_null_target_column_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(lineage_columns=[None])])))
        assert exc.value.code == "invalid_lineage_column"

    def test_object_target_column_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(lineage_columns=[{"name": "x"}])])))
        assert exc.value.code == "invalid_lineage_column"

    def test_numeric_target_column_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(lineage_columns=[1.5])])))
        assert exc.value.code == "invalid_lineage_column"

    def test_blank_target_column_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(lineage_columns=["   "])])))
        assert exc.value.code == "invalid_lineage_column"

    def test_oversized_target_column_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(lineage_columns=["x" * 600])])))
        assert exc.value.code == "invalid_lineage_column"

    def test_null_control_chars_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(lineage_columns=["bad\x00col"])])))
        assert exc.value.code == "invalid_lineage_column"

    def test_duplicate_normalized_target_column_rejected(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(lineage_columns=["customer_id", "CUSTOMER_ID"])])))
        assert exc.value.code == "duplicate_lineage_column"

    def test_no_silent_dedup(self) -> None:
        with pytest.raises(DataHubColumnLineageExecutionError):
            run(structured_response(nonempty_payload([column_item(lineage_columns=["customer_id", "customer_id"])])))

    def test_per_target_collection_bound(self) -> None:
        columns = [f"col{i}" for i in range(65)]
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([column_item(lineage_columns=columns)])))
        assert exc.value.code == "invalid_column_lineage_target"

    def test_total_collection_bound(self) -> None:
        items = [column_item(urn=f"urn:li:dataset:(urn:li:dataPlatform:postgres,db.t{i},PROD)", lineage_columns=[f"c{j}" for j in range(64)]) for i in range(5)]
        with pytest.raises(DataHubColumnLineageExecutionError) as exc:
            run(structured_response(nonempty_payload(items, returned=5)))
        assert exc.value.code == "column_lineage_count_mismatch"

    def test_bound_overflow_fails_instead_of_truncating(self) -> None:
        items = [column_item(urn=f"urn:li:dataset:(urn:li:dataPlatform:postgres,db.t{i},PROD)", lineage_columns=[f"c{j}" for j in range(64)]) for i in range(5)]
        with pytest.raises(DataHubColumnLineageExecutionError):
            run(structured_response(nonempty_payload(items, returned=5)))


class TestColumnSemantics:
    def test_user_id_to_customer_id_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(lineage_columns=["customer_id"])])))
        assert result.column_lineage_slice.targets[0].lineage_columns == ("customer_id",)

    def test_user_id_to_user_key_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(lineage_columns=["user_key"])])))
        assert result.column_lineage_slice.targets[0].lineage_columns == ("user_key",)

    def test_no_exact_source_target_comparison_required(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(lineage_columns=["completely_different_name"])])))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.OBSERVED

    def test_no_fuzzy_matching(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(lineage_columns=["custmr_id"])])))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.OBSERVED

    def test_no_alias_matching(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(lineage_columns=["cust_id"])])))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.OBSERVED

    def test_no_deepseek_semantic_matching(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(lineage_columns=["customer_identifier"])])))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.OBSERVED
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "DeepSeek" not in source

    def test_target_names_stored_as_observations_only(self) -> None:
        result, _ = run(structured_response(nonempty_payload([column_item(lineage_columns=["account_id"])])))
        assert result.column_lineage_slice.targets[0].lineage_columns == ("account_id",)


class TestObservation:
    def test_target_with_lineage_column_observed(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.OBSERVED

    def test_multiple_targets_with_columns_observed(self) -> None:
        items = [column_item(), column_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,db.b,PROD)", lineage_columns=["user_key"])]
        result, _ = run(structured_response(nonempty_payload(items, returned=2)))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.OBSERVED

    def test_search_result_target_but_empty_columns_not_observed(self) -> None:
        item = {"entity": {"urn": TARGET_DATASET_URN, "type": "DATASET"}, "degree": 1, "lineageColumns": []}
        result, _ = run(structured_response(nonempty_payload([item])))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.NOT_OBSERVED

    def test_no_search_results_not_observed(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.NOT_OBSERVED

    def test_not_observed_creates_no_absent_claim(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        dumped = json.dumps(result.model_dump())
        assert "absent" not in dumped and "missing" not in dumped

    def test_observed_creates_no_validation_success(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        assert "pass" not in dumped and "valid" not in dumped and "safe" not in dumped

    def test_observed_creates_no_block_warn(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        assert "BLOCK" not in dumped and "WARN" not in dumped

    def test_dataset_result_count_does_not_define_column_observation(self) -> None:
        item = {"entity": {"urn": TARGET_DATASET_URN, "type": "DATASET"}, "degree": 1, "lineageColumns": []}
        result, _ = run(structured_response(nonempty_payload([item])))
        assert result.column_lineage_slice.provider_returned == 1
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.NOT_OBSERVED


class TestImmutability:
    def test_target_model_frozen(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        target = result.column_lineage_slice.targets[0]
        assert isinstance(target, DataHubColumnDownstreamTarget)
        assert target.model_config["frozen"] is True

    def test_dataset_urn_mutation_rejected(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.column_lineage_slice.targets[0].dataset_urn = CUSTOMERS_URN  # type: ignore[misc]

    def test_display_name_mutation_rejected(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.column_lineage_slice.targets[0].display_name = "MUTATED"  # type: ignore[misc]

    def test_relation_mutation_rejected(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.column_lineage_slice.targets[0].relation = DataHubLineageRelation.SUBJECT  # type: ignore[misc]

    def test_depth_mutation_rejected(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.column_lineage_slice.targets[0].depth = 2  # type: ignore[misc]

    def test_lineage_columns_tuple_immutable(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert isinstance(result.column_lineage_slice.targets[0].lineage_columns, tuple)

    def test_lineage_column_item_cannot_be_replaced(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(TypeError):
            result.column_lineage_slice.targets[0].lineage_columns[0] = "x"  # type: ignore[index]

    def test_slice_frozen(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.column_lineage_slice.model_config["frozen"] is True

    def test_slice_targets_immutable(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.column_lineage_slice.targets = ()  # type: ignore[misc]

    def test_source_column_mutation_rejected(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.column_lineage_slice.source_column = "other"  # type: ignore[misc]

    def test_result_frozen(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.model_config["frozen"] is True

    def test_result_slice_replacement_rejected(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.column_lineage_slice = result.column_lineage_slice  # type: ignore[misc]

    def test_no_mutable_lineage_node_nested(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert type(result.column_lineage_slice.targets[0]).__name__ == "DataHubColumnDownstreamTarget"
        assert "DataHubLineageNode" not in repr(result.column_lineage_slice.targets[0])

    def test_no_raw_list_nested(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert isinstance(result.column_lineage_slice.targets[0].lineage_columns, tuple)
        dumped = json.dumps(result.model_dump())
        assert "searchResults" not in dumped and "lineageColumns" not in dumped


class TestDefensiveSeparation:
    def test_mutate_provider_entity_urn_after_execution(self) -> None:
        item = column_item()
        result, _ = run(structured_response(nonempty_payload([item])))
        item["entity"]["urn"] = CUSTOMERS_URN
        assert result.column_lineage_slice.targets[0].dataset_urn == TARGET_DATASET_URN

    def test_mutate_provider_display_name(self) -> None:
        item = column_item()
        result, _ = run(structured_response(nonempty_payload([item])))
        item["entity"]["name"] = "MUTATED"
        assert result.column_lineage_slice.targets[0].display_name == "orders_usage"

    def test_mutate_provider_degree(self) -> None:
        item = column_item()
        result, _ = run(structured_response(nonempty_payload([item])))
        item["degree"] = 5
        assert result.column_lineage_slice.targets[0].depth == 1

    def test_mutate_provider_lineage_columns_list(self) -> None:
        item = column_item(lineage_columns=["customer_id"])
        result, _ = run(structured_response(nonempty_payload([item])))
        item["lineageColumns"].append("mutated")
        assert result.column_lineage_slice.targets[0].lineage_columns == ("customer_id",)

    def test_mutate_provider_lineage_column_value(self) -> None:
        item = column_item(lineage_columns=["customer_id"])
        result, _ = run(structured_response(nonempty_payload([item])))
        item["lineageColumns"][0] = "mutated"
        assert result.column_lineage_slice.targets[0].lineage_columns == ("customer_id",)

    def test_mutate_search_results_list(self) -> None:
        item = column_item()
        result, _ = run(structured_response(nonempty_payload([item])))
        payload = nonempty_payload([item])
        payload["downstreams"]["searchResults"].append(column_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,db.extra,PROD)"))
        assert len(result.column_lineage_slice.targets) == 1

    def test_model_dump_unchanged_after_provider_mutation(self) -> None:
        item = column_item()
        result, _ = run(structured_response(nonempty_payload([item])))
        before = json.dumps(result.model_dump())
        item["entity"]["urn"] = CUSTOMERS_URN
        item["lineageColumns"][0] = "mutated"
        assert json.dumps(result.model_dump()) == before


class TestPaginationCompleteness:
    def test_has_more_false_preserved_as_observation(self) -> None:
        result, _ = run(structured_response(nonempty_payload(has_more=False)))
        assert result.column_lineage_slice.provider_has_more is False

    def test_has_more_false_no_complete_field(self) -> None:
        result, _ = run(structured_response(nonempty_payload(has_more=False)))
        assert "complete" not in json.dumps(result.model_dump())

    def test_has_more_true_no_second_call(self) -> None:
        _, transport = run(structured_response(nonempty_payload(has_more=True)))
        assert len(transport.calls) == 1

    def test_has_more_true_no_pagination(self) -> None:
        result, transport = run(structured_response(nonempty_payload(has_more=True)))
        assert len(transport.calls) == 1
        assert json.loads(transport.calls[0][0])["params"]["arguments"]["offset"] == 0

    def test_truncation_true_no_retry(self) -> None:
        _, transport = run(structured_response(nonempty_payload(truncated=True)))
        assert len(transport.calls) == 1

    def test_truncation_true_no_second_request(self) -> None:
        result, transport = run(structured_response(nonempty_payload(truncated=True)))
        assert len(transport.calls) == 1
        assert result.column_lineage_slice.provider_truncated_due_to_token_budget is True

    def test_provider_total_zero_no_zero_impact_claim(self) -> None:
        result, _ = run(structured_response(downstreams_payload(total=0)))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.NOT_OBSERVED
        assert "zero_impact" not in json.dumps(result.model_dump())

    def test_missing_has_more_not_synthesized(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.column_lineage_slice.provider_has_more is None

    def test_provider_metadata_does_not_affect_observation(self) -> None:
        payload = downstreams_payload([column_item()], offset=0, returned=1, has_more=False, metadata={"requestedColumn": "customer_id"})
        result, _ = run(structured_response(payload))
        assert result.column_lineage_slice.column_lineage_observation is DataHubColumnLineageObservation.OBSERVED
        assert "requestedColumn" not in json.dumps(result.model_dump())


class TestResult:
    def test_exact_execution_result_fields(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert set(result.model_dump()) == {"request_id", "next_request_id", "column_lineage_request_fingerprint", "input_schema_fingerprint", "source_dataset_urn", "source_column", "column_lineage_slice", "result_version"}

    def test_request_id_equals_d1_column_id(self) -> None:
        _, _, _, ctx, _, dataset_exec, _ = full_setup()
        result, _ = run(structured_response(nonempty_payload()))
        assert result.request_id == ctx.column_lineage_request_id == dataset_exec.next_request_id

    def test_request_id_equals_d2_next_id(self) -> None:
        _, _, _, _, _, dataset_exec, _ = full_setup()
        result, _ = run(structured_response(nonempty_payload()))
        assert result.request_id == dataset_exec.next_request_id

    def test_next_request_id_equals_plus_one(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.next_request_id == result.request_id + 1

    def test_fingerprint_valid(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert re.fullmatch(r"[0-9a-f]{64}", result.column_lineage_request_fingerprint)

    def test_schema_fingerprint_preserved(self) -> None:
        _, _, _, ctx, plan, _, _ = full_setup()
        result, _ = run(structured_response(nonempty_payload()))
        assert result.input_schema_fingerprint == plan.input_schema_fingerprint == ctx.discovery.get_lineage_contract.input_schema_fingerprint

    def test_source_dataset_exact(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.source_dataset_urn == ORDERS_URN

    def test_source_column_exact(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.source_column == "customer_id"

    def test_slice_immutable(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.column_lineage_slice.model_config["frozen"] is True

    def test_result_immutable(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.model_config["frozen"] is True

    def test_result_version_fixed(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.result_version == "1.0"
        assert result.column_lineage_slice.slice_version == "1.0"

    def test_no_raw_request(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        assert "arguments" not in dumped and "max_hops" not in dumped and "max_results" not in dumped

    def test_no_call_tool_result(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        assert "CallToolResult" not in dumped and "isError" not in dumped

    def test_no_content(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert "content" not in json.dumps(result.model_dump())

    def test_no_structured_content(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert "structuredContent" not in json.dumps(result.model_dump())

    def test_no_metadata_blob(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert "metadata" not in json.dumps(result.model_dump())

    def test_no_paths(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert "paths" not in json.dumps(result.model_dump())

    def test_no_endpoint_token_session(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        for token in ("datahub.example.com", "test-token", "session-1"):
            assert token not in dumped

    def test_no_risk_authority(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert "risk" not in json.dumps(result.model_dump())

    def test_no_validation_authority(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert "validation" not in json.dumps(result.model_dump())

    def test_no_deployment_writeback_authority(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        assert "deployment" not in dumped and "writeback" not in dumped and "authority" not in dumped


class TestScopeRegression:
    def test_no_dataset_lineage_execution(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "execute_datahub_dataset_lineage" not in source
        assert "build_datahub_dataset_lineage_tools_call_request" not in source

    def test_no_request_without_column(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert '"column":"customer_id"' in transport.calls[0][0].decode("utf-8")

    def test_no_get_lineage_paths_between(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "get_lineage_paths_between" not in source

    def test_no_search(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "execute_datahub_search" not in source

    def test_no_get_entities(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "get_entities" not in source

    def test_no_list_schema_fields(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "list_schema_fields" not in source

    def test_no_tools_list(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "tools/list" not in source

    def test_no_initialize(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "initialize" not in source

    def test_no_retry(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert len(transport.calls) == 1

    def test_no_pagination(self) -> None:
        _, transport = run(structured_response(nonempty_payload(has_more=True, truncated=True)))
        assert len(transport.calls) == 1

    def test_no_deepseek(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "DeepSeek" not in source

    def test_no_persistence(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "persistence" not in source

    def test_no_fastapi_integration(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "FastAPI" not in source and "APIRouter" not in source

    def test_no_live_network(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        for token in ("import requests", "import httpx", "import aiohttp", "urllib", "http.client", "os.environ", "json_repair", "except Exception", "logging", "print("):
            assert token not in source

    def test_no_risk_integration(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "risk" not in source

    def test_no_validation_integration(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "validation" not in source

    def test_no_writeback(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/column_lineage_execution.py").read_text(encoding="utf-8")
        assert "writeback" not in source and "deployment" not in source

    def test_protocol_remains_2025_11_25(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert transport.calls[0][2] == "2025-11-25"

    def test_execution_signature(self) -> None:
        params = set(inspect.signature(execute_datahub_column_lineage).parameters)
        assert params == {"config", "session", "lineage_context", "column_plan", "dataset_lineage_execution", "schema_execution", "transport"}

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
