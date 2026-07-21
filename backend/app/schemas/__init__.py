"""Shared Pydantic schemas for the RIFTLESS API."""

from app.schemas.changes import ChangeIntakeData, ChangeIntakeRequest
from app.schemas.common import ErrorBody, ErrorResponse, SuccessResponse
from app.schemas.dbt_validation import DbtParseInput, MAX_MODEL_SQL_LENGTH
from app.schemas.duckdb_validation import (
    DuckDbFixture,
    DuckDbFixtureColumn,
    DuckDbFixtureColumnType,
    DuckDbRenameInput,
)
from app.schemas.risk import RiskEvaluateRequest, RiskEvaluationData
from app.schemas.runs import AnalysisRunData, AnalysisRunRequest
from app.schemas.sql_validation import MAX_SQL_LENGTH, SqlDialect, SqlParseInput
from app.schemas.validation import (
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    OverallExecutionStatus,
    ValidationArtifact,
    ValidationCheckResult,
    ValidationEvidence,
)
from app.schemas.validation_api import ValidationExecutionMeta, validation_execution_meta
from app.schemas.validation_plan import ValidationPlanChecks, ValidationPlanInput

__all__ = [
    "AnalysisRunData",
    "AnalysisRunRequest",
    "ChangeIntakeData",
    "ChangeIntakeRequest",
    "CheckExecutionStatus",
    "CheckKind",
    "CheckOutcome",
    "DbtParseInput",
    "DuckDbFixture",
    "DuckDbFixtureColumn",
    "DuckDbFixtureColumnType",
    "DuckDbRenameInput",
    "ErrorBody",
    "ErrorResponse",
    "MAX_MODEL_SQL_LENGTH",
    "MAX_SQL_LENGTH",
    "OverallExecutionStatus",
    "RiskEvaluateRequest",
    "RiskEvaluationData",
    "SqlDialect",
    "SqlParseInput",
    "SuccessResponse",
    "ValidationArtifact",
    "ValidationCheckResult",
    "ValidationEvidence",
    "ValidationExecutionMeta",
    "ValidationPlanChecks",
    "ValidationPlanInput",
    "validation_execution_meta",
]
