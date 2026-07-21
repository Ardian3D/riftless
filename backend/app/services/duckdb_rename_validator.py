"""DuckDB in-memory rename_column validator (phase F6.3).

Executes a server-generated rename against a structured fixture table in an
isolated DuckDB ``:memory:`` connection. Caller-provided SQL is never accepted
or executed.

PASS means the rename succeeded on the supplied in-memory fixture only.
It is not vendor compatibility, production safety, or deployment authorization.
"""

from __future__ import annotations

import importlib.metadata
import uuid
from typing import Any

import duckdb

from app.schemas.duckdb_validation import (
    DuckDbFixture,
    DuckDbRenameInput,
    duckdb_sql_type,
)
from app.schemas.validation import (
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    ValidationCheckResult,
    ValidationEvidence,
)
from app.utils.sql_identifiers import quote_ident

DUCKDB_RENAME_SCOPE = "duckdb_in_memory_rename_simulation"
ENGINE_NAME = "duckdb"

_SUMMARY_PASS = "The rename operation completed in the isolated DuckDB fixture."
_SUMMARY_SOURCE_MISSING = (
    "The source column was not present in the supplied in-memory fixture."
)
_SUMMARY_TARGET_EXISTS = (
    "The target column was already present in the supplied in-memory fixture."
)
_SUMMARY_RENAME_FAILED = (
    "DuckDB could not apply the rename operation to the supplied in-memory fixture."
)
_SUMMARY_POSTCONDITION = (
    "The expected column state was not observed after the rename operation."
)
_SUMMARY_FIXTURE_SETUP = (
    "The in-memory fixture could not be prepared for the rename check."
)
_SUMMARY_ERROR = "DuckDB execution did not complete."


class DuckDbRenameRejected(Exception):
    """DuckDB rejected the rename operation (maps to COMPLETED + FAIL)."""


class DuckDbFixtureSetupFailed(Exception):
    """Fixture could not be prepared (maps to COMPLETED + INCONCLUSIVE)."""


def get_duckdb_version() -> str:
    """Return the installed DuckDB package version (runtime metadata)."""
    return importlib.metadata.version("duckdb")


def _column_names_casefold(fixture: DuckDbFixture) -> dict[str, str]:
    """Map casefolded name → original name for fixture columns."""
    return {col.name.casefold(): col.name for col in fixture.columns}


def _find_column(fixture: DuckDbFixture, name: str) -> str | None:
    return _column_names_casefold(fixture).get(name.casefold())


def _evidence(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None,
) -> ValidationEvidence:
    return ValidationEvidence(code=code, message=message, details=details)


def _result(
    *,
    required: bool,
    execution_status: CheckExecutionStatus,
    outcome: CheckOutcome | None,
    summary: str,
    evidence: list[ValidationEvidence],
    engine_version: str,
) -> ValidationCheckResult:
    return ValidationCheckResult(
        check_id=uuid.uuid4(),
        check_kind=CheckKind.DUCKDB_EXECUTION,
        required=required,
        execution_status=execution_status,
        outcome=outcome,
        scope=DUCKDB_RENAME_SCOPE,
        summary=summary,
        evidence=evidence,
        engine_name=ENGINE_NAME,
        engine_version=engine_version,
    )


def _apply_connection_hardening(connection: duckdb.DuckDBPyConnection) -> None:
    """Disable external access and extension auto install/load; lock config.

    Uses settings supported by the pinned DuckDB version. Raises if a required
    restriction cannot be applied (do not silently continue open).
    """
    required_settings = (
        ("enable_external_access", False),
        ("autoinstall_known_extensions", False),
        ("autoload_known_extensions", False),
    )
    for name, value in required_settings:
        connection.execute(f"SET {name}={str(value).lower()}")
        current = connection.execute(f"SELECT current_setting('{name}')").fetchone()
        if current is None or bool(current[0]) is not value:
            raise RuntimeError(f"failed to apply DuckDB setting {name}")
    # Prevent later SET from re-enabling external features on this connection.
    connection.execute("SET lock_configuration=true")


def _open_isolated_connection() -> duckdb.DuckDBPyConnection:
    """Open a new hardened ``:memory:`` connection (never a file path)."""
    connection = duckdb.connect(database=":memory:")
    try:
        _apply_connection_hardening(connection)
    except Exception:
        connection.close()
        raise
    return connection


def _build_create_table_sql(table_name: str, fixture: DuckDbFixture) -> str:
    """Server-generated CREATE TABLE DDL (types from allowlist only)."""
    parts: list[str] = []
    for col in fixture.columns:
        sql_type = duckdb_sql_type(col.type)
        null_sql = "" if col.nullable else " NOT NULL"
        parts.append(f"{quote_ident(col.name)} {sql_type}{null_sql}")
    columns_sql = ", ".join(parts)
    return f"CREATE TABLE {quote_ident(table_name)} ({columns_sql})"


def _build_insert_sql(table_name: str, fixture: DuckDbFixture) -> str:
    """Server-generated INSERT with positional placeholders (no value concat)."""
    col_list = ", ".join(quote_ident(col.name) for col in fixture.columns)
    placeholders = ", ".join("?" for _ in fixture.columns)
    return (
        f"INSERT INTO {quote_ident(table_name)} ({col_list}) "
        f"VALUES ({placeholders})"
    )


def _build_rename_sql(table_name: str, source: str, target: str) -> str:
    return (
        f"ALTER TABLE {quote_ident(table_name)} "
        f"RENAME COLUMN {quote_ident(source)} TO {quote_ident(target)}"
    )


def _list_columns(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
) -> list[str]:
    rows = connection.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = ?
        ORDER BY ordinal_position
        """,
        [table_name],
    ).fetchall()
    return [str(row[0]) for row in rows]


def _column_present(columns: list[str], name: str) -> bool:
    target = name.casefold()
    return any(col.casefold() == target for col in columns)


def _row_count(connection: duckdb.DuckDBPyConnection, table_name: str) -> int:
    row = connection.execute(
        f"SELECT COUNT(*) FROM {quote_ident(table_name)}"
    ).fetchone()
    return int(row[0]) if row is not None else 0


def _setup_fixture(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
    fixture: DuckDbFixture,
) -> None:
    """Create table and insert rows via parameter binding."""
    try:
        create_sql = _build_create_table_sql(table_name, fixture)
        connection.execute(create_sql)
        if fixture.rows:
            insert_sql = _build_insert_sql(table_name, fixture)
            for row in fixture.rows:
                connection.execute(insert_sql, list(row))
    except Exception as exc:
        raise DuckDbFixtureSetupFailed from exc


def run_duckdb_rename_check(rename_input: DuckDbRenameInput) -> ValidationCheckResult:
    """Run an isolated DuckDB in-memory rename simulation.

    Never mutates the input. Never returns generated SQL, fixture cell values,
    exception messages, or tracebacks in the result surface.
    """
    engine_version = get_duckdb_version()
    required = bool(rename_input.required)
    change = rename_input.normalized_change
    fixture = rename_input.fixture
    table_name = change.asset.name
    source_column = change.source_column
    target_column = change.target_column

    # ---- Precondition checks (no DuckDB yet) ---------------------------------
    source_in_fixture = _find_column(fixture, source_column)
    if source_in_fixture is None:
        return _result(
            required=required,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.FAIL,
            summary=_SUMMARY_SOURCE_MISSING,
            evidence=[
                _evidence(
                    code="duckdb_source_column_missing",
                    message=(
                        "The source column was not present in the supplied "
                        "in-memory fixture."
                    ),
                    details=None,
                )
            ],
            engine_version=engine_version,
        )

    if _find_column(fixture, target_column) is not None:
        return _result(
            required=required,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.FAIL,
            summary=_SUMMARY_TARGET_EXISTS,
            evidence=[
                _evidence(
                    code="duckdb_target_column_exists",
                    message=(
                        "The target column was already present in the supplied "
                        "in-memory fixture."
                    ),
                    details=None,
                )
            ],
            engine_version=engine_version,
        )

    # Use the fixture's original source casing for the rename statement.
    source_for_sql = source_in_fixture
    target_for_sql = target_column

    connection: duckdb.DuckDBPyConnection | None = None
    try:
        try:
            connection = _open_isolated_connection()
        except Exception:
            return _result(
                required=required,
                execution_status=CheckExecutionStatus.ERROR,
                outcome=None,
                summary=_SUMMARY_ERROR,
                evidence=[
                    _evidence(
                        code="duckdb_execution_error",
                        message=(
                            "The DuckDB engine could not complete the in-memory check."
                        ),
                        details=None,
                    )
                ],
                engine_version=engine_version,
            )

        # Fixture setup
        try:
            _setup_fixture(connection, table_name, fixture)
        except DuckDbFixtureSetupFailed:
            return _result(
                required=required,
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.INCONCLUSIVE,
                summary=_SUMMARY_FIXTURE_SETUP,
                evidence=[
                    _evidence(
                        code="duckdb_fixture_setup_inconclusive",
                        message=(
                            "The in-memory fixture could not be prepared "
                            "for the rename check."
                        ),
                        details={"stage": "fixture_setup"},
                    )
                ],
                engine_version=engine_version,
            )

        try:
            row_count_before = _row_count(connection, table_name)
        except Exception:
            return _result(
                required=required,
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.INCONCLUSIVE,
                summary=_SUMMARY_FIXTURE_SETUP,
                evidence=[
                    _evidence(
                        code="duckdb_fixture_setup_inconclusive",
                        message=(
                            "The in-memory fixture could not be prepared "
                            "for the rename check."
                        ),
                        details={"stage": "fixture_setup"},
                    )
                ],
                engine_version=engine_version,
            )

        # Rename operation
        try:
            rename_sql = _build_rename_sql(
                table_name, source_for_sql, target_for_sql
            )
            connection.execute(rename_sql)
        except Exception as exc:
            # DuckDB operation rejection → COMPLETED + FAIL (not ERROR).
            _ = exc  # intentionally discarded — never surface
            return _result(
                required=required,
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.FAIL,
                summary=_SUMMARY_RENAME_FAILED,
                evidence=[
                    _evidence(
                        code="duckdb_rename_failed",
                        message=(
                            "DuckDB could not apply the rename operation to the "
                            "supplied in-memory fixture."
                        ),
                        details={"stage": "rename_operation"},
                    )
                ],
                engine_version=engine_version,
            )

        # Postconditions
        try:
            columns_after = _list_columns(connection, table_name)
            row_count_after = _row_count(connection, table_name)
            # Internal verification that row values remain addressable after
            # rename (not returned in evidence).
            if fixture.rows:
                connection.execute(
                    f"SELECT {quote_ident(target_for_sql)} "
                    f"FROM {quote_ident(table_name)} LIMIT 1"
                ).fetchone()
        except Exception:
            return _result(
                required=required,
                execution_status=CheckExecutionStatus.ERROR,
                outcome=None,
                summary=_SUMMARY_ERROR,
                evidence=[
                    _evidence(
                        code="duckdb_execution_error",
                        message=(
                            "The DuckDB engine could not complete the in-memory check."
                        ),
                        details=None,
                    )
                ],
                engine_version=engine_version,
            )

        source_absent = not _column_present(columns_after, source_column)
        target_present = _column_present(columns_after, target_column)
        row_preserved = row_count_before == row_count_after

        if not (source_absent and target_present and row_preserved):
            return _result(
                required=required,
                execution_status=CheckExecutionStatus.COMPLETED,
                outcome=CheckOutcome.FAIL,
                summary=_SUMMARY_POSTCONDITION,
                evidence=[
                    _evidence(
                        code="duckdb_postcondition_failed",
                        message=(
                            "The expected column state was not observed after "
                            "the rename operation."
                        ),
                        details={
                            "source_column_absent_after": source_absent,
                            "target_column_present_after": target_present,
                            "row_count_preserved": row_preserved,
                        },
                    )
                ],
                engine_version=engine_version,
            )

        return _result(
            required=required,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            summary=_SUMMARY_PASS,
            evidence=[
                _evidence(
                    code="duckdb_rename_succeeded",
                    message=(
                        "DuckDB applied the rename operation and the expected "
                        "column state was observed."
                    ),
                    details={
                        "fixture_column_count": len(fixture.columns),
                        "fixture_row_count": len(fixture.rows),
                        "source_column_absent_after": True,
                        "target_column_present_after": True,
                        "row_count_preserved": True,
                    },
                )
            ],
            engine_version=engine_version,
        )
    except Exception:
        return _result(
            required=required,
            execution_status=CheckExecutionStatus.ERROR,
            outcome=None,
            summary=_SUMMARY_ERROR,
            evidence=[
                _evidence(
                    code="duckdb_execution_error",
                    message=(
                        "The DuckDB engine could not complete the in-memory check."
                    ),
                    details=None,
                )
            ],
            engine_version=engine_version,
        )
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
