"""Request and response schemas for synchronous analysis runs (F5.3 / F6.7)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.changes import ChangeIntakeData, ChangeIntakeRequest
from app.schemas.risk import EvaluationContext, RiskEvaluationData
from app.schemas.run_validation import RunValidationInput
from app.schemas.validation import ValidationArtifact

# F6.7 adds optional validation_artifact to the run response.
RUN_ARTIFACT_VERSION = "1.1"


class AnalysisRunRequest(BaseModel):
    """Client request body for POST /api/v1/runs/analyze.

    Clients supply the change, evaluation context, and optionally validation
    check inputs. Server-generated identifiers, fingerprints, normalized
    payloads, decisions, and validation results must not be sent by the client.
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
    run_artifact_version: Literal["1.1"] = "1.1"
