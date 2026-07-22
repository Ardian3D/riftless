"""Pure builders for F8.1 DataHubContextArtifact contracts."""

from __future__ import annotations

import uuid

from app.schemas.datahub_context import (
    DataHubContextArtifact, DataHubContextExecutionStatus, DataHubContextPack,
    DataHubContextSourceKind, DataHubContextStatusDetail,
)
from app.utils.datahub_fingerprint import fingerprint_datahub_context


def build_completed_datahub_context_artifact(*, context: DataHubContextPack, source_kind: DataHubContextSourceKind) -> DataHubContextArtifact:
    if not isinstance(context, DataHubContextPack): raise TypeError("context must be a DataHubContextPack")
    if not isinstance(source_kind, DataHubContextSourceKind): raise TypeError("source_kind must be a DataHubContextSourceKind")
    if not context.completeness.required_categories_complete: raise ValueError("completed context requires complete required categories")
    return DataHubContextArtifact(context_id=uuid.uuid4(), subject_fingerprint=context.subject_fingerprint, context_fingerprint=fingerprint_datahub_context(context), source_kind=source_kind, execution_status=DataHubContextExecutionStatus.COMPLETED, context_pack=context, status_detail=None)


def build_partial_datahub_context_artifact(*, context: DataHubContextPack, source_kind: DataHubContextSourceKind, status_detail: DataHubContextStatusDetail) -> DataHubContextArtifact:
    if not isinstance(context, DataHubContextPack): raise TypeError("context must be a DataHubContextPack")
    if not isinstance(source_kind, DataHubContextSourceKind): raise TypeError("source_kind must be a DataHubContextSourceKind")
    if not isinstance(status_detail, DataHubContextStatusDetail): raise TypeError("status_detail must be a DataHubContextStatusDetail")
    if context.completeness.required_categories_complete: raise ValueError("partial context requires incomplete required categories")
    return DataHubContextArtifact(context_id=uuid.uuid4(), subject_fingerprint=context.subject_fingerprint, context_fingerprint=fingerprint_datahub_context(context), source_kind=source_kind, execution_status=DataHubContextExecutionStatus.PARTIAL, context_pack=context, status_detail=status_detail)


def build_noncompleted_datahub_context_artifact(*, subject_fingerprint: str, source_kind: DataHubContextSourceKind, execution_status: DataHubContextExecutionStatus, status_detail: DataHubContextStatusDetail) -> DataHubContextArtifact:
    if execution_status not in {DataHubContextExecutionStatus.ERROR, DataHubContextExecutionStatus.UNAVAILABLE, DataHubContextExecutionStatus.SKIPPED}:
        raise ValueError("noncompleted builder accepts error, unavailable, or skipped only")
    return DataHubContextArtifact(context_id=uuid.uuid4(), subject_fingerprint=subject_fingerprint, context_fingerprint=None, source_kind=source_kind, execution_status=execution_status, context_pack=None, status_detail=status_detail)
