"""Unit tests for F6.4 controlled dbt project parse validator."""

from __future__ import annotations

import copy
import importlib.metadata
import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.schemas.dbt_validation import MAX_MODEL_SQL_LENGTH, DbtParseInput
from app.schemas.validation import (
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    OverallExecutionStatus,
)
from app.services.dbt_parse_validator import (
    ALLOWED_COMMAND,
    DBT_PARSE_SCOPE,
    ENGINE_NAME,
    build_dbt_parse_command,
    build_sanitized_env,
    get_dbt_core_version,
    get_dbt_duckdb_version,
    resolve_dbt_executable,
    run_dbt_parse_check,
)
from app.services.validation_engine import build_validation_artifact
from app.utils.controlled_dbt_project import (
    ADAPTER_NAME,
    PROJECT_NAME,
    create_controlled_dbt_project,
)

SUBJECT_FP = "d" * 64
INSTALLED_DBT_CORE = importlib.metadata.version("dbt-core")
INSTALLED_DBT_DUCKDB = importlib.metadata.version("dbt-duckdb")
SECRET_SQL = "select secret_column_xyz as account_id from customers"


def _input(
    *,
    model_name: str = "customers_renamed",
    model_sql: str = "select customer_id as account_id from customers",
    required: bool = True,
) -> DbtParseInput:
    return DbtParseInput(
        model_name=model_name,
        model_sql=model_sql,
        required=required,
    )


# ---- Input contract ----------------------------------------------------------


def test_valid_model_input_accepted() -> None:
    parse_input = _input()
    assert parse_input.model_name == "customers_renamed"
    result = run_dbt_parse_check(parse_input)
    assert result.outcome == CheckOutcome.PASS.value


def test_invalid_model_name_rejected() -> None:
    with pytest.raises(ValidationError):
        DbtParseInput(model_name="Customers", model_sql="select 1 as x")
    with pytest.raises(ValidationError):
        DbtParseInput(model_name="1starts_digit", model_sql="select 1 as x")
    with pytest.raises(ValidationError):
        DbtParseInput(model_name="has-dash", model_sql="select 1 as x")


def test_path_traversal_model_name_rejected() -> None:
    with pytest.raises(ValidationError):
        DbtParseInput(model_name="../etc/passwd", model_sql="select 1 as x")
    with pytest.raises(ValidationError):
        DbtParseInput(model_name="a/b", model_sql="select 1 as x")
    with pytest.raises(ValidationError):
        DbtParseInput(model_name=r"a\b", model_sql="select 1 as x")


def test_blank_model_sql_rejected() -> None:
    with pytest.raises(ValidationError):
        DbtParseInput(model_name="m1", model_sql="   ")
    with pytest.raises(ValidationError):
        DbtParseInput(model_name="m1", model_sql="")


def test_model_sql_over_max_length_rejected() -> None:
    with pytest.raises(ValidationError):
        DbtParseInput(
            model_name="m1",
            model_sql="select 1 -- " + ("x" * MAX_MODEL_SQL_LENGTH),
        )


def test_null_byte_rejected() -> None:
    with pytest.raises(ValidationError):
        DbtParseInput(model_name="m1", model_sql="select 1\x00 as x")


def test_unknown_field_rejected() -> None:
    with pytest.raises(ValidationError):
        DbtParseInput(
            model_name="m1",
            model_sql="select 1 as x",
            extra_flag=True,  # type: ignore[call-arg]
        )


def test_caller_command_field_rejected() -> None:
    with pytest.raises(ValidationError):
        DbtParseInput.model_validate(
            {
                "model_name": "m1",
                "model_sql": "select 1 as x",
                "command": "run",
            }
        )


def test_caller_project_path_rejected() -> None:
    with pytest.raises(ValidationError):
        DbtParseInput.model_validate(
            {
                "model_name": "m1",
                "model_sql": "select 1 as x",
                "project_dir": "/tmp/evil",
            }
        )
    with pytest.raises(ValidationError):
        DbtParseInput.model_validate(
            {
                "model_name": "m1",
                "model_sql": "select 1 as x",
                "profiles_dir": "/tmp/evil",
            }
        )


def test_jinja_double_brace_rejected() -> None:
    with pytest.raises(ValidationError):
        DbtParseInput(
            model_name="m1",
            model_sql="select {{ ref('x') }} as y",
        )


def test_jinja_percent_brace_rejected() -> None:
    with pytest.raises(ValidationError):
        DbtParseInput(
            model_name="m1",
            model_sql="{% set x = 1 %} select 1 as y",
        )


def test_jinja_hash_brace_rejected() -> None:
    with pytest.raises(ValidationError):
        DbtParseInput(
            model_name="m1",
            model_sql="{# comment #} select 1 as y",
        )


# ---- Controlled project ------------------------------------------------------


def test_temporary_directory_created_per_invocation() -> None:
    a = create_controlled_dbt_project(
        model_name="m_a", model_sql="select 1 as x"
    )
    b = create_controlled_dbt_project(
        model_name="m_b", model_sql="select 2 as x"
    )
    try:
        assert a.root_dir != b.root_dir
        assert a.root_dir.is_dir()
        assert b.root_dir.is_dir()
    finally:
        a.cleanup()
        b.cleanup()


def test_project_only_has_allowlisted_files() -> None:
    project = create_controlled_dbt_project(
        model_name="customers_renamed",
        model_sql="select 1 as x",
    )
    try:
        files = {p for p in project.project_dir.rglob("*") if p.is_file()}
        # Only dbt_project.yml and the model sql under project (target/logs empty).
        rel = {p.relative_to(project.project_dir).as_posix() for p in files}
        assert "dbt_project.yml" in rel
        assert "models/customers_renamed.sql" in rel
        assert not any(name.startswith("target/") for name in rel)
        assert not any(name.startswith("logs/") for name in rel)
        assert (project.profiles_dir / "profiles.yml").is_file()
    finally:
        project.cleanup()


def test_no_packages_yml() -> None:
    project = create_controlled_dbt_project(
        model_name="m1", model_sql="select 1 as x"
    )
    try:
        assert not (project.project_dir / "packages.yml").exists()
        assert not (project.project_dir / "dependencies.yml").exists()
    finally:
        project.cleanup()


def test_no_macros_directory() -> None:
    project = create_controlled_dbt_project(
        model_name="m1", model_sql="select 1 as x"
    )
    try:
        assert not (project.project_dir / "macros").exists()
    finally:
        project.cleanup()


def test_profile_uses_duckdb_controlled_target() -> None:
    project = create_controlled_dbt_project(
        model_name="m1", model_sql="select 1 as x"
    )
    try:
        text = (project.profiles_dir / "profiles.yml").read_text(encoding="utf-8")
        assert "type: duckdb" in text
        assert "path: ':memory:'" in text
        assert PROJECT_NAME in text or "riftless_validation" in text
    finally:
        project.cleanup()


def test_caller_cannot_change_project_name() -> None:
    with pytest.raises(ValidationError):
        DbtParseInput.model_validate(
            {
                "model_name": "m1",
                "model_sql": "select 1 as x",
                "project_name": "evil_project",
            }
        )


def test_caller_cannot_change_adapter() -> None:
    with pytest.raises(ValidationError):
        DbtParseInput.model_validate(
            {
                "model_name": "m1",
                "model_sql": "select 1 as x",
                "adapter": "snowflake",
            }
        )


# ---- Command -----------------------------------------------------------------


def test_only_parse_command_in_argv() -> None:
    project = create_controlled_dbt_project(
        model_name="m1", model_sql="select 1 as x"
    )
    try:
        dbt = resolve_dbt_executable()
        assert dbt is not None
        cmd = build_dbt_parse_command(dbt_executable=dbt, project=project)
        assert cmd[1] == ALLOWED_COMMAND == "parse"
        assert "run" not in cmd
        assert "build" not in cmd
        assert "deps" not in cmd
        assert "test" not in cmd
    finally:
        project.cleanup()


def test_shell_false_and_list_args() -> None:
    captured: dict[str, Any] = {}

    def fake_run(*args: Any, **kwargs: Any) -> Any:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            args=args[0] if args else [],
            returncode=0,
            stdout="",
            stderr="",
        )

    with patch(
        "app.services.dbt_parse_validator.subprocess.run",
        side_effect=fake_run,
    ):
        with patch(
            "app.services.dbt_parse_validator._verify_manifest",
            return_value=(True, None),
        ):
            run_dbt_parse_check(_input())
    assert captured["kwargs"]["shell"] is False
    assert isinstance(captured["args"][0], list)
    cmd = captured["args"][0]
    assert "--project-dir" in cmd
    assert "--profiles-dir" in cmd
    assert "--target-path" in cmd
    assert "--log-path" in cmd


def test_dbt_run_build_deps_never_invoked() -> None:
    source = Path(
        __import__(
            "app.services.dbt_parse_validator", fromlist=["__file__"]
        ).__file__
    ).read_text(encoding="utf-8")
    # Command constant is only parse; no run/build/deps strings as commands.
    assert 'ALLOWED_COMMAND = "parse"' in source
    assert '"run"' not in source
    assert '"build"' not in source
    assert '"deps"' not in source


def test_timeout_applied() -> None:
    from app.services.dbt_parse_validator import DBT_TIMEOUT_SECONDS

    assert DBT_TIMEOUT_SECONDS == 60

    def raise_timeout(*args: Any, **kwargs: Any) -> Any:
        assert kwargs.get("timeout") == 60
        raise subprocess.TimeoutExpired(cmd=args[0] if args else [], timeout=60)

    with patch(
        "app.services.dbt_parse_validator.subprocess.run",
        side_effect=raise_timeout,
    ):
        result = run_dbt_parse_check(_input())
    assert result.execution_status == CheckExecutionStatus.ERROR.value
    assert result.outcome is None
    assert result.evidence[0].code == "dbt_execution_timeout"


# ---- Success -----------------------------------------------------------------


def test_successful_parse_completed_pass() -> None:
    result = run_dbt_parse_check(_input())
    assert result.execution_status == CheckExecutionStatus.COMPLETED.value
    assert result.outcome == CheckOutcome.PASS.value
    assert result.evidence[0].code == "dbt_parse_succeeded"


def test_manifest_contains_exactly_one_expected_model() -> None:
    result = run_dbt_parse_check(_input(model_name="customers_renamed"))
    details = result.evidence[0].details
    assert details["model_count"] == 1
    assert details["expected_model_present"] is True
    assert details["adapter_name"] == "duckdb"
    assert details["command"] == "parse"


def test_check_kind_and_scope() -> None:
    result = run_dbt_parse_check(_input())
    assert result.check_kind == CheckKind.DBT_VALIDATION.value
    assert (
        result.scope
        == DBT_PARSE_SCOPE
        == "dbt_server_generated_project_manifest_parse"
    )


def test_required_preserved() -> None:
    assert run_dbt_parse_check(_input(required=True)).required is True
    assert run_dbt_parse_check(_input(required=False)).required is False


def test_check_id_uuid() -> None:
    result = run_dbt_parse_check(_input())
    uuid.UUID(str(result.check_id))


def test_engine_metadata() -> None:
    result = run_dbt_parse_check(_input())
    assert result.engine_name == ENGINE_NAME == "dbt-core"
    assert result.engine_version == INSTALLED_DBT_CORE
    assert get_dbt_core_version() == INSTALLED_DBT_CORE
    assert result.evidence[0].details.get("adapter_version") == INSTALLED_DBT_DUCKDB
    assert get_dbt_duckdb_version() == INSTALLED_DBT_DUCKDB


# ---- Failure -----------------------------------------------------------------


def test_nonzero_parse_is_execution_error() -> None:
    """Generic non-zero dbt exit is ERROR, not a proven caller validation FAIL."""
    secret_sql = "select secret_model_sql_token from nowhere"
    parse_input = _input(model_sql=secret_sql)

    def fake_run(*args: Any, **kwargs: Any) -> Any:
        cmd = args[0] if args else []
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=2,
            stdout="PARSE ERROR INTERNAL C:\\Users\\secret\\path",
            stderr="bad model secret_path traceback",
        )

    with patch(
        "app.services.dbt_parse_validator.subprocess.run",
        side_effect=fake_run,
    ):
        result = run_dbt_parse_check(parse_input)
    assert result.execution_status == CheckExecutionStatus.ERROR.value
    assert result.outcome is None
    assert result.evidence[0].code == "dbt_parse_process_failed"
    assert result.summary == "dbt validation execution did not complete."
    serialized = json.dumps(result.model_dump(mode="json"))
    assert "PARSE ERROR INTERNAL" not in serialized
    assert "bad model" not in serialized
    assert "secret_path" not in serialized
    assert "traceback" not in serialized.lower()
    assert "secret_model_sql_token" not in serialized
    assert secret_sql not in serialized
    assert "c:\\\\users" not in serialized.lower()
    assert "appdata" not in serialized.lower()
    assert "riftless_dbt_" not in serialized
    # Command path / argv must not leak into the result surface.
    assert "dbt.exe" not in serialized.lower()
    assert "--project-dir" not in serialized


def test_plain_invalid_sql_still_manifest_pass_on_pinned_dbt() -> None:
    """dbt parse is not a SQL grammar validator (that is F6.2 / SQLGlot).

    On dbt-core 1.10.15 + dbt-duckdb 1.10.1, plain invalid SQL without Jinja
    still registers the model in the manifest (exit 0). PASS only means
    project/manifest registration succeeded.
    """
    invalid_sql = "SELECT FROM WHERE THIS IS NOT VALID SQL ;;;"
    result = run_dbt_parse_check(
        _input(model_name="bad_model", model_sql=invalid_sql)
    )
    assert result.execution_status == CheckExecutionStatus.COMPLETED.value
    assert result.outcome == CheckOutcome.PASS.value
    assert result.evidence[0].code == "dbt_parse_succeeded"
    assert result.evidence[0].details["expected_model_present"] is True
    serialized = json.dumps(result.model_dump(mode="json"))
    assert invalid_sql not in serialized
    assert "THIS IS NOT VALID SQL" not in serialized


def test_timeout_error_null_outcome() -> None:
    with patch(
        "app.services.dbt_parse_validator.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["dbt"], timeout=60),
    ):
        result = run_dbt_parse_check(_input())
    assert result.execution_status == CheckExecutionStatus.ERROR.value
    assert result.outcome is None
    assert result.evidence[0].code == "dbt_execution_timeout"


def test_dbt_unavailable() -> None:
    with patch(
        "app.services.dbt_parse_validator.resolve_dbt_executable",
        return_value=None,
    ):
        result = run_dbt_parse_check(_input())
    assert result.execution_status == CheckExecutionStatus.UNAVAILABLE.value
    assert result.outcome is None
    assert result.evidence[0].code == "dbt_engine_unavailable"


def test_missing_manifest_after_success_is_error() -> None:
    def fake_run(*args: Any, **kwargs: Any) -> Any:
        return subprocess.CompletedProcess(
            args=args[0] if args else [],
            returncode=0,
            stdout="",
            stderr="",
        )

    with patch(
        "app.services.dbt_parse_validator.subprocess.run",
        side_effect=fake_run,
    ):
        # Real project has no manifest because dbt was not actually run.
        result = run_dbt_parse_check(_input())
    assert result.execution_status == CheckExecutionStatus.ERROR.value
    assert result.outcome is None
    assert result.evidence[0].code == "dbt_manifest_verification_error"


def test_invalid_manifest_is_error() -> None:
    real_create = create_controlled_dbt_project

    def create_with_bad_manifest(**kwargs: Any) -> Any:
        project = real_create(**kwargs)
        (project.target_dir / "manifest.json").write_text(
            "{not-json", encoding="utf-8"
        )
        return project

    def fake_run(*args: Any, **kwargs: Any) -> Any:
        return subprocess.CompletedProcess(
            args=args[0] if args else [],
            returncode=0,
            stdout="",
            stderr="",
        )

    with patch(
        "app.services.dbt_parse_validator.create_controlled_dbt_project",
        side_effect=create_with_bad_manifest,
    ):
        with patch(
            "app.services.dbt_parse_validator.subprocess.run",
            side_effect=fake_run,
        ):
            result = run_dbt_parse_check(_input())
    assert result.execution_status == CheckExecutionStatus.ERROR.value
    assert result.evidence[0].code == "dbt_manifest_verification_error"


def test_unexpected_extra_model_in_manifest_is_error() -> None:
    real_create = create_controlled_dbt_project

    def create_with_extra_model(**kwargs: Any) -> Any:
        project = real_create(**kwargs)
        manifest = {
            "nodes": {
                f"model.{PROJECT_NAME}.customers_renamed": {
                    "name": "customers_renamed",
                    "resource_type": "model",
                },
                f"model.{PROJECT_NAME}.extra_model": {
                    "name": "extra_model",
                    "resource_type": "model",
                },
            }
        }
        (project.target_dir / "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        return project

    def fake_run(*args: Any, **kwargs: Any) -> Any:
        return subprocess.CompletedProcess(
            args=args[0] if args else [],
            returncode=0,
            stdout="",
            stderr="",
        )

    with patch(
        "app.services.dbt_parse_validator.create_controlled_dbt_project",
        side_effect=create_with_extra_model,
    ):
        with patch(
            "app.services.dbt_parse_validator.subprocess.run",
            side_effect=fake_run,
        ):
            result = run_dbt_parse_check(_input())
    assert result.execution_status == CheckExecutionStatus.ERROR.value
    assert result.evidence[0].code == "dbt_manifest_verification_error"


def test_project_setup_failure_is_error() -> None:
    with patch(
        "app.services.dbt_parse_validator.create_controlled_dbt_project",
        side_effect=OSError("disk full secret"),
    ):
        result = run_dbt_parse_check(_input())
    assert result.execution_status == CheckExecutionStatus.ERROR.value
    assert result.outcome is None
    assert result.evidence[0].code == "dbt_project_setup_error"
    serialized = json.dumps(result.model_dump(mode="json"))
    assert "disk full" not in serialized
    assert "secret" not in serialized


# ---- Privacy -----------------------------------------------------------------


def test_raw_sql_not_in_serialized_result() -> None:
    result = run_dbt_parse_check(_input(model_sql=SECRET_SQL))
    serialized = json.dumps(result.model_dump(mode="json"))
    assert SECRET_SQL not in serialized
    assert "secret_column_xyz" not in serialized


def test_stdout_stderr_not_in_result() -> None:
    def fake_run(*args: Any, **kwargs: Any) -> Any:
        return subprocess.CompletedProcess(
            args=args[0] if args else [],
            returncode=2,
            stdout="STDOUT_LEAK_TOKEN",
            stderr="STDERR_LEAK_TOKEN",
        )

    with patch(
        "app.services.dbt_parse_validator.subprocess.run",
        side_effect=fake_run,
    ):
        result = run_dbt_parse_check(_input())
    serialized = json.dumps(result.model_dump(mode="json"))
    assert "STDOUT_LEAK_TOKEN" not in serialized
    assert "STDERR_LEAK_TOKEN" not in serialized


def test_temporary_path_not_in_result() -> None:
    result = run_dbt_parse_check(_input())
    serialized = json.dumps(result.model_dump(mode="json")).lower()
    assert "appdata" not in serialized
    assert "temp\\" not in serialized
    assert "riftless_dbt_" not in serialized
    assert "c:\\users" not in serialized


def test_simulated_exception_message_not_leaked() -> None:
    with patch(
        "app.services.dbt_parse_validator.create_controlled_dbt_project",
        side_effect=RuntimeError("boom_exception_secret_xyz"),
    ):
        result = run_dbt_parse_check(_input())
    serialized = json.dumps(result.model_dump(mode="json"))
    assert "boom_exception_secret_xyz" not in serialized
    assert "RuntimeError" not in serialized


def test_environment_secrets_not_forwarded() -> None:
    root = Path(os.environ.get("TEMP", ".")) / "riftless_env_probe"
    root.mkdir(exist_ok=True)
    try:
        scripts = Path(
            __import__("sys").executable
        ).resolve().parent
        env = build_sanitized_env(tmp_root=root, scripts_dir=scripts)
        forbidden_keys = {
            "RIFTLESS_API_KEY",
            "GITHUB_TOKEN",
            "DATAHUB_TOKEN",
            "DEEPSEEK_API_KEY",
            "GEMINI_API_KEY",
            "OPENAI_API_KEY",
            "VITE_SECRET",
        }
        for key in forbidden_keys:
            assert key not in env
        # Parent secrets must not be copied even if present.
        with patch.dict(
            os.environ,
            {"RIFTLESS_API_KEY": "secret", "GITHUB_TOKEN": "ghp_x"},
            clear=False,
        ):
            env2 = build_sanitized_env(tmp_root=root, scripts_dir=scripts)
            assert "RIFTLESS_API_KEY" not in env2
            assert "GITHUB_TOKEN" not in env2
            assert env2.get("DBT_SEND_ANONYMOUS_USAGE_STATS") == "False"
            assert env2.get("DO_NOT_TRACK") == "1"
    finally:
        import shutil

        shutil.rmtree(root, ignore_errors=True)


# ---- Cleanup -----------------------------------------------------------------


def test_temp_dir_removed_after_success() -> None:
    created: list[Path] = []
    real_create = create_controlled_dbt_project

    def tracking_create(**kwargs: Any) -> Any:
        project = real_create(**kwargs)
        created.append(project.root_dir)
        return project

    with patch(
        "app.services.dbt_parse_validator.create_controlled_dbt_project",
        side_effect=tracking_create,
    ):
        result = run_dbt_parse_check(_input())
    assert result.outcome == CheckOutcome.PASS.value
    assert created
    assert not created[0].exists()


def test_temp_dir_removed_after_nonzero_process_exit() -> None:
    created: list[Path] = []
    real_create = create_controlled_dbt_project

    def tracking_create(**kwargs: Any) -> Any:
        project = real_create(**kwargs)
        created.append(project.root_dir)
        return project

    def fake_run(*args: Any, **kwargs: Any) -> Any:
        return subprocess.CompletedProcess(
            args=args[0] if args else [],
            returncode=1,
            stdout="",
            stderr="",
        )

    with patch(
        "app.services.dbt_parse_validator.create_controlled_dbt_project",
        side_effect=tracking_create,
    ):
        with patch(
            "app.services.dbt_parse_validator.subprocess.run",
            side_effect=fake_run,
        ):
            result = run_dbt_parse_check(_input())
    assert result.execution_status == CheckExecutionStatus.ERROR.value
    assert result.outcome is None
    assert result.evidence[0].code == "dbt_parse_process_failed"
    assert created
    assert not created[0].exists()


def test_temp_dir_removed_after_timeout() -> None:
    created: list[Path] = []
    real_create = create_controlled_dbt_project

    def tracking_create(**kwargs: Any) -> Any:
        project = real_create(**kwargs)
        created.append(project.root_dir)
        return project

    with patch(
        "app.services.dbt_parse_validator.create_controlled_dbt_project",
        side_effect=tracking_create,
    ):
        with patch(
            "app.services.dbt_parse_validator.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["dbt"], timeout=60),
        ):
            result = run_dbt_parse_check(_input())
    assert result.evidence[0].code == "dbt_execution_timeout"
    assert created
    assert not created[0].exists()


def test_temp_dir_removed_after_unexpected_error() -> None:
    created: list[Path] = []
    real_create = create_controlled_dbt_project

    def tracking_create(**kwargs: Any) -> Any:
        project = real_create(**kwargs)
        created.append(project.root_dir)
        return project

    with patch(
        "app.services.dbt_parse_validator.create_controlled_dbt_project",
        side_effect=tracking_create,
    ):
        with patch(
            "app.services.dbt_parse_validator.subprocess.run",
            side_effect=RuntimeError("unexpected"),
        ):
            result = run_dbt_parse_check(_input())
    assert result.execution_status == CheckExecutionStatus.ERROR.value
    assert created
    assert not created[0].exists()


# ---- Safety ------------------------------------------------------------------


def test_telemetry_disabled_in_env() -> None:
    root = Path(os.environ.get("TEMP", ".")) / "riftless_tel_probe"
    root.mkdir(exist_ok=True)
    try:
        scripts = Path(
            __import__("sys").executable
        ).resolve().parent
        env = build_sanitized_env(tmp_root=root, scripts_dir=scripts)
        assert env["DBT_SEND_ANONYMOUS_USAGE_STATS"] == "False"
        assert env["DO_NOT_TRACK"] == "1"
        assert env["DBT_NO_TRACKING"] == "1"
    finally:
        import shutil

        shutil.rmtree(root, ignore_errors=True)


def test_no_package_retrieval_or_checkout_in_source() -> None:
    source = Path(
        __import__(
            "app.services.dbt_parse_validator", fromlist=["__file__"]
        ).__file__
    ).read_text(encoding="utf-8")
    project_source = Path(
        __import__(
            "app.utils.controlled_dbt_project", fromlist=["__file__"]
        ).__file__
    ).read_text(encoding="utf-8")
    combined = source + project_source
    assert "packages.yml" not in combined or "packages.yml" in project_source
    # packages.yml is only mentioned to assert absence
    assert "git clone" not in combined.lower()
    assert "github.com" not in combined.lower()
    assert "dbt deps" not in combined.lower()


def test_no_persistent_duckdb_in_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.iterdir())
    run_dbt_parse_check(_input())
    after = set(tmp_path.iterdir())
    created = after - before
    for path in created:
        assert path.suffix.lower() not in {".db", ".duckdb", ".wal"}


def test_no_network_or_shell_interpolation_in_source() -> None:
    source = Path(
        __import__(
            "app.services.dbt_parse_validator", fromlist=["__file__"]
        ).__file__
    ).read_text(encoding="utf-8")
    assert "shell=False" in source or "shell=false" in source.lower()
    assert "shell=True" not in source
    for token in ("socket", "urllib", "httpx", "requests"):
        assert f"import {token}" not in source
        assert f"from {token}" not in source


# ---- Determinism -------------------------------------------------------------


def test_same_input_same_semantic_result_except_check_id() -> None:
    parse_input = _input()
    a = run_dbt_parse_check(parse_input)
    b = run_dbt_parse_check(parse_input)
    assert a.check_id != b.check_id
    da = a.model_dump(mode="json")
    db = b.model_dump(mode="json")
    da.pop("check_id")
    db.pop("check_id")
    assert da == db


def test_input_not_mutated() -> None:
    parse_input = _input(model_sql=SECRET_SQL)
    snapshot = copy.deepcopy(parse_input)
    run_dbt_parse_check(parse_input)
    assert parse_input.model_dump() == snapshot.model_dump()


# ---- F6.1 aggregation --------------------------------------------------------


def test_pass_aggregates_to_pass() -> None:
    check = run_dbt_parse_check(_input(required=True))
    artifact = build_validation_artifact(
        subject_fingerprint=SUBJECT_FP, checks=[check]
    )
    assert artifact.execution_status == OverallExecutionStatus.COMPLETED.value
    assert artifact.outcome == CheckOutcome.PASS.value


def test_required_nonzero_process_aggregates_to_inconclusive() -> None:
    """Non-zero dbt exit is ERROR (not FAIL); overall outcome stays INCONCLUSIVE."""

    def fake_run(*args: Any, **kwargs: Any) -> Any:
        return subprocess.CompletedProcess(
            args=args[0] if args else [],
            returncode=1,
            stdout="",
            stderr="",
        )

    with patch(
        "app.services.dbt_parse_validator.subprocess.run",
        side_effect=fake_run,
    ):
        check = run_dbt_parse_check(_input(required=True))
    assert check.execution_status == CheckExecutionStatus.ERROR.value
    assert check.outcome is None
    artifact = build_validation_artifact(
        subject_fingerprint=SUBJECT_FP, checks=[check]
    )
    assert artifact.outcome == CheckOutcome.INCONCLUSIVE.value
    assert artifact.execution_status == OverallExecutionStatus.EXECUTION_FAILED.value


def test_unavailable_aggregates_to_inconclusive() -> None:
    with patch(
        "app.services.dbt_parse_validator.resolve_dbt_executable",
        return_value=None,
    ):
        check = run_dbt_parse_check(_input(required=True))
    artifact = build_validation_artifact(
        subject_fingerprint=SUBJECT_FP, checks=[check]
    )
    assert artifact.outcome == CheckOutcome.INCONCLUSIVE.value
    assert artifact.execution_status == OverallExecutionStatus.NOT_RUN.value


def test_optional_process_error_does_not_override_required_pass() -> None:
    required_pass = run_dbt_parse_check(_input(required=True))

    def fake_run(*args: Any, **kwargs: Any) -> Any:
        return subprocess.CompletedProcess(
            args=args[0] if args else [],
            returncode=1,
            stdout="",
            stderr="",
        )

    with patch(
        "app.services.dbt_parse_validator.subprocess.run",
        side_effect=fake_run,
    ):
        optional_error = run_dbt_parse_check(_input(required=False))
    assert optional_error.execution_status == CheckExecutionStatus.ERROR.value
    artifact = build_validation_artifact(
        subject_fingerprint=SUBJECT_FP,
        checks=[required_pass, optional_error],
    )
    assert artifact.outcome == CheckOutcome.PASS.value
    assert artifact.execution_status == OverallExecutionStatus.PARTIAL.value


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
    assert not any("dbt" in path for path in paths)
