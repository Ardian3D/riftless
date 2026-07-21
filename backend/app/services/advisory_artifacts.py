"""Pure builders for AdvisoryArtifact (phase F7.1).

No network, environment, filesystem, logging, or provider calls.
Does not grant risk, validation, or deployment authority.
"""

from __future__ import annotations

import uuid

from app.schemas.advisory import (
    ADVISORY_ARTIFACT_VERSION,
    ADVISORY_AUTHORITY,
    ADVISORY_PROVIDER_NAME,
    ADVISORY_RISK_EFFECT,
    ADVISORY_SCOPE,
    ADVISORY_VALIDATION_EFFECT,
    AdvisoryArtifact,
    AdvisoryContent,
    AdvisoryContextPack,
    AdvisoryExecutionStatus,
    AdvisoryStatusDetail,
)
from app.utils.advisory_fingerprint import fingerprint_advisory_context


def build_completed_advisory_artifact(
    *,
    context: AdvisoryContextPack,
    content: AdvisoryContent,
    model_name: str,
) -> AdvisoryArtifact:
    """Build a COMPLETED advisory artifact bound to a redacted context pack.

    Server assigns ``advisory_id`` and computes ``context_fingerprint``.
    Caller cannot override authority, effects, persistence, or provider.
    """
    if not isinstance(context, AdvisoryContextPack):
        raise TypeError("context must be an AdvisoryContextPack")
    if not isinstance(content, AdvisoryContent):
        raise TypeError("content must be an AdvisoryContent")
    if not isinstance(model_name, str) or not model_name.strip():
        raise ValueError("model_name must be a non-blank string")

    context_fp = fingerprint_advisory_context(context)

    return AdvisoryArtifact(
        advisory_id=uuid.uuid4(),
        subject_fingerprint=context.subject_fingerprint,
        context_fingerprint=context_fp,
        scope=ADVISORY_SCOPE,
        execution_status=AdvisoryExecutionStatus.COMPLETED,
        content=content,
        status_detail=None,
        provider_name=ADVISORY_PROVIDER_NAME,
        model_name=model_name.strip(),
        authority=ADVISORY_AUTHORITY,
        risk_effect=ADVISORY_RISK_EFFECT,
        validation_effect=ADVISORY_VALIDATION_EFFECT,
        deployment_authorized=False,
        persistence="none",
        retrieval_available=False,
        artifact_version=ADVISORY_ARTIFACT_VERSION,
    )


def build_noncompleted_advisory_artifact(
    *,
    context: AdvisoryContextPack,
    execution_status: AdvisoryExecutionStatus | str,
    status_detail: AdvisoryStatusDetail,
    model_name: str | None = None,
) -> AdvisoryArtifact:
    """Build ERROR / UNAVAILABLE / SKIPPED advisory artifact (content null).

    Rejects COMPLETED — use ``build_completed_advisory_artifact`` instead.
    """
    if not isinstance(context, AdvisoryContextPack):
        raise TypeError("context must be an AdvisoryContextPack")
    if not isinstance(status_detail, AdvisoryStatusDetail):
        raise TypeError("status_detail must be an AdvisoryStatusDetail")

    if isinstance(execution_status, AdvisoryExecutionStatus):
        status = execution_status
    else:
        try:
            status = AdvisoryExecutionStatus(str(execution_status))
        except ValueError as exc:
            raise ValueError(
                f"invalid advisory execution_status: {execution_status!r}"
            ) from exc

    if status == AdvisoryExecutionStatus.COMPLETED:
        raise ValueError(
            "build_noncompleted_advisory_artifact rejects completed; "
            "use build_completed_advisory_artifact"
        )

    context_fp = fingerprint_advisory_context(context)
    cleaned_model: str | None = None
    if model_name is not None:
        cleaned_model = model_name.strip()
        if not cleaned_model:
            raise ValueError("model_name must be null or non-blank")

    return AdvisoryArtifact(
        advisory_id=uuid.uuid4(),
        subject_fingerprint=context.subject_fingerprint,
        context_fingerprint=context_fp,
        scope=ADVISORY_SCOPE,
        execution_status=status,
        content=None,
        status_detail=status_detail,
        provider_name=ADVISORY_PROVIDER_NAME,
        model_name=cleaned_model,
        authority=ADVISORY_AUTHORITY,
        risk_effect=ADVISORY_RISK_EFFECT,
        validation_effect=ADVISORY_VALIDATION_EFFECT,
        deployment_authorized=False,
        persistence="none",
        retrieval_available=False,
        artifact_version=ADVISORY_ARTIFACT_VERSION,
    )
