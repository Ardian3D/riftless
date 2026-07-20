"""dbt controlled project parse input contracts (phase F6.4).

Caller supplies only a plain-SQL model name and body. Project paths, profiles,
commands, packages, macros, and Jinja are never accepted from the caller.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_MODEL_SQL_LENGTH = 100_000
_MODEL_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_DISALLOWED_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_JINJA_OPENERS = ("{{", "{%", "{#")

# Request keys that would imply caller control of dbt project/runtime.
_FORBIDDEN_KEYS = frozenset(
    {
        "project_name",
        "project_dir",
        "profiles_dir",
        "target_path",
        "log_path",
        "profile",
        "adapter",
        "database",
        "database_path",
        "command",
        "arguments",
        "args",
        "environment",
        "env",
        "macro",
        "macros",
        "package",
        "packages",
        "selector",
        "target",
        "sql",
        "setup_sql",
        "query",
        "script",
    }
)


class DbtParseInput(BaseModel):
    """Internal input for the controlled dbt parse validator."""

    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(min_length=1, max_length=64)
    model_sql: str = Field(min_length=1, max_length=MAX_MODEL_SQL_LENGTH)
    required: bool = True

    @model_validator(mode="before")
    @classmethod
    def reject_forbidden_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            forbidden = _FORBIDDEN_KEYS.intersection(data.keys())
            if forbidden:
                raise ValueError(
                    "caller-controlled dbt fields are not allowed: "
                    + ", ".join(sorted(forbidden))
                )
        return data

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, value: str) -> str:
        if value is None or not str(value).strip():
            raise ValueError("model_name must not be blank")
        cleaned = str(value)
        if cleaned != cleaned.strip():
            raise ValueError("model_name must not have leading or trailing whitespace")
        # Reject path/traversal tokens before the pattern message for clarity.
        if any(token in cleaned for token in ("/", "\\", "..", " ")):
            raise ValueError("model_name must not be a path or traversal segment")
        if not _MODEL_NAME_RE.fullmatch(cleaned):
            raise ValueError(
                "model_name must be lowercase snake_case matching "
                "^[a-z][a-z0-9_]{0,63}$"
            )
        return cleaned

    @field_validator("model_sql")
    @classmethod
    def validate_model_sql(cls, value: str) -> str:
        if value is None or not str(value).strip():
            raise ValueError("model_sql must not be blank")
        if len(value) > MAX_MODEL_SQL_LENGTH:
            raise ValueError(
                f"model_sql must be at most {MAX_MODEL_SQL_LENGTH} characters"
            )
        if _DISALLOWED_CONTROL.search(value):
            raise ValueError(
                "model_sql must not contain disallowed control characters "
                "(null bytes and C0 controls other than tab/newline/carriage return)"
            )
        for opener in _JINJA_OPENERS:
            if opener in value:
                raise ValueError(
                    "model_sql must be plain SQL; dbt/Jinja template syntax is not allowed"
                )
        # Return original string unchanged (no rewrite).
        return value
