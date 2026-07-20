"""Change intake and normalization service (phase F5.1).

Responsibilities:
- preserve submitted_input separately from normalized_change
- apply deterministic normalization rules (no AI, no side effects)
- generate a SHA-256 content fingerprint over normalized_change only

Fingerprint notes
-----------------
``content_fingerprint`` is a deterministic content identifier for the
normalized artifact. It is **not** a digital signature, security proof,
authorization token, blockchain hash, or ledger entry.

``reason`` is part of ``normalized_change``. When present (or when null),
it is included in the canonical JSON and therefore affects the fingerprint.
Two intakes that differ only by reason will produce different fingerprints.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.core.errors import AppError, ErrorCode
from app.schemas.changes import (
    AssetNormalized,
    ChangeIntakeData,
    ChangeIntakeRequest,
    NormalizedChange,
)
from app.utils.fingerprint import fingerprint_payload


ARTIFACT_VERSION = "1.0"
SUPPORTED_CHANGE_TYPES = ("rename_column",)


def _trim(value: str) -> str:
    return value.strip()


def normalize_change(request: ChangeIntakeRequest) -> NormalizedChange:
    """Apply deterministic normalization rules to a validated intake request.

    Rules:
    1. Trim whitespace on all strings.
    2. Lowercase controlled values: change_type, asset.platform.
    3. Preserve casing (after trim) for database, schema, name, columns.
    4. reason: trim; keep content/casing; null when absent or blank after trim.
    5. Reject when source_column == target_column after normalization.
    """
    change_type = _trim(request.change_type).lower()
    if change_type != "rename_column":
        # Defensive: schema already restricts Literal; keep service honest.
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="The request could not be validated.",
            status_code=422,
            details=[
                {
                    "loc": ["body", "change_type"],
                    "msg": f"Unsupported change_type. Supported: {list(SUPPORTED_CHANGE_TYPES)}",
                    "type": "value_error.unsupported_change_type",
                }
            ],
        )

    platform = _trim(request.asset.platform).lower()
    database = _trim(request.asset.database)
    schema_name = _trim(request.asset.schema_name)
    name = _trim(request.asset.name)
    source_column = _trim(request.source_column)
    target_column = _trim(request.target_column)

    if not platform:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="The request could not be validated.",
            status_code=422,
            details=[
                {
                    "loc": ["body", "asset", "platform"],
                    "msg": "platform must not be blank after normalization",
                    "type": "value_error.blank",
                }
            ],
        )

    for field_name, value in (
        ("database", database),
        ("schema", schema_name),
        ("name", name),
        ("source_column", source_column),
        ("target_column", target_column),
    ):
        if not value:
            loc = (
                ["body", "asset", field_name]
                if field_name in {"database", "schema", "name"}
                else ["body", field_name]
            )
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message="The request could not be validated.",
                status_code=422,
                details=[
                    {
                        "loc": loc,
                        "msg": f"{field_name} must not be blank after normalization",
                        "type": "value_error.blank",
                    }
                ],
            )

    if source_column == target_column:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="The request could not be validated.",
            status_code=422,
            details=[
                {
                    "loc": ["body", "target_column"],
                    "msg": "source_column and target_column must differ after normalization",
                    "type": "value_error.identical_columns",
                }
            ],
        )

    reason: str | None
    if request.reason is None:
        reason = None
    else:
        trimmed_reason = _trim(request.reason)
        reason = trimmed_reason if trimmed_reason else None

    return NormalizedChange(
        change_type="rename_column",
        asset=AssetNormalized(
            platform=platform,
            database=database,
            schema_name=schema_name,
            name=name,
        ),
        source_column=source_column,
        target_column=target_column,
        reason=reason,
    )


def compute_content_fingerprint(normalized: NormalizedChange) -> str:
    """Return lowercase hex SHA-256 over canonical JSON of normalized_change.

    Delegates to the shared fingerprint utility so F5.1 and F5.2 use one
    locked algorithm. Only ``normalized_change`` is hashed — never
    ``submitted_input`` or ``intake_id``.
    """
    return fingerprint_payload(normalized.fingerprint_payload())


def process_change_intake(request: ChangeIntakeRequest) -> ChangeIntakeData:
    """Run full intake: snapshot → normalize → fingerprint → artifact.

    Side-effect free: no network, database, filesystem, or AI calls.
    Persistence is intentionally none in F5.1.
    """
    submitted_input = request.submitted_snapshot()
    normalized = normalize_change(request)
    fingerprint = compute_content_fingerprint(normalized)
    intake_id = uuid.uuid4()

    return ChangeIntakeData(
        intake_id=intake_id,
        submitted_input=submitted_input,
        normalized_change=normalized.fingerprint_payload(),
        content_fingerprint=fingerprint,
        artifact_version=ARTIFACT_VERSION,
    )


def intake_meta() -> dict[str, Any]:
    """Honest operation metadata for the success envelope."""
    return {
        "operation": "change_intake",
        "phase": "F5.1",
        "supported_change_types": list(SUPPORTED_CHANGE_TYPES),
        "persistence": "none",
    }
