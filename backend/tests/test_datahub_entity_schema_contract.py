from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import pytest

from app.integrations.datahub.asset_resolution import (
    DataHubAssetCandidateResolution,
    DataHubAssetResolutionConfidence,
    DataHubAssetResolutionMethod,
    DataHubAssetResolutionStatus,
    DataHubAssetResolutionSubject,
    resolve_datahub_asset_candidate,
)
from app.integrations.datahub.config import DATAHUB_MCP_PROTOCOL_VERSION, load_datahub_mcp_config
from app.integrations.datahub.entity_schema_contract import (
    DataHubEntitySchemaContractError,
    DataHubEntitySchemaContext,
    DataHubEntitySchemaToolDiscoveryBundle,
    DataHubGetEntitiesArgumentPlan,
    DataHubGetEntitiesSchemaContract,
    DataHubListSchemaFieldsArgumentPlan,
    DataHubListSchemaFieldsSchemaContract,
    attest_datahub_get_entities_schema,
    attest_datahub_list_schema_fields_schema,
    bind_datahub_entity_schema_context,
    build_datahub_get_entities_argument_plan,
    build_datahub_get_entities_tools_call_request,
    build_datahub_list_schema_fields_argument_plan,
    build_datahub_list_schema_fields_tools_call_request,
    discover_datahub_entity_schema_tool_bundle,
    serialize_datahub_get_entities_tools_call_request,
    serialize_datahub_list_schema_fields_tools_call_request,
)
from app.integrations.datahub.initialization import DataHubMCPSession
from app.integrations.datahub.mcp_protocol import serialize_jsonrpc
from app.integrations.datahub.search_contract import discover_datahub_read_tool_bundle
from app.integrations.datahub.search_execution import DataHubDatasetSearchRecord, DataHubSearchExecutionResult
from app.integrations.datahub.tool_discovery import CATALOG_VERSION, READ_TOOL_ORDER, discover_datahub_read_tools, fingerprint_datahub_tool_input_schema
from app.integrations.datahub.transport import DataHubMCPHTTPResponse

ENDPOINT = "https://datahub.example.com/mcp"
ORDERS_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.orders,PROD)"
CUSTOMERS_URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.customers,PROD)"

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


def required_tools(*, get_entities_schema: dict | None = None, list_schema_fields_schema: dict | None = None) -> list[dict]:
    return [tool(item.value, get_entities_schema if item.value == "get_entities" else (list_schema_fields_schema if item.value == "list_schema_fields" else None)) for item in READ_TOOL_ORDER]


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
        raise AssertionError("F8.3C1 must not send notifications")


def cfg_session() -> tuple[object, DataHubMCPSession]:
    config = load_datahub_mcp_config({"DATAHUB_MCP_URL": ENDPOINT, "DATAHUB_TOKEN": "test-token"})
    session = DataHubMCPSession(endpoint_url=ENDPOINT, protocol_version=DATAHUB_MCP_PROTOCOL_VERSION, server_name="DataHub", server_version="1", tools_supported=True, session_id="session-1")
    return config, session


def discover(*, get_entities_schema: dict | None = None, list_schema_fields_schema: dict | None = None, responses: list[DataHubMCPHTTPResponse] | None = None):
    config, session = cfg_session()
    transport = FakeTransport(responses or [page(required_tools(get_entities_schema=get_entities_schema, list_schema_fields_schema=list_schema_fields_schema))])
    return discover_datahub_entity_schema_tool_bundle(config=config, session=session, transport=transport), transport


def subject() -> DataHubAssetResolutionSubject:
    return DataHubAssetResolutionSubject(platform="snowflake", database="analytics", schema_name="core", table_name="orders", affected_column="customer_id")


def record(urn: str = ORDERS_URN, position: int = 0) -> DataHubDatasetSearchRecord:
    return DataHubDatasetSearchRecord(dataset_urn=urn, display_name="orders", source_position=position)


def search_execution(bundle: DataHubEntitySchemaToolDiscoveryBundle, *, records: tuple[DataHubDatasetSearchRecord, ...] | None = None, input_schema_fingerprint: str | None = None) -> DataHubSearchExecutionResult:
    records = (record(),) if records is None else records
    next_id = bundle.read_discovery.next_request_id + 1
    return DataHubSearchExecutionResult(
        request_id=next_id - 1,
        next_request_id=next_id,
        search_request_fingerprint="a" * 64,
        input_schema_fingerprint=input_schema_fingerprint or bundle.read_discovery.search_contract.input_schema_fingerprint,
        records=records,
        provider_start=0,
        provider_count=len(records),
        provider_total=len(records),
        non_dataset_result_count=0,
        result_version="1.0",
    )


def context_bundle():
    bundle, transport = discover()
    search_exec = search_execution(bundle)
    resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=search_exec)
    context = bind_datahub_entity_schema_context(subject=subject(), resolution=resolution, search_execution=search_exec, discovery=bundle)
    return bundle, transport, search_exec, resolution, context


class TestGetEntitiesAttestation:
    def test_compatible_urns_array_schema_accepted(self) -> None:
        contract = attest_datahub_get_entities_schema(schema=GET_ENTITIES_SCHEMA, catalog_fingerprint=fp(GET_ENTITIES_SCHEMA))
        assert isinstance(contract, DataHubGetEntitiesSchemaContract)
        assert contract.supports_single_item_urn_array
        assert contract.contract_version == "1.0"

    def test_urns_required(self) -> None:
        schema = {"type": "object", "properties": {"urns": {"type": "array", "items": {"type": "string"}}}}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_missing_urns_rejected(self) -> None:
        schema = {"type": "object", "properties": {"value": {"type": "string"}}}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_scalar_only_urns_schema_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urns": {"type": "string"}}, "required": ["urns"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_array_with_string_items_accepted(self) -> None:
        schema = {"type": "object", "properties": {"urns": {"type": "array", "items": {"type": "string"}}}, "required": ["urns"]}
        contract = attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.supports_single_item_urn_array

    def test_non_string_items_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urns": {"type": "array", "items": {"type": "integer"}}}, "required": ["urns"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_exactly_one_item_compatible_bounds_accepted(self) -> None:
        schema = {"type": "object", "properties": {"urns": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 1}}, "required": ["urns"]}
        contract = attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.supports_single_item_urn_array

    def test_max_items_zero_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urns": {"type": "array", "items": {"type": "string"}, "maxItems": 0}}, "required": ["urns"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_min_items_greater_than_one_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urns": {"type": "array", "items": {"type": "string"}, "minItems": 2}}, "required": ["urns"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_urn_item_max_length_below_1024_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urns": {"type": "array", "items": {"type": "string", "maxLength": 100}}}, "required": ["urns"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_unknown_optional_property_ignored(self) -> None:
        schema = {"type": "object", "properties": {"urns": {"type": "array", "items": {"type": "string"}}, "extra": {"type": "string"}}, "required": ["urns"]}
        contract = attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.supports_single_item_urn_array

    def test_unknown_required_property_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urns": {"type": "array", "items": {"type": "string"}}, "extra": {"type": "string"}}, "required": ["urns", "extra"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "unsupported_required_entity_argument"

    def test_external_ref_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urns": {"$ref": "#/definitions/urns"}}, "required": ["urns"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_recursive_or_unsupported_schema_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urns": {"type": "array", "items": {"$ref": "#"}}}, "required": ["urns"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_provider_description_ignored(self) -> None:
        schema = {"type": "object", "description": "provider tool description", "properties": {"urns": {"type": "array", "items": {"type": "string"}, "description": "urns"}}, "required": ["urns"]}
        contract = attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.supports_single_item_urn_array

    def test_provider_default_ignored(self) -> None:
        schema = {"type": "object", "properties": {"urns": {"type": "array", "items": {"type": "string"}, "default": []}}, "required": ["urns"]}
        contract = attest_datahub_get_entities_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.supports_single_item_urn_array

    def test_raw_schema_not_retained(self) -> None:
        contract = attest_datahub_get_entities_schema(schema=GET_ENTITIES_SCHEMA, catalog_fingerprint=fp(GET_ENTITIES_SCHEMA))
        dumped = contract.model_dump()
        assert set(dumped) == {"input_schema_fingerprint", "supports_single_item_urn_array", "contract_version"}
        for token in ("properties", "items", "urns", "maxLength"):
            assert token not in repr(contract)

    def test_fingerprint_match_required(self) -> None:
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_get_entities_schema(schema=GET_ENTITIES_SCHEMA, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_fingerprint_mismatch"


class TestListSchemaFieldsAttestation:
    def test_compatible_schema_accepted(self) -> None:
        contract = attest_datahub_list_schema_fields_schema(schema=LIST_SCHEMA_FIELDS_SCHEMA, catalog_fingerprint=fp(LIST_SCHEMA_FIELDS_SCHEMA))
        assert isinstance(contract, DataHubListSchemaFieldsSchemaContract)
        assert contract.urn_supported and contract.keywords_supported and contract.limit_50_supported and contract.offset_zero_supported

    def test_urn_required(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "keywords": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "integer"}, "offset": {"type": "integer"}}}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_missing_urn_rejected(self) -> None:
        schema = {"type": "object", "properties": {"keywords": {"type": "array", "items": {"type": "string"}}}, "required": ["keywords"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_non_string_urn_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "integer"}, "keywords": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_urn_max_length_below_1024_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string", "maxLength": 100}, "keywords": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_keywords_array_of_string_accepted(self) -> None:
        contract = attest_datahub_list_schema_fields_schema(schema=LIST_SCHEMA_FIELDS_SCHEMA, catalog_fingerprint=fp(LIST_SCHEMA_FIELDS_SCHEMA))
        assert contract.keywords_supported

    def test_missing_keywords_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "limit": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_scalar_only_keywords_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "keywords": {"type": "string"}, "limit": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_non_string_keyword_items_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "keywords": {"type": "array", "items": {"type": "integer"}}, "limit": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_one_keyword_compatible_bounds_accepted(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "keywords": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 1}, "limit": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        contract = attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.keywords_supported

    def test_limit_integer_accepted(self) -> None:
        contract = attest_datahub_list_schema_fields_schema(schema=LIST_SCHEMA_FIELDS_SCHEMA, catalog_fingerprint=fp(LIST_SCHEMA_FIELDS_SCHEMA))
        assert contract.limit_50_supported

    def test_limit_supporting_50_accepted(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "keywords": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "integer", "minimum": 1, "maximum": 50}, "offset": {"type": "integer"}}, "required": ["urn"]}
        contract = attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.limit_50_supported

    def test_limit_rejecting_50_incompatible(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "keywords": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "integer", "maximum": 10}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_offset_integer_accepted(self) -> None:
        contract = attest_datahub_list_schema_fields_schema(schema=LIST_SCHEMA_FIELDS_SCHEMA, catalog_fingerprint=fp(LIST_SCHEMA_FIELDS_SCHEMA))
        assert contract.offset_zero_supported

    def test_offset_supporting_zero_accepted(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "keywords": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "integer"}, "offset": {"type": "integer", "minimum": 0, "maximum": 1000}}, "required": ["urn"]}
        contract = attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.offset_zero_supported

    def test_offset_rejecting_zero_incompatible(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "keywords": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "integer"}, "offset": {"type": "integer", "minimum": 1}}, "required": ["urn"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_bool_as_integer_semantics_not_accepted(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "keywords": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "boolean"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_unknown_optional_property_ignored(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "keywords": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "integer"}, "offset": {"type": "integer"}, "extra": {"type": "string"}}, "required": ["urn"]}
        contract = attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint=fp(schema))
        assert contract.urn_supported

    def test_unknown_required_property_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"type": "string"}, "keywords": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "integer"}, "offset": {"type": "integer"}, "extra": {"type": "string"}}, "required": ["urn", "extra"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "unsupported_required_schema_argument"

    def test_external_schema_reference_rejected(self) -> None:
        schema = {"type": "object", "properties": {"urn": {"$ref": "#/definitions/urn"}, "keywords": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "integer"}, "offset": {"type": "integer"}}, "required": ["urn"]}
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_list_schema_fields_schema(schema=schema, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_schema_incompatible"

    def test_raw_schema_not_retained(self) -> None:
        contract = attest_datahub_list_schema_fields_schema(schema=LIST_SCHEMA_FIELDS_SCHEMA, catalog_fingerprint=fp(LIST_SCHEMA_FIELDS_SCHEMA))
        dumped = contract.model_dump()
        assert set(dumped) == {"input_schema_fingerprint", "urn_supported", "keywords_supported", "limit_50_supported", "offset_zero_supported", "contract_version"}
        for token in ("properties", "items", "maxLength", "minLength", "enum"):
            assert token not in repr(contract)

    def test_fingerprint_match_required(self) -> None:
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            attest_datahub_list_schema_fields_schema(schema=LIST_SCHEMA_FIELDS_SCHEMA, catalog_fingerprint="0" * 64)
        assert exc.value.code == "entity_schema_fingerprint_mismatch"


class TestDiscoveryBundle:
    def test_one_tools_list_sequence_creates_complete_bundle(self) -> None:
        bundle, transport = discover()
        assert isinstance(bundle, DataHubEntitySchemaToolDiscoveryBundle)
        assert bundle.get_entities_contract.supports_single_item_urn_array
        assert bundle.list_schema_fields_contract.urn_supported
        assert len(transport.calls) == 1

    def test_existing_search_discovery_remains_present(self) -> None:
        bundle, _ = discover()
        assert bundle.read_discovery.search_contract.query_supported
        assert bundle.read_discovery.next_request_id == 3

    def test_get_entities_fingerprint_matches_catalog(self) -> None:
        bundle, _ = discover()
        capability = next(tool for tool in bundle.read_discovery.catalog.tools if tool.name.value == "get_entities")
        assert bundle.get_entities_contract.input_schema_fingerprint == capability.input_schema_fingerprint

    def test_list_schema_fields_fingerprint_matches_catalog(self) -> None:
        bundle, _ = discover()
        capability = next(tool for tool in bundle.read_discovery.catalog.tools if tool.name.value == "list_schema_fields")
        assert bundle.list_schema_fields_contract.input_schema_fingerprint == capability.input_schema_fingerprint

    def test_raw_schemas_absent_from_bundle(self) -> None:
        bundle, _ = discover()
        text = repr(bundle) + str(bundle.model_dump())
        for token in ("properties", "items", "maxLength", "minLength", "enum"):
            assert token not in text

    def test_descriptions_defaults_absent(self) -> None:
        get_schema = dict(GET_ENTITIES_SCHEMA, description="get entities")
        get_schema["properties"]["urns"]["default"] = []
        schema_schema = dict(LIST_SCHEMA_FIELDS_SCHEMA, description="schema fields")
        bundle, _ = discover(get_entities_schema=get_schema, list_schema_fields_schema=schema_schema)
        text = repr(bundle) + str(bundle.model_dump())
        assert "description" not in text and "default" not in text

    def test_existing_discover_datahub_read_tools_result_unchanged(self) -> None:
        bundle, _ = discover()
        config, session = cfg_session()
        catalog = discover_datahub_read_tools(config=config, session=session, transport=FakeTransport([page(required_tools())]))
        assert catalog.model_dump() == bundle.read_discovery.catalog.model_dump()

    def test_existing_discover_datahub_read_tool_bundle_result_unchanged(self) -> None:
        bundle, _ = discover()
        config, session = cfg_session()
        existing = discover_datahub_read_tool_bundle(config=config, session=session, transport=FakeTransport([page(required_tools())]))
        assert existing.model_dump() == bundle.read_discovery.model_dump()

    def test_existing_discovery_performs_no_additional_request(self) -> None:
        config, session = cfg_session()
        catalog_transport = FakeTransport([page(required_tools())])
        discover_datahub_read_tools(config=config, session=session, transport=catalog_transport)
        bundle_transport = FakeTransport([page(required_tools())])
        discover_datahub_read_tool_bundle(config=config, session=session, transport=bundle_transport)
        assert len(catalog_transport.calls) == 1 and len(bundle_transport.calls) == 1

    def test_new_discovery_performs_one_request_per_page(self) -> None:
        config, session = cfg_session()
        first = required_tools()[:2]
        second = required_tools()[2:]
        transport = FakeTransport([page(first, 2, "opaque-cursor"), page(second, 3)])
        bundle = discover_datahub_entity_schema_tool_bundle(config=config, session=session, transport=transport)
        assert bundle.get_entities_contract.supports_single_item_urn_array
        assert bundle.list_schema_fields_contract.urn_supported
        assert len(transport.calls) == 2

    def test_pagination_request_ids_remain_unchanged(self) -> None:
        config, session = cfg_session()
        first = required_tools()[:2]
        second = required_tools()[2:]
        transport = FakeTransport([page(first, 2, "opaque-cursor"), page(second, 3)])
        discover_datahub_entity_schema_tool_bundle(config=config, session=session, transport=transport)
        assert json.loads(transport.calls[0][0])["id"] == 2
        assert json.loads(transport.calls[1][0])["id"] == 3
        assert json.loads(transport.calls[1][0])["params"]["cursor"] == "opaque-cursor"

    def test_catalog_version_unchanged(self) -> None:
        bundle, _ = discover()
        assert bundle.read_discovery.catalog.catalog_version == CATALOG_VERSION

    def test_existing_bundle_version_unchanged(self) -> None:
        bundle, _ = discover()
        assert bundle.read_discovery.bundle_version == "1.0"

    def test_new_bundle_version_fixed(self) -> None:
        bundle, _ = discover()
        assert bundle.bundle_version == "1.0"

    def test_no_tools_call_during_discovery(self) -> None:
        config, session = cfg_session()
        transport = FakeTransport([page(required_tools())])
        discover_datahub_entity_schema_tool_bundle(config=config, session=session, transport=transport)
        for body, _, _ in transport.calls:
            assert b"tools/call" not in body
            assert b"tools/list" in body


class TestBinding:
    def test_valid_resolved_candidate_binding_accepted(self) -> None:
        _, _, _, _, context = context_bundle()
        assert isinstance(context, DataHubEntitySchemaContext)
        assert context.dataset_urn == ORDERS_URN
        assert context.affected_column == "customer_id"

    def test_unresolved_resolution_rejected(self) -> None:
        bundle, _ = discover()
        search_exec = search_execution(bundle, records=())
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=search_exec)
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            bind_datahub_entity_schema_context(subject=subject(), resolution=resolution, search_execution=search_exec, discovery=bundle)
        assert exc.value.code == "invalid_entity_schema_binding"

    def test_ambiguous_resolution_rejected(self) -> None:
        bundle, _ = discover()
        second = "urn:li:dataset:(urn:li:dataPlatform:snowflake,analytics.core.orders,DEV)"
        records = (record(ORDERS_URN, 0), DataHubDatasetSearchRecord(dataset_urn=second, display_name="orders", source_position=1))
        search_exec = search_execution(bundle, records=records)
        resolution = resolve_datahub_asset_candidate(subject=subject(), search_result=search_exec)
        assert resolution.status is DataHubAssetResolutionStatus.AMBIGUOUS
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            bind_datahub_entity_schema_context(subject=subject(), resolution=resolution, search_execution=search_exec, discovery=bundle)
        assert exc.value.code == "invalid_entity_schema_binding"

    def test_selected_urn_missing_rejected(self) -> None:
        bundle, _ = discover()
        search_exec = search_execution(bundle)
        resolution = DataHubAssetCandidateResolution.model_construct(
            status=DataHubAssetResolutionStatus.RESOLVED, selected_dataset_urn=None,
            confidence=DataHubAssetResolutionConfidence.EXACT, resolution_method=DataHubAssetResolutionMethod.EXACT_FULLY_QUALIFIED,
            candidate_count=1, strongest_match_count=1, selected_source_position=0,
        )
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            bind_datahub_entity_schema_context(subject=subject(), resolution=resolution, search_execution=search_exec, discovery=bundle)
        assert exc.value.code == "invalid_entity_schema_binding"

    def test_selected_source_position_missing_rejected(self) -> None:
        bundle, _ = discover()
        search_exec = search_execution(bundle)
        resolution = DataHubAssetCandidateResolution.model_construct(
            status=DataHubAssetResolutionStatus.RESOLVED, selected_dataset_urn=ORDERS_URN,
            confidence=DataHubAssetResolutionConfidence.EXACT, resolution_method=DataHubAssetResolutionMethod.EXACT_FULLY_QUALIFIED,
            candidate_count=1, strongest_match_count=1, selected_source_position=None,
        )
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            bind_datahub_entity_schema_context(subject=subject(), resolution=resolution, search_execution=search_exec, discovery=bundle)
        assert exc.value.code == "invalid_entity_schema_binding"

    def test_candidate_count_mismatch_rejected(self) -> None:
        bundle, _ = discover()
        search_exec = search_execution(bundle)
        resolution = DataHubAssetCandidateResolution.model_construct(
            status=DataHubAssetResolutionStatus.RESOLVED, selected_dataset_urn=ORDERS_URN,
            confidence=DataHubAssetResolutionConfidence.EXACT, resolution_method=DataHubAssetResolutionMethod.EXACT_FULLY_QUALIFIED,
            candidate_count=2, strongest_match_count=1, selected_source_position=0,
        )
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            bind_datahub_entity_schema_context(subject=subject(), resolution=resolution, search_execution=search_exec, discovery=bundle)
        assert exc.value.code == "invalid_entity_schema_binding"

    def test_selected_urn_absent_from_search_records_rejected(self) -> None:
        bundle, _ = discover()
        search_exec = search_execution(bundle, records=(DataHubDatasetSearchRecord(dataset_urn=CUSTOMERS_URN, display_name="customers", source_position=0),))
        resolution = DataHubAssetCandidateResolution.model_construct(
            status=DataHubAssetResolutionStatus.RESOLVED, selected_dataset_urn=ORDERS_URN,
            confidence=DataHubAssetResolutionConfidence.EXACT, resolution_method=DataHubAssetResolutionMethod.EXACT_FULLY_QUALIFIED,
            candidate_count=1, strongest_match_count=1, selected_source_position=0,
        )
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            bind_datahub_entity_schema_context(subject=subject(), resolution=resolution, search_execution=search_exec, discovery=bundle)
        assert exc.value.code == "invalid_entity_schema_binding"

    def test_selected_urn_appears_only_once(self) -> None:
        bundle, _ = discover()
        search_exec = DataHubSearchExecutionResult.model_construct(
            request_id=3, next_request_id=4, search_request_fingerprint="a" * 64,
            input_schema_fingerprint=bundle.read_discovery.search_contract.input_schema_fingerprint,
            records=(record(ORDERS_URN, 0), record(ORDERS_URN, 0)),
            provider_start=0, provider_count=2, provider_total=2, non_dataset_result_count=0, result_version="1.0",
        )
        resolution = DataHubAssetCandidateResolution.model_construct(
            status=DataHubAssetResolutionStatus.RESOLVED, selected_dataset_urn=ORDERS_URN,
            confidence=DataHubAssetResolutionConfidence.EXACT, resolution_method=DataHubAssetResolutionMethod.EXACT_FULLY_QUALIFIED,
            candidate_count=2, strongest_match_count=1, selected_source_position=0,
        )
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            bind_datahub_entity_schema_context(subject=subject(), resolution=resolution, search_execution=search_exec, discovery=bundle)
        assert exc.value.code == "invalid_entity_schema_binding"

    def test_selected_source_position_mismatch_rejected(self) -> None:
        bundle, _ = discover()
        search_exec = search_execution(bundle)
        resolution = DataHubAssetCandidateResolution.model_construct(
            status=DataHubAssetResolutionStatus.RESOLVED, selected_dataset_urn=ORDERS_URN,
            confidence=DataHubAssetResolutionConfidence.EXACT, resolution_method=DataHubAssetResolutionMethod.EXACT_FULLY_QUALIFIED,
            candidate_count=1, strongest_match_count=1, selected_source_position=5,
        )
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            bind_datahub_entity_schema_context(subject=subject(), resolution=resolution, search_execution=search_exec, discovery=bundle)
        assert exc.value.code == "invalid_entity_schema_binding"

    def test_platform_mismatch_rejected(self) -> None:
        bundle, _, search_exec, resolution, _ = context_bundle()
        postgres_subject = DataHubAssetResolutionSubject(platform="postgres", database="analytics", schema_name="core", table_name="orders", affected_column="customer_id")
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            bind_datahub_entity_schema_context(subject=postgres_subject, resolution=resolution, search_execution=search_exec, discovery=bundle)
        assert exc.value.code == "invalid_entity_schema_binding"

    def test_search_fingerprint_mismatch_rejected(self) -> None:
        bundle, _, _, resolution, _ = context_bundle()
        bad_search = DataHubSearchExecutionResult.model_construct(
            request_id=3, next_request_id=4, search_request_fingerprint="a" * 64,
            input_schema_fingerprint="0" * 64,
            records=(record(ORDERS_URN, 0),),
            provider_start=0, provider_count=1, provider_total=1, non_dataset_result_count=0, result_version="1.0",
        )
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            bind_datahub_entity_schema_context(subject=subject(), resolution=resolution, search_execution=bad_search, discovery=bundle)
        assert exc.value.code == "entity_schema_fingerprint_mismatch"

    def test_get_entities_fingerprint_mismatch_rejected(self) -> None:
        bundle, _, search_exec, resolution, _ = context_bundle()
        bad_contract = DataHubGetEntitiesSchemaContract.model_construct(input_schema_fingerprint="0" * 64, supports_single_item_urn_array=True, contract_version="1.0")
        bad_bundle = DataHubEntitySchemaToolDiscoveryBundle.model_construct(read_discovery=bundle.read_discovery, get_entities_contract=bad_contract, list_schema_fields_contract=bundle.list_schema_fields_contract, bundle_version="1.0")
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            bind_datahub_entity_schema_context(subject=subject(), resolution=resolution, search_execution=search_exec, discovery=bad_bundle)
        assert exc.value.code == "entity_schema_fingerprint_mismatch"

    def test_schema_fingerprint_mismatch_rejected(self) -> None:
        bundle, _, search_exec, resolution, _ = context_bundle()
        bad_contract = DataHubListSchemaFieldsSchemaContract.model_construct(input_schema_fingerprint="0" * 64, urn_supported=True, keywords_supported=True, limit_50_supported=True, offset_zero_supported=True, contract_version="1.0")
        bad_bundle = DataHubEntitySchemaToolDiscoveryBundle.model_construct(read_discovery=bundle.read_discovery, get_entities_contract=bundle.get_entities_contract, list_schema_fields_contract=bad_contract, bundle_version="1.0")
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            bind_datahub_entity_schema_context(subject=subject(), resolution=resolution, search_execution=search_exec, discovery=bad_bundle)
        assert exc.value.code == "entity_schema_fingerprint_mismatch"

    def test_mixed_discovery_bundle_rejected(self) -> None:
        other_schema = {"type": "object", "properties": {"urns": {"type": "array", "items": {"type": "string", "maxLength": 2048}}}, "required": ["urns"]}
        other_bundle, _ = discover(get_entities_schema=other_schema)
        bundle, _, search_exec, resolution, _ = context_bundle()
        mixed = DataHubEntitySchemaToolDiscoveryBundle.model_construct(
            read_discovery=bundle.read_discovery,
            get_entities_contract=other_bundle.get_entities_contract,
            list_schema_fields_contract=bundle.list_schema_fields_contract,
            bundle_version="1.0",
        )
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            bind_datahub_entity_schema_context(subject=subject(), resolution=resolution, search_execution=search_exec, discovery=mixed)
        assert exc.value.code == "entity_schema_fingerprint_mismatch"

    def test_binding_does_zero_transport_calls(self) -> None:
        assert set(inspect.signature(bind_datahub_entity_schema_context).parameters) == {"subject", "resolution", "search_execution", "discovery"}
        context_bundle()


class TestArgumentPlans:
    def test_get_entities_uses_exactly_one_element_urns_array(self) -> None:
        _, _, _, _, context = context_bundle()
        plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        assert isinstance(plan, DataHubGetEntitiesArgumentPlan)
        assert dict(plan.arguments) == {"urns": (ORDERS_URN,)}

    def test_get_entities_never_uses_scalar_or_stringified_json(self) -> None:
        _, _, _, _, context = context_bundle()
        plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        urns = dict(plan.arguments)["urns"]
        assert isinstance(urns, tuple) and not isinstance(urns, str)
        body = serialize_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=plan)
        parsed = json.loads(body)
        assert isinstance(parsed["params"]["arguments"]["urns"], list)

    def test_get_entities_cannot_accept_arbitrary_urns(self) -> None:
        _, _, _, _, context = context_bundle()
        with pytest.raises(TypeError):
            build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract, urns=[ORDERS_URN])

    def test_get_entities_plan_immutable(self) -> None:
        _, _, _, _, context = context_bundle()
        plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        with pytest.raises(TypeError):
            plan.arguments["urns"] = (CUSTOMERS_URN,)  # type: ignore[index]

    def test_schema_plan_exact_urn(self) -> None:
        _, _, _, _, context = context_bundle()
        plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        assert isinstance(plan, DataHubListSchemaFieldsArgumentPlan)
        assert plan.dataset_urn == ORDERS_URN
        assert dict(plan.arguments)["urn"] == ORDERS_URN

    def test_schema_plan_exact_affected_column_keyword(self) -> None:
        _, _, _, _, context = context_bundle()
        plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        assert plan.affected_column == "customer_id"
        assert dict(plan.arguments)["keywords"] == ("customer_id",)

    def test_schema_limit_exact_50(self) -> None:
        _, _, _, _, context = context_bundle()
        plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        assert dict(plan.arguments)["limit"] == 50

    def test_schema_offset_exact_zero(self) -> None:
        _, _, _, _, context = context_bundle()
        plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        assert dict(plan.arguments)["offset"] == 0

    def test_caller_cannot_override_keywords(self) -> None:
        _, _, _, _, context = context_bundle()
        with pytest.raises(TypeError):
            build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract, keywords=["custom"])

    def test_caller_cannot_override_limit(self) -> None:
        _, _, _, _, context = context_bundle()
        with pytest.raises(TypeError):
            build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract, limit=10)

    def test_caller_cannot_override_offset(self) -> None:
        _, _, _, _, context = context_bundle()
        with pytest.raises(TypeError):
            build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract, offset=5)

    def test_arguments_immutable_defensively_copied(self) -> None:
        _, _, _, _, context = context_bundle()
        plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        with pytest.raises(TypeError):
            plan.arguments["urn"] = CUSTOMERS_URN  # type: ignore[index]
        with pytest.raises(TypeError):
            plan.arguments["keywords"] = ("other",)  # type: ignore[index]

    def test_no_query_in_plans(self) -> None:
        _, _, _, _, context = context_bundle()
        get_plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        schema_plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        assert "query" not in dict(get_plan.arguments) and "query" not in dict(schema_plan.arguments)

    def test_no_sql_in_plans(self) -> None:
        _, _, _, _, context = context_bundle()
        schema_plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        for value in dict(schema_plan.arguments).values():
            if isinstance(value, str):
                assert "select" not in value and "insert" not in value

    def test_no_token_endpoint_session_in_plans(self) -> None:
        _, _, _, _, context = context_bundle()
        get_plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        schema_plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        for plan in (get_plan, schema_plan):
            text = repr(plan) + str(dict(plan.arguments))
            for token in ("token", "endpoint", "session"):
                assert token not in text

    def test_deterministic_same_input_same_plans(self) -> None:
        _, _, _, _, first = context_bundle()
        _, _, _, _, second = context_bundle()
        get_a = build_datahub_get_entities_argument_plan(context=first, contract=first.discovery.get_entities_contract)
        get_b = build_datahub_get_entities_argument_plan(context=second, contract=second.discovery.get_entities_contract)
        schema_a = build_datahub_list_schema_fields_argument_plan(context=first, contract=first.discovery.list_schema_fields_contract)
        schema_b = build_datahub_list_schema_fields_argument_plan(context=second, contract=second.discovery.list_schema_fields_contract)
        assert dict(get_a.arguments) == dict(get_b.arguments)
        assert dict(schema_a.arguments) == dict(schema_b.arguments)


class TestRequestIdsAndShapes:
    def test_get_entities_request_id_equals_search_next_request_id(self) -> None:
        bundle, _, search_exec, _, context = context_bundle()
        plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        request = build_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=plan)
        assert request.id == search_exec.next_request_id
        assert request.id == bundle.read_discovery.next_request_id + 1

    def test_schema_request_id_equals_plus_one(self) -> None:
        _, _, search_exec, _, context = context_bundle()
        plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        request = build_datahub_list_schema_fields_tools_call_request(context=context, contract=context.discovery.list_schema_fields_contract, argument_plan=plan)
        assert request.id == search_exec.next_request_id + 1

    def test_post_schema_next_id_equals_plus_two(self) -> None:
        _, _, search_exec, _, context = context_bundle()
        assert context.get_entities_request_id == search_exec.next_request_id
        assert context.list_schema_fields_request_id == search_exec.next_request_id + 1
        assert context.post_metadata_next_request_id == search_exec.next_request_id + 2

    def test_caller_cannot_override_ids(self) -> None:
        _, _, _, _, context = context_bundle()
        plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        with pytest.raises(TypeError):
            build_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=plan, request_id=9)

    def test_exact_get_entities_tools_call_shape(self) -> None:
        _, _, _, _, context = context_bundle()
        plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        body = serialize_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=plan)
        assert json.loads(body) == {
            "jsonrpc": "2.0",
            "id": context.get_entities_request_id,
            "method": "tools/call",
            "params": {"name": "get_entities", "arguments": {"urns": [ORDERS_URN]}},
        }

    def test_exact_get_entities_tool_name(self) -> None:
        _, _, _, _, context = context_bundle()
        plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        request = build_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=plan)
        assert request.params["name"] == "get_entities"

    def test_exact_list_schema_fields_tools_call_shape(self) -> None:
        _, _, _, _, context = context_bundle()
        plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        body = serialize_datahub_list_schema_fields_tools_call_request(context=context, contract=context.discovery.list_schema_fields_contract, argument_plan=plan)
        assert json.loads(body) == {
            "jsonrpc": "2.0",
            "id": context.list_schema_fields_request_id,
            "method": "tools/call",
            "params": {"name": "list_schema_fields", "arguments": {"urn": ORDERS_URN, "keywords": ["customer_id"], "limit": 50, "offset": 0}},
        }

    def test_exact_list_schema_fields_tool_name(self) -> None:
        _, _, _, _, context = context_bundle()
        plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        request = build_datahub_list_schema_fields_tools_call_request(context=context, contract=context.discovery.list_schema_fields_contract, argument_plan=plan)
        assert request.params["name"] == "list_schema_fields"

    def test_no_task_in_requests(self) -> None:
        _, _, _, _, context = context_bundle()
        get_plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        schema_plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        for body in (
            serialize_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=get_plan),
            serialize_datahub_list_schema_fields_tools_call_request(context=context, contract=context.discovery.list_schema_fields_contract, argument_plan=schema_plan),
        ):
            assert b"task" not in body

    def test_no_meta_in_requests(self) -> None:
        _, _, _, _, context = context_bundle()
        get_plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        schema_plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        for body in (
            serialize_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=get_plan),
            serialize_datahub_list_schema_fields_tools_call_request(context=context, contract=context.discovery.list_schema_fields_contract, argument_plan=schema_plan),
        ):
            assert b"_meta" not in body

    def test_no_progress_token(self) -> None:
        _, _, _, _, context = context_bundle()
        get_plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        body = serialize_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=get_plan)
        assert b"progress" not in body

    def test_no_cursor_in_requests(self) -> None:
        _, _, _, _, context = context_bundle()
        schema_plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        body = serialize_datahub_list_schema_fields_tools_call_request(context=context, contract=context.discovery.list_schema_fields_contract, argument_plan=schema_plan)
        assert b"cursor" not in body

    def test_no_arbitrary_params(self) -> None:
        _, _, _, _, context = context_bundle()
        get_plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        schema_plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        get_request = build_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=get_plan)
        schema_request = build_datahub_list_schema_fields_tools_call_request(context=context, contract=context.discovery.list_schema_fields_contract, argument_plan=schema_plan)
        assert set(get_request.params) == {"name", "arguments"}
        assert set(schema_request.params) == {"name", "arguments"}

    def test_plan_fingerprint_mismatch_rejected(self) -> None:
        _, _, _, _, context = context_bundle()
        bad_get_plan = DataHubGetEntitiesArgumentPlan.model_construct(dataset_urn=ORDERS_URN, arguments={"urns": (ORDERS_URN,)}, input_schema_fingerprint="0" * 64, plan_version="1.0")
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            build_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=bad_get_plan)
        assert exc.value.code == "entity_schema_fingerprint_mismatch"
        bad_schema_plan = DataHubListSchemaFieldsArgumentPlan.model_construct(
            dataset_urn=ORDERS_URN, affected_column="customer_id",
            arguments={"urn": ORDERS_URN, "keywords": ("customer_id",), "limit": 50, "offset": 0},
            input_schema_fingerprint="0" * 64, plan_version="1.0",
        )
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            build_datahub_list_schema_fields_tools_call_request(context=context, contract=context.discovery.list_schema_fields_contract, argument_plan=bad_schema_plan)
        assert exc.value.code == "entity_schema_fingerprint_mismatch"


class TestSerializationZeroExecution:
    def test_canonical_serialization_deterministic(self) -> None:
        _, _, _, _, context = context_bundle()
        get_plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        schema_plan = build_datahub_list_schema_fields_argument_plan(context=context, contract=context.discovery.list_schema_fields_contract)
        first = serialize_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=get_plan)
        second = serialize_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=get_plan)
        schema_first = serialize_datahub_list_schema_fields_tools_call_request(context=context, contract=context.discovery.list_schema_fields_contract, argument_plan=schema_plan)
        schema_second = serialize_datahub_list_schema_fields_tools_call_request(context=context, contract=context.discovery.list_schema_fields_contract, argument_plan=schema_plan)
        assert first == second and schema_first == schema_second
        assert first == serialize_jsonrpc(build_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=get_plan))

    def test_utf8(self) -> None:
        _, _, _, _, context = context_bundle()
        get_plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        body = serialize_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=get_plan)
        assert isinstance(body.decode("utf-8"), str)

    def test_nan_rejected(self) -> None:
        _, _, _, _, context = context_bundle()
        bad_plan = DataHubGetEntitiesArgumentPlan.model_construct(
            dataset_urn=ORDERS_URN,
            arguments={"urns": (float("nan"),)},
            input_schema_fingerprint=context.discovery.get_entities_contract.input_schema_fingerprint,
            plan_version="1.0",
        )
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            serialize_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=bad_plan)
        assert exc.value.code == "entity_schema_request_invalid"

    def test_request_size_bound_reused(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_schema_contract.py").read_text(encoding="utf-8")
        assert "DATAHUB_MCP_MAX_REQUEST_BYTES" in source
        _, _, _, _, context = context_bundle()
        get_plan = build_datahub_get_entities_argument_plan(context=context, contract=context.discovery.get_entities_contract)
        body = serialize_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=get_plan)
        assert len(body) <= 65_536

    def test_oversized_request_rejected(self) -> None:
        _, _, _, _, context = context_bundle()
        huge_plan = DataHubGetEntitiesArgumentPlan.model_construct(
            dataset_urn=ORDERS_URN,
            arguments={"urns": ("x" * 70_000,)},
            input_schema_fingerprint=context.discovery.get_entities_contract.input_schema_fingerprint,
            plan_version="1.0",
        )
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            serialize_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=huge_plan)
        assert exc.value.code == "entity_schema_request_too_large"

    def test_request_body_excluded_from_safe_error(self) -> None:
        _, _, _, _, context = context_bundle()
        huge_plan = DataHubGetEntitiesArgumentPlan.model_construct(
            dataset_urn=ORDERS_URN,
            arguments={"urns": ("x" * 70_000,)},
            input_schema_fingerprint=context.discovery.get_entities_contract.input_schema_fingerprint,
            plan_version="1.0",
        )
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            serialize_datahub_get_entities_tools_call_request(context=context, contract=context.discovery.get_entities_contract, argument_plan=huge_plan)
        assert ORDERS_URN not in str(exc.value)
        assert "x" * 100 not in str(exc.value)

    def test_request_builders_perform_zero_transport_calls(self) -> None:
        assert set(inspect.signature(build_datahub_get_entities_tools_call_request).parameters) == {"context", "contract", "argument_plan"}
        assert set(inspect.signature(build_datahub_list_schema_fields_tools_call_request).parameters) == {"context", "contract", "argument_plan"}

    def test_serializers_perform_zero_transport_calls(self) -> None:
        assert set(inspect.signature(serialize_datahub_get_entities_tools_call_request).parameters) == {"context", "contract", "argument_plan"}
        assert set(inspect.signature(serialize_datahub_list_schema_fields_tools_call_request).parameters) == {"context", "contract", "argument_plan"}

    def test_no_metadata_execution_service(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_schema_contract.py").read_text(encoding="utf-8")
        assert "execute_datahub_get_entities" not in source

    def test_no_schema_execution_service(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_schema_contract.py").read_text(encoding="utf-8")
        assert "execute_datahub_list_schema_fields" not in source

    def test_no_call_tool_result_parser(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_schema_contract.py").read_text(encoding="utf-8")
        assert "CallToolResult" not in source

    def test_no_structured_content_parsing(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_schema_contract.py").read_text(encoding="utf-8")
        assert "structuredContent" not in source

    def test_no_is_error_parsing(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_schema_contract.py").read_text(encoding="utf-8")
        assert "isError" not in source

    def test_no_get_lineage_call(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_schema_contract.py").read_text(encoding="utf-8")
        assert "get_lineage" not in source

    def test_no_live_network_test(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_schema_contract.py").read_text(encoding="utf-8")
        for token in ("post_request", "import requests", "import httpx", "import aiohttp", "urllib", "http.client", "os.environ"):
            assert token not in source


class TestScopeRegression:
    def test_plan_builder_rejects_mixed_contract(self) -> None:
        _, _, _, _, context = context_bundle()
        foreign = DataHubGetEntitiesSchemaContract.model_construct(input_schema_fingerprint="0" * 64, supports_single_item_urn_array=True, contract_version="1.0")
        with pytest.raises(DataHubEntitySchemaContractError) as exc:
            build_datahub_get_entities_argument_plan(context=context, contract=foreign)
        assert exc.value.code == "entity_schema_fingerprint_mismatch"

    def test_module_source_has_no_broad_exception_or_logging(self) -> None:
        source = Path(__file__).parents[1].joinpath("app/integrations/datahub/entity_schema_contract.py").read_text(encoding="utf-8")
        assert "except Exception" not in source
        assert "logging" not in source
        assert "print(" not in source
