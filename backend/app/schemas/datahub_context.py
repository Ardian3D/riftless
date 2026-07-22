"""Strict, normalized DataHub context contracts for F8.1.

This module is contract-only.  It deliberately has no source adapter, client,
configuration, environment access, or policy authority.
"""

from __future__ import annotations

import math
import re
from enum import Enum
from typing import Any, ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.utils.fingerprint import is_sha256_hex

_SNAKE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_URN_PREFIX = "urn:li:"
_CONTROL = "".join(chr(i) for i in range(32) if i not in (9, 10, 13))
_REQUIRED = ("schema", "field_metadata", "downstream_lineage")
DATAHUB_CONTEXT_CATEGORY_ORDER = (
    "schema", "field_metadata", "downstream_lineage", "column_lineage",
    "ownership", "tags", "glossary_terms", "domain", "descriptions",
    "query_usage", "quality_signals", "incidents", "ml_lineage",
)


class _StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class DataHubContextExecutionStatus(_StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    ERROR = "error"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"


class DataHubContextSourceKind(_StrEnum):
    LIVE = "live"
    SNAPSHOT = "snapshot"


class DataHubEntityKind(_StrEnum):
    DATASET = "dataset"
    DATA_JOB = "data_job"
    DASHBOARD = "dashboard"
    CHART = "chart"
    ML_FEATURE = "ml_feature"
    ML_MODEL = "ml_model"
    ML_MODEL_GROUP = "ml_model_group"
    DEPLOYMENT = "deployment"
    OTHER = "other"


class DataHubResolutionMethod(_StrEnum):
    EXACT_URN = "exact_urn"
    EXACT_IDENTIFIER = "exact_identifier"
    DBT_MANIFEST = "dbt_manifest"
    CONFIGURED_MAPPING = "configured_mapping"
    DATAHUB_SEARCH = "datahub_search"
    SNAPSHOT_REFERENCE = "snapshot_reference"


class DataHubOwnerKind(_StrEnum):
    USER = "user"
    GROUP = "group"
    TECHNICAL_OWNER = "technical_owner"
    BUSINESS_OWNER = "business_owner"
    UNKNOWN = "unknown"


class DataHubLineageRelation(_StrEnum):
    SUBJECT = "subject"
    DOWNSTREAM = "downstream"


class DataHubContextCategory(_StrEnum):
    SCHEMA = "schema"
    FIELD_METADATA = "field_metadata"
    DOWNSTREAM_LINEAGE = "downstream_lineage"
    COLUMN_LINEAGE = "column_lineage"
    OWNERSHIP = "ownership"
    TAGS = "tags"
    GLOSSARY_TERMS = "glossary_terms"
    DOMAIN = "domain"
    DESCRIPTIONS = "descriptions"
    QUERY_USAGE = "query_usage"
    QUALITY_SIGNALS = "quality_signals"
    INCIDENTS = "incidents"
    ML_LINEAGE = "ml_lineage"

def _text(value: str, *, name: str, max_len: int, required: bool = True) -> str | None:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    if "\x00" in value or any(ch in value for ch in _CONTROL):
        raise ValueError(f"{name} contains a forbidden control character")
    result = value.strip()
    if required and not result:
        raise ValueError(f"{name} must not be blank")
    if len(result) > max_len:
        raise ValueError(f"{name} must be at most {max_len} characters")
    return result or None


def _snake(value: str, *, name: str) -> str:
    result = _text(value, name=name, max_len=64)
    if result is None or not _SNAKE.fullmatch(result):
        raise ValueError(f"{name} must be lowercase snake_case")
    return result


def _urn(value: str, *, name: str = "urn") -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    if not (8 <= len(value.strip()) <= 1024) or value != value.strip():
        raise ValueError(f"{name} must be trimmed and 8-1024 characters")
    if not value.startswith(_URN_PREFIX) or any(ch.isspace() for ch in value):
        raise ValueError(f"{name} must be a structural DataHub URN")
    if "\x00" in value or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ValueError(f"{name} contains a forbidden control character")
    return value


def _unique(items: list[Any], *, name: str, key, max_items: int) -> list[Any]:
    if len(items) > max_items:
        raise ValueError(f"{name} must contain at most {max_items} items")
    seen = set()
    for item in items:
        marker = key(item)
        if marker in seen:
            raise ValueError(f"{name} must not contain duplicates")
        seen.add(marker)
    return items


def _finite(value: float, *, name: str) -> float:
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and between 0 and 1")
    return value


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DataHubContextStatusDetail(_Strict):
    code: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=500)

    @field_validator("code")
    @classmethod
    def code_ok(cls, value: str) -> str:
        return _snake(value, name="code")

    @field_validator("message")
    @classmethod
    def message_ok(cls, value: str) -> str:
        return _text(value, name="message", max_len=500)  # type: ignore[return-value]


class DataHubResolvedSubject(_Strict):
    dataset_urn: str
    entity_kind: DataHubEntityKind
    platform: str
    field_path: str | None = None
    resolution_method: DataHubResolutionMethod
    confidence: float

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str: return _urn(value, name="dataset_urn")

    @field_validator("platform")
    @classmethod
    def platform_ok(cls, value: str) -> str: return _snake(value, name="platform")

    @field_validator("entity_kind")
    @classmethod
    def subject_kind_ok(cls, value: DataHubEntityKind) -> DataHubEntityKind:
        if value != DataHubEntityKind.DATASET:
            raise ValueError("resolved subject entity_kind must be dataset")
        return value

    @field_validator("field_path")
    @classmethod
    def field_ok(cls, value: str | None) -> str | None:
        return None if value is None else _text(value, name="field_path", max_len=512)

    @field_validator("confidence")
    @classmethod
    def confidence_ok(cls, value: float) -> float: return _finite(value, name="confidence")


class DataHubNamedReference(_Strict):
    urn: str
    name: str

    @field_validator("urn")
    @classmethod
    def urn_ok(cls, value: str) -> str: return _urn(value)

    @field_validator("name")
    @classmethod
    def name_ok(cls, value: str) -> str: return _text(value, name="name", max_len=512)  # type: ignore[return-value]


class DataHubOwnerReference(_Strict):
    owner_urn: str
    owner_kind: DataHubOwnerKind
    display_name: str | None = None

    @field_validator("owner_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str: return _urn(value, name="owner_urn")

    @field_validator("display_name")
    @classmethod
    def display_ok(cls, value: str | None) -> str | None:
        return None if value is None else _text(value, name="display_name", max_len=512)


class DataHubFieldMetadata(_Strict):
    field_path: str
    native_type: str | None = None
    nullable: bool | None = None
    description: str | None = None
    tags: list[DataHubNamedReference] = Field(default_factory=list, max_length=32)
    glossary_terms: list[DataHubNamedReference] = Field(default_factory=list, max_length=32)

    @field_validator("field_path")
    @classmethod
    def path_ok(cls, value: str) -> str: return _text(value, name="field_path", max_len=512)  # type: ignore[return-value]

    @field_validator("native_type")
    @classmethod
    def type_ok(cls, value: str | None) -> str | None:
        return None if value is None else _text(value, name="native_type", max_len=128)

    @field_validator("description")
    @classmethod
    def description_ok(cls, value: str | None) -> str | None:
        return None if value is None else _text(value, name="description", max_len=2000)

    @model_validator(mode="after")
    def unique_refs(self) -> "DataHubFieldMetadata":
        _unique(self.tags, name="tags", key=lambda x: x.urn, max_items=32)
        _unique(self.glossary_terms, name="glossary_terms", key=lambda x: x.urn, max_items=32)
        return self


class DataHubSchemaContext(_Strict):
    dataset_urn: str
    fields: list[DataHubFieldMetadata] = Field(default_factory=list, max_length=500)

    @field_validator("dataset_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str: return _urn(value, name="dataset_urn")

    @model_validator(mode="after")
    def unique_fields(self) -> "DataHubSchemaContext":
        _unique(self.fields, name="fields", key=lambda x: x.field_path, max_items=500)
        return self


class DataHubLineageNode(_Strict):
    urn: str
    entity_kind: DataHubEntityKind
    platform: str | None = None
    display_name: str | None = None
    relation: DataHubLineageRelation
    depth: int = Field(ge=0, le=5)

    @field_validator("urn")
    @classmethod
    def urn_ok(cls, value: str) -> str: return _urn(value)

    @field_validator("platform")
    @classmethod
    def platform_ok(cls, value: str | None) -> str | None:
        return None if value is None else _snake(value, name="platform")

    @field_validator("display_name")
    @classmethod
    def display_ok(cls, value: str | None) -> str | None:
        return None if value is None else _text(value, name="display_name", max_len=512)

    @model_validator(mode="after")
    def relation_depth(self) -> "DataHubLineageNode":
        if self.relation == DataHubLineageRelation.SUBJECT and self.depth != 0:
            raise ValueError("subject lineage node must have depth 0")
        if self.relation == DataHubLineageRelation.DOWNSTREAM and self.depth < 1:
            raise ValueError("downstream lineage node must have depth >= 1")
        return self


class DataHubLineageEdge(_Strict):
    upstream_urn: str
    downstream_urn: str

    @field_validator("upstream_urn", "downstream_urn")
    @classmethod
    def urn_ok(cls, value: str, info) -> str: return _urn(value, name=info.field_name)

    @model_validator(mode="after")
    def not_self(self) -> "DataHubLineageEdge":
        if self.upstream_urn == self.downstream_urn:
            raise ValueError("lineage edge must not be a self edge")
        return self


class DataHubDownstreamLineage(_Strict):
    subject_urn: str
    nodes: list[DataHubLineageNode] = Field(max_length=200)
    edges: list[DataHubLineageEdge] = Field(default_factory=list, max_length=400)
    requested_depth: int = Field(ge=1, le=5)
    observed_max_depth: int = Field(ge=0, le=5)
    truncated: bool

    @field_validator("subject_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str: return _urn(value, name="subject_urn")

    @model_validator(mode="after")
    def graph_invariants(self) -> "DataHubDownstreamLineage":
        if self.observed_max_depth > self.requested_depth:
            raise ValueError("observed_max_depth must not exceed requested_depth")
        _unique(self.nodes, name="nodes", key=lambda x: x.urn, max_items=200)
        _unique(self.edges, name="edges", key=lambda x: (x.upstream_urn, x.downstream_urn), max_items=400)
        subjects = [n for n in self.nodes if n.urn == self.subject_urn]
        if len(subjects) != 1 or subjects[0].relation != DataHubLineageRelation.SUBJECT or subjects[0].depth != 0:
            raise ValueError("graph must contain exactly one subject node at depth 0")
        urns = {n.urn for n in self.nodes}
        if any(e.upstream_urn not in urns or e.downstream_urn not in urns for e in self.edges):
            raise ValueError("lineage edge endpoint is not present in nodes")
        if any(n.urn != self.subject_urn and n.relation != DataHubLineageRelation.DOWNSTREAM for n in self.nodes):
            raise ValueError("all non-subject nodes must be downstream")
        return self


class DataHubColumnLineageEdge(_Strict):
    source_dataset_urn: str
    source_field_path: str
    target_dataset_urn: str
    target_field_path: str

    @field_validator("source_dataset_urn", "target_dataset_urn")
    @classmethod
    def dataset_ok(cls, value: str, info) -> str: return _urn(value, name=info.field_name)

    @field_validator("source_field_path", "target_field_path")
    @classmethod
    def field_ok(cls, value: str, info) -> str: return _text(value, name=info.field_name, max_len=512)  # type: ignore[return-value]

    @model_validator(mode="after")
    def not_identical(self) -> "DataHubColumnLineageEdge":
        if (self.source_dataset_urn, self.source_field_path) == (self.target_dataset_urn, self.target_field_path):
            raise ValueError("column lineage source and target must differ")
        return self


class DataHubIncidentReference(_Strict):
    incident_urn: str
    status_code: str

    @field_validator("incident_urn")
    @classmethod
    def urn_ok(cls, value: str) -> str: return _urn(value, name="incident_urn")

    @field_validator("status_code")
    @classmethod
    def status_ok(cls, value: str) -> str: return _snake(value, name="status_code")


class DataHubMLDependencyReference(_Strict):
    urn: str
    entity_kind: DataHubEntityKind
    display_name: str | None = None

    @field_validator("urn")
    @classmethod
    def urn_ok(cls, value: str) -> str: return _urn(value)

    @field_validator("display_name")
    @classmethod
    def display_ok(cls, value: str | None) -> str | None:
        return None if value is None else _text(value, name="display_name", max_len=512)

    @field_validator("entity_kind")
    @classmethod
    def kind_ok(cls, value: DataHubEntityKind) -> DataHubEntityKind:
        if value not in {DataHubEntityKind.ML_FEATURE, DataHubEntityKind.ML_MODEL, DataHubEntityKind.ML_MODEL_GROUP, DataHubEntityKind.DEPLOYMENT}:
            raise ValueError("unsupported ML dependency entity kind")
        return value


class DataHubOperationalSignals(_Strict):
    query_usage_available: bool
    query_reference_count: int | None = Field(default=None, ge=0, le=1_000_000)
    quality_signal_codes: list[str] = Field(default_factory=list, max_length=64)
    incidents: list[DataHubIncidentReference] = Field(default_factory=list, max_length=64)
    ml_dependencies: list[DataHubMLDependencyReference] = Field(default_factory=list, max_length=100)

    @field_validator("quality_signal_codes")
    @classmethod
    def quality_ok(cls, value: list[str]) -> list[str]:
        return _unique([_snake(v, name="quality_signal_codes item") for v in value], name="quality_signal_codes", key=lambda x: x, max_items=64)

    @model_validator(mode="after")
    def signals_invariants(self) -> "DataHubOperationalSignals":
        if self.query_usage_available != (self.query_reference_count is not None):
            raise ValueError("query usage availability and count must agree")
        _unique(self.incidents, name="incidents", key=lambda x: x.incident_urn, max_items=64)
        _unique(self.ml_dependencies, name="ml_dependencies", key=lambda x: x.urn, max_items=100)
        return self


class DataHubGovernanceContext(_Strict):
    owners: list[DataHubOwnerReference] = Field(default_factory=list, max_length=50)
    tags: list[DataHubNamedReference] = Field(default_factory=list, max_length=100)
    glossary_terms: list[DataHubNamedReference] = Field(default_factory=list, max_length=100)
    domain: DataHubNamedReference | None = None
    description: str | None = None

    @field_validator("description")
    @classmethod
    def description_ok(cls, value: str | None) -> str | None:
        return None if value is None else _text(value, name="description", max_len=4000)

    @model_validator(mode="after")
    def unique_refs(self) -> "DataHubGovernanceContext":
        _unique(self.owners, name="owners", key=lambda x: x.owner_urn, max_items=50)
        _unique(self.tags, name="tags", key=lambda x: x.urn, max_items=100)
        _unique(self.glossary_terms, name="glossary_terms", key=lambda x: x.urn, max_items=100)
        return self


class DataHubContextCompleteness(_Strict):
    available_categories: list[DataHubContextCategory]
    unavailable_categories: list[DataHubContextCategory]
    truncated_categories: list[DataHubContextCategory] = Field(default_factory=list)
    required_categories_complete: bool
    reason_codes: list[str] = Field(default_factory=list, max_length=32)

    @model_validator(mode="after")
    def categories_ok(self) -> "DataHubContextCompleteness":
        all_values = set(DATAHUB_CONTEXT_CATEGORY_ORDER)
        av = [x.value for x in self.available_categories]
        un = [x.value for x in self.unavailable_categories]
        tr = [x.value for x in self.truncated_categories]
        if len(set(av)) != len(av) or len(set(un)) != len(un) or len(set(tr)) != len(tr):
            raise ValueError("categories must be unique")
        if set(av) & set(un) or set(av) | set(un) != all_values or not set(tr) <= set(av):
            raise ValueError("categories must be a complete, non-overlapping partition")
        order = {v: i for i, v in enumerate(DATAHUB_CONTEXT_CATEGORY_ORDER)}
        if av != sorted(av, key=order.get) or un != sorted(un, key=order.get) or tr != sorted(tr, key=order.get):
            raise ValueError("categories must use canonical order")
        expected = all(x in av and x not in tr for x in _REQUIRED)
        if self.required_categories_complete != expected:
            raise ValueError("required_categories_complete does not match categories")
        _unique([_snake(x, name="reason_code") for x in self.reason_codes], name="reason_codes", key=lambda x: x, max_items=32)
        return self


class DataHubContextPack(_Strict):
    subject_fingerprint: str
    resolved_subject: DataHubResolvedSubject
    schema_context: DataHubSchemaContext
    downstream_lineage: DataHubDownstreamLineage
    column_lineage: list[DataHubColumnLineageEdge] = Field(default_factory=list, max_length=400)
    governance: DataHubGovernanceContext
    operational_signals: DataHubOperationalSignals
    completeness: DataHubContextCompleteness
    context_pack_version: str = "1.0"

    @field_validator("subject_fingerprint")
    @classmethod
    def fingerprint_ok(cls, value: str) -> str:
        if not is_sha256_hex(value): raise ValueError("subject_fingerprint must be lowercase SHA-256 hex")
        return value

    @field_validator("context_pack_version")
    @classmethod
    def version_ok(cls, value: str) -> str:
        if value != "1.0": raise ValueError("context_pack_version must be 1.0")
        return value

    @model_validator(mode="after")
    def pack_invariants(self) -> "DataHubContextPack":
        if self.resolved_subject.dataset_urn != self.schema_context.dataset_urn or self.resolved_subject.dataset_urn != self.downstream_lineage.subject_urn:
            raise ValueError("subject URNs must agree across context pack")
        if self.completeness.available_categories.count(DataHubContextCategory.FIELD_METADATA) and self.resolved_subject.field_path:
            if self.resolved_subject.field_path not in {f.field_path for f in self.schema_context.fields}:
                raise ValueError("resolved field must be present when field metadata is available")
        _unique(self.column_lineage, name="column_lineage", key=lambda x: (x.source_dataset_urn, x.source_field_path, x.target_dataset_urn, x.target_field_path), max_items=400)
        return self


class DataHubContextArtifact(_Strict):
    context_id: UUID
    subject_fingerprint: str
    context_fingerprint: str | None
    source_kind: DataHubContextSourceKind
    execution_status: DataHubContextExecutionStatus
    context_pack: DataHubContextPack | None
    status_detail: DataHubContextStatusDetail | None
    source_system: str = "datahub"
    metadata_trust: str = "external_unverified"
    provenance_verified: bool = False
    authority: str = "context_only"
    decision_authority: str = "none"
    validation_effect: str = "none"
    writeback_authorized: bool = False
    deployment_authorized: bool = False
    persistence: str = "none"
    retrieval_available: bool = False
    artifact_version: str = "1.0"

    @field_validator("subject_fingerprint")
    @classmethod
    def subject_fp_ok(cls, value: str) -> str:
        if not is_sha256_hex(value): raise ValueError("invalid subject_fingerprint")
        return value

    @field_validator("context_fingerprint")
    @classmethod
    def context_fp_ok(cls, value: str | None) -> str | None:
        if value is not None and not is_sha256_hex(value): raise ValueError("invalid context_fingerprint")
        return value

    @model_validator(mode="after")
    def constants_and_state(self) -> "DataHubContextArtifact":
        constants = {"source_system": "datahub", "metadata_trust": "external_unverified", "provenance_verified": False, "authority": "context_only", "decision_authority": "none", "validation_effect": "none", "writeback_authorized": False, "deployment_authorized": False, "persistence": "none", "retrieval_available": False, "artifact_version": "1.0"}
        for key, expected in constants.items():
            if getattr(self, key) != expected: raise ValueError(f"{key} is server-owned")
        status = self.execution_status
        if status == DataHubContextExecutionStatus.COMPLETED:
            if self.context_pack is None or self.context_fingerprint is None or self.status_detail is not None or not self.context_pack.completeness.required_categories_complete: raise ValueError("invalid completed artifact state")
        elif status == DataHubContextExecutionStatus.PARTIAL:
            if self.context_pack is None or self.context_fingerprint is None or self.status_detail is None or self.context_pack.completeness.required_categories_complete: raise ValueError("invalid partial artifact state")
        else:
            if self.context_pack is not None or self.context_fingerprint is not None or self.status_detail is None: raise ValueError("invalid noncompleted artifact state")
        if self.context_pack is not None and self.subject_fingerprint != self.context_pack.subject_fingerprint: raise ValueError("subject fingerprint mismatch")
        if self.context_pack is not None and self.context_fingerprint is not None:
            # Local import avoids a module cycle; builders use the same helper.
            from app.utils.datahub_fingerprint import fingerprint_datahub_context
            if self.context_fingerprint != fingerprint_datahub_context(self.context_pack):
                raise ValueError("context_fingerprint does not match context_pack")
        return self


__all__ = [name for name in globals() if name.startswith("DataHub")] + ["DATAHUB_CONTEXT_CATEGORY_ORDER"]
