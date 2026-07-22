"""Contract and purity tests for F8.1 (no DataHub source is contacted)."""

from __future__ import annotations

import copy
import math
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.datahub_context import *
from app.services.datahub_context_artifacts import (
    build_completed_datahub_context_artifact,
    build_noncompleted_datahub_context_artifact,
    build_partial_datahub_context_artifact,
)
from app.utils.datahub_fingerprint import fingerprint_datahub_context

U = "urn:li:dataset:(urn:li:dataPlatform:postgres,analytics.orders,PROD)"
U2 = "urn:li:dataset:(urn:li:dataPlatform:postgres,analytics.daily,PROD)"
FP = "a" * 64


def completeness(*, missing: set[str] = set(), truncated: set[str] = set()) -> DataHubContextCompleteness:
    all_categories = list(DATAHUB_CONTEXT_CATEGORY_ORDER)
    available = [DataHubContextCategory(x) for x in all_categories if x not in missing]
    unavailable = [DataHubContextCategory(x) for x in all_categories if x in missing]
    truncated_values = [DataHubContextCategory(x) for x in all_categories if x in truncated]
    complete = all(x in {c.value for c in available} and x not in truncated for x in ("schema", "field_metadata", "downstream_lineage"))
    return DataHubContextCompleteness(available_categories=available, unavailable_categories=unavailable, truncated_categories=truncated_values, required_categories_complete=complete)


def pack(*, missing: set[str] = set(), truncated: set[str] = set(), field_path: str | None = "customer_id", schema_fields: list[DataHubFieldMetadata] | None = None) -> DataHubContextPack:
    fields = schema_fields if schema_fields is not None else [DataHubFieldMetadata(field_path="customer_id", native_type="bigint", nullable=False, description="An external description.")]
    return DataHubContextPack(
        subject_fingerprint=FP,
        resolved_subject=DataHubResolvedSubject(dataset_urn=U, entity_kind="dataset", platform="postgres", field_path=field_path, resolution_method="exact_urn", confidence=1.0),
        schema_context=DataHubSchemaContext(dataset_urn=U, fields=fields),
        downstream_lineage=DataHubDownstreamLineage(subject_urn=U, nodes=[DataHubLineageNode(urn=U, entity_kind="dataset", relation="subject", depth=0)], edges=[], requested_depth=5, observed_max_depth=0, truncated=False),
        column_lineage=[], governance=DataHubGovernanceContext(), operational_signals=DataHubOperationalSignals(query_usage_available=False), completeness=completeness(missing=missing, truncated=truncated),
    )


def test_enums_and_canonical_order() -> None:
    assert [x.value for x in DataHubContextExecutionStatus] == ["completed", "partial", "error", "unavailable", "skipped"]
    assert [x.value for x in DataHubContextSourceKind] == ["live", "snapshot"]
    assert [x.value for x in DataHubEntityKind] == ["dataset", "data_job", "dashboard", "chart", "ml_feature", "ml_model", "ml_model_group", "deployment", "other"]
    assert [x.value for x in DataHubResolutionMethod] == ["exact_urn", "exact_identifier", "dbt_manifest", "configured_mapping", "datahub_search", "snapshot_reference"]
    assert DATAHUB_CONTEXT_CATEGORY_ORDER[:3] == ("schema", "field_metadata", "downstream_lineage")


@pytest.mark.parametrize("value", ["dataset:bad", " urn:li:dataset:x", "urn:li:dataset:\x00x", "urn:li:dataset: x"])
def test_urn_boundary_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValidationError): DataHubNamedReference(urn=value, name="tag")


def test_valid_urn_and_reference() -> None:
    assert DataHubNamedReference(urn=U, name=" orders ").name == "orders"


def test_subject_contract_and_finite_confidence() -> None:
    assert DataHubResolvedSubject(dataset_urn=U, entity_kind="dataset", platform="postgres", resolution_method="exact_urn", confidence=0).confidence == 0
    assert DataHubResolvedSubject(dataset_urn=U, entity_kind="dataset", platform="postgres", resolution_method="exact_urn", confidence=1).confidence == 1
    for confidence in (-0.1, 1.1, math.nan, math.inf):
        with pytest.raises(ValidationError): DataHubResolvedSubject(dataset_urn=U, entity_kind="dataset", platform="postgres", resolution_method="exact_urn", confidence=confidence)
    with pytest.raises(ValidationError): DataHubResolvedSubject(dataset_urn=U, entity_kind="dashboard", platform="postgres", resolution_method="exact_urn", confidence=0.5)
    with pytest.raises(ValidationError): DataHubResolvedSubject(dataset_urn=U, entity_kind="dataset", platform="Bad Platform", resolution_method="exact_urn", confidence=0.5)


def test_strict_models_reject_authority_and_raw_metadata() -> None:
    with pytest.raises(ValidationError): DataHubResolvedSubject(dataset_urn=U, entity_kind="dataset", platform="postgres", resolution_method="exact_urn", confidence=0.5, decision="block")
    with pytest.raises(ValidationError): DataHubFieldMetadata(field_path="id", sample_values=[1])
    with pytest.raises(ValidationError): DataHubFieldMetadata(field_path="id", raw_profile={})
    with pytest.raises(ValidationError): DataHubGovernanceContext(metadata={})
    with pytest.raises(ValidationError): DataHubContextStatusDetail(code="bad", message="x", details={})


def test_schema_and_governance_duplicates_and_bounds() -> None:
    ref1 = DataHubNamedReference(urn=U, name="tag")
    with pytest.raises(ValidationError): DataHubSchemaContext(dataset_urn=U, fields=[DataHubFieldMetadata(field_path="id"), DataHubFieldMetadata(field_path="id")])
    with pytest.raises(ValidationError): DataHubGovernanceContext(tags=[ref1, ref1])
    with pytest.raises(ValidationError): DataHubFieldMetadata(field_path="id", description="x" * 2001)
    assert DataHubSchemaContext(dataset_urn=U, fields=[]).fields == []


def test_lineage_graph_invariants() -> None:
    downstream = DataHubLineageNode(urn=U2, entity_kind="dataset", relation="downstream", depth=1)
    graph = DataHubDownstreamLineage(subject_urn=U, nodes=[DataHubLineageNode(urn=U, entity_kind="dataset", relation="subject", depth=0), downstream], edges=[DataHubLineageEdge(upstream_urn=U, downstream_urn=U2)], requested_depth=2, observed_max_depth=1, truncated=False)
    assert len(graph.nodes) == 2
    with pytest.raises(ValidationError): DataHubDownstreamLineage(subject_urn=U, nodes=[downstream], edges=[], requested_depth=1, observed_max_depth=0, truncated=False)
    with pytest.raises(ValidationError): DataHubDownstreamLineage(subject_urn=U, nodes=[DataHubLineageNode(urn=U, entity_kind="dataset", relation="subject", depth=0)], edges=[DataHubLineageEdge(upstream_urn=U, downstream_urn=U2)], requested_depth=1, observed_max_depth=0, truncated=False)
    with pytest.raises(ValidationError): DataHubLineageNode(urn=U, entity_kind="dataset", relation="downstream", depth=0)
    with pytest.raises(ValidationError): DataHubLineageEdge(upstream_urn=U, downstream_urn=U)


def test_column_lineage_and_signals() -> None:
    edge = DataHubColumnLineageEdge(source_dataset_urn=U, source_field_path="id", target_dataset_urn=U2, target_field_path="id")
    assert edge.source_field_path == "id"
    with pytest.raises(ValidationError): DataHubColumnLineageEdge(source_dataset_urn=U, source_field_path="id", target_dataset_urn=U, target_field_path="id")
    with pytest.raises(ValidationError): DataHubOperationalSignals(query_usage_available=False, query_reference_count=1)
    with pytest.raises(ValidationError): DataHubOperationalSignals(query_usage_available=True)
    with pytest.raises(ValidationError): DataHubOperationalSignals(query_usage_available=False, quality_signal_codes=["same", "same"])
    assert DataHubOperationalSignals(query_usage_available=True, query_reference_count=0).query_reference_count == 0


def test_completeness_partition_and_optional_missing() -> None:
    assert completeness(missing={"query_usage"}).required_categories_complete is True
    assert completeness(missing={"schema"}).required_categories_complete is False
    with pytest.raises(ValidationError): DataHubContextCompleteness(available_categories=["schema"], unavailable_categories=[], required_categories_complete=False)
    with pytest.raises(ValidationError): DataHubContextCompleteness(available_categories=["schema", "field_metadata", "downstream_lineage"], unavailable_categories=["schema"], required_categories_complete=True)
    assert DataHubContextCompleteness(available_categories=list(DataHubContextCategory), unavailable_categories=[], required_categories_complete=True).required_categories_complete


def test_pack_subject_and_field_invariants() -> None:
    assert pack().context_pack_version == "1.0"
    with pytest.raises(ValidationError): pack(schema_fields=[DataHubFieldMetadata(field_path="other")])
    with pytest.raises(ValidationError): DataHubContextPack(**{**pack().model_dump(), "subject_fingerprint": "A" * 64})
    with pytest.raises(ValidationError): DataHubContextPack(**{**pack().model_dump(), "schema_context": {**pack().schema_context.model_dump(), "dataset_urn": U2}})
    assert pack(missing={"field_metadata"}).resolved_subject.field_path == "customer_id"


def test_fingerprint_is_stable_and_sensitive_without_mutation() -> None:
    context = pack()
    before = copy.deepcopy(context.model_dump())
    first = fingerprint_datahub_context(context)
    changed = pack(schema_fields=[DataHubFieldMetadata(field_path="customer_id", description="changed")])
    assert first == fingerprint_datahub_context(context)
    assert first != fingerprint_datahub_context(changed)
    assert context.model_dump() == before
    assert len(first) == 64 and first == first.lower()


def test_artifact_builders_and_state_guarantees() -> None:
    context = pack()
    completed = build_completed_datahub_context_artifact(context=context, source_kind=DataHubContextSourceKind.SNAPSHOT)
    assert isinstance(completed.context_id, UUID) and completed.context_fingerprint == fingerprint_datahub_context(context)
    with pytest.raises(ValidationError): DataHubContextArtifact(**{**completed.model_dump(), "writeback_authorized": True})
    incomplete = pack(missing={"schema"})
    detail = DataHubContextStatusDetail(code="context_incomplete", message="Required context is unavailable.")
    partial = build_partial_datahub_context_artifact(context=incomplete, source_kind=DataHubContextSourceKind.LIVE, status_detail=detail)
    assert partial.execution_status == DataHubContextExecutionStatus.PARTIAL
    with pytest.raises(ValueError): build_partial_datahub_context_artifact(context=context, source_kind=DataHubContextSourceKind.LIVE, status_detail=detail)
    for status in ("error", "unavailable", "skipped"):
        artifact = build_noncompleted_datahub_context_artifact(subject_fingerprint=FP, source_kind=DataHubContextSourceKind.LIVE, execution_status=status, status_detail=detail)
        assert artifact.context_pack is None and artifact.context_fingerprint is None
    with pytest.raises(ValueError): build_noncompleted_datahub_context_artifact(subject_fingerprint=FP, source_kind=DataHubContextSourceKind.LIVE, execution_status="completed", status_detail=detail)


def test_pure_modules_have_no_forbidden_integration_symbols() -> None:
    for relative in ("app/schemas/datahub_context.py", "app/services/datahub_context_artifacts.py", "app/utils/datahub_fingerprint.py"):
        source = Path(__file__).parents[1].joinpath(relative).read_text(encoding="utf-8")
        assert "DATAHUB_TOKEN" not in source
        assert "requests" not in source
        assert "httpx" not in source
        assert "subprocess" not in source
