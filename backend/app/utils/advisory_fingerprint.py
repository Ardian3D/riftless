"""Deterministic fingerprint for AdvisoryContextPack (phase F7.1).

Reuses the locked F5 canonical JSON + SHA-256 helper. Fingerprint proves
content consistency of the redacted context pack only — not authenticity,
provenance, persistence, ownership, signature, immutability, or authorization.
"""

from __future__ import annotations

from app.schemas.advisory import AdvisoryContextPack
from app.utils.fingerprint import fingerprint_payload


def fingerprint_advisory_context(context: AdvisoryContextPack) -> str:
    """Return lowercase hex SHA-256 over canonical JSON of the context pack.

    Serializes the full pack (change, risk, validation, trust, redaction,
    versions, subject_fingerprint) with sorted keys and stable separators.
    Does not mutate ``context``.
    """
    payload = context.model_dump(mode="json")
    return fingerprint_payload(payload)
