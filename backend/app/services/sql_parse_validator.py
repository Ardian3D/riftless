"""SQLGlot parse validator (phase F6.2).

Runs SQLGlot syntax parsing for a declared dialect and returns a
ValidationCheckResult. Does **not** execute SQL, connect to databases,
resolve schemas, rewrite SQL, or call network/AI services.

PASS means SQLGlot found no syntax error in the parse scope for the engine
version used. PASS is not execution success, schema existence, semantic
correctness, production safety, or deployment authorization.
"""

from __future__ import annotations

import importlib.metadata
import uuid
from typing import Any

import sqlglot
from sqlglot.errors import ParseError

from app.schemas.sql_validation import SqlDialect, SqlParseInput
from app.schemas.validation import (
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    ValidationCheckResult,
    ValidationEvidence,
)

SQL_PARSE_SCOPE = "sql_syntax_for_declared_dialect"
ENGINE_NAME = "sqlglot"

_SUMMARY_PASS = "SQL parsing completed without a detected syntax error."
_SUMMARY_FAIL = "SQL parsing detected a syntax error."
_SUMMARY_NO_STATEMENT = "SQL parsing completed but no SQL statement was detected."
_SUMMARY_ERROR = "SQL parser execution did not complete."


def get_sqlglot_version() -> str:
    """Return the installed SQLGlot package version (runtime metadata)."""
    return importlib.metadata.version("sqlglot")


def _dialect_value(dialect: SqlDialect | str) -> str:
    if isinstance(dialect, SqlDialect):
        return dialect.value
    return str(dialect)


def _safe_line_col(value: Any) -> int | None:
    """Accept only finite positive-ish integers for line/col metadata."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None


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
    engine_version: str | None,
) -> ValidationCheckResult:
    return ValidationCheckResult(
        check_id=uuid.uuid4(),
        check_kind=CheckKind.SQL_PARSE,
        required=required,
        execution_status=execution_status,
        outcome=outcome,
        scope=SQL_PARSE_SCOPE,
        summary=summary,
        evidence=evidence,
        engine_name=ENGINE_NAME if engine_version is not None else ENGINE_NAME,
        engine_version=engine_version,
    )


def run_sql_parse_check(parse_input: SqlParseInput) -> ValidationCheckResult:
    """Parse ``parse_input.sql`` with SQLGlot for the declared dialect.

    Returns a ValidationCheckResult. Never mutates the input. Never returns
    AST, rewritten SQL, or raw SQL in evidence/summary.
    """
    dialect = _dialect_value(parse_input.dialect)
    required = bool(parse_input.required)
    engine_version = get_sqlglot_version()

    try:
        expressions = sqlglot.parse(
            parse_input.sql,
            read=dialect,
            error_level=sqlglot.ErrorLevel.RAISE,
        )
    except ParseError as exc:
        return _build_parse_failure(
            required=required,
            dialect=dialect,
            engine_version=engine_version,
            parse_error=exc,
        )
    except Exception:
        # Unexpected engine/runtime failure — not a validation FAIL.
        return _result(
            required=required,
            execution_status=CheckExecutionStatus.ERROR,
            outcome=None,
            summary=_SUMMARY_ERROR,
            evidence=[
                _evidence(
                    code="sql_parser_execution_error",
                    message="The SQL parser could not complete the check.",
                    details={"dialect": dialect},
                )
            ],
            engine_version=engine_version,
        )

    # SQLGlot may return None placeholders for empty/comment-only segments.
    statements = [expr for expr in expressions if expr is not None]
    statement_count = len(statements)

    if statement_count == 0:
        return _result(
            required=required,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.FAIL,
            summary=_SUMMARY_NO_STATEMENT,
            evidence=[
                _evidence(
                    code="sql_no_statement",
                    message="No SQL statement was detected in the supplied input.",
                    details={
                        "dialect": dialect,
                        "statement_count": 0,
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
                code="sql_parse_succeeded",
                message="SQLGlot parsed the supplied SQL for the declared dialect.",
                details={
                    "dialect": dialect,
                    "statement_count": statement_count,
                },
            )
        ],
        engine_version=engine_version,
    )


def _build_parse_failure(
    *,
    required: bool,
    dialect: str,
    engine_version: str,
    parse_error: ParseError,
) -> ValidationCheckResult:
    """Map a SQLGlot ParseError to COMPLETED + FAIL with safe evidence only."""
    raw_errors = getattr(parse_error, "errors", None)
    if isinstance(raw_errors, list) and raw_errors:
        error_count = len(raw_errors)
        first = raw_errors[0] if isinstance(raw_errors[0], dict) else {}
    else:
        error_count = 1
        first = {}

    details: dict[str, Any] = {
        "dialect": dialect,
        "error_count": error_count,
    }

    line = _safe_line_col(first.get("line") if isinstance(first, dict) else None)
    col = _safe_line_col(first.get("col") if isinstance(first, dict) else None)
    if line is not None:
        details["line"] = line
    if col is not None:
        details["column"] = col

    # Intentionally omit: description, start_context, highlight, end_context,
    # exception message/repr, traceback, raw SQL.

    return _result(
        required=required,
        execution_status=CheckExecutionStatus.COMPLETED,
        outcome=CheckOutcome.FAIL,
        summary=_SUMMARY_FAIL,
        evidence=[
            _evidence(
                code="sql_parse_failed",
                message=(
                    "SQLGlot could not parse the supplied SQL for the declared dialect."
                ),
                details=details,
            )
        ],
        engine_version=engine_version,
    )
