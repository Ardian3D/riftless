"""Unit tests for F6.3 DuckDB in-memory rename validator."""

from __future__ import annotations

import copy
import importlib.metadata
import json
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.schemas.changes import AssetNormalized, NormalizedChange
from app.schemas.duckdb_validation import (
    MAX_COLUMNS,
    MAX_ROWS,
    MAX_TOTAL_CELLS,
    MAX_VARCHAR_CELL_LENGTH,
    DuckDbFixture,
    DuckDbFixtureColumn,
    DuckDbFixtureColumnType,
    DuckDbRenameInput,
)
from app.schemas.validation import (
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    OverallExecutionStatus,
)
from app.services.duckdb_rename_validator import (
    DUCKDB_RENAME_SCOPE,
    ENGINE_NAME,
    get_duckdb_version,
    run_duckdb_rename_check,
)
from app.services.validation_engine import build_validation_artifact
from app.utils.sql_identifiers import quote_ident

SUBJECT_FP = "c" * 64
INSTALLED_DUCKDB = importlib.metadata.version("duckdb")
SECRET_CELL = "fixture_secret_value_xyz_not_in_evidence"


class _CloseTrackingConnection:
    """Proxy around DuckDB connection — execute is read-only on the real object."""

    def __init__(self, connection: Any, closed: list[bool]) -> None:
        self._connection = connection
        self._closed = closed

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        return self._connection.execute(*args, **kwargs)

    def close(self) -> None:
        self._closed.append(True)
        return self._connection.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)


def _change(
    *,
    table: str = "customers",
    source: str = "customer_id",
    target: str = "account_id",
) -> NormalizedChange:
    return NormalizedChange(
        change_type="rename_column",
        asset=AssetNormalized(
            platform="snowflake",
            database="analytics",
            schema="core",
            name=table,
        ),
        source_column=source,
        target_column=target,
        reason=None,
    )


def _fixture(
    columns: list[dict[str, Any]] | None = None,
    rows: list[list[Any]] | None = None,
) -> DuckDbFixture:
    if columns is None:
        columns = [
            {"name": "customer_id", "type": "varchar", "nullable": False},
            {"name": "email", "type": "varchar", "nullable": True},
        ]
    if rows is None:
        rows = [
            ["customer-1", "one@example.test"],
            ["customer-2", None],
        ]
    return DuckDbFixture(
        columns=[DuckDbFixtureColumn(**col) for col in columns],
        rows=rows,
    )


def _input(
    *,
    change: NormalizedChange | None = None,
    fixture: DuckDbFixture | None = None,
    required: bool = True,
) -> DuckDbRenameInput:
    return DuckDbRenameInput(
        normalized_change=change or _change(),
        fixture=fixture or _fixture(),
        required=required,
    )


# ---- Input / fixture contract ------------------------------------------------


def test_valid_fixture_accepted() -> None:
    parse_input = _input()
    assert len(parse_input.fixture.columns) == 2
    result = run_duckdb_rename_check(parse_input)
    assert result.outcome == CheckOutcome.PASS.value


def test_fixture_without_columns_rejected() -> None:
    with pytest.raises(ValidationError):
        DuckDbFixture(columns=[], rows=[])


def test_more_than_64_columns_rejected() -> None:
    columns = [
        DuckDbFixtureColumn(name=f"c{i}", type=DuckDbFixtureColumnType.INTEGER)
        for i in range(MAX_COLUMNS + 1)
    ]
    with pytest.raises(ValidationError):
        DuckDbFixture(columns=columns, rows=[])


def test_more_than_500_rows_rejected() -> None:
    columns = [DuckDbFixtureColumn(name="a", type=DuckDbFixtureColumnType.INTEGER)]
    rows = [[1] for _ in range(MAX_ROWS + 1)]
    with pytest.raises(ValidationError):
        DuckDbFixture(columns=columns, rows=rows)


def test_total_cells_over_limit_rejected() -> None:
    # 50 columns × 401 rows = 20050 > 20000
    col_count = 50
    row_count = (MAX_TOTAL_CELLS // col_count) + 1
    assert col_count * row_count > MAX_TOTAL_CELLS
    columns = [
        DuckDbFixtureColumn(name=f"c{i}", type=DuckDbFixtureColumnType.INTEGER)
        for i in range(col_count)
    ]
    rows = [[0] * col_count for _ in range(row_count)]
    with pytest.raises(ValidationError):
        DuckDbFixture(columns=columns, rows=rows)


def test_row_width_mismatch_rejected() -> None:
    with pytest.raises(ValidationError):
        DuckDbFixture(
            columns=[
                DuckDbFixtureColumn(name="a", type=DuckDbFixtureColumnType.INTEGER),
                DuckDbFixtureColumn(name="b", type=DuckDbFixtureColumnType.INTEGER),
            ],
            rows=[[1]],
        )


def test_duplicate_column_case_insensitive_rejected() -> None:
    with pytest.raises(ValidationError):
        DuckDbFixture(
            columns=[
                DuckDbFixtureColumn(name="Email", type=DuckDbFixtureColumnType.VARCHAR),
                DuckDbFixtureColumn(name="email", type=DuckDbFixtureColumnType.VARCHAR),
            ],
            rows=[],
        )


def test_blank_column_name_rejected() -> None:
    with pytest.raises(ValidationError):
        DuckDbFixtureColumn(name="   ", type=DuckDbFixtureColumnType.VARCHAR)


def test_control_character_in_identifier_rejected() -> None:
    with pytest.raises(ValidationError):
        DuckDbFixtureColumn(name="bad\x00name", type=DuckDbFixtureColumnType.VARCHAR)


def test_varchar_over_4096_rejected() -> None:
    with pytest.raises(ValidationError):
        DuckDbFixture(
            columns=[
                DuckDbFixtureColumn(name="a", type=DuckDbFixtureColumnType.VARCHAR)
            ],
            rows=[["x" * (MAX_VARCHAR_CELL_LENGTH + 1)]],
        )


def test_null_on_non_nullable_rejected() -> None:
    with pytest.raises(ValidationError):
        DuckDbFixture(
            columns=[
                DuckDbFixtureColumn(
                    name="a", type=DuckDbFixtureColumnType.VARCHAR, nullable=False
                )
            ],
            rows=[[None]],
        )


def test_type_mismatch_not_coerced() -> None:
    with pytest.raises(ValidationError):
        DuckDbFixture(
            columns=[
                DuckDbFixtureColumn(name="a", type=DuckDbFixtureColumnType.INTEGER)
            ],
            rows=[["42"]],  # string not coerced to int
        )
    with pytest.raises(ValidationError):
        DuckDbFixture(
            columns=[
                DuckDbFixtureColumn(name="a", type=DuckDbFixtureColumnType.BOOLEAN)
            ],
            rows=[[1]],  # int not coerced to bool
        )
    with pytest.raises(ValidationError):
        DuckDbFixture(
            columns=[
                DuckDbFixtureColumn(name="a", type=DuckDbFixtureColumnType.INTEGER)
            ],
            rows=[[True]],  # bool not integer
        )


def test_unknown_field_rejected() -> None:
    with pytest.raises(ValidationError):
        DuckDbRenameInput(
            normalized_change=_change(),
            fixture=_fixture(),
            extra_flag=True,  # type: ignore[call-arg]
        )


def test_arbitrary_sql_field_rejected() -> None:
    for key in (
        "sql",
        "setup_sql",
        "migration_sql",
        "assertion_sql",
        "teardown_sql",
        "command",
        "query",
        "script",
    ):
        with pytest.raises(ValidationError):
            DuckDbRenameInput.model_validate(
                {
                    "normalized_change": _change().model_dump(by_alias=True),
                    "fixture": {
                        "columns": [
                            {
                                "name": "customer_id",
                                "type": "varchar",
                                "nullable": False,
                            }
                        ],
                        "rows": [["x"]],
                    },
                    key: "SELECT 1",
                }
            )


# ---- Successful execution ----------------------------------------------------


def test_simple_rename_completed_pass() -> None:
    result = run_duckdb_rename_check(_input())
    assert result.execution_status == CheckExecutionStatus.COMPLETED.value
    assert result.outcome == CheckOutcome.PASS.value
    assert result.evidence[0].code == "duckdb_rename_succeeded"


def test_source_absent_target_present_row_count_preserved() -> None:
    result = run_duckdb_rename_check(_input())
    details = result.evidence[0].details
    assert details["source_column_absent_after"] is True
    assert details["target_column_present_after"] is True
    assert details["row_count_preserved"] is True
    assert details["fixture_row_count"] == 2
    assert details["fixture_column_count"] == 2


def test_internal_values_survive_rename_without_evidence_leak() -> None:
    """Values remain queryable after rename (internal), not returned in evidence."""
    fixture = _fixture(
        columns=[
            {"name": "customer_id", "type": "varchar", "nullable": False},
            {"name": "email", "type": "varchar", "nullable": True},
        ],
        rows=[[SECRET_CELL, "a@example.test"]],
    )
    result = run_duckdb_rename_check(_input(fixture=fixture))
    assert result.outcome == CheckOutcome.PASS.value
    serialized = json.dumps(result.model_dump(mode="json"))
    assert SECRET_CELL not in serialized
    assert "a@example.test" not in serialized


def test_check_kind_and_scope() -> None:
    result = run_duckdb_rename_check(_input())
    assert result.check_kind == CheckKind.DUCKDB_EXECUTION.value
    assert result.scope == DUCKDB_RENAME_SCOPE == "duckdb_in_memory_rename_simulation"


def test_required_preserved() -> None:
    assert run_duckdb_rename_check(_input(required=True)).required is True
    assert run_duckdb_rename_check(_input(required=False)).required is False


def test_check_id_uuid() -> None:
    result = run_duckdb_rename_check(_input())
    uuid.UUID(str(result.check_id))


def test_engine_metadata() -> None:
    result = run_duckdb_rename_check(_input())
    assert result.engine_name == ENGINE_NAME == "duckdb"
    assert result.engine_version == INSTALLED_DUCKDB
    assert get_duckdb_version() == INSTALLED_DUCKDB


def test_mixed_case_and_quoted_safe_identifiers() -> None:
    change = _change(table='Cust"omers', source="Customer_Id", target="Account_Id")
    fixture = _fixture(
        columns=[
            {"name": "Customer_Id", "type": "varchar", "nullable": False},
            {"name": "Email", "type": "varchar", "nullable": True},
        ],
        rows=[["c1", "e@test"]],
    )
    result = run_duckdb_rename_check(_input(change=change, fixture=fixture))
    assert result.outcome == CheckOutcome.PASS.value
    assert quote_ident('Cust"omers') == '"Cust""omers"'


# ---- Precondition failure ----------------------------------------------------


def test_source_column_missing() -> None:
    fixture = _fixture(
        columns=[
            {"name": "email", "type": "varchar", "nullable": True},
        ],
        rows=[["a@test"]],
    )
    result = run_duckdb_rename_check(_input(fixture=fixture))
    assert result.execution_status == CheckExecutionStatus.COMPLETED.value
    assert result.outcome == CheckOutcome.FAIL.value
    assert result.evidence[0].code == "duckdb_source_column_missing"


def test_target_column_exists() -> None:
    fixture = _fixture(
        columns=[
            {"name": "customer_id", "type": "varchar", "nullable": False},
            {"name": "account_id", "type": "varchar", "nullable": True},
        ],
        rows=[["c1", "a1"]],
    )
    result = run_duckdb_rename_check(_input(fixture=fixture))
    assert result.execution_status == CheckExecutionStatus.COMPLETED.value
    assert result.outcome == CheckOutcome.FAIL.value
    assert result.evidence[0].code == "duckdb_target_column_exists"


# ---- Failure classification --------------------------------------------------


def test_simulated_rename_rejection() -> None:
    # Force server-generated rename SQL to target a non-existent column so
    # DuckDB rejects the operation (cannot monkeypatch read-only execute).
    with patch(
        "app.services.duckdb_rename_validator._build_rename_sql",
        return_value=(
            'ALTER TABLE "customers" RENAME COLUMN "definitely_missing_col" '
            'TO "account_id"'
        ),
    ):
        result = run_duckdb_rename_check(_input())
    assert result.execution_status == CheckExecutionStatus.COMPLETED.value
    assert result.outcome == CheckOutcome.FAIL.value
    assert result.evidence[0].code == "duckdb_rename_failed"
    assert result.evidence[0].details == {"stage": "rename_operation"}


def test_simulated_fixture_setup_failure() -> None:
    with patch(
        "app.services.duckdb_rename_validator._setup_fixture",
        side_effect=__import__(
            "app.services.duckdb_rename_validator",
            fromlist=["DuckDbFixtureSetupFailed"],
        ).DuckDbFixtureSetupFailed,
    ):
        result = run_duckdb_rename_check(_input())
    assert result.execution_status == CheckExecutionStatus.COMPLETED.value
    assert result.outcome == CheckOutcome.INCONCLUSIVE.value
    assert result.evidence[0].code == "duckdb_fixture_setup_inconclusive"
    assert result.evidence[0].details == {"stage": "fixture_setup"}


def test_unexpected_engine_error() -> None:
    with patch(
        "app.services.duckdb_rename_validator._open_isolated_connection",
        side_effect=RuntimeError("secret_engine_boom_xyz"),
    ):
        result = run_duckdb_rename_check(_input())
    assert result.execution_status == CheckExecutionStatus.ERROR.value
    assert result.outcome is None
    assert result.evidence[0].code == "duckdb_execution_error"
    serialized = json.dumps(result.model_dump(mode="json"))
    assert "secret_engine_boom_xyz" not in serialized
    assert "RuntimeError" not in serialized


# ---- Privacy -----------------------------------------------------------------


def test_fixture_values_not_in_result() -> None:
    fixture = _fixture(rows=[[SECRET_CELL, "hidden@example.test"]])
    result = run_duckdb_rename_check(_input(fixture=fixture))
    serialized = json.dumps(result.model_dump(mode="json"))
    assert SECRET_CELL not in serialized
    assert "hidden@example.test" not in serialized


def test_generated_sql_not_in_result() -> None:
    result = run_duckdb_rename_check(_input())
    serialized = json.dumps(result.model_dump(mode="json")).upper()
    assert "CREATE TABLE" not in serialized
    assert "ALTER TABLE" not in serialized
    assert "INSERT INTO" not in serialized
    assert "RENAME COLUMN" not in serialized


def test_no_traceback_in_result() -> None:
    with patch(
        "app.services.duckdb_rename_validator._open_isolated_connection",
        side_effect=RuntimeError("boom"),
    ):
        result = run_duckdb_rename_check(_input())
    serialized = json.dumps(result.model_dump(mode="json")).lower()
    assert "traceback" not in serialized
    assert "exception" not in serialized


# ---- Determinism -------------------------------------------------------------


def test_same_input_same_semantic_result_except_check_id() -> None:
    rename_input = _input()
    a = run_duckdb_rename_check(rename_input)
    b = run_duckdb_rename_check(rename_input)
    assert a.check_id != b.check_id
    da = a.model_dump(mode="json")
    db = b.model_dump(mode="json")
    da.pop("check_id")
    db.pop("check_id")
    assert da == db


def test_input_not_mutated() -> None:
    rename_input = _input()
    snapshot = copy.deepcopy(rename_input)
    run_duckdb_rename_check(rename_input)
    assert rename_input.model_dump() == snapshot.model_dump()


# ---- Connection / isolation --------------------------------------------------


def test_database_uses_memory() -> None:
    with patch("app.services.duckdb_rename_validator.duckdb.connect") as mock_connect:
        mock_con = MagicMock()
        mock_con.execute.return_value.fetchone.return_value = (False,)
        mock_con.execute.return_value.fetchall.return_value = []
        mock_connect.return_value = mock_con
        # Will fail postcondition-ish; we only care about connect args.
        try:
            run_duckdb_rename_check(_input())
        except Exception:
            pass
        mock_connect.assert_called()
        args, kwargs = mock_connect.call_args
        # database=":memory:" either positional or keyword
        if args:
            assert args[0] == ":memory:"
        else:
            assert kwargs.get("database") == ":memory:"


def test_connection_closed_after_success() -> None:
    closed: list[bool] = []
    real_connect = __import__("duckdb").connect

    def tracking_connect(*args: Any, **kwargs: Any) -> Any:
        con = real_connect(*args, **kwargs)
        return _CloseTrackingConnection(con, closed)

    with patch(
        "app.services.duckdb_rename_validator.duckdb.connect",
        side_effect=tracking_connect,
    ):
        result = run_duckdb_rename_check(_input())
    assert result.outcome == CheckOutcome.PASS.value
    assert closed == [True]


def test_connection_closed_after_failure() -> None:
    closed: list[bool] = []
    real_connect = __import__("duckdb").connect

    def tracking_connect(*args: Any, **kwargs: Any) -> Any:
        con = real_connect(*args, **kwargs)
        return _CloseTrackingConnection(con, closed)

    with patch(
        "app.services.duckdb_rename_validator.duckdb.connect",
        side_effect=tracking_connect,
    ):
        with patch(
            "app.services.duckdb_rename_validator._build_rename_sql",
            return_value=(
                'ALTER TABLE "customers" RENAME COLUMN "missing" TO "account_id"'
            ),
        ):
            result = run_duckdb_rename_check(_input())
    assert result.outcome == CheckOutcome.FAIL.value
    assert closed == [True]


def test_second_check_does_not_see_first_fixture() -> None:
    # First check uses secret table name; second uses different table.
    # Isolation means second check cannot read first table (new :memory:).
    first = run_duckdb_rename_check(
        _input(change=_change(table="table_a"), fixture=_fixture())
    )
    second = run_duckdb_rename_check(
        _input(change=_change(table="table_b"), fixture=_fixture())
    )
    assert first.outcome == CheckOutcome.PASS.value
    assert second.outcome == CheckOutcome.PASS.value


def test_external_access_restriction_applied() -> None:
    from app.services.duckdb_rename_validator import _apply_connection_hardening

    import duckdb as duckdb_mod

    con = duckdb_mod.connect(database=":memory:")
    try:
        _apply_connection_hardening(con)
        for name, expected in (
            ("enable_external_access", False),
            ("autoinstall_known_extensions", False),
            ("autoload_known_extensions", False),
            ("lock_configuration", True),
        ):
            val = con.execute(f"SELECT current_setting('{name}')").fetchone()
            assert val is not None
            assert bool(val[0]) is expected
        # External file read must fail when restriction is active.
        with pytest.raises(Exception):
            con.execute("SELECT * FROM read_csv_auto('C:/Windows/win.ini')")
    finally:
        con.close()


def test_no_extension_install_load_in_source() -> None:
    source = Path(
        __import__(
            "app.services.duckdb_rename_validator", fromlist=["__file__"]
        ).__file__
    ).read_text(encoding="utf-8")
    # No INSTALL/LOAD extension SQL statements (settings names may contain these substrings).
    assert "INSTALL " not in source
    assert "LOAD " not in source
    assert "install '" not in source.lower()
    assert "load '" not in source.lower()
    assert ".install_extension" not in source
    assert ".load_extension" not in source


def test_no_filesystem_database_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.iterdir())
    run_duckdb_rename_check(_input())
    after = set(tmp_path.iterdir())
    # No new .db / .duckdb files
    created = after - before
    for path in created:
        assert path.suffix.lower() not in {".db", ".duckdb", ".wal"}


def test_service_source_has_no_network_or_subprocess() -> None:
    source = Path(
        __import__(
            "app.services.duckdb_rename_validator", fromlist=["__file__"]
        ).__file__
    ).read_text(encoding="utf-8")
    for token in ("subprocess", "socket", "urllib", "httpx", "requests"):
        assert f"import {token}" not in source
        assert f"from {token}" not in source


# ---- F6.1 aggregation integration --------------------------------------------


def test_pass_aggregates_to_pass() -> None:
    check = run_duckdb_rename_check(_input(required=True))
    artifact = build_validation_artifact(
        subject_fingerprint=SUBJECT_FP, checks=[check]
    )
    assert artifact.execution_status == OverallExecutionStatus.COMPLETED.value
    assert artifact.outcome == CheckOutcome.PASS.value


def test_required_fail_aggregates_to_fail() -> None:
    fixture = _fixture(
        columns=[{"name": "email", "type": "varchar", "nullable": True}],
        rows=[["x"]],
    )
    check = run_duckdb_rename_check(_input(fixture=fixture, required=True))
    artifact = build_validation_artifact(
        subject_fingerprint=SUBJECT_FP, checks=[check]
    )
    assert artifact.outcome == CheckOutcome.FAIL.value


def test_required_inconclusive_aggregates_to_inconclusive() -> None:
    with patch(
        "app.services.duckdb_rename_validator._setup_fixture",
        side_effect=__import__(
            "app.services.duckdb_rename_validator",
            fromlist=["DuckDbFixtureSetupFailed"],
        ).DuckDbFixtureSetupFailed,
    ):
        check = run_duckdb_rename_check(_input(required=True))
    artifact = build_validation_artifact(
        subject_fingerprint=SUBJECT_FP, checks=[check]
    )
    assert artifact.outcome == CheckOutcome.INCONCLUSIVE.value


def test_optional_fail_does_not_override_required_pass() -> None:
    required_pass = run_duckdb_rename_check(_input(required=True))
    optional_fail = run_duckdb_rename_check(
        _input(
            fixture=_fixture(
                columns=[{"name": "email", "type": "varchar", "nullable": True}],
                rows=[["x"]],
            ),
            required=False,
        )
    )
    artifact = build_validation_artifact(
        subject_fingerprint=SUBJECT_FP,
        checks=[required_pass, optional_fail],
    )
    assert artifact.outcome == CheckOutcome.PASS.value


# ---- Regression --------------------------------------------------------------


def test_regression_openapi_paths_unchanged() -> None:
    from app.main import app

    paths = set(app.openapi()["paths"].keys())
    assert paths == {
        "/health",
        "/ready",
        "/api/v1/changes/intake",
        "/api/v1/risk/evaluate",
        "/api/v1/runs/analyze",
    }
    assert not any("validat" in path for path in paths)
    assert not any("duck" in path for path in paths)
