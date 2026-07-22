"""Advisory domain contracts for phase F7.1.

Contract-only foundation for model-based advisory. Does **not**:
- call DeepSeek or any provider
- read API keys or environment secrets
- build redacted context packs from run artifacts
- expose an HTTP endpoint
- authorize risk, validation, policy, or deployment

Advisory has execution_status only — no outcome, no ALLOW/WARN/BLOCK.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.risk import DecisionLevel
from app.schemas.validation import (
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    OverallExecutionStatus,
)
from app.utils.fingerprint import is_sha256_hex

# ---- Bounds ------------------------------------------------------------------

_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_MAX_SUMMARY = 1200
_MAX_OBSERVATION = 600
_MAX_REVIEW_QUESTION = 500
_MAX_LIMITATION = 500
_MAX_LIST_ITEMS = 12
_MAX_STATUS_MESSAGE = 500
_MAX_MODEL_NAME = 128
_MAX_REASON_CODES = 32
_MAX_EVIDENCE_CODES = 16
_MAX_REASON_CODE_LEN = 64

# ---- Constants (server-owned; not caller authority) --------------------------

ADVISORY_ARTIFACT_VERSION = "1.0"
ADVISORY_SCOPE = "redacted_context_only"
ADVISORY_PROVIDER_NAME = "deepseek"
ADVISORY_AUTHORITY = "advisory_only"
ADVISORY_RISK_EFFECT = "none"
ADVISORY_VALIDATION_EFFECT = "none"
ADVISORY_CONTEXT_PACK_VERSION = "1.0"
ADVISORY_REDACTION_VERSION = "1.0"

# Canonical excluded categories for redacted context packs (F7.1 contract only).
# Order is stable; schema normalizes to this order.
REDACTION_EXCLUDED_CATEGORIES: tuple[str, ...] = (
    "raw_sql",
    "model_sql",
    "fixture_values",
    "credentials",
    "secrets",
    "provider_tokens",
    "exception_details",
    "stdout_stderr",
    "temporary_paths",
    "raw_repository_content",
)

_REDACTION_CATEGORY_SET = frozenset(REDACTION_EXCLUDED_CATEGORIES)

# Forbidden authority / executable fields on content and artifact construction.
_FORBIDDEN_AUTHORITY_KEYS = frozenset(
    {
        "decision",
        "recommended_decision",
        "risk_decision",
        "allow",
        "warn",
        "block",
        "approval",
        "approved",
        "authorization",
        "policy_result",
        "deployment_status",
        "remediation_sql",
        "executable_sql",
        "command",
        "action_to_execute",
        "outcome",
        "confidence",
        "probability",
        "severity",
        "sql",
        "code_block",
        "remediation_payload",
    }
)


# ---- Enums -------------------------------------------------------------------


class AdvisoryExecutionStatus(str, Enum):
    """Whether advisory content was formed — not pass/fail and not risk.

    Advisory has no outcome. COMPLETED means structured content exists.
    """

    COMPLETED = "completed"
    ERROR = "error"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"


class RedactionExcludedCategory(str, Enum):
    """Minimum exclusion categories for a redacted advisory context pack."""

    RAW_SQL = "raw_sql"
    MODEL_SQL = "model_sql"
    FIXTURE_VALUES = "fixture_values"
    CREDENTIALS = "credentials"
    SECRETS = "secrets"
    PROVIDER_TOKENS = "provider_tokens"
    EXCEPTION_DETAILS = "exception_details"
    STDOUT_STDERR = "stdout_stderr"
    TEMPORARY_PATHS = "temporary_paths"
    RAW_REPOSITORY_CONTENT = "raw_repository_content"


# ---- Helpers -----------------------------------------------------------------


def _reject_blank(value: str, *, field_name: str) -> str:
    if value is None or not str(value).strip():
        raise ValueError(f"{field_name} must not be blank")
    return value


def _trim_nonblank(value: str, *, field_name: str, max_len: int) -> str:
    cleaned = _reject_blank(value, field_name=field_name).strip()
    if len(cleaned) > max_len:
        raise ValueError(f"{field_name} must be at most {max_len} characters")
    return cleaned


def _validate_snake_code(value: str, *, field_name: str) -> str:
    cleaned = _reject_blank(value, field_name=field_name).strip()
    if not _SNAKE_CASE.fullmatch(cleaned):
        raise ValueError(
            f"{field_name} must be lowercase snake_case "
            f"(^[a-z][a-z0-9_]{{0,63}}$)"
        )
    return cleaned


def _validate_unique_ordered_strings(
    items: list[str],
    *,
    field_name: str,
    max_items: int,
    max_item_len: int,
    min_items: int = 0,
    snake_case: bool = False,
) -> list[str]:
    if len(items) < min_items:
        raise ValueError(f"{field_name} must contain at least {min_items} item(s)")
    if len(items) > max_items:
        raise ValueError(f"{field_name} must contain at most {max_items} items")
    cleaned: list[str] = []
    seen: set[str] = set()
    for index, raw in enumerate(items):
        if not isinstance(raw, str):
            raise ValueError(f"{field_name}[{index}] must be a string")
        if snake_case:
            item = _validate_snake_code(raw, field_name=f"{field_name}[{index}]")
        else:
            item = _trim_nonblank(
                raw, field_name=f"{field_name}[{index}]", max_len=max_item_len
            )
        if len(item) > max_item_len:
            raise ValueError(
                f"{field_name}[{index}] must be at most {max_item_len} characters"
            )
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicate items")
        seen.add(item)
        cleaned.append(item)
    return cleaned


def _reject_forbidden_keys(data: Any, *, label: str) -> Any:
    if isinstance(data, dict):
        forbidden = _FORBIDDEN_AUTHORITY_KEYS.intersection(data.keys())
        if forbidden:
            raise ValueError(
                f"{label} must not include authority or executable fields: "
                + ", ".join(sorted(forbidden))
            )
    return data


def _validate_fingerprint(value: str, *, field_name: str) -> str:
    if not is_sha256_hex(value):
        raise ValueError(
            f"{field_name} must be a 64-character lowercase hexadecimal SHA-256 digest"
        )
    return value


# ---- Content -----------------------------------------------------------------


class AdvisoryContent(BaseModel):
    """Structured advisory prose. Not a decision, approval, or executable plan."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=_MAX_SUMMARY)
    observations: list[str] = Field(default_factory=list, max_length=_MAX_LIST_ITEMS)
    review_questions: list[str] = Field(
        default_factory=list, max_length=_MAX_LIST_ITEMS
    )
    limitations: list[str] = Field(min_length=1, max_length=_MAX_LIST_ITEMS)

    @model_validator(mode="before")
    @classmethod
    def reject_authority_fields(cls, data: Any) -> Any:
        return _reject_forbidden_keys(data, label="advisory content")

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        return _trim_nonblank(value, field_name="summary", max_len=_MAX_SUMMARY)

    @field_validator("observations")
    @classmethod
    def validate_observations(cls, value: list[str]) -> list[str]:
        return _validate_unique_ordered_strings(
            value,
            field_name="observations",
            max_items=_MAX_LIST_ITEMS,
            max_item_len=_MAX_OBSERVATION,
        )

    @field_validator("review_questions")
    @classmethod
    def validate_review_questions(cls, value: list[str]) -> list[str]:
        return _validate_unique_ordered_strings(
            value,
            field_name="review_questions",
            max_items=_MAX_LIST_ITEMS,
            max_item_len=_MAX_REVIEW_QUESTION,
        )

    @field_validator("limitations")
    @classmethod
    def validate_limitations(cls, value: list[str]) -> list[str]:
        return _validate_unique_ordered_strings(
            value,
            field_name="limitations",
            max_items=_MAX_LIST_ITEMS,
            max_item_len=_MAX_LIMITATION,
            min_items=1,
        )


# ---- Status detail -----------------------------------------------------------


class AdvisoryStatusDetail(BaseModel):
    """Bounded status detail for non-completed advisory execution."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=_MAX_STATUS_MESSAGE)

    @model_validator(mode="before")
    @classmethod
    def reject_unsafe_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            banned = {
                "details",
                "exception",
                "traceback",
                "stack_trace",
                "raw_response",
                "raw_prompt",
                "api_key",
                "authorization",
                "sql",
                "fixture_values",
            }.intersection(data.keys())
            if banned:
                raise ValueError(
                    "status detail must not include unsafe fields: "
                    + ", ".join(sorted(banned))
                )
        return data

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        return _validate_snake_code(value, field_name="code")

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        return _trim_nonblank(
            value, field_name="message", max_len=_MAX_STATUS_MESSAGE
        )


# ---- Context pack sub-models -------------------------------------------------


class AdvisoryChangeSummary(BaseModel):
    """Redacted change summary. Uses aliases — not raw asset identifiers."""

    model_config = ConfigDict(extra="forbid")

    change_type: Literal["rename_column"]
    asset_platform: str = Field(min_length=1, max_length=64)
    asset_alias: str
    source_column_alias: str
    target_column_alias: str
    reason_present: bool

    @model_validator(mode="before")
    @classmethod
    def reject_raw_identity_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            banned = {
                "database",
                "schema",
                "table",
                "table_name",
                "asset_name",
                "name",
                "source_column",
                "target_column",
                "reason",
                "reason_text",
                "sql",
                "raw_sql",
            }.intersection(data.keys())
            if banned:
                raise ValueError(
                    "change summary must not include raw identity or SQL fields: "
                    + ", ".join(sorted(banned))
                )
        return data

    @field_validator("asset_platform")
    @classmethod
    def validate_platform(cls, value: str) -> str:
        return _trim_nonblank(value, field_name="asset_platform", max_len=64)

    @field_validator("asset_alias", "source_column_alias", "target_column_alias")
    @classmethod
    def validate_aliases(cls, value: str) -> str:
        return _validate_snake_code(value, field_name="alias")


class AdvisoryRiskSummary(BaseModel):
    """Redacted risk summary. Decision is report-only — not advisory authority."""

    model_config = ConfigDict(extra="forbid")

    decision: DecisionLevel
    reason_codes: list[str] = Field(default_factory=list, max_length=_MAX_REASON_CODES)
    context_complete: bool
    downstream_dependency_count: int | None = None
    protected_asset: bool

    @field_validator("reason_codes")
    @classmethod
    def validate_reason_codes(cls, value: list[str]) -> list[str]:
        return _validate_unique_ordered_strings(
            value,
            field_name="reason_codes",
            max_items=_MAX_REASON_CODES,
            max_item_len=_MAX_REASON_CODE_LEN,
            snake_case=True,
        )

    @field_validator("downstream_dependency_count")
    @classmethod
    def validate_dependency_count(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("downstream_dependency_count must be >= 0")
        return value


class AdvisoryValidationCheckSummary(BaseModel):
    """Redacted per-check validation summary. Codes only — no evidence bodies."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    check_kind: CheckKind
    required: bool
    execution_status: CheckExecutionStatus
    outcome: CheckOutcome | None = None
    evidence_codes: list[str] = Field(
        default_factory=list, max_length=_MAX_EVIDENCE_CODES
    )

    @model_validator(mode="before")
    @classmethod
    def reject_evidence_bodies(cls, data: Any) -> Any:
        if isinstance(data, dict):
            banned = {
                "evidence",
                "evidence_message",
                "evidence_details",
                "details",
                "message",
                "summary",
                "raw_sql",
                "sql",
                "fixture",
                "fixture_values",
                "generated_sql",
                "dbt_logs",
                "engine_exception",
            }.intersection(data.keys())
            if banned:
                raise ValueError(
                    "validation check summary must not include evidence bodies "
                    "or raw payloads: " + ", ".join(sorted(banned))
                )
        return data

    @field_validator("evidence_codes")
    @classmethod
    def validate_evidence_codes(cls, value: list[str]) -> list[str]:
        return _validate_unique_ordered_strings(
            value,
            field_name="evidence_codes",
            max_items=_MAX_EVIDENCE_CODES,
            max_item_len=_MAX_REASON_CODE_LEN,
            snake_case=True,
        )


class AdvisoryValidationSummary(BaseModel):
    """Redacted projection of an F6 ValidationArtifact for advisory context.

    Mirrors F6 aggregation semantics. Does not invent PASS/FAIL/INCONCLUSIVE,
    does not treat execution_failed as FAIL, and does not treat not_run as
    INCONCLUSIVE beyond what F6 already aggregated. Empty ``checks`` is valid
    when F6 produced an empty-check artifact (not_run + inconclusive).
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    requested: bool
    artifact_present: bool
    execution_status: OverallExecutionStatus | None = None
    outcome: CheckOutcome | None = None
    checks: list[AdvisoryValidationCheckSummary] = Field(default_factory=list)

    @model_validator(mode="after")
    def enforce_validation_invariants(self) -> AdvisoryValidationSummary:
        if not self.requested:
            if self.artifact_present:
                raise ValueError(
                    "artifact_present must be false when validation was not requested"
                )
            if self.execution_status is not None:
                raise ValueError(
                    "execution_status must be null when validation was not requested"
                )
            if self.outcome is not None:
                raise ValueError(
                    "outcome must be null when validation was not requested"
                )
            if self.checks:
                raise ValueError("checks must be empty when validation was not requested")
            return self

        # requested=true — must carry a formed F6 ValidationArtifact projection.
        # F6 overall outcome is always pass|fail|inconclusive (never null).
        # F6 checks may be empty (aggregate → not_run + inconclusive).
        if not self.artifact_present:
            raise ValueError(
                "artifact_present must be true when validation was requested "
                "(F7.1 requires a formed ValidationArtifact for requested validation)"
            )
        if self.execution_status is None:
            raise ValueError(
                "execution_status is required when validation artifact is present"
            )
        if self.outcome is None:
            raise ValueError(
                "outcome is required when validation artifact is present "
                "(F6 ValidationArtifact always forms pass|fail|inconclusive)"
            )
        # checks may be empty — mirrors F6 empty-check ValidationArtifact.
        return self


class AdvisoryTrustSummary(BaseModel):
    """Honest trust labels for advisory context. Provenance is never verified in F7.1."""

    model_config = ConfigDict(extra="forbid")

    subject_origin: Literal["riftless_runtime", "caller_provided"]
    subject_scope: Literal["current_request_only", "provided_reference_only"]
    subject_persisted: Literal[False] = False
    input_origin: Literal["caller_provided"] = "caller_provided"
    input_trust: Literal["unverified"] = "unverified"
    provenance_verified: Literal[False] = False

    @model_validator(mode="before")
    @classmethod
    def reject_trusted_claims(cls, data: Any) -> Any:
        if isinstance(data, dict):
            banned_values = {
                "trusted",
                "verified",
                "authentic",
                "durable",
                "immutable",
                "persisted",
                "GitHub_verified",
                "DataHub_verified",
                "production_derived",
            }
            for key, value in data.items():
                if isinstance(value, str) and value in banned_values:
                    raise ValueError(
                        f"trust summary must not claim {value!r} for field {key!r}"
                    )
            if data.get("subject_persisted") is True:
                raise ValueError("subject_persisted must be false in F7.1")
            if data.get("provenance_verified") is True:
                raise ValueError("provenance_verified must be false in F7.1")
            if data.get("input_trust") not in (None, "unverified"):
                raise ValueError("input_trust must be unverified in F7.1")
            if data.get("input_origin") not in (None, "caller_provided"):
                raise ValueError("input_origin must be caller_provided in F7.1")
        return data


class AdvisoryRedactionSummary(BaseModel):
    """Declares minimum exclusion requirements for a redacted context pack.

    F7.1 does **not** implement a redaction algorithm. ``applied=true`` means
    the pack claims exclusions were applied by a future builder (F7.2+).
    """

    model_config = ConfigDict(extra="forbid")

    applied: Literal[True] = True
    version: Literal["1.0"] = "1.0"
    excluded_categories: list[str] = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def reject_applied_false(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("applied") is False:
            raise ValueError("redaction.applied must be true for advisory context packs")
        return data

    @field_validator("excluded_categories")
    @classmethod
    def validate_excluded_categories(cls, value: list[str]) -> list[str]:
        if not isinstance(value, list) or not value:
            raise ValueError("excluded_categories must be a non-empty list")
        normalized: list[str] = []
        seen: set[str] = set()
        for index, raw in enumerate(value):
            if isinstance(raw, RedactionExcludedCategory):
                item = raw.value
            elif isinstance(raw, str):
                item = raw.strip()
            else:
                raise ValueError(f"excluded_categories[{index}] must be a string")
            if item not in _REDACTION_CATEGORY_SET:
                raise ValueError(
                    f"excluded_categories[{index}] is not an allowed category: {item!r}"
                )
            if item in seen:
                raise ValueError("excluded_categories must not contain duplicates")
            seen.add(item)
            normalized.append(item)
        if seen != _REDACTION_CATEGORY_SET:
            missing = sorted(_REDACTION_CATEGORY_SET - seen)
            raise ValueError(
                "excluded_categories must include all required categories; missing: "
                + ", ".join(missing)
            )
        # Canonical stable order — caller order is not authoritative.
        return list(REDACTION_EXCLUDED_CATEGORIES)


# ---- Context pack ------------------------------------------------------------


class AdvisoryContextPack(BaseModel):
    """Structured redacted context pack for future model advisory.

    F7.1 defines the contract only. Packs are not built from run artifacts here.
    Arbitrary blobs, raw SQL, fixture values, and secrets are rejected.
    """

    model_config = ConfigDict(extra="forbid")

    subject_fingerprint: str = Field(min_length=64, max_length=64)
    change: AdvisoryChangeSummary
    risk: AdvisoryRiskSummary
    validation: AdvisoryValidationSummary
    trust: AdvisoryTrustSummary
    redaction: AdvisoryRedactionSummary
    context_pack_version: Literal["1.0"] = "1.0"

    @model_validator(mode="before")
    @classmethod
    def reject_raw_payloads(cls, data: Any) -> Any:
        if isinstance(data, dict):
            banned = {
                "raw_sql",
                "sql",
                "model_sql",
                "fixture",
                "fixture_values",
                "credentials",
                "secrets",
                "api_key",
                "prompt",
                "raw_prompt",
                "raw_response",
                "stdout",
                "stderr",
                "repository_content",
                "blob",
                "arbitrary",
            }.intersection(data.keys())
            if banned:
                raise ValueError(
                    "context pack must not include raw payloads or secrets: "
                    + ", ".join(sorted(banned))
                )
        return data

    @field_validator("subject_fingerprint")
    @classmethod
    def validate_subject_fingerprint(cls, value: str) -> str:
        return _validate_fingerprint(value, field_name="subject_fingerprint")


# ---- Advisory artifact -------------------------------------------------------


class AdvisoryArtifact(BaseModel):
    """Model advisory artifact. Advisory-only — no risk/validation/deployment effect.

    Not persisted. No retrieval. No raw prompt/response storage.
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    advisory_id: UUID
    subject_fingerprint: str = Field(min_length=64, max_length=64)
    context_fingerprint: str = Field(min_length=64, max_length=64)
    scope: Literal["redacted_context_only"] = "redacted_context_only"
    execution_status: AdvisoryExecutionStatus
    content: AdvisoryContent | None = None
    status_detail: AdvisoryStatusDetail | None = None
    provider_name: Literal["deepseek"] = "deepseek"
    model_name: str | None = Field(default=None, max_length=_MAX_MODEL_NAME)
    authority: Literal["advisory_only"] = "advisory_only"
    risk_effect: Literal["none"] = "none"
    validation_effect: Literal["none"] = "none"
    deployment_authorized: Literal[False] = False
    persistence: Literal["none"] = "none"
    retrieval_available: Literal[False] = False
    artifact_version: Literal["1.0"] = "1.0"

    @model_validator(mode="before")
    @classmethod
    def reject_authority_fields(cls, data: Any) -> Any:
        return _reject_forbidden_keys(data, label="advisory artifact")

    @field_validator("subject_fingerprint")
    @classmethod
    def validate_subject_fingerprint(cls, value: str) -> str:
        return _validate_fingerprint(value, field_name="subject_fingerprint")

    @field_validator("context_fingerprint")
    @classmethod
    def validate_context_fingerprint(cls, value: str) -> str:
        return _validate_fingerprint(value, field_name="context_fingerprint")

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("model_name must be null or non-blank")
        if len(cleaned) > _MAX_MODEL_NAME:
            raise ValueError(
                f"model_name must be at most {_MAX_MODEL_NAME} characters"
            )
        return cleaned

    @model_validator(mode="after")
    def enforce_state_invariants(self) -> AdvisoryArtifact:
        status = self.execution_status
        if isinstance(status, AdvisoryExecutionStatus):
            status_value = status.value
        else:
            status_value = str(status)

        completed = AdvisoryExecutionStatus.COMPLETED.value

        if status_value == completed:
            if self.content is None:
                raise ValueError("content is required when execution_status is completed")
            if self.status_detail is not None:
                raise ValueError(
                    "status_detail must be null when execution_status is completed"
                )
            if self.model_name is None:
                raise ValueError(
                    "model_name is required when execution_status is completed"
                )
            return self

        # Non-completed: content null, status_detail required.
        if self.content is not None:
            raise ValueError(
                f"content must be null when execution_status is {status_value}"
            )
        if self.status_detail is None:
            raise ValueError(
                f"status_detail is required when execution_status is {status_value}"
            )
        return self
