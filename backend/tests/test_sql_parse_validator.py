"""Unit tests for F6.2 SQLGlot parse validator."""

from __future__ import annotations

import copy
import importlib.metadata
import json
import uuid
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.schemas.sql_validation import MAX_SQL_LENGTH, SqlDialect, SqlParseInput
from app.schemas.validation import (
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    OverallExecutionStatus,
)
from app.services.sql_parse_validator import (
    ENGINE_NAME,
    SQL_PARSE_SCOPE,
    get_sqlglot_version,
    run_sql_parse_check,
)
from app.services.validation_engine import build_validation_artifact

SUBJECT_FP = "b" * 64
INSTALLED_SQLGLOT = importlib.metadata.version("sqlglot")


def _input(
    sql: str = "SELECT 1",
    dialect: SqlDialect = SqlDialect.SNOWFLAKE,
    required: bool = True,
) -> SqlParseInput:
    return SqlParseInput(sql=sql, dialect=dialect, required=required)


# ---- Input contract ----------------------------------------------------------


def test_valid_snowflake_sql_accepted() -> None:
    parse_input = _input(sql="SELECT 1 AS n", dialect=SqlDialect.SNOWFLAKE)
    assert parse_input.dialect == SqlDialect.SNOWFLAKE
    result = run_sql_parse_check(parse_input)
    assert result.execution_status == CheckExecutionStatus.COMPLETED.value
    assert result.outcome == CheckOutcome.PASS.value


def test_valid_postgres_sql_accepted() -> None:
    result = run_sql_parse_check(
        _input(sql="SELECT 1", dialect=SqlDialect.POSTGRES)
    )
    assert result.outcome == CheckOutcome.PASS.value


def test_valid_bigquery_sql_accepted() -> None:
    result = run_sql_parse_check(
        _input(sql="SELECT 1", dialect=SqlDialect.BIGQUERY)
    )
    assert result.outcome == CheckOutcome.PASS.value


def test_valid_duckdb_sql_accepted() -> None:
    result = run_sql_parse_check(
        _input(sql="SELECT 1", dialect=SqlDialect.DUCKDB)
    )
    assert result.outcome == CheckOutcome.PASS.value


def test_unsupported_dialect_rejected() -> None:
    with pytest.raises(ValidationError):
        SqlParseInput(sql="SELECT 1", dialect="postgresql")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        SqlParseInput(sql="SELECT 1", dialect="bq")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        SqlParseInput(sql="SELECT 1", dialect="sf")  # type: ignore[arg-type]


def test_blank_sql_rejected() -> None:
    with pytest.raises(ValidationError):
        SqlParseInput(sql="   ", dialect=SqlDialect.SNOWFLAKE)
    with pytest.raises(ValidationError):
        SqlParseInput(sql="", dialect=SqlDialect.SNOWFLAKE)


def test_sql_over_max_length_rejected() -> None:
    with pytest.raises(ValidationError):
        SqlParseInput(
            sql="SELECT 1 -- " + ("x" * MAX_SQL_LENGTH),
            dialect=SqlDialect.SNOWFLAKE,
        )


def test_null_byte_rejected() -> None:
    with pytest.raises(ValidationError):
        SqlParseInput(sql="SELECT 1\x00", dialect=SqlDialect.SNOWFLAKE)


def test_tab_and_newline_accepted() -> None:
    parse_input = SqlParseInput(
        sql="SELECT\n\t1\r\nAS n",
        dialect=SqlDialect.SNOWFLAKE,
    )
    assert "\n" in parse_input.sql
    assert "\t" in parse_input.sql
    result = run_sql_parse_check(parse_input)
    assert result.outcome == CheckOutcome.PASS.value


def test_unknown_field_rejected() -> None:
    with pytest.raises(ValidationError):
        SqlParseInput(
            sql="SELECT 1",
            dialect=SqlDialect.SNOWFLAKE,
            extra_flag=True,  # type: ignore[call-arg]
        )


# ---- Successful parsing ------------------------------------------------------


def test_simple_select_completed_pass() -> None:
    result = run_sql_parse_check(_input(sql="SELECT 1"))
    assert result.execution_status == CheckExecutionStatus.COMPLETED.value
    assert result.outcome == CheckOutcome.PASS.value
    assert result.evidence[0].code == "sql_parse_succeeded"


def test_rename_column_style_sql_pass() -> None:
    sql = (
        "ALTER TABLE analytics.core.customers "
        "RENAME COLUMN customer_id TO account_id"
    )
    result = run_sql_parse_check(_input(sql=sql, dialect=SqlDialect.SNOWFLAKE))
    assert result.outcome == CheckOutcome.PASS.value


def test_multiple_statements_statement_count() -> None:
    result = run_sql_parse_check(
        _input(sql="SELECT 1; SELECT 2; SELECT 3", dialect=SqlDialect.POSTGRES)
    )
    assert result.outcome == CheckOutcome.PASS.value
    assert result.evidence[0].details["statement_count"] == 3


def test_check_kind_sql_parse() -> None:
    result = run_sql_parse_check(_input())
    assert result.check_kind == CheckKind.SQL_PARSE.value


def test_required_flag_preserved() -> None:
    result_true = run_sql_parse_check(_input(required=True))
    result_false = run_sql_parse_check(_input(required=False))
    assert result_true.required is True
    assert result_false.required is False


def test_check_id_is_uuid() -> None:
    result = run_sql_parse_check(_input())
    uuid.UUID(str(result.check_id))


def test_engine_name_sqlglot() -> None:
    result = run_sql_parse_check(_input())
    assert result.engine_name == ENGINE_NAME == "sqlglot"


def test_engine_version_matches_installed() -> None:
    result = run_sql_parse_check(_input())
    assert result.engine_version == INSTALLED_SQLGLOT
    assert get_sqlglot_version() == INSTALLED_SQLGLOT


def test_scope_sql_syntax_for_declared_dialect() -> None:
    result = run_sql_parse_check(_input())
    assert result.scope == SQL_PARSE_SCOPE == "sql_syntax_for_declared_dialect"


# ---- Parse failure -----------------------------------------------------------


def test_invalid_sql_completed_fail() -> None:
    # Fixture guaranteed to fail on pinned SQLGlot for snowflake dialect.
    result = run_sql_parse_check(
        _input(sql="SELECT FROM WHERE", dialect=SqlDialect.SNOWFLAKE)
    )
    assert result.execution_status == CheckExecutionStatus.COMPLETED.value
    assert result.outcome == CheckOutcome.FAIL.value


def test_parse_failure_evidence_code() -> None:
    result = run_sql_parse_check(_input(sql="SELECT FROM WHERE"))
    assert result.evidence[0].code == "sql_parse_failed"


def test_parse_failure_excludes_raw_sql() -> None:
    sql = "SELECT FROM WHERE bad_token_xyz"
    result = run_sql_parse_check(_input(sql=sql))
    serialized = json.dumps(result.model_dump(mode="json"))
    assert sql not in serialized
    assert "bad_token_xyz" not in serialized
    assert "SELECT FROM" not in serialized


def test_parse_failure_excludes_traceback_and_exception_repr() -> None:
    result = run_sql_parse_check(_input(sql="SELECT FROM WHERE"))
    serialized = json.dumps(result.model_dump(mode="json")).lower()
    assert "traceback" not in serialized
    assert "parseerror" not in serialized
    assert "exception" not in serialized
    # SQLGlot error description fields must not leak.
    assert "token_type" not in serialized
    assert "start_context" not in serialized


def test_evidence_order_stable() -> None:
    result = run_sql_parse_check(_input(sql="SELECT FROM WHERE"))
    assert len(result.evidence) == 1
    assert result.evidence[0].code == "sql_parse_failed"
    # Re-run: evidence content stable (same code/message shape).
    result2 = run_sql_parse_check(_input(sql="SELECT FROM WHERE"))
    assert result2.evidence[0].code == result.evidence[0].code
    assert result2.evidence[0].message == result.evidence[0].message


# ---- No statement ------------------------------------------------------------


def test_comment_only_completed_fail_no_statement() -> None:
    result = run_sql_parse_check(
        _input(sql="-- this is only a comment\n/* block */")
    )
    assert result.execution_status == CheckExecutionStatus.COMPLETED.value
    assert result.outcome == CheckOutcome.FAIL.value
    assert result.evidence[0].code == "sql_no_statement"
    assert result.evidence[0].details["statement_count"] == 0


# ---- Execution error ---------------------------------------------------------


def test_unexpected_parser_error_execution_error() -> None:
    with patch(
        "app.services.sql_parse_validator.sqlglot.parse",
        side_effect=RuntimeError("internal boom with path C:\\secret\\file.sql"),
    ):
        result = run_sql_parse_check(_input(sql="SELECT 1"))
    assert result.execution_status == CheckExecutionStatus.ERROR.value
    assert result.outcome is None
    assert len(result.evidence) >= 1
    assert result.evidence[0].code == "sql_parser_execution_error"
    assert result.engine_name == "sqlglot"
    assert result.engine_version == INSTALLED_SQLGLOT


def test_unexpected_error_does_not_leak_exception_message() -> None:
    secret = "super_secret_exception_detail_xyz"
    with patch(
        "app.services.sql_parse_validator.sqlglot.parse",
        side_effect=RuntimeError(secret),
    ):
        result = run_sql_parse_check(_input(sql="SELECT 1"))
    serialized = json.dumps(result.model_dump(mode="json"))
    assert secret not in serialized
    assert "RuntimeError" not in serialized


# ---- Determinism -------------------------------------------------------------


def test_same_input_same_semantic_result_except_check_id() -> None:
    parse_input = _input(sql="SELECT 1 AS x", dialect=SqlDialect.SNOWFLAKE)
    a = run_sql_parse_check(parse_input)
    b = run_sql_parse_check(parse_input)
    assert a.check_id != b.check_id
    da = a.model_dump(mode="json")
    db = b.model_dump(mode="json")
    da.pop("check_id")
    db.pop("check_id")
    assert da == db


def test_service_does_not_mutate_input_sql() -> None:
    original_sql = "SELECT 1 /* keep me */"
    parse_input = _input(sql=original_sql)
    snapshot = copy.deepcopy(parse_input)
    run_sql_parse_check(parse_input)
    assert parse_input.sql == snapshot.sql == original_sql
    assert parse_input.dialect == snapshot.dialect
    assert parse_input.required == snapshot.required


# ---- Integration with F6.1 aggregation ---------------------------------------


def test_pass_check_aggregates_to_pass() -> None:
    check = run_sql_parse_check(_input(sql="SELECT 1", required=True))
    artifact = build_validation_artifact(
        subject_fingerprint=SUBJECT_FP,
        checks=[check],
    )
    assert artifact.execution_status == OverallExecutionStatus.COMPLETED.value
    assert artifact.outcome == CheckOutcome.PASS.value


def test_required_fail_aggregates_to_fail() -> None:
    check = run_sql_parse_check(_input(sql="SELECT FROM WHERE", required=True))
    artifact = build_validation_artifact(
        subject_fingerprint=SUBJECT_FP,
        checks=[check],
    )
    assert artifact.outcome == CheckOutcome.FAIL.value
    assert artifact.execution_status == OverallExecutionStatus.COMPLETED.value


def test_optional_fail_does_not_override_required_pass() -> None:
    required_pass = run_sql_parse_check(_input(sql="SELECT 1", required=True))
    optional_fail = run_sql_parse_check(
        _input(sql="SELECT FROM WHERE", required=False)
    )
    artifact = build_validation_artifact(
        subject_fingerprint=SUBJECT_FP,
        checks=[required_pass, optional_fail],
    )
    assert artifact.outcome == CheckOutcome.PASS.value
    assert artifact.execution_status == OverallExecutionStatus.COMPLETED.value


# ---- Safety / regression -----------------------------------------------------


def test_service_has_no_network_db_file_subprocess_side_effects() -> None:
    """Sanity: module imports are bounded; no side-effect APIs used at runtime."""
    from pathlib import Path

    import app.services.sql_parse_validator as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    for token in (
        "subprocess",
        "socket",
        "urllib",
        "httpx",
        "requests",
        "sqlite3",
        "psycopg",
    ):
        assert f"import {token}" not in source
        assert f"from {token}" not in source
    for token in ("write_text", "write_bytes", "Path(", "open("):
        assert token not in source


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
    assert not any("sql" in path for path in paths)


def test_pass_evidence_excludes_raw_sql() -> None:
    sql = "SELECT secret_column_name_abc FROM t"
    result = run_sql_parse_check(_input(sql=sql))
    serialized = json.dumps(result.model_dump(mode="json"))
    assert "secret_column_name_abc" not in serialized
    assert sql not in serialized


def test_success_evidence_details_shape() -> None:
    result = run_sql_parse_check(
        _input(sql="SELECT 1", dialect=SqlDialect.SNOWFLAKE)
    )
    details = result.evidence[0].details
    assert details == {
        "dialect": "snowflake",
        "statement_count": 1,
    }


def test_dialect_enum_serialized_values() -> None:
    assert SqlDialect.SNOWFLAKE.value == "snowflake"
    assert SqlDialect.POSTGRES.value == "postgres"
    assert SqlDialect.BIGQUERY.value == "bigquery"
    assert SqlDialect.DUCKDB.value == "duckdb"
