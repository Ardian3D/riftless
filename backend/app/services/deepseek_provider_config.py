"""Server-side DeepSeek provider configuration (phase F7.4).

Loads only ``DEEPSEEK_API_KEY`` from an explicit environment mapping.
Does **not**:
- read ``.env`` files
- accept model / URL / timeout overrides
- crash application import when the key is missing
- put the key into artifacts, errors, or logs
"""

from __future__ import annotations

import os
from typing import Mapping

DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"


class DeepSeekProviderConfig:
    """Bounded server-side provider config. Holds only the API key.

    The key is never shown in ``str`` / ``repr`` and is never serializable
    into advisory artifacts.
    """

    __slots__ = ("_api_key",)

    def __init__(self, *, api_key: str) -> None:
        if not isinstance(api_key, str):
            raise TypeError("api_key must be a string")
        cleaned = api_key.strip()
        if not cleaned:
            raise ValueError("api_key must be a non-blank string")
        object.__setattr__(self, "_api_key", cleaned)

    @property
    def api_key(self) -> str:
        return self._api_key

    def __repr__(self) -> str:
        return "DeepSeekProviderConfig(api_key=***)"

    def __str__(self) -> str:
        return "DeepSeekProviderConfig(api_key=***)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DeepSeekProviderConfig):
            return NotImplemented
        return self._api_key == other._api_key

    def __hash__(self) -> int:
        return hash(self._api_key)


def load_deepseek_provider_config(
    environ: Mapping[str, str] | None = None,
) -> DeepSeekProviderConfig | None:
    """Load config from ``DEEPSEEK_API_KEY`` only.

    Returns ``None`` when the variable is missing or blank after trim.
    Does not mutate ``environ``. Does not read other environment keys.
    """
    source: Mapping[str, str]
    if environ is None:
        source = os.environ
    else:
        source = environ

    raw = source.get(DEEPSEEK_API_KEY_ENV)
    if raw is None:
        return None
    if not isinstance(raw, str):
        return None
    cleaned = raw.strip()
    if not cleaned:
        return None
    return DeepSeekProviderConfig(api_key=cleaned)
