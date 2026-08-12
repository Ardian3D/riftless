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
from app.integrations.datahub.dataset_lineage_execution import (
    DataHubDatasetDownstreamSlice,
    DataHubDatasetDownstreamTarget,
    DataHubDatasetLineageExecutionError,
    DataHubDatasetLineageExecutionResult,
    DataHubDownstreamObservation,
    execute_datahub_dataset_lineage,
)
from app.integrations.datahub.entity_execution import DataHubDatasetEntityMetadata, DataHubEntityMetadataExecutionResult
from app.integrations.datahub.entity_schema_contract import (
    DataHubEntitySchemaContext,
    DataHubEntitySchemaToolDiscoveryBundle,
    bind_datahub_entity_schema_context,
)
from app.integrations.datahub.initialization import DataHubMCPSession
from app.integrations.datahub.lineage_contract import (
    DataHubDatasetLineageArgumentPlan,
    DataHubGetLineageSchemaContract,
    DataHubLineageContext,
    DataHubLineageToolDiscoveryBundle,
    bind_datahub_lineage_context,
    build_datahub_dataset_lineage_argument_plan,
    build_datahub_dataset_lineage_tools_call_request,
    discover_datahub_lineage_tool_bundle,
    serialize_datahub_dataset_lineage_tools_call_request,
)
from app.integrations.datahub.mcp_protocol import serialize_jsonrpc
from app.integrations.datahub.schema_execution import (
    DataHubAffectedFieldObservation,
    DataHubDatasetSchemaSlice,
    DataHubSchemaFieldsExecutionResult,
)
from app.integrations.datahub.search_contract import DataHubReadToolDiscoveryBundle
from app.integrations.datahub.search_execution import DataHubDatasetSearchRecord, DataHubSearchExecutionResult
from app.integrations.datahub.tool_discovery import CATALOG_VERSION, READ_TOOL_ORDER, DataHubReadToolCatalog
from app.integrations.datahub.transport import DataHubMCPHTTPResponse
from app.schemas.datahub_context import DataHubEntityKind, DataHubLineageRelation

ENDPOINT = "https://datahub.example.com/mcp"
ORDERS_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.orders,PROD)"
CUSTOMERS_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.customers,PROD)"
TARGET_DATASET_URN = "urn:li:dataset:(urn:li:dataPlatform:postgres,analytics.orders_usage,PROD)"
TARGET_DASHBOARD_URN = "urn:li:dashboard:(urn:li:dashboardPlatform:looker,orders_overview)"
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
        raise AssertionError("F8.3D2 must not send notifications")


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


def full_setup(*, observation: DataHubAffectedFieldObservation = DataHubAffectedFieldObservation.NOT_OBSERVED, urn: str = ORDERS_URN, name: str = "orders"):
    lineage_bundle, lineage_transport = lineage_discover()
    c1_bundle = lineage_bundle.entity_schema_discovery
    config, session = cfg_session()
    search_exec = search_execution(c1_bundle, records=(record(urn, name),))
    subj = subject(name)
    resolution = resolve_datahub_asset_candidate(subject=subj, search_result=search_exec)
    esc = bind_datahub_entity_schema_context(subject=subj, resolution=resolution, search_execution=search_exec, discovery=c1_bundle)
    entity_exec = entity_execution_result(esc)
    schema_exec = schema_execution_result(esc, observation=observation)
    ctx = bind_datahub_lineage_context(subject=subj, resolution=resolution, search_execution=search_exec, entity_execution=entity_exec, schema_execution=schema_exec, entity_schema_context=esc, discovery=lineage_bundle)
    plan = build_datahub_dataset_lineage_argument_plan(context=ctx, contract=lineage_bundle.get_lineage_contract)
    return config, session, lineage_bundle, ctx, plan, schema_exec


def run(response: DataHubMCPHTTPResponse, *, config=None, session=None, lineage_context=None, dataset_plan=None, schema_execution=None, transport=None):
    default_config, default_session, _, ctx, plan, schema_exec = full_setup()
    transport = transport or FakeTransport([response])
    result = execute_datahub_dataset_lineage(
        config=config if config is not None else default_config,
        session=session if session is not None else default_session,
        lineage_context=lineage_context if lineage_context is not None else ctx,
        dataset_plan=dataset_plan if dataset_plan is not None else plan,
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


def bad_plan(plan: DataHubDatasetLineageArgumentPlan, **overrides) -> DataHubDatasetLineageArgumentPlan:
    values = {
        "dataset_urn": plan.dataset_urn,
        "arguments": dict(plan.arguments),
        "input_schema_fingerprint": plan.input_schema_fingerprint,
        "plan_version": "1.0",
    }
    values.update(overrides)
    return DataHubDatasetLineageArgumentPlan.model_construct(**values)


def bad_schema_exec(schema_exec: DataHubSchemaFieldsExecutionResult, *, dataset_urn: str | None = None, next_request_id: int | None = None) -> DataHubSchemaFieldsExecutionResult:
    return DataHubSchemaFieldsExecutionResult.model_construct(
        request_id=schema_exec.request_id,
        next_request_id=next_request_id if next_request_id is not None else schema_exec.next_request_id,
        schema_request_fingerprint=schema_exec.schema_request_fingerprint,
        input_schema_fingerprint=schema_exec.input_schema_fingerprint,
        dataset_urn=dataset_urn if dataset_urn is not None else schema_exec.dataset_urn,
        schema_slice=schema_exec.schema_slice,
    )


def bad_entity_exec(ctx: DataHubLineageContext, *, dataset_urn: str = CUSTOMERS_URN) -> DataHubEntityMetadataExecutionResult:
    return DataHubEntityMetadataExecutionResult.model_construct(
        request_id=ctx.entity_execution.request_id,
        next_request_id=ctx.entity_execution.next_request_id,
        entity_request_fingerprint=ctx.entity_execution.entity_request_fingerprint,
        input_schema_fingerprint=ctx.entity_execution.input_schema_fingerprint,
        dataset_urn=dataset_urn,
        metadata=DataHubDatasetEntityMetadata(dataset_urn=dataset_urn),
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


def downstream_item(*, urn: str = TARGET_DATASET_URN, entity_type: str = "Dataset", name: str = "orders_usage", degree: object = 1, **extra) -> dict:
    entity = {"urn": urn, "type": entity_type, "name": name}
    entity.update(extra)
    return {"entity": entity, "degree": degree}


_UNSET = object()


def downstreams_payload(search_results: object = _UNSET, *, total: object = _UNSET, offset: object = _UNSET, returned: object = _UNSET, has_more: object = _UNSET, truncated: object = _UNSET, upstreams: object = _UNSET) -> dict:
    data: dict = {}
    if search_results is not _UNSET:
        data["searchResults"] = search_results
    if total is not _UNSET:
        data["total"] = total
    if offset is not _UNSET:
        data["offset"] = offset
    if returned is not _UNSET:
        data["returned"] = returned
    if has_more is not _UNSET:
        data["hasMore"] = has_more
    if truncated is not _UNSET:
        data["truncatedDueToTokenBudget"] = truncated
    payload: dict = {"downstreams": data}
    if upstreams is not _UNSET:
        payload["upstreams"] = upstreams
    return payload


def nonempty_payload(items: list[dict] | None = None, *, total: object = _UNSET, offset: int = 0, returned: object = _UNSET, has_more: bool = False, truncated: object = _UNSET) -> dict:
    items = [downstream_item()] if items is None else items
    return downstreams_payload(
        items,
        total=total,
        offset=offset,
        returned=len(items) if returned is _UNSET else returned,
        has_more=has_more,
        truncated=truncated,
    )


def mcp_response(*, content: list[dict] | None = None, result_dict: dict | None = None, is_error: object = False, response_id: int = 6) -> DataHubMCPHTTPResponse:
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
    def test_valid_d2_execution_context_accepted(self) -> None:
        result, transport = run(structured_response(nonempty_payload()))
        assert isinstance(result, DataHubDatasetLineageExecutionResult)
        assert len(transport.calls) == 1

    def test_endpoint_mismatch_zero_calls(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_copy(update={"endpoint_url": "https://other.example.com/mcp"})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), session=bad_session, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_protocol_mismatch_zero_calls(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_construct(endpoint_url=ENDPOINT, protocol_version="2024-11-05", server_name="DataHub", server_version="1", tools_supported=True, session_id="session-1")
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), session=bad_session, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_tools_unsupported_zero_calls(self) -> None:
        _, session = cfg_session()
        bad_session = session.model_copy(update={"tools_supported": False})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), session=bad_session, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_unready_catalog_zero_calls(self) -> None:
        config, session, lineage_bundle, ctx, plan, schema_exec = full_setup()
        bad_bundle = unready_lineage_bundle(lineage_bundle)
        bad_ctx = construct_lineage_ctx(ctx, discovery=bad_bundle)
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=bad_ctx, dataset_plan=plan, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_lineage_fingerprint_mismatch_zero_calls(self) -> None:
        config, session, lineage_bundle, ctx, plan, schema_exec = full_setup()
        bad_bundle = fingerprint_mismatch_lineage_bundle(lineage_bundle)
        bad_ctx = construct_lineage_ctx(ctx, discovery=bad_bundle)
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=bad_ctx, dataset_plan=plan, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_plan_fingerprint_mismatch_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        bad = bad_plan(plan, input_schema_fingerprint="0" * 64)
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, dataset_plan=bad, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_source_dataset_mismatch_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        bad = bad_plan(plan, dataset_urn=CUSTOMERS_URN, arguments={"urn": CUSTOMERS_URN, "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, dataset_plan=bad, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_entity_execution_dataset_mismatch_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        bad_entity = bad_entity_exec(ctx)
        bad_ctx = construct_lineage_ctx(ctx, entity_execution=bad_entity)
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=bad_ctx, dataset_plan=plan, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_schema_execution_dataset_mismatch_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        bad_schema = bad_schema_exec(schema_exec, dataset_urn=CUSTOMERS_URN)
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, dataset_plan=plan, schema_execution=bad_schema, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_platform_mismatch_for_source_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        postgres_subject = subject(column="customer_id").model_copy(update={"platform": "postgres"})
        bad_ctx = construct_lineage_ctx(ctx, subject=postgres_subject)
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=bad_ctx, dataset_plan=plan, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_request_id_mismatch_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        bad_schema = bad_schema_exec(schema_exec, next_request_id=7)
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, dataset_plan=plan, schema_execution=bad_schema, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_upstream_not_false_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "upstream": True, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, dataset_plan=bad, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_max_hops_not_one_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "upstream": False, "max_hops": 2, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, dataset_plan=bad, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_max_results_not_30_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "upstream": False, "max_hops": 1, "max_results": 50, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, dataset_plan=bad, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_offset_not_zero_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "upstream": False, "max_hops": 1, "max_results": 30, "offset": 30})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, dataset_plan=bad, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_column_present_in_dataset_plan_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "column": "customer_id", "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, dataset_plan=bad, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_query_present_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "query": "x", "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, dataset_plan=bad, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_filter_present_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": ORDERS_URN, "filter": "x", "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, dataset_plan=bad, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls

    def test_oversized_serialized_request_zero_calls(self) -> None:
        _, _, _, ctx, plan, schema_exec = full_setup()
        bad = bad_plan(plan, arguments={"urn": "x" * 70_000, "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0})
        transport = FakeTransport([structured_response(nonempty_payload())])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload()), lineage_context=ctx, dataset_plan=bad, schema_execution=schema_exec, transport=transport)
        assert exc.value.code == "dataset_lineage_execution_context_mismatch" and not transport.calls


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

    def test_exact_source_urn(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert json.loads(transport.calls[0][0])["params"]["arguments"]["urn"] == ORDERS_URN

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

    def test_no_column(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert "column" not in json.loads(transport.calls[0][0])["params"]["arguments"]

    def test_no_query(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert "query" not in json.loads(transport.calls[0][0])["params"]["arguments"]

    def test_no_filter(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert "filter" not in json.loads(transport.calls[0][0])["params"]["arguments"]

    def test_exact_request_id(self) -> None:
        _, _, _, ctx, _, schema_exec = full_setup()
        _, transport = run(structured_response(nonempty_payload()))
        assert json.loads(transport.calls[0][0])["id"] == ctx.dataset_lineage_request_id == schema_exec.next_request_id

    def test_exact_canonical_bytes(self) -> None:
        _, _, lineage_bundle, ctx, plan, _ = full_setup()
        _, transport = run(structured_response(nonempty_payload()))
        expected = serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=lineage_bundle.get_lineage_contract, argument_plan=plan)
        assert transport.calls[0][0] == expected
        assert transport.calls[0][0] == serialize_jsonrpc(build_datahub_dataset_lineage_tools_call_request(context=ctx, contract=lineage_bundle.get_lineage_contract, argument_plan=plan))

    def test_protocol_header_reused(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert transport.calls[0][2] == DATAHUB_MCP_PROTOCOL_VERSION == "2025-11-25"

    def test_session_header_reused(self) -> None:
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

    def test_no_column_lineage_call(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert "column" not in transport.calls[0][0].decode("utf-8")

    def test_no_pagination(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert len(transport.calls) == 1


class TestFingerprint:
    def test_deterministic_request_fingerprint(self) -> None:
        first, _ = run(structured_response(nonempty_payload()))
        second, _ = run(structured_response(nonempty_payload()))
        assert first.dataset_lineage_request_fingerprint == second.dataset_lineage_request_fingerprint

    def test_64_lowercase_hex(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert len(result.dataset_lineage_request_fingerprint) == 64
        assert re.fullmatch(r"[0-9a-f]{64}", result.dataset_lineage_request_fingerprint)

    def test_request_change_changes_fingerprint(self) -> None:
        first, _ = run(structured_response(nonempty_payload()))
        _, _, lineage_bundle, ctx, plan, _ = full_setup()
        config2, session2, lineage_bundle2, ctx2, plan2, _ = full_setup(urn=CUSTOMERS_URN, name="customers")
        body_a = serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=lineage_bundle.get_lineage_contract, argument_plan=plan)
        body_b = serialize_datahub_dataset_lineage_tools_call_request(context=ctx2, contract=lineage_bundle2.get_lineage_contract, argument_plan=plan2)
        assert body_a != body_b
        assert first.dataset_lineage_request_fingerprint == hashlib.sha256(body_a).hexdigest()
        assert first.dataset_lineage_request_fingerprint != hashlib.sha256(body_b).hexdigest()
        _ = (config2, session2)

    def test_endpoint_excluded(self) -> None:
        result, transport = run(structured_response(nonempty_payload()))
        assert ENDPOINT.encode() not in transport.calls[0][0]
        assert "datahub.example.com" not in result.dataset_lineage_request_fingerprint

    def test_token_excluded(self) -> None:
        result, transport = run(structured_response(nonempty_payload()))
        assert b"test-token" not in transport.calls[0][0]
        assert "test-token" not in result.dataset_lineage_request_fingerprint

    def test_session_excluded(self) -> None:
        result, transport = run(structured_response(nonempty_payload()))
        assert b"session-1" not in transport.calls[0][0]
        assert "session-1" not in result.dataset_lineage_request_fingerprint

    def test_response_excluded(self) -> None:
        result, transport = run(structured_response(nonempty_payload()))
        assert result.dataset_lineage_request_fingerprint == hashlib.sha256(transport.calls[0][0]).hexdigest()


class TestCallToolResult:
    def test_valid_call_tool_result_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.downstream_slice.source_dataset_urn == ORDERS_URN

    def test_is_error_absent_false(self) -> None:
        response = mcp_response(result_dict={"structuredContent": nonempty_payload()}, is_error=None)
        result, _ = run(response)
        assert result.source_dataset_urn == ORDERS_URN

    def test_is_error_false_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload(), is_error=False))
        assert result.source_dataset_urn == ORDERS_URN

    def test_is_error_true_safe_failure(self) -> None:
        transport = FakeTransport([structured_response(nonempty_payload(), is_error=True)])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload(), is_error=True), transport=transport)
        assert exc.value.code == "dataset_lineage_tool_execution_failed" and len(transport.calls) == 1

    def test_non_bool_is_error_rejected(self) -> None:
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload(), is_error="true"))
        assert exc.value.code == "invalid_dataset_lineage_tool_result"

    def test_content_required(self) -> None:
        response = DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, json.dumps({"jsonrpc": "2.0", "id": 6, "result": {"structuredContent": nonempty_payload()}}).encode())
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_dataset_lineage_tool_result"

    def test_content_list_required(self) -> None:
        response = mcp_response(content={"not": "a list"}, result_dict={"structuredContent": nonempty_payload()})
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_dataset_lineage_tool_result"

    def test_max_blocks_enforced(self) -> None:
        response = structured_response(nonempty_payload(), content=[{"type": "text", "text": "x"} for _ in range(9)])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "unsupported_dataset_lineage_content"

    def test_valid_text_block_accepted(self) -> None:
        result, _ = run(text_response(nonempty_payload()))
        assert result.source_dataset_urn == ORDERS_URN

    def test_unsupported_content_type_rejected(self) -> None:
        response = structured_response(nonempty_payload(), content=[{"type": "image", "data": "x"}])
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "unsupported_dataset_lineage_content"

    def test_utf8_enforced(self) -> None:
        response = text_response(nonempty_payload(), text="\ud800")
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "unsupported_dataset_lineage_content"

    def test_null_byte_rejected(self) -> None:
        response = text_response(nonempty_payload(), text='{"downstreams": {"x": "y\u0000"}}')
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "dataset_lineage_content_too_large"

    def test_individual_text_bound(self) -> None:
        big = "x" * 262_145
        response = mcp_response(content=[{"type": "text", "text": big}], result_dict={"structuredContent": nonempty_payload()})
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "dataset_lineage_content_too_large"

    def test_combined_text_bound(self) -> None:
        response = mcp_response(content=[{"type": "text", "text": "x" * 200_000}, {"type": "text", "text": "y" * 200_000}], result_dict={"structuredContent": nonempty_payload()})
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "dataset_lineage_content_too_large"

    def test_structured_size_bound(self) -> None:
        payload = nonempty_payload()
        payload["blob"] = "x" * 524_300
        response = mcp_response(result_dict={"structuredContent": payload})
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "dataset_lineage_content_too_large"

    def test_meta_ignored(self) -> None:
        result, _ = run(mcp_response(result_dict={"structuredContent": nonempty_payload(), "_meta": {"progressToken": "t"}}))
        assert result.source_dataset_urn == ORDERS_URN

    def test_unknown_result_fields_ignored(self) -> None:
        result, _ = run(mcp_response(result_dict={"structuredContent": nonempty_payload(), "unknown": {"x": 1}}))
        assert result.source_dataset_urn == ORDERS_URN

    def test_raw_call_tool_result_discarded(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        for token in ("structuredContent", "isError", "CallToolResult", "content"):
            assert token not in dumped


class TestPayloadSource:
    def test_direct_structured_content_object_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.downstream_slice.downstream_observation is DataHubDownstreamObservation.OBSERVED

    def test_structured_content_priority_over_text(self) -> None:
        response = mcp_response(content=[{"type": "text", "text": "this is not json"}], result_dict={"structuredContent": nonempty_payload()})
        result, _ = run(response)
        assert result.downstream_slice.downstream_observation is DataHubDownstreamObservation.OBSERVED

    def test_text_not_parsed_when_structured_selected(self) -> None:
        response = mcp_response(content=[{"type": "text", "text": "this is not json"}], result_dict={"structuredContent": nonempty_payload()})
        result, _ = run(response)
        assert result.downstream_slice.targets[0].urn == TARGET_DATASET_URN

    def test_structured_content_non_object_rejected(self) -> None:
        response = mcp_response(result_dict={"structuredContent": [1, 2]})
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_strict_object_text_fallback_accepted(self) -> None:
        result, _ = run(text_response(nonempty_payload()))
        assert result.downstream_slice.targets[0].urn == TARGET_DATASET_URN

    def test_array_fallback_rejected(self) -> None:
        response = text_response(nonempty_payload(), text=json.dumps([nonempty_payload()]))
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_primitive_rejected(self) -> None:
        response = text_response(nonempty_payload(), text='"just a string"')
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_fence_rejected(self) -> None:
        response = text_response(nonempty_payload(), text="```json\n" + json.dumps(nonempty_payload()) + "\n```")
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_prose_prefix_rejected(self) -> None:
        response = text_response(nonempty_payload(), text="result " + json.dumps(nonempty_payload()))
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_prose_suffix_rejected(self) -> None:
        response = text_response(nonempty_payload(), text=json.dumps(nonempty_payload()) + " done")
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_duplicate_keys_rejected(self) -> None:
        response = text_response(nonempty_payload(), text='{"downstreams": {"x": 1, "x": 2}}')
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_nan_infinity_rejected(self) -> None:
        for text in ('{"downstreams": {"x": NaN}}', '{"downstreams": {"x": Infinity}}', '{"downstreams": {"x": -Infinity}}'):
            with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
                run(text_response(nonempty_payload(), text=text))
            assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_null_byte_rejected(self) -> None:
        response = text_response(nonempty_payload(), text='{"downstreams": {"x": "y\u0000"}}')
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "dataset_lineage_content_too_large"

    def test_malformed_json_rejected(self) -> None:
        response = text_response(nonempty_payload(), text="{")
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(response)
        assert exc.value.code == "invalid_dataset_lineage_payload"


class TestDirection:
    def test_downstreams_object_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.downstream_slice.downstream_observation is DataHubDownstreamObservation.OBSERVED

    def test_missing_downstreams_rejected(self) -> None:
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response({"other": {}}))
        assert exc.value.code == "dataset_lineage_direction_mismatch"

    def test_non_object_downstreams_rejected(self) -> None:
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response({"downstreams": []}))
        assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_absent_upstreams_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.source_dataset_urn == ORDERS_URN

    def test_semantically_empty_upstreams_ignored(self) -> None:
        payload = downstreams_payload([downstream_item()], offset=0, returned=1, has_more=False, upstreams={"total": 0})
        result, _ = run(structured_response(payload))
        assert result.downstream_slice.downstream_observation is DataHubDownstreamObservation.OBSERVED

    def test_non_empty_upstream_data_rejected(self) -> None:
        payload = downstreams_payload([downstream_item()], offset=0, returned=1, has_more=False, upstreams={"searchResults": [downstream_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,raw.orders,PROD)")]})
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "dataset_lineage_direction_mismatch"

    def test_upstream_data_never_normalized(self) -> None:
        payload = downstreams_payload([downstream_item()], offset=0, returned=1, has_more=False, upstreams={"searchResults": [downstream_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,raw.orders,PROD)", name="raw_orders")]})
        with pytest.raises(DataHubDatasetLineageExecutionError):
            run(structured_response(payload))


class TestZeroResult:
    def test_empty_downstreams_compatible_zero_observation(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.downstream_slice.downstream_observation is DataHubDownstreamObservation.NOT_OBSERVED
        assert result.downstream_slice.targets == ()

    def test_downstreams_total_zero_without_search_results_accepted(self) -> None:
        result, _ = run(structured_response(downstreams_payload(total=0)))
        assert result.downstream_slice.downstream_observation is DataHubDownstreamObservation.NOT_OBSERVED
        assert result.downstream_slice.provider_total == 0

    def test_missing_search_results_zero_targets(self) -> None:
        result, _ = run(structured_response(downstreams_payload(total=0)))
        assert len(result.downstream_slice.targets) == 0

    def test_zero_targets_not_observed(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.downstream_slice.downstream_observation is DataHubDownstreamObservation.NOT_OBSERVED

    def test_zero_targets_does_not_mean_no_consumers(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        dumped = json.dumps(result.model_dump())
        assert "no_consumers" not in dumped and "no_consumers" not in repr(result.downstream_slice)

    def test_absent_returned_remains_none(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.downstream_slice.provider_returned is None

    def test_absent_offset_remains_none(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.downstream_slice.provider_offset is None

    def test_absent_has_more_remains_none(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.downstream_slice.provider_has_more is None

    def test_absent_truncation_flag_remains_none(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.downstream_slice.provider_truncated_due_to_token_budget is None

    def test_present_returned_zero_accepted(self) -> None:
        result, _ = run(structured_response(downstreams_payload([], offset=0, returned=0, has_more=False)))
        assert result.downstream_slice.provider_returned == 0
        assert result.downstream_slice.downstream_observation is DataHubDownstreamObservation.NOT_OBSERVED

    def test_present_offset_zero_accepted(self) -> None:
        result, _ = run(structured_response(downstreams_payload([], offset=0, returned=0, has_more=False)))
        assert result.downstream_slice.provider_offset == 0

    def test_present_has_more_real_bool_accepted(self) -> None:
        result, _ = run(structured_response(downstreams_payload([], offset=0, returned=0, has_more=True)))
        assert result.downstream_slice.provider_has_more is True

    def test_malformed_zero_result_pagination_rejected(self) -> None:
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(downstreams_payload([], offset=0, returned="0", has_more=False)))
        assert exc.value.code == "invalid_dataset_lineage_payload"


class TestNonemptyResult:
    def test_one_target_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert len(result.downstream_slice.targets) == 1

    def test_thirty_targets_accepted(self) -> None:
        items = [downstream_item(urn=f"urn:li:dataset:(urn:li:dataPlatform:postgres,db.t{i},PROD)") for i in range(30)]
        result, _ = run(structured_response(nonempty_payload(items)))
        assert len(result.downstream_slice.targets) == 30

    def test_over_30_rejected(self) -> None:
        items = [downstream_item(urn=f"urn:li:dataset:(urn:li:dataPlatform:postgres,db.t{i},PROD)") for i in range(31)]
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload(items)))
        assert exc.value.code == "dataset_lineage_count_mismatch"

    def test_returned_required_when_nonempty(self) -> None:
        payload = downstreams_payload([downstream_item()], offset=0, has_more=False)
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_returned_equals_len_results(self) -> None:
        result, _ = run(structured_response(nonempty_payload([downstream_item()])))
        assert result.downstream_slice.provider_returned == 1 == len(result.downstream_slice.targets)

    def test_returned_mismatch_rejected(self) -> None:
        payload = downstreams_payload([downstream_item()], offset=0, returned=2, has_more=False)
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "dataset_lineage_count_mismatch"

    def test_offset_required_nonempty_exact_zero(self) -> None:
        payload = downstreams_payload([downstream_item()], offset=1, returned=1, has_more=False)
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_has_more_required_nonempty_real_bool(self) -> None:
        payload = downstreams_payload([downstream_item()], offset=0, returned=1, has_more=False)
        result, _ = run(structured_response(payload))
        assert result.downstream_slice.provider_has_more is False

    def test_has_more_integer_rejected(self) -> None:
        payload = downstreams_payload([downstream_item()], offset=0, returned=1, has_more=1)
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_truncation_bool_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload(truncated=True)))
        assert result.downstream_slice.provider_truncated_due_to_token_budget is True

    def test_truncation_non_bool_rejected(self) -> None:
        payload = downstreams_payload([downstream_item()], offset=0, returned=1, has_more=False, truncated="yes")
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_provider_total_optional(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.downstream_slice.provider_total is None

    def test_valid_provider_total_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload(total=5)))
        assert result.downstream_slice.provider_total == 5

    def test_total_below_returned_rejected(self) -> None:
        payload = nonempty_payload([downstream_item(), downstream_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,db.t2,PROD)")], total=1, returned=2)
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "dataset_lineage_count_mismatch"

    def test_bool_total_rejected(self) -> None:
        payload = downstreams_payload([downstream_item()], total=True, offset=0, returned=1, has_more=False)
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_dataset_lineage_payload"

    def test_total_bound_enforced(self) -> None:
        payload = downstreams_payload([downstream_item()], total=1_000_001, offset=0, returned=1, has_more=False)
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(payload))
        assert exc.value.code == "invalid_dataset_lineage_payload"


class TestTargets:
    def test_valid_generic_datahub_target_urn(self) -> None:
        result, _ = run(structured_response(nonempty_payload([downstream_item(urn=TARGET_DASHBOARD_URN, entity_type="Dashboard", name="orders_overview")])))
        assert result.downstream_slice.targets[0].urn == TARGET_DASHBOARD_URN
        assert result.downstream_slice.targets[0].entity_kind is DataHubEntityKind.DASHBOARD

    def test_missing_target_urn_rejected(self) -> None:
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([downstream_item(urn=None)])))
        assert exc.value.code == "invalid_dataset_lineage_target"

    def test_blank_target_urn_rejected(self) -> None:
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([downstream_item(urn="   ")])))
        assert exc.value.code == "invalid_dataset_lineage_target"

    def test_malformed_target_urn_rejected(self) -> None:
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([downstream_item(urn="not-a-urn")])))
        assert exc.value.code == "invalid_dataset_lineage_target"

    def test_oversized_urn_rejected(self) -> None:
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([downstream_item(urn="urn:li:" + "x" * 1100)])))
        assert exc.value.code == "invalid_dataset_lineage_target"

    def test_duplicate_target_urn_rejected(self) -> None:
        items = [downstream_item(), downstream_item(name="orders_usage_2")]
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload(items, returned=2)))
        assert exc.value.code == "duplicate_dataset_lineage_target"

    def test_duplicate_target_not_silently_deduped(self) -> None:
        items = [downstream_item(), downstream_item(name="orders_usage_2")]
        with pytest.raises(DataHubDatasetLineageExecutionError):
            run(structured_response(nonempty_payload(items, returned=2)))

    def test_non_dataset_target_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload([downstream_item(urn=TARGET_DASHBOARD_URN, entity_type="Dashboard")])))
        assert result.downstream_slice.targets[0].entity_kind is DataHubEntityKind.DASHBOARD

    def test_cross_platform_dataset_target_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload([downstream_item(urn=CROSS_PLATFORM_URN)])))
        assert result.downstream_slice.targets[0].urn == CROSS_PLATFORM_URN

    def test_source_platform_not_target_eligibility_gate(self) -> None:
        result, _ = run(structured_response(nonempty_payload([downstream_item(urn="urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.orders_usage,PROD)")])))
        assert len(result.downstream_slice.targets) == 1

    def test_bounded_target_display_data(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.downstream_slice.targets[0].display_name == "orders_usage"

    def test_arbitrary_target_metadata_discarded(self) -> None:
        result, _ = run(structured_response(nonempty_payload([downstream_item(extra_prop={"x": 1})])))
        dumped = json.dumps(result.model_dump())
        assert "extra_prop" not in dumped and '"x"' not in dumped

    def test_target_descriptions_discarded(self) -> None:
        result, _ = run(structured_response(nonempty_payload([downstream_item(description="usage table")])))
        assert "usage table" not in json.dumps(result.model_dump())

    def test_target_urls_discarded(self) -> None:
        result, _ = run(structured_response(nonempty_payload([downstream_item(url="https://example.com")])))
        assert "example.com" not in json.dumps(result.model_dump())

    def test_target_sql_query_discarded(self) -> None:
        result, _ = run(structured_response(nonempty_payload([downstream_item(sql="select * from orders")])))
        assert "select * from orders" not in json.dumps(result.model_dump())


class TestDegree:
    def test_degree_one_accepted(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.downstream_slice.targets[0].depth == 1

    def test_bool_degree_rejected(self) -> None:
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([downstream_item(degree=True)])))
        assert exc.value.code == "invalid_dataset_lineage_target"

    def test_degree_zero_rejected(self) -> None:
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([downstream_item(degree=0)])))
        assert exc.value.code == "invalid_dataset_lineage_target"

    def test_degree_two_rejected(self) -> None:
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([downstream_item(degree=2)])))
        assert exc.value.code == "invalid_dataset_lineage_target"

    def test_string_degree_rejected(self) -> None:
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([downstream_item(degree="1")])))
        assert exc.value.code == "invalid_dataset_lineage_target"

    def test_missing_degree_rejected(self) -> None:
        item = {"entity": {"urn": TARGET_DATASET_URN, "type": "Dataset", "name": "orders_usage"}}
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload([item])))
        assert exc.value.code == "invalid_dataset_lineage_target"

    def test_degree_never_affects_risk_score(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert "risk" not in json.dumps(result.model_dump())

    def test_degree_never_acts_as_priority(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert "priority" not in json.dumps(result.model_dump()) and "severity" not in json.dumps(result.model_dump())


class TestProviderOrder:
    def test_provider_order_preserved_as_observation(self) -> None:
        items = [downstream_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,db.a,PROD)"), downstream_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,db.b,PROD)")]
        result, _ = run(structured_response(nonempty_payload(items, returned=2)))
        assert [t.urn for t in result.downstream_slice.targets] == [items[0]["entity"]["urn"], items[1]["entity"]["urn"]]

    def test_order_does_not_change_target_identity(self) -> None:
        items = [downstream_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,db.a,PROD)"), downstream_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,db.b,PROD)")]
        forward = run(structured_response(nonempty_payload(items, returned=2)))[0]
        reversed_result = run(structured_response(nonempty_payload(list(reversed(items)), returned=2)))[0]
        assert {t.urn for t in forward.downstream_slice.targets} == {t.urn for t in reversed_result.downstream_slice.targets}

    def test_first_result_no_special_authority(self) -> None:
        items = [downstream_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,db.a,PROD)"), downstream_item(urn="urn:li:dataset:(urn:li:dataPlatform:postgres,db.b,PROD)")]
        result, _ = run(structured_response(nonempty_payload(items, returned=2)))
        assert result.downstream_slice.downstream_observation is DataHubDownstreamObservation.OBSERVED

    def test_no_risk_ranking_from_order(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert "risk" not in json.dumps(result.model_dump())

    def test_no_source_position_authority_field(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert "source_position" not in json.dumps(result.model_dump())


class TestHasMoreCompleteness:
    def test_has_more_false_preserved_as_observation(self) -> None:
        result, _ = run(structured_response(nonempty_payload(has_more=False)))
        assert result.downstream_slice.provider_has_more is False

    def test_has_more_false_creates_no_complete_field(self) -> None:
        result, _ = run(structured_response(nonempty_payload(has_more=False)))
        assert "complete" not in json.dumps(result.model_dump())

    def test_has_more_true_creates_no_second_call(self) -> None:
        _, transport = run(structured_response(nonempty_payload(has_more=True)))
        assert len(transport.calls) == 1

    def test_has_more_true_creates_no_pagination(self) -> None:
        result, transport = run(structured_response(nonempty_payload(has_more=True)))
        assert len(transport.calls) == 1
        assert json.loads(transport.calls[0][0])["params"]["arguments"]["offset"] == 0

    def test_absent_has_more_does_not_synthesize_false(self) -> None:
        result, _ = run(structured_response(downstreams_payload()))
        assert result.downstream_slice.provider_has_more is None

    def test_token_truncation_true_creates_no_retry(self) -> None:
        _, transport = run(structured_response(nonempty_payload(truncated=True)))
        assert len(transport.calls) == 1

    def test_token_truncation_true_creates_no_second_call(self) -> None:
        result, transport = run(structured_response(nonempty_payload(truncated=True)))
        assert len(transport.calls) == 1
        assert result.downstream_slice.provider_truncated_due_to_token_budget is True

    def test_provider_total_zero_no_authoritative_no_consumers_claim(self) -> None:
        result, _ = run(structured_response(downstreams_payload(total=0)))
        assert result.downstream_slice.downstream_observation is DataHubDownstreamObservation.NOT_OBSERVED
        assert "no_consumers" not in json.dumps(result.model_dump())


class TestResult:
    def test_exact_immutable_execution_result_fields(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert set(result.model_dump()) == {"request_id", "next_request_id", "dataset_lineage_request_fingerprint", "input_schema_fingerprint", "source_dataset_urn", "downstream_slice", "result_version"}

    def test_request_id_exact_d1_dataset_id(self) -> None:
        _, _, _, ctx, _, _ = full_setup()
        result, _ = run(structured_response(nonempty_payload()))
        assert result.request_id == ctx.dataset_lineage_request_id

    def test_next_request_id_equals_request_plus_one(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.next_request_id == result.request_id + 1

    def test_next_id_equals_d1_column_lineage_request_id(self) -> None:
        _, _, _, ctx, _, _ = full_setup()
        result, _ = run(structured_response(nonempty_payload()))
        assert result.next_request_id == ctx.column_lineage_request_id

    def test_fingerprint_preserved(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert re.fullmatch(r"[0-9a-f]{64}", result.dataset_lineage_request_fingerprint)

    def test_input_schema_fingerprint_preserved(self) -> None:
        _, _, _, ctx, plan, _ = full_setup()
        result, _ = run(structured_response(nonempty_payload()))
        assert result.input_schema_fingerprint == plan.input_schema_fingerprint == ctx.discovery.get_lineage_contract.input_schema_fingerprint

    def test_source_dataset_exact(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.source_dataset_urn == ORDERS_URN

    def test_downstream_slice_immutable(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.downstream_slice.model_config["frozen"] is True

    def test_targets_immutable(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert isinstance(result.downstream_slice.targets, tuple)

    def test_target_entries_immutable(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        target = result.downstream_slice.targets[0]
        assert isinstance(target, DataHubDatasetDownstreamTarget)
        assert target.model_config["frozen"] is True
        assert target.relation is DataHubLineageRelation.DOWNSTREAM and target.depth == 1
        assert result.model_config["frozen"] is True
        assert result.downstream_slice.model_config["frozen"] is True

    def test_result_version_fixed(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert result.result_version == "1.0"
        assert result.downstream_slice.slice_version == "1.0"

    def test_no_raw_request_args(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        assert "arguments" not in dumped and "max_hops" not in dumped and "max_results" not in dumped

    def test_no_raw_provider_result(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        assert "downstreams" not in dumped and "searchResults" not in dumped

    def test_no_content_structured_content(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        assert "content" not in dumped and "structuredContent" not in dumped and "isError" not in dumped

    def test_no_token_endpoint_session(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        for token in ("datahub.example.com", "test-token", "session-1"):
            assert token not in dumped

    def test_no_validation_authority(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert "validation" not in json.dumps(result.model_dump())

    def test_no_risk_authority(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert "risk" not in json.dumps(result.model_dump())

    def test_no_deployment_authority(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        assert "deployment" not in json.dumps(result.model_dump())

    def test_no_writeback_authority(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        dumped = json.dumps(result.model_dump())
        assert "writeback" not in dumped and "authority" not in dumped


class TestDeepImmutability:
    def test_downstream_target_model_is_frozen(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        target = result.downstream_slice.targets[0]
        assert isinstance(target, DataHubDatasetDownstreamTarget)
        assert target.model_config["frozen"] is True

    def test_target_urn_cannot_be_changed_after_creation(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.downstream_slice.targets[0].urn = CUSTOMERS_URN  # type: ignore[misc]

    def test_target_entity_kind_cannot_be_changed(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.downstream_slice.targets[0].entity_kind = DataHubEntityKind.DATA_JOB  # type: ignore[misc]

    def test_target_display_name_cannot_be_changed(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.downstream_slice.targets[0].display_name = "MUTATED"  # type: ignore[misc]

    def test_target_relation_cannot_be_changed(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.downstream_slice.targets[0].relation = DataHubLineageRelation.SUBJECT  # type: ignore[misc]

    def test_target_depth_cannot_be_changed(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.downstream_slice.targets[0].depth = 2  # type: ignore[misc]

    def test_slice_targets_cannot_be_replaced(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.downstream_slice.targets = ()  # type: ignore[misc]

    def test_target_tuple_cannot_be_mutated(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(TypeError):
            result.downstream_slice.targets[0] = result.downstream_slice.targets[0]

    def test_execution_result_slice_cannot_be_replaced(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        with pytest.raises(ValidationError):
            result.downstream_slice = result.downstream_slice  # type: ignore[misc]

    def test_no_mutable_lineage_node_nested_in_target(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        target = result.downstream_slice.targets[0]
        assert type(target).__name__ == "DataHubDatasetDownstreamTarget"
        assert "DataHubLineageNode" not in repr(target)

    def test_normalized_target_has_no_raw_provider_dict(self) -> None:
        result, _ = run(structured_response(nonempty_payload([downstream_item(extra_prop={"x": 1}, sql="select 1")])))
        target = result.downstream_slice.targets[0]
        assert set(target.model_dump()) == {"urn", "entity_kind", "display_name", "relation", "depth"}
        assert "extra_prop" not in repr(target) and "select 1" not in repr(target)

    def test_mutation_attempt_cannot_alter_serialization(self) -> None:
        result, _ = run(structured_response(nonempty_payload()))
        before = json.dumps(result.model_dump())
        with pytest.raises(ValidationError):
            result.downstream_slice.targets[0].display_name = "MUTATED"  # type: ignore[misc]
        assert json.dumps(result.model_dump()) == before

    def test_provider_input_mutation_cannot_change_normalized_evidence(self) -> None:
        item = downstream_item()
        result, _ = run(structured_response(nonempty_payload([item])))
        before_urn = result.downstream_slice.targets[0].urn
        item["entity"]["urn"] = CUSTOMERS_URN
        item["entity"]["name"] = "MUTATED"
        item["degree"] = 5
        assert result.downstream_slice.targets[0].urn == before_urn
        assert result.downstream_slice.targets[0].display_name == "orders_usage"
        assert result.downstream_slice.targets[0].depth == 1

    def test_duplicate_target_behavior_remains_unchanged(self) -> None:
        items = [downstream_item(), downstream_item(name="orders_usage_2")]
        with pytest.raises(DataHubDatasetLineageExecutionError) as exc:
            run(structured_response(nonempty_payload(items, returned=2)))
        assert exc.value.code == "duplicate_dataset_lineage_target"

    def test_cross_platform_target_behavior_remains_unchanged(self) -> None:
        result, _ = run(structured_response(nonempty_payload([downstream_item(urn=CROSS_PLATFORM_URN)])))
        assert result.downstream_slice.targets[0].urn == CROSS_PLATFORM_URN

    def test_non_dataset_target_behavior_remains_unchanged(self) -> None:
        result, _ = run(structured_response(nonempty_payload([downstream_item(urn=TARGET_DASHBOARD_URN, entity_type="Dashboard")])))
        assert result.downstream_slice.targets[0].entity_kind is DataHubEntityKind.DASHBOARD

    def test_entity_kind_mapping_remains_unchanged(self) -> None:
        chart = run(structured_response(nonempty_payload([downstream_item(entity_type="Chart", name="c")])))[0]
        assert chart.downstream_slice.targets[0].entity_kind is DataHubEntityKind.CHART
        unknown = run(structured_response(nonempty_payload([downstream_item(entity_type="DataJob")])))[0]
        assert unknown.downstream_slice.targets[0].entity_kind is DataHubEntityKind.OTHER

    def test_degree_one_behavior_remains_unchanged(self) -> None:
        result, _ = run(structured_response(nonempty_payload([downstream_item(degree=1)])))
        assert result.downstream_slice.targets[0].depth == 1
        with pytest.raises(DataHubDatasetLineageExecutionError):
            run(structured_response(nonempty_payload([downstream_item(degree=2)])))

    def test_no_extra_mcp_call_introduced(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert len(transport.calls) == 1
        assert json.loads(transport.calls[0][0])["params"]["name"] == "get_lineage"

    def test_no_pagination_introduced(self) -> None:
        _, transport = run(structured_response(nonempty_payload(has_more=True, truncated=True)))
        assert len(transport.calls) == 1

    def test_no_column_lineage_execution_introduced(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert '"column"' not in transport.calls[0][0].decode("utf-8")


class TestScopeRegression:
    def test_no_column_lineage_execution(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/dataset_lineage_execution.py").read_text(encoding="utf-8")
        assert "execute_datahub_column_lineage" not in source
        assert "build_datahub_column_lineage_tools_call_request" not in source

    def test_no_request_with_column_argument(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert '"column"' not in transport.calls[0][0].decode("utf-8")

    def test_no_get_lineage_paths_between(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/dataset_lineage_execution.py").read_text(encoding="utf-8")
        assert "get_lineage_paths_between" not in source

    def test_no_search(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/dataset_lineage_execution.py").read_text(encoding="utf-8")
        assert "execute_datahub_search" not in source

    def test_no_get_entities(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/dataset_lineage_execution.py").read_text(encoding="utf-8")
        assert "get_entities" not in source

    def test_no_list_schema_fields(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/dataset_lineage_execution.py").read_text(encoding="utf-8")
        assert "list_schema_fields" not in source

    def test_no_tools_list(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/dataset_lineage_execution.py").read_text(encoding="utf-8")
        assert "tools/list" not in source

    def test_no_initialization(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/dataset_lineage_execution.py").read_text(encoding="utf-8")
        assert "initialize" not in source

    def test_no_retry(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert len(transport.calls) == 1

    def test_no_pagination(self) -> None:
        _, transport = run(structured_response(nonempty_payload(has_more=True, truncated=True)))
        assert len(transport.calls) == 1

    def test_no_deepseek(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/dataset_lineage_execution.py").read_text(encoding="utf-8")
        assert "DeepSeek" not in source

    def test_no_persistence(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/dataset_lineage_execution.py").read_text(encoding="utf-8")
        assert "persistence" not in source

    def test_no_fastapi_integration(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/dataset_lineage_execution.py").read_text(encoding="utf-8")
        assert "FastAPI" not in source and "APIRouter" not in source

    def test_no_live_network(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/dataset_lineage_execution.py").read_text(encoding="utf-8")
        for token in ("import requests", "import httpx", "import aiohttp", "urllib", "http.client", "os.environ", "json_repair", "except Exception", "logging", "print("):
            assert token not in source

    def test_protocol_remains_2025_11_25(self) -> None:
        _, transport = run(structured_response(nonempty_payload()))
        assert transport.calls[0][2] == "2025-11-25"

    def test_execution_signature(self) -> None:
        params = set(inspect.signature(execute_datahub_dataset_lineage).parameters)
        assert params == {"config", "session", "lineage_context", "dataset_plan", "schema_execution", "transport"}

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
