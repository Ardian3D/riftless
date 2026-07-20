"""Request and response schemas for synchronous analysis runs (F5.3)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.changes import ChangeIntakeData, ChangeIntakeRequest
from app.schemas.risk import EvaluationContext, RiskEvaluationData

RUN_ARTIFACT_VERSION = "1.0"


class AnalysisRunRequest(BaseModel):
    """Client request body for POST /api/v1/runs/analyze.

    Clients supply only the change and evaluation context. Server-generated
    identifiers, fingerprints, normalized payloads, and decisions must not
    be sent by the client.
    """

    model_config = ConfigDict(extra="forbid")

    change: ChangeIntakeRequest = Field(
        description="Change request validated with the F5.1 intake schema.",
    )
    evaluation_context: EvaluationContext = Field(
        description="Caller-provided context validated with the F5.2 schema.",
    )


class AnalysisRunData(BaseModel):
    """Synchronous analysis run artifact returned in the success envelope."""

    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    orchestration_status: Literal["completed"] = "completed"
    change_intake: ChangeIntakeData
    risk_evaluation: RiskEvaluationData
    run_artifact_version: Literal["1.0"] = "1.0"
