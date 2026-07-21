"""API envelope helpers for validation execution (phase F6.6).

Request body reuses ``ValidationPlanInput`` (F6.5).
Success ``data`` reuses ``ValidationArtifact`` (F6.1).
This module only defines honest response meta for the HTTP boundary.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ValidationExecutionMeta(BaseModel):
    """Honest meta for POST /api/v1/validations/execute success responses.

    Documents trust and persistence boundaries. Does **not** claim provenance,
    registry verification, or deployment authorization.
    """

    model_config = ConfigDict(extra="forbid")

    operation: Literal["validation_execution"] = "validation_execution"
    phase: Literal["F6.6"] = "F6.6"
    execution_mode: Literal["synchronous_orchestration"] = "synchronous_orchestration"
    validation_scope: Literal["provided_artifacts_only"] = "provided_artifacts_only"
    persistence: Literal["none"] = "none"
    retrieval_available: Literal[False] = False
    intake_reference_origin: Literal["caller_provided"] = "caller_provided"
    intake_reference_trust: Literal["unverified"] = "unverified"
    subject_fingerprint_scope: Literal["normalized_change_only"] = (
        "normalized_change_only"
    )
    fingerprint_check: Literal["matched"] = "matched"
    cross_artifact_consistency: Literal["matched"] = "matched"
    cross_artifact_provenance: Literal["unverified"] = "unverified"
    sql_origin: Literal["caller_provided"] = "caller_provided"
    sql_trust: Literal["unverified"] = "unverified"
    fixture_origin: Literal["caller_provided"] = "caller_provided"
    fixture_trust: Literal["unverified"] = "unverified"
    model_used: Literal[False] = Field(
        default=False,
        description="No AI model is used for validation execution.",
    )
    deployment_authorized: Literal[False] = Field(
        default=False,
        description="Validation never authorizes deployment or writeback.",
    )


def validation_execution_meta() -> dict[str, Any]:
    """Return success-path meta for validation execution (JSON-serializable)."""
    return ValidationExecutionMeta().model_dump(mode="json")
