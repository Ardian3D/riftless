"""Shared pytest fixtures for the RIFTLESS backend foundation tests."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from app.core.config import clear_settings_cache

# Environment keys that tests may set. Cleared between tests so suites do not
# contaminate one another.
_RIFTLESS_ENV_KEYS = (
    "RIFTLESS_APP_ENV",
    "RIFTLESS_APP_VERSION",
    "RIFTLESS_API_PREFIX",
    "RIFTLESS_HOST",
    "RIFTLESS_PORT",
    "RIFTLESS_DEBUG",
)


@pytest.fixture(autouse=True)
def _reset_settings_isolation() -> Iterator[None]:
    """Clear settings cache and RIFTLESS env overrides around every test."""
    clear_settings_cache()
    for key in _RIFTLESS_ENV_KEYS:
        os.environ.pop(key, None)
    yield
    clear_settings_cache()
    for key in _RIFTLESS_ENV_KEYS:
        os.environ.pop(key, None)
