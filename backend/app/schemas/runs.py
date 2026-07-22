"""Request and response schemas for synchronous analysis runs (F5.3 / F6.7 / F7.5)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.advisory import AdvisoryArtifact
from app.schemas.changes import ChangeIntakeData, ChangeIntakeRequest
from app.schemas.risk import EvaluationContext, RiskEvaluationData
from app.schemas.run_validation import RunValidationInput
from app.schemas.validation import ValidationArtifact

# F7.5 adds optional advisory_artifact to the run response.
RUN_ARTIFACT_VERSION = "1.2"


class AdvisoryRunOptions(BaseModel):
    """Optional advisory request block on POST /api/v1/runs/analyze.

    Callers may only declare whether advisory is requested. Provider config,
    model, prompt, context pack, transport, and API keys are never accepted
    from the request body.
    """

    model_config = ConfigDict(extra="forbid")

    requested: bool = Field(
        default=False,
        description=(
            "When true, the server builds a redacted AdvisoryContextPack from "
            "current-request artifacts and executes the DeepSeek advisory "
            "provider boundary. When false or when the advisory object is "
            "omitted, no provider work is performed."
        ),
    )


class AnalysisRunRequest(BaseModel):
    """Client request body for POST /api/v1/runs/analyze.

    Clients supply the change, evaluation context, and optionally validation
    check inputs and/or an advisory request flag. Server-generated identifiers,
    fingerprints, normalized payloads, decisions, validation results, context
    packs, prompts, and provider configuration must not be sent by the client.
    """

    model_config = ConfigDict(extra="forbid")

    change: ChangeIntakeRequest = Field(
        description="Change request validated with the F5.1 intake schema.",
    )
    evaluation_context: EvaluationContext = Field(
        description="Caller-provided context validated with the F5.2 schema.",
    )
    validation: RunValidationInput | None = Field(
        default=None,
        description=(
            "Optional validation check inputs (SQL, fixture, dbt model). "
            "When omitted, validation is not executed. Runtime intake identity "
            "is never accepted from the client."
        ),
    )
    advisory: AdvisoryRunOptions | None = Field(
        default=None,
        description=(
            "Optional advisory request. When omitted or requested=false, "
            "advisory is not executed and advisory_artifact is null. Callers "
            "cannot supply API keys, model, prompt, context pack, or transport."
        ),
    )


class AnalysisRunData(BaseModel):
    """Synchronous analysis run artifact returned in the success envelope."""

    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    orchestration_status: Literal["completed"] = "completed"
    change_intake: ChangeIntakeData
    risk_evaluation: RiskEvaluationData
    validation_artifact: ValidationArtifact | None = Field(
        default=None,
        description=(
            "Null when validation was not requested. Otherwise the F6.1 "
            "ValidationArtifact produced by in-process orchestration."
        ),
    )
    advisory_requested: bool = Field(
        default=False,
        description=(
            "True when the request asked for advisory. Independent of risk "
            "decision and validation outcome."
        ),
    )
    advisory_artifact: AdvisoryArtifact | None = Field(
        default=None,
        description=(
            "Null when advisory was not requested. When requested, a formed "
            "AdvisoryArtifact (completed, error, unavailable, or skipped)."
        ),
    )
    run_artifact_version: Literal["1.2"] = "1.2"

    @model_validator(mode="after")
    def enforce_advisory_presence(self) -> AnalysisRunData:
        if not self.advisory_requested:
            if self.advisory_artifact is not None:
                raise ValueError(
                    "advisory_artifact must be null when advisory was not requested"
                )
            return self
        if self.advisory_artifact is None:
            raise ValueError(
                "advisory_artifact is required when advisory was requested"
            )
        return self
