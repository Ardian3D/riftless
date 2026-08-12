from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.integrations.datahub.asset_resolution import (
    DataHubAssetCandidateResolution,
    DataHubAssetResolutionConfidence,
    DataHubAssetResolutionMethod,
    DataHubAssetResolutionStatus,
    DataHubAssetResolutionSubject,
    resolve_datahub_asset_candidate,
)
from app.integrations.datahub.config import DATAHUB_MCP_PROTOCOL_VERSION, load_datahub_mcp_config
from app.integrations.datahub.entity_execution import DataHubDatasetEntityMetadata, DataHubEntityMetadataExecutionResult
from app.integrations.datahub.entity_schema_contract import (
    DataHubEntitySchemaContext,
    DataHubEntitySchemaToolDiscoveryBundle,
    DataHubGetEntitiesSchemaContract,
    DataHubListSchemaFieldsSchemaContract,
    bind_datahub_entity_schema_context,
    discover_datahub_entity_schema_tool_bundle,
)
from app.integrations.datahub.initialization import DataHubMCPSession
from app.integrations.datahub.lineage_contract import (
    DataHubColumnLineageArgumentPlan,
    DataHubDatasetLineageArgumentPlan,
    DataHubGetLineageSchemaContract,
    DataHubLineageContractError,
    DataHubLineageContext,
    DataHubLineageToolDiscoveryBundle,
    attest_datahub_get_lineage_schema,
    bind_datahub_lineage_context,
    build_datahub_column_lineage_argument_plan,
    build_datahub_column_lineage_tools_call_request,
    build_datahub_dataset_lineage_argument_plan,
    build_datahub_dataset_lineage_tools_call_request,
    discover_datahub_lineage_tool_bundle,
    serialize_datahub_column_lineage_tools_call_request,
    serialize_datahub_dataset_lineage_tools_call_request,
)
from app.integrations.datahub.mcp_protocol import serialize_jsonrpc
from app.integrations.datahub.schema_execution import (
    DataHubAffectedFieldObservation,
    DataHubDatasetSchemaSlice,
    DataHubSchemaFieldsExecutionResult,
)
from app.integrations.datahub.search_contract import discover_datahub_read_tool_bundle
from app.integrations.datahub.search_execution import DataHubDatasetSearchRecord, DataHubSearchExecutionResult
from app.integrations.datahub.tool_discovery import CATALOG_VERSION, READ_TOOL_ORDER, DataHubReadToolCatalog, discover_datahub_read_tools, fingerprint_datahub_tool_input_schema
from app.integrations.datahub.transport import DataHubMCPHTTPResponse
from app.schemas.datahub_context import DataHubFieldMetadata

ENDPOINT = "https://datahub.example.com/mcp"
ORDERS_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.orders,PROD)"
CUSTOMERS_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.customers,PROD)"

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


def fp(schema: dict) -> str:
    return fingerprint_datahub_tool_input_schema(schema)


def required_tools(*, get_lineage_schema: dict | None = None, get_entities_schema: dict | None = None) -> list[dict]:
    out = []
    for item in READ_TOOL_ORDER:
        name = item.value
        if name == "search":
            s = search_schema()
        elif name == "get_entities":
            s = GET_ENTITIES_SCHEMA if get_entities_schema is None else get_entities_schema
        elif name == "list_schema_fields":
            s = LIST_SCHEMA_FIELDS_SCHEMA
        else:
            s = GET_LINEAGE_SCHEMA if get_lineage_schema is None else get_lineage_schema
        out.append({"name": name, "inputSchema": s})
    return out


def page(tools: list[dict], request_id: int = 2, next_cursor: str | None = None) -> DataHubMCPHTTPResponse:
    result = {"tools": tools}
    if next_cursor is not None:
        result["nextCursor"] = next_cursor
    body = json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}).encode()
    return DataHubMCPHTTPResponse(200, {"Content-Type": "application/json"}, body)


class FakeTransport:
    def __init__(self, responses: list[DataHubMCPHTTPResponse]):
        self.responses = responses
        self.calls: list[tuple[bytes, str | None, str | None]] = []

    def post_request(self, body: bytes, *, session_id: str | None, protocol_version: str | None):
        self.calls.append((body, session_id, protocol_version))
        return self.responses[len(self.calls) - 1]

    def post_notification(self, body: bytes, *, session_id: str | None, protocol_version: str):
        raise AssertionError("F8.3D1 must not send notifications")


def cfg_session() -> tuple[object, DataHubMCPSession]:
    config = load_datahub_mcp_config({"DATAHUB_MCP_URL": ENDPOINT, "DATAHUB_TOKEN": "test-token"})
    session = DataHubMCPSession(endpoint_url=ENDPOINT, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION, server_name="DataHub", server_version="1", tools_supported=True, session_id="session-1")
    return config, session


def lineage_discover(*, get_lineage_schema: dict | None = None, get_entities_schema: dict | None = None, responses: list[DataHubMCPHTTPResponse] | None = None):
    config, session = cfg_session()
    transport = FakeTransport(responses or [page(required_tools(get_lineage_schema=get_lineage_schema, get_entities_schema=get_entities_schema))])
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
    if observation is DataHubAffectedFieldObservation.OBSERVED_EXACT:
        field = DataHubFieldMetadata(field_path=context.affected_column)
        schema_slice = DataHubDatasetSchemaSlice(
            dataset_urn=context.dataset_urn,
            fields=(field,),
            provider_total_fields=1,
            provider_returned=1,
            provider_remaining_count=0,
            provider_matching_count=1,
            provider_offset=0,
            affected_field_observation=observation,
            affected_field=field,
        )
    else:
        schema_slice = DataHubDatasetSchemaSlice(
            dataset_urn=context.dataset_urn,
            fields=(),
            provider_total_fields=0,
            provider_returned=0,
            provider_remaining_count=0,
            provider_matching_count=None,
            provider_offset=0,
            affected_field_observation=observation,
            affected_field=None,
        )
    return DataHubSchemaFieldsExecutionResult(
        request_id=context.list_schema_fields_request_id,
        next_request_id=context.list_schema_fields_request_id + 1,
        schema_request_fingerprint="b" * 64,
        input_schema_fingerprint=context.discovery.list_schema_fields_contract.input_schema_fingerprint,
        dataset_urn=context.dataset_urn,
        schema_slice=schema_slice,
    )


def full_setup(*, urn: str = ORDERS_URN, name: str = "orders", column: str = "customer_id", observation: DataHubAffectedFieldObservation = DataHubAffectedFieldObservation.NOT_OBSERVED, get_lineage_schema: dict | None = None):
    lineage_bundle, lineage_transport = lineage_discover(get_lineage_schema=get_lineage_schema)
    c1_bundle = lineage_bundle.entity_schema_discovery
    config, session = cfg_session()
    search_exec = search_execution(c1_bundle, records=(record(urn, name),))
    subj = subject(name, column)
    resolution = resolve_datahub_asset_candidate(subject=subj, search_result=search_exec)
    entity_schema_context = bind_datahub_entity_schema_context(subject=subj, resolution=resolution, search_execution=search_exec, discovery=c1_bundle)
    entity_exec = entity_execution_result(entity_schema_context)
    schema_exec = schema_execution_result(entity_schema_context, observation=observation)
    ctx = bind_datahub_lineage_context(subject=subj, resolution=resolution, search_execution=search_exec, entity_execution=entity_exec, schema_execution=schema_exec, entity_schema_context=entity_schema_context, discovery=lineage_bundle)
    return config, session, c1_bundle, lineage_bundle, search_exec, resolution, entity_schema_context, entity_exec, schema_exec, ctx


def bind_lineage(setup, **overrides):
    _, _, _, _, _, _, _, _, _, ctx = setup
    return bind_datahub_lineage_context(
        subject=overrides.get("subject", ctx.subject),
        resolution=overrides.get("resolution", ctx.resolution),
        search_execution=overrides.get("search_execution", ctx.search_execution),
        entity_execution=overrides.get("entity_execution", ctx.entity_execution),
        schema_execution=overrides.get("schema_execution", ctx.schema_execution),
        entity_schema_context=overrides.get("entity_schema_context", ctx.entity_schema_context),
        discovery=overrides.get("discovery", ctx.discovery),
    )


def construct_resolution(*, status: DataHubAssetResolutionStatus = DataHubAssetResolutionStatus.RESOLVED, urn: str | None = ORDERS_URN, position: int = 0, candidate_count: int = 1) -> DataHubAssetCandidateResolution:
    return DataHubAssetCandidateResolution.model_construct(
        status=status,
        selected_dataset_urn=urn,
        confidence=DataHubAssetResolutionConfidence.EXACT,
        resolution_method=DataHubAssetResolutionMethod.EXACT_FULLY_QUALIFIED,
        candidate_count=candidate_count,
        strongest_match_count=1,
        selected_source_position=position,
    )


def construct_entity_exec(context: DataHubEntitySchemaContext, *, dataset_urn: str | None = None, next_request_id: int | None = None) -> DataHubEntityMetadataExecutionResult:
    urn = dataset_urn if dataset_urn is not None else context.dataset_urn
    return DataHubEntityMetadataExecutionResult.model_construct(
        request_id=context.get_entities_request_id,
        next_request_id=next_request_id if next_request_id is not None else context.list_schema_fields_request_id,
        entity_request_fingerprint="a" * 64,
        input_schema_fingerprint=context.discovery.get_entities_contract.input_schema_fingerprint,
        dataset_urn=urn,
        metadata=DataHubDatasetEntityMetadata(dataset_urn=urn),
    )


def construct_schema_exec(context: DataHubEntitySchemaContext, *, dataset_urn: str | None = None, request_id: int | None = None, next_request_id: int | None = None) -> DataHubSchemaFieldsExecutionResult:
    urn = dataset_urn if dataset_urn is not None else context.dataset_urn
    return DataHubSchemaFieldsExecutionResult.model_construct(
        request_id=request_id if request_id is not None else context.list_schema_fields_request_id,
        next_request_id=next_request_id if next_request_id is not None else context.list_schema_fields_request_id + 1,
        schema_request_fingerprint="b" * 64,
        input_schema_fingerprint=context.discovery.list_schema_fields_contract.input_schema_fingerprint,
        dataset_urn=urn,
        schema_slice=schema_execution_result(context).schema_slice,
    )


def dataset_plan(ctx: DataHubLineageContext) -> DataHubDatasetLineageArgumentPlan:
    return build_datahub_dataset_lineage_argument_plan(context=ctx, contract=ctx.discovery.get_lineage_contract)


def column_plan(ctx: DataHubLineageContext) -> DataHubColumnLineageArgumentPlan:
    return build_datahub_column_lineage_argument_plan(context=ctx, contract=ctx.discovery.get_lineage_contract)


class TestGetLineageAttestation:
    def test_compatible_lineage_schema_accepted(self) -> None:
        contract = attest_datahub_get_lineage_schema(schema=GET_LINEAGE_SCHEMA, catalog_fingerprint=fp(GET_LINEAGE_SCHEMA))
        assert isinstance(contract, DataHubGetLineageSchemaContract)
        assert contract.urn_supported and contract.column_supported and contract.downstream_false_supported
        assert contract.max_hops_one_supported and contract.max_results_30_supported and contract.offset_zero_supported

    def test_urn_required(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_missing_urn_rejected(self) -> None:
        schema = {"type": "object", "properties": {"column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["column"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_non_string_urn_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "integer"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_bounded_1024_urn_compatibility_required(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string", "maxLength": 100}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_column_property_required_to_exist(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_column_may_remain_optional_for_dataset_plan(self) -> None:
        contract = attest_datahub_get_lineage_schema(schema=GET_LINEAGE_SCHEMA, catalog_fingerprint=fp(GET_LINEAGE_SCHEMA))
        assert contract.column_supported

    def test_column_string_compatibility_accepted(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        contract = attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.column_supported

    def test_column_bound_below_affected_column_max_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string", "maxLength": 100}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_column_required_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn", "column"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_upstream_real_bool_accepted(self) -> None:
        contract = attest_datahub_get_lineage_schema(schema=GET_LINEAGE_SCHEMA, catalog_fingerprint=fp(GET_LINEAGE_SCHEMA))
        assert contract.downstream_false_supported

    def test_upstream_schema_permitting_false_accepted(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean", "enum": [False, True]}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        contract = attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.downstream_false_supported

    def test_upstream_schema_permitting_only_true_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean", "const": True}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_integer_pretending_to_be_bool_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "integer"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_max_hops_integer_accepted(self) -> None:
        contract = attest_datahub_get_lineage_schema(schema=GET_LINEAGE_SCHEMA, catalog_fingerprint=fp(GET_LINEAGE_SCHEMA))
        assert contract.max_hops_one_supported

    def test_exact_max_hops_one_support_required(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer", "minimum": 2}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_max_hops_constraints_rejecting_one_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer", "enum": [3]}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_max_results_integer_accepted(self) -> None:
        contract = attest_datahub_get_lineage_schema(schema=GET_LINEAGE_SCHEMA, catalog_fingerprint=fp(GET_LINEAGE_SCHEMA))
        assert contract.max_results_30_supported

    def test_exact_max_results_30_support_required(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer", "maximum": 10}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_provider_constraints_rejecting_30_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer", "maximum": 20}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_offset_integer_accepted(self) -> None:
        contract = attest_datahub_get_lineage_schema(schema=GET_LINEAGE_SCHEMA, catalog_fingerprint=fp(GET_LINEAGE_SCHEMA))
        assert contract.offset_zero_supported

    def test_exact_offset_zero_support_required(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer", "minimum": 1}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_offset_constraints_rejecting_zero_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer", "enum": [10]}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_bool_as_integer_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "boolean"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_optional_query_ignored(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}, "query": {"type": "string"}}, "required": ["urn"]}
        contract = attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.urn_supported

    def test_optional_filter_ignored(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}, "filter": {"type": "string"}}, "required": ["urn"]}
        contract = attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.urn_supported

    def test_required_query_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}, "query": {"type": "string"}}, "required": ["urn", "query"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "unsupported_required_lineage_argument"

    def test_required_filter_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}, "filter": {"type": "string"}}, "required": ["urn", "filter"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "unsupported_required_lineage_argument"

    def test_unknown_optional_property_ignored(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}, "extra": {"type": "string"}}, "required": ["urn"]}
        contract = attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.urn_supported

    def test_unknown_required_property_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}, "extra": {"type": "string"}}, "required": ["urn", "extra"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "unsupported_required_lineage_argument"

    def test_external_ref_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"$ref": "#/definitions/urn"}, "column": {"type": "string"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_recursive_dynamic_schema_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"$ref": "#"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_incompatible"

    def test_provider_descriptions_ignored(self) -> None:
        schema = {"type": "object", "description": "lineage", "properties": {"urn": {"type": "string", "description": "urn"}, "column": {"type": "string", "description": "column"}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        contract = attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.urn_supported

    def test_provider_examples_ignored(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string", "examples": ["urn:li:dataset:(a,b,PROD)"]}, "column": {"type": "string", "examples": ["id"]}, "upstream": {"type": "boolean"}, "max_hops": {"type": "integer"}, "max_results": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        contract = attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.urn_supported

    def test_provider_defaults_ignored(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "column": {"type": "string", "default": "id"}, "upstream": {"type": "boolean", "default": True}, "max_hops": {"type": "integer", "default": 5}, "max_results": {"type": "integer", "default": 100}, "offset": {"type": "integer", "default": 0}}, "required": ["urn"]}
        contract = attest_datahub_get_lineage_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.downstream_false_supported and contract.max_hops_one_supported

    def test_raw_schema_absent_from_contract(self) -> None:
        contract = attest_datahub_get_lineage_schema(schema=GET_LINEAGE_SCHEMA, catalog_fingerprint=fp(GET_LINEAGE_SCHEMA))
        assert set(contract.model_dump()) == {"input_schema_fingerprint", "urn_supported", "column_supported", "downstream_false_supported", "max_hops_one_supported", "max_results_30_supported", "offset_zero_supported", "contract_version"}
        for token in ("properties", "items", "maxLength", "enum"):
            assert token not in repr(contract)

    def test_fingerprint_equality_required(self) -> None:
        with pytest.raises(DataHubLineageContractError) as exc:
            attest_datahub_get_lineage_schema(schema=GET_LINEAGE_SCHEMA, catalog_fingerprint="0" * 64)
        assert exc.value.code == "lineage_schema_fingerprint_mismatch"


class TestDiscovery:
    def test_one_tools_list_sequence_produces_lineage_bundle(self) -> None:
        bundle, transport = lineage_discover()
        assert isinstance(bundle, DataHubLineageToolDiscoveryBundle)
        assert len(transport.calls) == 1

    def test_lineage_bundle_contains_existing_entity_schema_discovery(self) -> None:
        bundle, _ = lineage_discover()
        assert isinstance(bundle.entity_schema_discovery, DataHubEntitySchemaToolDiscoveryBundle)
        assert bundle.entity_schema_discovery.get_entities_contract.supports_single_item_urn_array
        assert bundle.entity_schema_discovery.list_schema_fields_contract.urn_supported

    def test_search_contract_unchanged(self) -> None:
        bundle, _ = lineage_discover()
        assert bundle.entity_schema_discovery.read_discovery.search_contract.query_supported
        assert bundle.entity_schema_discovery.read_discovery.next_request_id == 3

    def test_get_entities_contract_unchanged(self) -> None:
        bundle, _ = lineage_discover()
        assert bundle.entity_schema_discovery.get_entities_contract.supports_single_item_urn_array

    def test_list_schema_fields_contract_unchanged(self) -> None:
        bundle, _ = lineage_discover()
        assert bundle.entity_schema_discovery.list_schema_fields_contract.limit_50_supported

    def test_get_lineage_contract_fingerprint_matches_catalog(self) -> None:
        bundle, _ = lineage_discover()
        capability = next(tool for tool in bundle.entity_schema_discovery.read_discovery.catalog.tools if tool.name.value == "get_lineage")
        assert bundle.get_lineage_contract.input_schema_fingerprint == capability.input_schema_fingerprint

    def test_raw_schemas_absent(self) -> None:
        bundle, _ = lineage_discover()
        text = repr(bundle) + str(bundle.model_dump())
        for token in ("properties", "items", "maxLength", "enum"):
            assert token not in text

    def test_provider_descriptions_absent(self) -> None:
        get_lineage = dict(GET_LINEAGE_SCHEMA, description="lineage tool")
        get_lineage["properties"]["urn"]["description"] = "urn"
        bundle, _ = lineage_discover(get_lineage_schema=get_lineage)
        assert "description" not in repr(bundle) + str(bundle.model_dump())

    def test_existing_discover_datahub_read_tools_unchanged(self) -> None:
        bundle, _ = lineage_discover()
        config, session = cfg_session()
        catalog = discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(required_tools())]))
        assert catalog.model_dump() == bundle.entity_schema_discovery.read_discovery.catalog.model_dump()

    def test_existing_discover_datahub_read_tool_bundle_unchanged(self) -> None:
        bundle, _ = lineage_discover()
        config, session = cfg_session()
        existing = discover_datahub_read_tool_bundle(config=config, session=session, transport=FakeTransport([page(required_tools())]))
        assert existing.model_dump() == bundle.entity_schema_discovery.read_discovery.model_dump()

    def test_existing_entity_schema_discovery_unchanged(self) -> None:
        bundle, _ = lineage_discover()
        config, session = cfg_session()
        existing = discover_datahub_entity_schema_tool_bundle(config=config, session=session, transport=FakeTransport([page(required_tools())]))
        assert existing.model_dump() == bundle.entity_schema_discovery.model_dump()

    def test_existing_apis_do_not_perform_extra_tools_list_requests(self) -> None:
        config, session = cfg_session()
        catalog_transport = FakeTransport([page(required_tools())])
        discover_datahub_read_tools(config=config, session=session, transport=catalog_transport)
        bundle_transport = FakeTransport([page(required_tools())])
        discover_datahub_read_tool_bundle(config=config, session=session, transport=bundle_transport)
        entity_transport = FakeTransport([page(required_tools())])
        discover_datahub_entity_schema_tool_bundle(config=config, session=session, transport=entity_transport)
        assert len(catalog_transport.calls) == 1 and len(bundle_transport.calls) == 1 and len(entity_transport.calls) == 1

    def test_new_lineage_discovery_performs_one_request_per_page(self) -> None:
        config, session = cfg_session()
        tools = required_tools()
        transport = FakeTransport([page(tools[:2], 2, "opaque-cursor"), page(tools[2:], 3)])
        bundle = discover_datahub_lineage_tool_bundle(config=config, session=session, transport=transport)
        assert bundle.get_lineage_contract.urn_supported
        assert len(transport.calls) == 2

    def test_pagination_ids_remain_compatible(self) -> None:
        config, session = cfg_session()
        tools = required_tools()
        transport = FakeTransport([page(tools[:2], 2, "opaque-cursor"), page(tools[2:], 3)])
        discover_datahub_lineage_tool_bundle(config=config, session=session, transport=transport)
        assert json.loads(transport.calls[0][0])["id"] == 2
        assert json.loads(transport.calls[1][0])["id"] == 3

    def test_no_tools_call_during_d1_discovery(self) -> None:
        _, transport = lineage_discover()
        for body, _, _ in transport.calls:
            assert b"tools/call" not in body
            assert b"tools/list" in body


class TestBinding:
    def test_valid_complete_chain_accepted(self) -> None:
        setup = full_setup()
        _, _, _, _, _, _, _, _, _, ctx = setup
        assert isinstance(ctx, DataHubLineageContext)
        assert ctx.dataset_urn == ORDERS_URN
        assert ctx.affected_column == "customer_id"

    def test_unresolved_asset_rejected(self) -> None:
        setup = full_setup()
        bad = construct_resolution(status=DataHubAssetResolutionStatus.UNRESOLVED, urn=None)
        with pytest.raises(DataHubLineageContractError) as exc:
            bind_lineage(setup, resolution=bad)
        assert exc.value.code == "invalid_lineage_binding"

    def test_ambiguous_asset_rejected(self) -> None:
        setup = full_setup()
        bad = construct_resolution(status=DataHubAssetResolutionStatus.AMBIGUOUS, urn=None)
        with pytest.raises(DataHubLineageContractError) as exc:
            bind_lineage(setup, resolution=bad)
        assert exc.value.code == "invalid_lineage_binding"

    def test_selected_dataset_mismatch_rejected(self) -> None:
        setup = full_setup()
        bad = construct_resolution(urn=CUSTOMERS_URN)
        with pytest.raises(DataHubLineageContractError) as exc:
            bind_lineage(setup, resolution=bad)
        assert exc.value.code == "invalid_lineage_binding"

    def test_search_selected_record_mismatch_rejected(self) -> None:
        setup = full_setup()
        _, _, c1_bundle, _, _, _, _, _, _, _ = setup
        other_search = search_execution(c1_bundle, records=(record(CUSTOMERS_URN, "customers"),))
        with pytest.raises(DataHubLineageContractError) as exc:
            bind_lineage(setup, search_execution=other_search)
        assert exc.value.code == "invalid_lineage_binding"

    def test_entity_execution_dataset_mismatch_rejected(self) -> None:
        setup = full_setup()
        _, _, _, _, _, _, esc, _, _, _ = setup
        bad = construct_entity_exec(esc, dataset_urn=CUSTOMERS_URN)
        with pytest.raises(DataHubLineageContractError) as exc:
            bind_lineage(setup, entity_execution=bad)
        assert exc.value.code == "invalid_lineage_binding"

    def test_schema_execution_dataset_mismatch_rejected(self) -> None:
        setup = full_setup()
        _, _, _, _, _, _, esc, _, _, _ = setup
        bad = construct_schema_exec(esc, dataset_urn=CUSTOMERS_URN)
        with pytest.raises(DataHubLineageContractError) as exc:
            bind_lineage(setup, schema_execution=bad)
        assert exc.value.code == "invalid_lineage_binding"

    def test_platform_mismatch_rejected(self) -> None:
        setup = full_setup()
        postgres_subject = subject(column="customer_id").model_copy(update={"platform": "postgres"})
        with pytest.raises(DataHubLineageContractError) as exc:
            bind_lineage(setup, subject=postgres_subject)
        assert exc.value.code == "invalid_lineage_binding"

    def test_invalid_affected_column_rejected(self) -> None:
        setup = full_setup()
        mismatched_subject = subject(column="other_col")
        with pytest.raises(DataHubLineageContractError) as exc:
            bind_lineage(setup, subject=mismatched_subject)
        assert exc.value.code == "invalid_lineage_binding"

    def test_lineage_fingerprint_mismatch_rejected(self) -> None:
        setup = full_setup()
        _, _, _, lineage_bundle, _, _, _, _, _, _ = setup
        bad_contract = DataHubGetLineageSchemaContract.model_construct(input_schema_fingerprint="0" * 64, urn_supported=True, column_supported=True, downstream_false_supported=True, max_hops_one_supported=True, max_results_30_supported=True, offset_zero_supported=True, contract_version="1.0")
        bad_discovery = DataHubLineageToolDiscoveryBundle.model_construct(entity_schema_discovery=lineage_bundle.entity_schema_discovery, get_lineage_contract=bad_contract, bundle_version="1.0")
        with pytest.raises(DataHubLineageContractError) as exc:
            bind_lineage(setup, discovery=bad_discovery)
        assert exc.value.code == "lineage_schema_fingerprint_mismatch"

    def test_mixed_discovery_bundle_rejected(self) -> None:
        setup = full_setup()
        config, session = cfg_session()
        other_ge = {"type": "object", "properties": {"urns": {"type": "array", "items": {"type": "string", "maxLength": 2048}}}, "required": ["urns"]}
        other_bundle = discover_datahub_entity_schema_tool_bundle(config=config, session=session, transport=FakeTransport([page(required_tools(get_entities_schema=other_ge))]))
        _, _, _, lineage_bundle, _, _, _, _, _, _ = setup
        mixed = DataHubLineageToolDiscoveryBundle.model_construct(entity_schema_discovery=other_bundle, get_lineage_contract=lineage_bundle.get_lineage_contract, bundle_version="1.0")
        with pytest.raises(DataHubLineageContractError) as exc:
            bind_lineage(setup, discovery=mixed)
        assert exc.value.code == "invalid_lineage_binding"

    def test_invalid_request_id_continuation_rejected(self) -> None:
        setup = full_setup()
        _, _, _, _, _, _, esc, _, _, _ = setup
        bad = construct_schema_exec(esc, next_request_id=2**63)
        with pytest.raises(DataHubLineageContractError) as exc:
            bind_lineage(setup, schema_execution=bad)
        assert exc.value.code == "lineage_request_id_invalid"

    def test_observed_exact_schema_state_accepted(self) -> None:
        setup = full_setup(observation=DataHubAffectedFieldObservation.OBSERVED_EXACT)
        _, _, _, _, _, _, _, _, _, ctx = setup
        assert ctx.dataset_urn == ORDERS_URN

    def test_not_observed_schema_state_accepted(self) -> None:
        setup = full_setup(observation=DataHubAffectedFieldObservation.NOT_OBSERVED)
        _, _, _, _, _, _, _, _, schema_exec, _ = setup
        assert schema_exec.schema_slice.affected_field_observation is DataHubAffectedFieldObservation.NOT_OBSERVED

    def test_not_observed_does_not_block_column_lineage_planning(self) -> None:
        setup = full_setup(observation=DataHubAffectedFieldObservation.NOT_OBSERVED)
        _, _, _, _, _, _, _, _, _, ctx = setup
        plan = column_plan(ctx)
        assert dict(plan.arguments)["column"] == "customer_id"

    def test_binding_performs_zero_lineage_tools_call(self) -> None:
        assert set(inspect.signature(bind_datahub_lineage_context).parameters) == {"subject", "resolution", "search_execution", "entity_execution", "schema_execution", "entity_schema_context", "discovery"}
        full_setup()


class TestDatasetPlan:
    def test_exact_dataset_urn(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert dict(dataset_plan(ctx).arguments)["urn"] == ORDERS_URN

    def test_exact_upstream_false(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert dict(dataset_plan(ctx).arguments)["upstream"] is False

    def test_exact_max_hops_one(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert dict(dataset_plan(ctx).arguments)["max_hops"] == 1

    def test_exact_max_results_30(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert dict(dataset_plan(ctx).arguments)["max_results"] == 30

    def test_exact_offset_zero(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert dict(dataset_plan(ctx).arguments)["offset"] == 0

    def test_column_key_absent(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert "column" not in dict(dataset_plan(ctx).arguments)

    def test_query_key_absent(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert "query" not in dict(dataset_plan(ctx).arguments)

    def test_filter_key_absent(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert "filter" not in dict(dataset_plan(ctx).arguments)

    def test_no_arbitrary_argument(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert set(dict(dataset_plan(ctx).arguments)) == {"urn", "upstream", "max_hops", "max_results", "offset"}

    def test_plan_immutable(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        plan = dataset_plan(ctx)
        assert plan.model_config["frozen"] is True
        with pytest.raises(ValidationError):
            plan.dataset_urn = CUSTOMERS_URN  # type: ignore[misc]

    def test_arguments_immutable_defensive(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        plan = dataset_plan(ctx)
        with pytest.raises(TypeError):
            plan.arguments["urn"] = CUSTOMERS_URN  # type: ignore[index]

    def test_deterministic_same_plan(self) -> None:
        first = full_setup()
        second = full_setup()
        assert dict(dataset_plan(first[9]).arguments) == dict(dataset_plan(second[9]).arguments)

    def test_caller_cannot_override_urn(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        with pytest.raises(TypeError):
            build_datahub_dataset_lineage_argument_plan(context=ctx, contract=ctx.discovery.get_lineage_contract, urn=CUSTOMERS_URN)

    def test_caller_cannot_request_upstream(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        with pytest.raises(TypeError):
            build_datahub_dataset_lineage_argument_plan(context=ctx, contract=ctx.discovery.get_lineage_contract, upstream=True)

    def test_caller_cannot_raise_max_hops(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        with pytest.raises(TypeError):
            build_datahub_dataset_lineage_argument_plan(context=ctx, contract=ctx.discovery.get_lineage_contract, max_hops=5)

    def test_caller_cannot_raise_max_results(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        with pytest.raises(TypeError):
            build_datahub_dataset_lineage_argument_plan(context=ctx, contract=ctx.discovery.get_lineage_contract, max_results=100)

    def test_caller_cannot_change_offset(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        with pytest.raises(TypeError):
            build_datahub_dataset_lineage_argument_plan(context=ctx, contract=ctx.discovery.get_lineage_contract, offset=50)


class TestColumnPlan:
    def test_exact_dataset_urn(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert dict(column_plan(ctx).arguments)["urn"] == ORDERS_URN

    def test_exact_affected_column(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert dict(column_plan(ctx).arguments)["column"] == "customer_id"

    def test_exact_one_column_value(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert isinstance(dict(column_plan(ctx).arguments)["column"], str)
        assert dict(column_plan(ctx).arguments)["column"] == "customer_id"

    def test_exact_upstream_false(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert dict(column_plan(ctx).arguments)["upstream"] is False

    def test_exact_max_hops_one(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert dict(column_plan(ctx).arguments)["max_hops"] == 1

    def test_exact_max_results_30(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert dict(column_plan(ctx).arguments)["max_results"] == 30

    def test_exact_offset_zero(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert dict(column_plan(ctx).arguments)["offset"] == 0

    def test_query_absent(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert "query" not in dict(column_plan(ctx).arguments)

    def test_filter_absent(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert "filter" not in dict(column_plan(ctx).arguments)

    def test_no_arbitrary_argument(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert set(dict(column_plan(ctx).arguments)) == {"urn", "column", "upstream", "max_hops", "max_results", "offset"}

    def test_plan_immutable(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        plan = column_plan(ctx)
        assert plan.model_config["frozen"] is True
        with pytest.raises(ValidationError):
            plan.affected_column = "other"  # type: ignore[misc]

    def test_arguments_immutable(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        plan = column_plan(ctx)
        with pytest.raises(TypeError):
            plan.arguments["column"] = "other"  # type: ignore[index]

    def test_caller_cannot_override_column(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        with pytest.raises(TypeError):
            build_datahub_column_lineage_argument_plan(context=ctx, contract=ctx.discovery.get_lineage_contract, affected_column="other")

    def test_caller_cannot_request_another_dataset(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        with pytest.raises(TypeError):
            build_datahub_column_lineage_argument_plan(context=ctx, contract=ctx.discovery.get_lineage_contract, dataset_urn=CUSTOMERS_URN)

    def test_not_observed_schema_still_produces_same_column_plan(self) -> None:
        observed = full_setup(observation=DataHubAffectedFieldObservation.OBSERVED_EXACT)
        not_observed = full_setup(observation=DataHubAffectedFieldObservation.NOT_OBSERVED)
        assert dict(column_plan(observed[9]).arguments) == dict(column_plan(not_observed[9]).arguments)


class TestRequestIdChain:
    def test_dataset_lineage_id_equals_schema_next_request_id(self) -> None:
        _, _, _, _, _, _, _, _, schema_exec, ctx = full_setup()
        assert ctx.dataset_lineage_request_id == schema_exec.next_request_id

    def test_column_lineage_id_equals_dataset_plus_one(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        assert ctx.column_lineage_request_id == ctx.dataset_lineage_request_id + 1

    def test_post_lineage_next_id_equals_plus_two(self) -> None:
        _, _, _, _, _, _, _, _, schema_exec, ctx = full_setup()
        assert ctx.post_lineage_next_request_id == schema_exec.next_request_id + 2

    def test_caller_cannot_override_ids(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        plan = dataset_plan(ctx)
        with pytest.raises(TypeError):
            build_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=plan, request_id=99)

    def test_random_ids_not_used(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/lineage_contract.py").read_text(encoding="utf-8")
        assert "random" not in source

    def test_global_counter_not_used(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/lineage_contract.py").read_text(encoding="utf-8")
        assert "counter" not in source and "itertools.count" not in source

    def test_timestamp_not_used(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/lineage_contract.py").read_text(encoding="utf-8")
        assert "time.time" not in source and "timestamp" not in source and "datetime" not in source

    def test_integer_overflow_rejected_before_request_construction(self) -> None:
        setup = full_setup()
        _, _, _, _, _, _, esc, _, _, _ = setup
        bad = construct_schema_exec(esc, next_request_id=2**63)
        with pytest.raises(DataHubLineageContractError) as exc:
            bind_lineage(setup, schema_execution=bad)
        assert exc.value.code == "lineage_request_id_invalid"


class TestRequestShapes:
    def test_dataset_jsonrpc_exact(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx))
        assert json.loads(body)["jsonrpc"] == "2.0"

    def test_dataset_method_exact_tools_call(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx))
        assert json.loads(body)["method"] == "tools/call"

    def test_dataset_name_exact_get_lineage(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx))
        assert json.loads(body)["params"]["name"] == "get_lineage"

    def test_dataset_arguments_exact(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx))
        assert json.loads(body)["params"]["arguments"] == {"urn": ORDERS_URN, "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0}

    def test_dataset_request_id_exact(self) -> None:
        _, _, _, _, _, _, _, _, schema_exec, ctx = full_setup()
        body = serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx))
        assert json.loads(body)["id"] == schema_exec.next_request_id

    def test_dataset_no_column(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx))
        assert "column" not in json.loads(body)["params"]["arguments"]

    def test_dataset_no_query_filter(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx))
        args = json.loads(body)["params"]["arguments"]
        assert "query" not in args and "filter" not in args

    def test_column_jsonrpc_exact(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_column_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=column_plan(ctx))
        assert json.loads(body)["jsonrpc"] == "2.0"

    def test_column_method_exact_tools_call(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_column_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=column_plan(ctx))
        assert json.loads(body)["method"] == "tools/call"

    def test_column_name_exact_get_lineage(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_column_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=column_plan(ctx))
        assert json.loads(body)["params"]["name"] == "get_lineage"

    def test_column_arguments_exact(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_column_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=column_plan(ctx))
        assert json.loads(body)["params"]["arguments"] == {"urn": ORDERS_URN, "column": "customer_id", "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0}

    def test_column_request_id_exact(self) -> None:
        _, _, _, _, _, _, _, _, schema_exec, ctx = full_setup()
        body = serialize_datahub_column_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=column_plan(ctx))
        assert json.loads(body)["id"] == schema_exec.next_request_id + 1

    def test_column_exact_affected_column(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_column_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=column_plan(ctx))
        assert json.loads(body)["params"]["arguments"]["column"] == "customer_id"

    def test_column_no_query_filter(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_column_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=column_plan(ctx))
        args = json.loads(body)["params"]["arguments"]
        assert "query" not in args and "filter" not in args

    def test_no_meta_cursor_progress_task(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        for body in (
            serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx)),
            serialize_datahub_column_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=column_plan(ctx)),
        ):
            for token in ("_meta", "cursor", "progress", "task"):
                assert token not in body.decode("utf-8")

    def test_no_arbitrary_params(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        dataset_request = build_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx))
        column_request = build_datahub_column_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=column_plan(ctx))
        assert set(dataset_request.params) == {"name", "arguments"}
        assert set(column_request.params) == {"name", "arguments"}


class TestSerializationZeroExecution:
    def test_deterministic_canonical_serialization(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        first = serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx))
        second = serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx))
        assert first == second
        assert first == serialize_jsonrpc(build_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx)))

    def test_utf8(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx))
        assert isinstance(body.decode("utf-8"), str)

    def test_nan_rejected(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        bad_plan = DataHubDatasetLineageArgumentPlan.model_construct(
            dataset_urn=ORDERS_URN,
            arguments={"urn": ORDERS_URN, "upstream": float("nan"), "max_hops": 1, "max_results": 30, "offset": 0},
            input_schema_fingerprint=ctx.discovery.get_lineage_contract.input_schema_fingerprint,
            plan_version="1.0",
        )
        with pytest.raises(DataHubLineageContractError) as exc:
            serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=bad_plan)
        assert exc.value.code == "lineage_request_invalid"

    def test_request_bound_reused(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/lineage_contract.py").read_text(encoding="utf-8")
        assert "DATAHUB_MCP_MAX_REQUEST_BYTES" in source
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        body = serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=dataset_plan(ctx))
        assert len(body) <= 65_536

    def test_oversized_dataset_request_rejected(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        bad_plan = DataHubDatasetLineageArgumentPlan.model_construct(
            dataset_urn=ORDERS_URN,
            arguments={"urn": "x" * 70_000, "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0},
            input_schema_fingerprint=ctx.discovery.get_lineage_contract.input_schema_fingerprint,
            plan_version="1.0",
        )
        with pytest.raises(DataHubLineageContractError) as exc:
            serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=bad_plan)
        assert exc.value.code == "lineage_request_too_large"

    def test_oversized_column_request_rejected(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        bad_plan = DataHubColumnLineageArgumentPlan.model_construct(
            dataset_urn=ORDERS_URN,
            affected_column="customer_id",
            arguments={"urn": ORDERS_URN, "column": "x" * 70_000, "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0},
            input_schema_fingerprint=ctx.discovery.get_lineage_contract.input_schema_fingerprint,
            plan_version="1.0",
        )
        with pytest.raises(DataHubLineageContractError) as exc:
            serialize_datahub_column_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=bad_plan)
        assert exc.value.code == "lineage_request_too_large"

    def test_safe_error_excludes_request_bytes(self) -> None:
        _, _, _, _, _, _, _, _, _, ctx = full_setup()
        bad_plan = DataHubDatasetLineageArgumentPlan.model_construct(
            dataset_urn=ORDERS_URN,
            arguments={"urn": "x" * 70_000, "upstream": False, "max_hops": 1, "max_results": 30, "offset": 0},
            input_schema_fingerprint=ctx.discovery.get_lineage_contract.input_schema_fingerprint,
            plan_version="1.0",
        )
        with pytest.raises(DataHubLineageContractError) as exc:
            serialize_datahub_dataset_lineage_tools_call_request(context=ctx, contract=ctx.discovery.get_lineage_contract, argument_plan=bad_plan)
        assert ORDERS_URN not in str(exc.value)
        assert "x" * 100 not in str(exc.value)

    def test_builders_make_zero_transport_calls(self) -> None:
        assert set(inspect.signature(build_datahub_dataset_lineage_tools_call_request).parameters) == {"context", "contract", "argument_plan"}
        assert set(inspect.signature(build_datahub_column_lineage_tools_call_request).parameters) == {"context", "contract", "argument_plan"}

    def test_serializers_make_zero_transport_calls(self) -> None:
        assert set(inspect.signature(serialize_datahub_dataset_lineage_tools_call_request).parameters) == {"context", "contract", "argument_plan"}
        assert set(inspect.signature(serialize_datahub_column_lineage_tools_call_request).parameters) == {"context", "contract", "argument_plan"}

    def test_no_lineage_execution_service_exists(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/lineage_contract.py").read_text(encoding="utf-8")
        assert "execute_datahub_get_lineage" not in source and "post_request" not in source

    def test_no_lineage_result_parser_exists(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/lineage_contract.py").read_text(encoding="utf-8")
        assert "CallToolResult" not in source

    def test_no_structured_content_parsing(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/lineage_contract.py").read_text(encoding="utf-8")
        assert "structuredContent" not in source and "isError" not in source

    def test_no_downstream_result_normalization(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/lineage_contract.py").read_text(encoding="utf-8")
        assert "hasMore" not in source and "downstreams" not in source

    def test_no_column_lineage_normalization(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/lineage_contract.py").read_text(encoding="utf-8")
        assert "lineageColumns" not in source and "degree" not in source

    def test_no_live_network_test(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/lineage_contract.py").read_text(encoding="utf-8")
        for token in ("import requests", "import httpx", "import aiohttp", "urllib", "http.client", "os.environ", "json_repair", "except Exception", "logging", "print(", "DeepSeek"):
            assert token not in source


class TestScopeRegression:
    def test_zero_get_entities_execution(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/lineage_contract.py").read_text(encoding="utf-8")
        assert "execute_datahub_get_entities" not in source

    def test_zero_other_execution(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/lineage_contract.py").read_text(encoding="utf-8")
        assert "execute_datahub_list_schema_fields" not in source and "execute_datahub_search" not in source

    def test_zero_persistence_fastapi_risk(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/lineage_contract.py").read_text(encoding="utf-8")
        for token in ("persistence", "FastAPI", "APIRouter", "risk", "validation"):
            assert token not in source

    def test_protocol_unchanged(self) -> None:
        assert DATAHUB_MCP_PROTOCOL_VERSION == "2025-11-25"

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
