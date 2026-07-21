"""SQL identifier quoting helpers for server-generated SQL (F6.3).

These utilities only quote and escape identifiers for DuckDB DDL/DML that
RIFTLESS constructs. They do not accept or execute caller SQL.
"""

from __future__ import annotations


def quote_ident(name: str) -> str:
    """Return a double-quoted SQL identifier with embedded quotes escaped.

    DuckDB (and SQL standard) escapes ``"`` inside a quoted identifier as
    ``""``.
    """
    if name is None:
        raise ValueError("identifier must not be None")
    if not isinstance(name, str):
        raise ValueError("identifier must be a string")
    escaped = name.replace('"', '""')
    return f'"{escaped}"'
