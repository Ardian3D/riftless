"""F8.3B3 deterministic asset candidate resolution.

This module is pure resolution logic. It consumes normalized F8.3B2 dataset
records and a bounded RIFTLESS subject identity and deterministically decides
whether exactly one dataset candidate is uniquely resolvable. It never
performs provider or network calls, metadata retrieval, model inference,
random behavior, or application integration. Provider ordering is an
observation only and is never used to select candidates or break ties.

Candidate DataHub platform compatibility is an eligibility gate: a candidate
whose safely parsed platform does not match the normalized subject platform
can never resolve through any name or display signal.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from app.schemas.changes import NormalizedChange
from app.schemas.datahub_context import DataHubEntityKind, DataHubResolutionMethod, DataHubResolvedSubject

from .search_contract import DataHubSearchContractError, _validate_query
from .search_execution import DataHubDatasetSearchRecord, DataHubSearchExecutionResult, _safe_urn

RESOLUTION_VERSION = "1.0"
MAX_CANDIDATES = 10

_DATASET_URN_PREFIX = "urn:li:dataset:("
_PLATFORM_PART_PREFIX = "urn:li:dataPlatform:"

_MAX_PLATFORM = 64
_MAX_DB_PART = 128
_MAX_ASSET_NAME = 256
_MAX_COLUMN = 256

_FQ_CLASS = 4
_DATASET_CLASS = 3
_DISPLAY_CLASS = 2
_URN_CLASS = 1


class DataHubAssetResolutionError(ValueError):
    """Safe asset-resolution error with no provider-controlled detail."""

    def __init__(self, code: str, message: str = "DataHub asset resolution failed.") -> None:
        self.code = code
        self.message = message
        self.retryable = False
        super().__init__(message)


class _StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class DataHubAssetResolutionStatus(_StrEnum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"


class DataHubAssetResolutionConfidence(_StrEnum):
    EXACT = "exact"
    HIGH = "high"
    AMBIGUOUS = "ambiguous"
    NONE = "none"


class DataHubAssetResolutionMethod(_StrEnum):
    EXACT_FULLY_QUALIFIED = "exact_fully_qualified"
    EXACT_DATASET_NAME = "exact_dataset_name"
    EXACT_DISPLAY_NAME = "exact_display_name"
    EXACT_URN_DATASET_NAME = "exact_urn_dataset_name"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


_METHOD_BY_CLASS = {
    _FQ_CLASS: DataHubAssetResolutionMethod.EXACT_FULLY_QUALIFIED,
    _DATASET_CLASS: DataHubAssetResolutionMethod.EXACT_DATASET_NAME,
    _DISPLAY_CLASS: DataHubAssetResolutionMethod.EXACT_DISPLAY_NAME,
    _URN_CLASS: DataHubAssetResolutionMethod.EXACT_URN_DATASET_NAME,
}
_CONFIDENCE_BY_CLASS = {
    _FQ_CLASS: DataHubAssetResolutionConfidence.EXACT,
    _DATASET_CLASS: DataHubAssetResolutionConfidence.HIGH,
    _DISPLAY_CLASS: DataHubAssetResolutionConfidence.HIGH,
    _URN_CLASS: DataHubAssetResolutionConfidence.HIGH,
}
# "exact" means an exact match across every deterministic RIFTLESS identity
# dimension available and checked by this resolver (platform plus normalized
# qualified dataset name). It does not verify the DataHub environment,
# metadata freshness, provenance, or provider authenticity.
_EXACT_METHODS = frozenset(_METHOD_BY_CLASS.values())
_RESOLVED_CONFIDENCE_FLOAT = {
    DataHubAssetResolutionConfidence.EXACT: 1.0,
    DataHubAssetResolutionConfidence.HIGH: 0.75,
}


def _identity_text(value: Any, *, name: str, max_len: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    if "\x00" in value or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ValueError(f"{name} contains a forbidden control character")
    result = value.strip()
    if not result:
        raise ValueError(f"{name} must not be blank")
    if len(result) > max_len:
        raise ValueError(f"{name} must be at most {max_len} characters")
    return result


class DataHubAssetResolutionSubject(_Strict):
    """Minimum stable RIFTLESS identity used only for dataset resolution.

    Fields mirror the normalized F5.1 asset reference plus the affected
    column. No raw SQL, prose, query text, credentials, risk, or validation
    content is carried.
    """

    platform: str
    database: str
    schema_name: str
    table_name: str
    affected_column: str | None = None

    @field_validator("platform")
    @classmethod
    def platform_ok(cls, value: str) -> str:
        return _identity_text(value, name="platform", max_len=_MAX_PLATFORM)

    @field_validator("database")
    @classmethod
    def database_ok(cls, value: str) -> str:
        return _identity_text(value, name="database", max_len=_MAX_DB_PART)

    @field_validator("schema_name")
    @classmethod
    def schema_ok(cls, value: str) -> str:
        return _identity_text(value, name="schema_name", max_len=_MAX_DB_PART)

    @field_validator("table_name")
    @classmethod
    def table_ok(cls, value: str) -> str:
        return _identity_text(value, name="table_name", max_len=_MAX_ASSET_NAME)

    @field_validator("affected_column")
    @classmethod
    def column_ok(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _identity_text(value, name="affected_column", max_len=_MAX_COLUMN)


class DataHubAssetCandidateResolution(_Strict):
    """Bounded, immutable outcome of deterministic candidate resolution.

    Stores only the selection evidence: status, selected URN, confidence,
    method, bounded counts, and the observed source position. It never stores
    raw candidate payloads, search queries, provider responses, credentials,
    or any authorization-relevant runtime state.
    """

    status: DataHubAssetResolutionStatus
    selected_dataset_urn: str | None = None
    confidence: DataHubAssetResolutionConfidence
    resolution_method: DataHubAssetResolutionMethod
    candidate_count: StrictInt = Field(ge=0, le=MAX_CANDIDATES)
    strongest_match_count: StrictInt = Field(ge=0, le=MAX_CANDIDATES)
    selected_source_position: StrictInt | None = Field(default=None, ge=0, le=9)
    resolution_version: str = RESOLUTION_VERSION

    @field_validator("selected_dataset_urn")
    @classmethod
    def urn_ok(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _safe_urn(value)

    @model_validator(mode="after")
    def invariants(self) -> "DataHubAssetCandidateResolution":
        if self.resolution_version != RESOLUTION_VERSION:
            raise ValueError("invalid resolution version")
        if self.candidate_count < self.strongest_match_count:
            raise ValueError("strongest match count must not exceed candidate count")
        if self.status is DataHubAssetResolutionStatus.RESOLVED:
            if self.selected_dataset_urn is None or self.selected_source_position is None or self.strongest_match_count != 1:
                raise ValueError("invalid resolved resolution state")
            if self.confidence not in (DataHubAssetResolutionConfidence.EXACT, DataHubAssetResolutionConfidence.HIGH) or self.resolution_method not in _EXACT_METHODS:
                raise ValueError("invalid resolved resolution method or confidence")
        elif self.status is DataHubAssetResolutionStatus.AMBIGUOUS:
            if self.selected_dataset_urn is not None or self.selected_source_position is not None or self.strongest_match_count < 2:
                raise ValueError("invalid ambiguous resolution state")
            if self.confidence is not DataHubAssetResolutionConfidence.AMBIGUOUS or self.resolution_method is not DataHubAssetResolutionMethod.AMBIGUOUS:
                raise ValueError("invalid ambiguous resolution method or confidence")
        elif self.status is DataHubAssetResolutionStatus.UNRESOLVED:
            if self.selected_dataset_urn is not None or self.selected_source_position is not None or self.strongest_match_count != 0:
                raise ValueError("invalid unresolved resolution state")
            if self.confidence is not DataHubAssetResolutionConfidence.NONE or self.resolution_method is not DataHubAssetResolutionMethod.UNRESOLVED:
                raise ValueError("invalid unresolved resolution method or confidence")
        else:
            raise ValueError("invalid resolution status")
        return self


def _qualified_subject_name(subject: DataHubAssetResolutionSubject) -> str:
    return f"{subject.database}.{subject.schema_name}.{subject.table_name}"


def _norm(value: str) -> str:
    return value.strip().lower()


def _dataset_urn_parts(urn: str) -> tuple[str, str] | None:
    """Safely extract ``(platform, dataset_name)`` from a narrow bounded URN.

    Returns ``None`` instead of guessing whenever the dataset URN does not
    match the exact ``urn:li:dataset:(urn:li:dataPlatform:<p>,<name>,<env>)``
    shape with three top-level comma-separated parts. The environment token
    is observed but not trusted or compared.
    """
    if not urn.startswith(_DATASET_URN_PREFIX) or not urn.endswith(")"):
        return None
    inner = urn[len(_DATASET_URN_PREFIX):-1]
    parts = inner.split(",")
    if len(parts) != 3:
        return None
    platform_part, name, _env = parts
    if not platform_part.startswith(_PLATFORM_PART_PREFIX):
        return None
    platform = platform_part[len(_PLATFORM_PART_PREFIX):]
    if not platform or len(platform) > _MAX_PLATFORM or any(ch.isspace() for ch in platform) or any(ord(ch) < 32 or ord(ch) == 127 for ch in platform):
        return None
    if not name or len(name) > 1024 or any(ch.isspace() for ch in name):
        return None
    return platform, name


def _last_path_component(value: str) -> str:
    if "." in value:
        return value.rsplit(".", 1)[-1]
    return value


def _signal_class(subject_platform: str, subject_fq: str, subject_name: str, record: DataHubDatasetSearchRecord) -> int:
    """Return the strongest deterministic exact-match class for one candidate.

    Platform compatibility is an eligibility gate: a candidate whose safely
    parsed DataHub platform does not equal the normalized subject platform
    (or whose platform cannot be safely parsed) receives class 0 and can
    never be rescued by any name or display signal.

    Eligible classes: 4 = exact fully-qualified identity, 3 = exact dataset
    name, 2 = exact display name, 1 = exact URN dataset name, 0 = ineligible
    or no exact signal.
    """
    parts = _dataset_urn_parts(record.dataset_urn)
    if parts is None:
        return 0
    platform, urn_name = parts
    if _norm(platform) != subject_platform:
        return 0
    display = record.display_name
    if _norm(urn_name) == subject_fq:
        return _FQ_CLASS
    if display is not None and _norm(display) == subject_fq:
        return _FQ_CLASS
    if _norm(_last_path_component(urn_name)) == subject_name:
        return _DATASET_CLASS
    if display is not None and _norm(display) == subject_name:
        return _DISPLAY_CLASS
    if _norm(urn_name) == subject_name:
        return _URN_CLASS
    return 0


def build_datahub_asset_resolution_subject(*, normalized: NormalizedChange) -> DataHubAssetResolutionSubject:
    """Project a normalized F5.1 change into the bounded resolution subject.

    Only stable dataset identity and the affected column are copied. The
    change reason, target column, and any prose are deliberately not carried.
    """
    if not isinstance(normalized, NormalizedChange):
        raise DataHubAssetResolutionError("invalid_asset_resolution_subject", "DataHub asset resolution subject is invalid.")
    try:
        return DataHubAssetResolutionSubject(
            platform=normalized.asset.platform,
            database=normalized.asset.database,
            schema_name=normalized.asset.schema_name,
            table_name=normalized.asset.name,
            affected_column=normalized.source_column,
        )
    except ValueError:
        raise DataHubAssetResolutionError("invalid_asset_resolution_subject", "DataHub asset resolution subject is invalid.") from None


def build_datahub_asset_search_query(*, subject: DataHubAssetResolutionSubject) -> str:
    """Derive the deterministic bounded ``/q `` search query from subject identity.

    The query uses the fully-qualified dataset name when it fits the locked
    F8.3B1 4-512 character contract, otherwise the plain table name. A caller
    cannot supply query text.
    """
    if not isinstance(subject, DataHubAssetResolutionSubject):
        raise DataHubAssetResolutionError("invalid_asset_resolution_subject", "DataHub asset resolution subject is invalid.")
    qualified = _qualified_subject_name(subject)
    content = qualified if len(qualified) + len("/q ") <= 512 else subject.table_name
    try:
        return _validate_query(f"/q {content}")
    except DataHubSearchContractError:
        raise DataHubAssetResolutionError("asset_resolution_query_invalid", "DataHub asset resolution query is invalid.") from None


def resolve_datahub_asset_candidate(*, subject: DataHubAssetResolutionSubject, search_result: DataHubSearchExecutionResult) -> DataHubAssetCandidateResolution:
    """Deterministically resolve a bounded search result to at most one dataset.

    The strongest exact identity class is computed per candidate without
    order dependence. Only a unique strongest-class candidate is resolved;
    ties are ambiguous; no exact signal is unresolved.
    """
    if not isinstance(subject, DataHubAssetResolutionSubject):
        raise DataHubAssetResolutionError("invalid_asset_resolution_subject", "DataHub asset resolution subject is invalid.")
    if not isinstance(search_result, DataHubSearchExecutionResult):
        raise DataHubAssetResolutionError("invalid_asset_resolution_candidate", "DataHub asset resolution candidates are invalid.")
    records = search_result.records
    candidate_count = len(records)
    if not 0 <= candidate_count <= MAX_CANDIDATES or any(not isinstance(record, DataHubDatasetSearchRecord) for record in records):
        raise DataHubAssetResolutionError("invalid_asset_resolution_candidate", "DataHub asset resolution candidates are invalid.")
    subject_platform = _norm(subject.platform)
    subject_fq = _norm(_qualified_subject_name(subject))
    subject_name = _norm(subject.table_name)
    classes = [_signal_class(subject_platform, subject_fq, subject_name, record) for record in records]
    strongest = max(classes) if classes else 0
    if strongest == 0:
        return DataHubAssetCandidateResolution(status=DataHubAssetResolutionStatus.UNRESOLVED, confidence=DataHubAssetResolutionConfidence.NONE, resolution_method=DataHubAssetResolutionMethod.UNRESOLVED, candidate_count=candidate_count, strongest_match_count=0)
    winners = [record for record, cls in zip(records, classes) if cls == strongest]
    strongest_match_count = len(winners)
    if strongest_match_count == 1:
        selected = winners[0]
        return DataHubAssetCandidateResolution(
            status=DataHubAssetResolutionStatus.RESOLVED,
            selected_dataset_urn=selected.dataset_urn,
            confidence=_CONFIDENCE_BY_CLASS[strongest],
            resolution_method=_METHOD_BY_CLASS[strongest],
            candidate_count=candidate_count,
            strongest_match_count=1,
            selected_source_position=selected.source_position,
        )
    return DataHubAssetCandidateResolution(status=DataHubAssetResolutionStatus.AMBIGUOUS, confidence=DataHubAssetResolutionConfidence.AMBIGUOUS, resolution_method=DataHubAssetResolutionMethod.AMBIGUOUS, candidate_count=candidate_count, strongest_match_count=strongest_match_count)


def build_datahub_resolved_subject_from_resolution(*, subject: DataHubAssetResolutionSubject, resolution: DataHubAssetCandidateResolution) -> DataHubResolvedSubject:
    """Map a uniquely resolved candidate onto the locked F8.1 resolved subject.

    Only ``resolved`` outcomes convert, the selected dataset URN must parse
    through the bounded adapter, and the selected candidate's platform must
    match the normalized subject platform before ``platform`` is populated.
    Ambiguous and unresolved outcomes can never fabricate a resolved subject.
    Confidence and method use fixed server-owned values within the F8.1
    contract.
    """
    if not isinstance(subject, DataHubAssetResolutionSubject) or not isinstance(resolution, DataHubAssetCandidateResolution):
        raise DataHubAssetResolutionError("invalid_asset_resolution_subject", "DataHub asset resolution subject is invalid.")
    if resolution.status is not DataHubAssetResolutionStatus.RESOLVED or resolution.selected_dataset_urn is None:
        raise DataHubAssetResolutionError("asset_resolution_invariant_violation", "Only a uniquely resolved candidate can form a resolved subject.")
    parts = _dataset_urn_parts(resolution.selected_dataset_urn)
    if parts is None or _norm(parts[0]) != _norm(subject.platform):
        raise DataHubAssetResolutionError("asset_resolution_invariant_violation", "Selected candidate platform is not compatible with the resolution subject.")
    try:
        return DataHubResolvedSubject(
            dataset_urn=resolution.selected_dataset_urn,
            entity_kind=DataHubEntityKind.DATASET,
            platform=subject.platform,
            field_path=subject.affected_column,
            resolution_method=DataHubResolutionMethod.DATAHUB_SEARCH,
            confidence=_RESOLVED_CONFIDENCE_FLOAT[resolution.confidence],
        )
    except ValueError:
        raise DataHubAssetResolutionError("asset_resolution_invariant_violation", "Resolved subject conversion is not supported for this resolution.") from None


__all__ = [
    "DataHubAssetCandidateResolution",
    "DataHubAssetResolutionConfidence",
    "DataHubAssetResolutionError",
    "DataHubAssetResolutionMethod",
    "DataHubAssetResolutionStatus",
    "DataHubAssetResolutionSubject",
    "RESOLUTION_VERSION",
    "build_datahub_asset_resolution_subject",
    "build_datahub_asset_search_query",
    "build_datahub_resolved_subject_from_resolution",
    "resolve_datahub_asset_candidate",
]
