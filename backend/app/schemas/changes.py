"""Request and response schemas for change intake (phase F5.1).

Only ``rename_column`` is supported. Schemas enforce structure, unknown-field
rejection, length limits, and safe identifier checks. Business normalization
(trim, lowercasing controlled fields, fingerprint) lives in the service layer
so ``submitted_input`` can remain distinct from ``normalized_change``.
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Reasonable bounds to prevent unbounded payloads (not security claims).
_MAX_PLATFORM = 64
_MAX_DB_PART = 128
_MAX_ASSET_NAME = 256
_MAX_COLUMN = 256
_MAX_REASON = 2000


def _reject_blank_or_control(value: str, *, field_name: str) -> str:
    """Reject empty/whitespace-only strings and control characters.

    Does not mutate the value (no trim). Business trimming happens in the
    normalization service so submitted_input can retain the original text.
    """
    if value is None or value == "":
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be blank or whitespace-only")
    for ch in value:
        code = ord(ch)
        if code < 32 or code == 127:
            raise ValueError(f"{field_name} contains invalid control characters")
    return value


class AssetRef(BaseModel):
    """Physical asset reference for a data change."""

    model_config = ConfigDict(extra="forbid")

    platform: str = Field(
        min_length=1,
        max_length=_MAX_PLATFORM,
        description="Data platform identifier (e.g. snowflake).",
    )
    database: str = Field(min_length=1, max_length=_MAX_DB_PART)
    schema_name: str = Field(
        min_length=1,
        max_length=_MAX_DB_PART,
        alias="schema",
        description="Schema name. Serialized as 'schema' in JSON.",
    )
    name: str = Field(
        min_length=1,
        max_length=_MAX_ASSET_NAME,
        description="Table or relation name.",
    )

    @field_validator("platform", "database", "schema_name", "name")
    @classmethod
    def validate_asset_strings(cls, value: str, info: Any) -> str:
        return _reject_blank_or_control(value, field_name=str(info.field_name))


class ChangeIntakeRequest(BaseModel):
    """Client request body for POST /api/v1/changes/intake."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    change_type: Literal["rename_column"] = Field(
        description="Only rename_column is supported in F5.1.",
    )
    asset: AssetRef
    source_column: str = Field(min_length=1, max_length=_MAX_COLUMN)
    target_column: str = Field(min_length=1, max_length=_MAX_COLUMN)
    reason: str | None = Field(default=None, max_length=_MAX_REASON)

    @field_validator("source_column", "target_column")
    @classmethod
    def validate_columns(cls, value: str, info: Any) -> str:
        return _reject_blank_or_control(value, field_name=str(info.field_name))

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # Blank/whitespace-only reason is treated as not provided after validation
        # would be ambiguous; reject control chars but allow content with spaces.
        for ch in value:
            code = ord(ch)
            if code < 32 or code == 127:
                raise ValueError("reason contains invalid control characters")
        return value

    def submitted_snapshot(self) -> dict[str, Any]:
        """Return the accepted request as a JSON-serializable dict.

        Uses the client-facing key ``schema`` for the asset schema field.
        Values are as accepted by schema validation (before business
        normalization).
        """
        return self.model_dump(by_alias=True, mode="json")


class AssetNormalized(BaseModel):
    """Normalized asset reference."""

    model_config = ConfigDict(extra="forbid")

    platform: str
    database: str
    schema_name: str = Field(serialization_alias="schema")
    name: str


class NormalizedChange(BaseModel):
    """Deterministically normalized rename_column change."""

    model_config = ConfigDict(extra="forbid")

    change_type: Literal["rename_column"]
    asset: AssetNormalized
    source_column: str
    target_column: str
    reason: str | None = None

    def fingerprint_payload(self) -> dict[str, Any]:
        """Stable dict used as fingerprint input (by_alias for schema key)."""
        return self.model_dump(by_alias=True, mode="json")


class ChangeIntakeData(BaseModel):
    """Success data payload for change intake."""

    model_config = ConfigDict(extra="forbid")

    intake_id: UUID
    submitted_input: dict[str, Any]
    normalized_change: dict[str, Any]
    content_fingerprint: str
    artifact_version: Literal["1.0"] = "1.0"
