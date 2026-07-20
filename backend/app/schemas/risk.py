"""Request and response schemas for deterministic risk evaluation (F5.2)."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.changes import NormalizedChange
from app.utils.fingerprint import is_sha256_hex

DecisionLevel = Literal["ALLOW", "WARN", "BLOCK"]
POLICY_VERSION = "1.0"
SUPPORTED_ARTIFACT_VERSION = "1.0"


class EvaluationContext(BaseModel):
    """Caller-provided evaluation context.

    Origin and trust are reported in response meta as caller_provided /
    unverified. F5.2 does not load this context from DataHub or any
    external system.
    """

    model_config = ConfigDict(extra="forbid")

    context_complete: bool
    downstream_dependency_count: int | None = Field(
        default=None,
        description=(
            "Non-negative dependency count when known. "
            "May be null only when context_complete is false."
        ),
    )
    protected_asset: bool

    @field_validator("downstream_dependency_count")
    @classmethod
    def validate_dependency_count(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("downstream_dependency_count must be >= 0")
        return value

    @model_validator(mode="after")
    def complete_context_requires_count(self) -> EvaluationContext:
        if self.context_complete and self.downstream_dependency_count is None:
            raise ValueError(
                "downstream_dependency_count is required when context_complete is true"
            )
        return self

    def snapshot(self) -> dict[str, Any]:
        """Schema-accepted context snapshot for the response."""
        return self.model_dump(mode="json")


class IntakeReference(BaseModel):
    """Caller-provided intake reference for risk evaluation.

    In F5.2 the caller re-sends the intake payload. The server does **not**
    look up ``intake_id`` in a registry (none exists yet). After schema
    validation, only a fingerprint consistency check is performed against
    ``normalized_change``. Provenance remains unverified.
    """

    model_config = ConfigDict(extra="forbid")

    intake_id: UUID = Field(
        description=(
            "Caller-supplied UUID. Not matched against server-side storage "
            "in F5.2."
        ),
    )
    normalized_change: NormalizedChange
    content_fingerprint: str = Field(
        min_length=64,
        max_length=64,
        description=(
            "SHA-256 hex of normalized_change. Checked for consistency only; "
            "not a signature or provenance proof."
        ),
    )
    artifact_version: Literal["1.0"]

    @field_validator("content_fingerprint")
    @classmethod
    def validate_fingerprint_format(cls, value: str) -> str:
        if not is_sha256_hex(value):
            raise ValueError(
                "content_fingerprint must be a 64-character lowercase hexadecimal SHA-256 digest"
            )
        return value


class RiskEvaluateRequest(BaseModel):
    """Client request body for POST /api/v1/risk/evaluate."""

    model_config = ConfigDict(extra="forbid")

    intake_reference: IntakeReference
    evaluation_context: EvaluationContext


class RiskReason(BaseModel):
    """Structured reason produced by a deterministic rule."""

    model_config = ConfigDict(extra="forbid")

    code: str
    level: DecisionLevel
    message: str
    evidence: dict[str, Any] | None = None


class RiskEvaluationData(BaseModel):
    """Success data payload for deterministic risk evaluation."""

    model_config = ConfigDict(extra="forbid")

    evaluation_id: UUID
    intake_id: UUID
    decision: DecisionLevel
    scope: Literal["provided_context_only"] = "provided_context_only"
    reasons: list[RiskReason]
    evaluated_content_fingerprint: str
    evaluation_context: dict[str, Any]
    policy_version: Literal["1.0"] = "1.0"
    artifact_version: Literal["1.0"] = "1.0"
