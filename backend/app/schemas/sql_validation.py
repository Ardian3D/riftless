"""SQL parse input contracts for phase F6.2.

Defines the limited dialect set and the SqlParseInput shape consumed by the
SQLGlot parse validator. Declaring a dialect only means SQLGlot will be
invoked with that dialect name — not that a live database is connected or
that vendor semantics are fully verified.
"""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Maximum SQL payload length for F6.2 (characters, not bytes).
MAX_SQL_LENGTH = 100_000

# Control characters other than tab / LF / CR are rejected.
_DISALLOWED_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


class SqlDialect(str, Enum):
    """Supported SQL dialects for F6.2 SQLGlot parsing.

    Presence in this enum means the parser will be called with the given
    dialect string. It does **not** mean a database connection exists or that
    the query is compatible with a real runtime.
    """

    SNOWFLAKE = "snowflake"
    POSTGRES = "postgres"
    BIGQUERY = "bigquery"
    DUCKDB = "duckdb"


class SqlParseInput(BaseModel):
    """Internal input for the SQLGlot parse validator.

    The ``sql`` field is validated for emptiness and unsafe control characters
    only. It is **not** normalized, rewritten, or executed. Raw SQL must never
    be copied into ValidationEvidence.
    """

    model_config = ConfigDict(extra="forbid")

    sql: str = Field(min_length=1, max_length=MAX_SQL_LENGTH)
    dialect: SqlDialect
    required: bool = True

    @field_validator("sql")
    @classmethod
    def validate_sql(cls, value: str) -> str:
        if value is None:
            raise ValueError("sql must not be blank")
        # Reject emptiness after trim without mutating the stored SQL.
        if not str(value).strip():
            raise ValueError("sql must not be blank")
        if len(value) > MAX_SQL_LENGTH:
            raise ValueError(f"sql must be at most {MAX_SQL_LENGTH} characters")
        if _DISALLOWED_CONTROL.search(value):
            raise ValueError(
                "sql must not contain disallowed control characters "
                "(null bytes and C0 controls other than tab/newline/carriage return)"
            )
        # Return the original string unchanged (no reformat / rewrite).
        return value
