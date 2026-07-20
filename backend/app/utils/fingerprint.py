"""Deterministic content fingerprint utilities (shared by F5.1 and F5.2).

``content_fingerprint`` is a deterministic content identifier derived from
canonical JSON of a normalized change payload. It is **not** a digital
signature, security proof, authorization token, blockchain hash, or ledger
entry.

Canonical form (locked by F5.1 — must not change):
- UTF-8 encoding
- keys sorted recursively via ``sort_keys=True``
- compact separators ``(',', ':')``
- ``ensure_ascii=False``
- SHA-256 digest as lowercase hexadecimal (64 chars)
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def canonical_json_bytes(payload: Mapping[str, Any] | dict[str, Any]) -> bytes:
    """Serialize payload to the locked F5.1 canonical JSON byte form."""
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return canonical.encode("utf-8")


def fingerprint_payload(payload: Mapping[str, Any] | dict[str, Any]) -> str:
    """Return lowercase hex SHA-256 over canonical JSON of ``payload``."""
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def is_sha256_hex(value: str) -> bool:
    """Return True when value is exactly 64 lowercase hex characters."""
    return bool(isinstance(value, str) and _SHA256_HEX.fullmatch(value))


def fingerprints_match(expected: str, provided: str) -> bool:
    """Exact equality comparison for fingerprints (both must be lowercase hex)."""
    return expected == provided
