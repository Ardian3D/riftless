"""Controlled dbt project parse validator (phase F6.4).

Runs allowlisted ``dbt parse`` against a server-generated temporary project.
Never executes dbt run/build/test, never accepts caller paths/commands/Jinja,
and never returns raw SQL, stdout/stderr, or temporary paths in evidence.

This is **not** a SQL grammar validator (see F6.2 / SQLGlot). PASS only means
the controlled project was discovered, configuration was parsed, and the
expected model was registered in the manifest. Generic non-zero process exits
are classified as execution ERROR, not caller validation FAIL.
"""

from __future__ import annotations

import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

from app.schemas.dbt_validation import DbtParseInput
from app.schemas.validation import (
    CheckExecutionStatus,
    CheckKind,
    CheckOutcome,
    ValidationCheckResult,
    ValidationEvidence,
)
from app.utils.controlled_dbt_project import (
    ADAPTER_NAME,
    PROJECT_NAME,
    ControlledDbtProject,
    create_controlled_dbt_project,
)

# Scope: server-controlled project discovery, config parse, and expected model
# registration in the manifest only. Not a SQL grammar or execution check.
DBT_PARSE_SCOPE = "dbt_server_generated_project_manifest_parse"
ENGINE_NAME = "dbt-core"
ALLOWED_COMMAND = "parse"
DBT_TIMEOUT_SECONDS = 60

_SUMMARY_PASS = "The controlled dbt project was parsed successfully."
_SUMMARY_PROCESS_FAILED = "dbt validation execution did not complete."
_SUMMARY_TIMEOUT = "The dbt parse operation exceeded the execution time limit."
_SUMMARY_UNAVAILABLE = "The required dbt validation engine was not available."
_SUMMARY_ERROR = "dbt validation execution did not complete."


def get_dbt_core_version() -> str:
    """Return installed dbt-core package version."""
    return importlib.metadata.version("dbt-core")


def get_dbt_duckdb_version() -> str:
    """Return installed dbt-duckdb package version."""
    return importlib.metadata.version("dbt-duckdb")


def resolve_dbt_executable() -> Path | None:
    """Resolve the dbt CLI from the current backend virtual environment.

    Prefers ``dbt.exe`` / ``dbt`` next to ``sys.executable``. Does not rely on
    an unrelated global install.
    """
    scripts_dir = Path(sys.executable).resolve().parent
    for name in ("dbt.exe", "dbt"):
        candidate = scripts_dir / name
        if candidate.is_file():
            return candidate
    which = shutil.which("dbt", path=str(scripts_dir))
    if which:
        path = Path(which)
        if path.is_file():
            return path
    return None


def build_sanitized_env(*, tmp_root: Path, scripts_dir: Path) -> dict[str, str]:
    """Build a minimal process environment for dbt (no RIFTLESS secrets).

    Does not copy the full parent environment. Telemetry is disabled.
    """
    env: dict[str, str] = {}

    system_root = (
        os.environ.get("SYSTEMROOT")
        or os.environ.get("SystemRoot")
        or os.environ.get("WINDIR")
        or r"C:\Windows"
    )
    env["SYSTEMROOT"] = system_root
    env["SystemRoot"] = system_root
    env["WINDIR"] = os.environ.get("WINDIR", system_root)
    env["COMSPEC"] = os.environ.get(
        "COMSPEC", str(Path(system_root) / "System32" / "cmd.exe")
    )
    env["PATHEXT"] = os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD;.VBS;.JS")
    if "NUMBER_OF_PROCESSORS" in os.environ:
        env["NUMBER_OF_PROCESSORS"] = os.environ["NUMBER_OF_PROCESSORS"]
    if "PROCESSOR_ARCHITECTURE" in os.environ:
        env["PROCESSOR_ARCHITECTURE"] = os.environ["PROCESSOR_ARCHITECTURE"]

    path_parts = [
        str(scripts_dir),
        str(Path(system_root) / "System32"),
        str(Path(system_root) / "System32" / "WindowsPowerShell" / "v1.0"),
        system_root,
    ]
    env["PATH"] = os.pathsep.join(path_parts)

    os_temp = tmp_root / "os_temp"
    home = tmp_root / "home"
    os_temp.mkdir(parents=True, exist_ok=True)
    home.mkdir(parents=True, exist_ok=True)
    env["TEMP"] = str(os_temp)
    env["TMP"] = str(os_temp)
    env["TMPDIR"] = str(os_temp)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["APPDATA"] = str(home / "AppData" / "Roaming")
    env["LOCALAPPDATA"] = str(home / "AppData" / "Local")
    (home / "AppData" / "Roaming").mkdir(parents=True, exist_ok=True)
    (home / "AppData" / "Local").mkdir(parents=True, exist_ok=True)

    # Disable dbt / generic anonymous telemetry.
    env["DO_NOT_TRACK"] = "1"
    env["DBT_SEND_ANONYMOUS_USAGE_STATS"] = "False"
    env["DBT_NO_TRACKING"] = "1"

    # Explicitly omit: API keys, GitHub/DataHub/DeepSeek/Gemini tokens,
    # VITE_*, arbitrary RIFTLESS secrets, full parent env dump.
    return env


def build_dbt_parse_command(
    *,
    dbt_executable: Path,
    project: ControlledDbtProject,
) -> list[str]:
    """Return the allowlisted ``dbt parse`` argv list (shell=False)."""
    return [
        str(dbt_executable),
        ALLOWED_COMMAND,
        "--project-dir",
        str(project.project_dir),
        "--profiles-dir",
        str(project.profiles_dir),
        "--target-path",
        str(project.target_dir),
        "--log-path",
        str(project.log_dir),
        "--no-version-check",
        "--quiet",
    ]


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
        check_kind=CheckKind.DBT_VALIDATION,
        required=required,
        execution_status=execution_status,
        outcome=outcome,
        scope=DBT_PARSE_SCOPE,
        summary=summary,
        evidence=evidence,
        engine_name=ENGINE_NAME if engine_version is not None else ENGINE_NAME,
        engine_version=engine_version,
    )


def _adapter_details(**extra: Any) -> dict[str, Any]:
    details: dict[str, Any] = {
        "adapter_name": ADAPTER_NAME,
        "command": ALLOWED_COMMAND,
    }
    details.update(extra)
    return details


def _verify_manifest(
    project: ControlledDbtProject,
    *,
    expected_model_name: str,
) -> tuple[bool, str | None]:
    """Verify manifest exists and contains exactly one expected project model.

    Returns (ok, error_kind) where error_kind is a short internal category
    (never returned to the caller).
    """
    manifest_path = project.target_dir / "manifest.json"
    if not manifest_path.is_file():
        return False, "missing"

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False, "invalid"

    if not isinstance(payload, dict):
        return False, "invalid"

    nodes = payload.get("nodes")
    if not isinstance(nodes, dict):
        return False, "invalid"

    project_models: list[dict[str, Any]] = []
    for node_id, node in nodes.items():
        if not isinstance(node, dict):
            continue
        if node.get("resource_type") != "model":
            continue
        # Only models belonging to the controlled project.
        if not str(node_id).startswith(f"model.{PROJECT_NAME}."):
            # Unexpected model package → treat as verification error.
            if str(node_id).startswith("model."):
                return False, "unexpected"
            continue
        project_models.append(node)

    if len(project_models) != 1:
        return False, "unexpected"

    model = project_models[0]
    if model.get("name") != expected_model_name:
        return False, "unexpected"

    return True, None


def run_dbt_parse_check(parse_input: DbtParseInput) -> ValidationCheckResult:
    """Run controlled dbt parse and return a ValidationCheckResult.

    Never mutates the input. Never returns raw SQL, stdout/stderr, temp paths,
    or exception messages in the result surface.
    """
    required = bool(parse_input.required)
    engine_version: str | None
    try:
        engine_version = get_dbt_core_version()
    except importlib.metadata.PackageNotFoundError:
        engine_version = None

    dbt_executable = resolve_dbt_executable()
    if dbt_executable is None or engine_version is None:
        return _result(
            required=required,
            execution_status=CheckExecutionStatus.UNAVAILABLE,
            outcome=None,
            summary=_SUMMARY_UNAVAILABLE,
            evidence=[
                _evidence(
                    code="dbt_engine_unavailable",
                    message="The required dbt validation engine was not available.",
                    details={"adapter_name": ADAPTER_NAME},
                )
            ],
            engine_version=engine_version,
        )

    # Confirm adapter package is importable/installed.
    try:
        get_dbt_duckdb_version()
    except importlib.metadata.PackageNotFoundError:
        return _result(
            required=required,
            execution_status=CheckExecutionStatus.UNAVAILABLE,
            outcome=None,
            summary=_SUMMARY_UNAVAILABLE,
            evidence=[
                _evidence(
                    code="dbt_engine_unavailable",
                    message="The required dbt validation engine was not available.",
                    details={"adapter_name": ADAPTER_NAME},
                )
            ],
            engine_version=engine_version,
        )

    project: ControlledDbtProject | None = None
    try:
        try:
            project = create_controlled_dbt_project(
                model_name=parse_input.model_name,
                model_sql=parse_input.model_sql,
            )
        except Exception:
            return _result(
                required=required,
                execution_status=CheckExecutionStatus.ERROR,
                outcome=None,
                summary=_SUMMARY_ERROR,
                evidence=[
                    _evidence(
                        code="dbt_project_setup_error",
                        message=(
                            "The controlled dbt project could not be prepared "
                            "for validation."
                        ),
                        details={"adapter_name": ADAPTER_NAME},
                    )
                ],
                engine_version=engine_version,
            )

        scripts_dir = Path(sys.executable).resolve().parent
        env = build_sanitized_env(tmp_root=project.root_dir, scripts_dir=scripts_dir)
        command = build_dbt_parse_command(
            dbt_executable=dbt_executable,
            project=project,
        )

        # Safety: only allowlisted command verb.
        if len(command) < 2 or command[1] != ALLOWED_COMMAND:
            return _result(
                required=required,
                execution_status=CheckExecutionStatus.ERROR,
                outcome=None,
                summary=_SUMMARY_ERROR,
                evidence=[
                    _evidence(
                        code="dbt_execution_error",
                        message=(
                            "The dbt validation engine could not complete the check."
                        ),
                        details={"adapter_name": ADAPTER_NAME},
                    )
                ],
                engine_version=engine_version,
            )

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                env=env,
                shell=False,
                timeout=DBT_TIMEOUT_SECONDS,
                cwd=str(project.root_dir),
                check=False,
            )
        except subprocess.TimeoutExpired:
            return _result(
                required=required,
                execution_status=CheckExecutionStatus.ERROR,
                outcome=None,
                summary=_SUMMARY_TIMEOUT,
                evidence=[
                    _evidence(
                        code="dbt_execution_timeout",
                        message=(
                            "The dbt parse operation exceeded the execution time limit."
                        ),
                        details=_adapter_details(),
                    )
                ],
                engine_version=engine_version,
            )
        except FileNotFoundError:
            return _result(
                required=required,
                execution_status=CheckExecutionStatus.UNAVAILABLE,
                outcome=None,
                summary=_SUMMARY_UNAVAILABLE,
                evidence=[
                    _evidence(
                        code="dbt_engine_unavailable",
                        message=(
                            "The required dbt validation engine was not available."
                        ),
                        details={"adapter_name": ADAPTER_NAME},
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
                        code="dbt_execution_error",
                        message=(
                            "The dbt validation engine could not complete the check."
                        ),
                        details={"adapter_name": ADAPTER_NAME},
                    )
                ],
                engine_version=engine_version,
            )

        # stdout/stderr captured for internal classification only — never returned.
        _ = completed.stdout
        _ = completed.stderr

        if completed.returncode != 0:
            # Conservative classification: a non-zero dbt exit is an execution
            # problem for the controlled process, not a proven caller-input
            # validation failure. stdout/stderr are not inspected or returned.
            return _result(
                required=required,
                execution_status=CheckExecutionStatus.ERROR,
                outcome=None,
                summary=_SUMMARY_PROCESS_FAILED,
                evidence=[
                    _evidence(
                        code="dbt_parse_process_failed",
                        message=(
                            "The dbt parse process did not complete successfully."
                        ),
                        details=_adapter_details(),
                    )
                ],
                engine_version=engine_version,
            )

        ok, _kind = _verify_manifest(
            project, expected_model_name=parse_input.model_name
        )
        if not ok:
            return _result(
                required=required,
                execution_status=CheckExecutionStatus.ERROR,
                outcome=None,
                summary=_SUMMARY_ERROR,
                evidence=[
                    _evidence(
                        code="dbt_manifest_verification_error",
                        message=(
                            "The dbt manifest could not be verified for the "
                            "controlled project."
                        ),
                        details=_adapter_details(),
                    )
                ],
                engine_version=engine_version,
            )

        adapter_version: str | None
        try:
            adapter_version = get_dbt_duckdb_version()
        except importlib.metadata.PackageNotFoundError:
            adapter_version = None

        details = _adapter_details(
            model_count=1,
            expected_model_present=True,
        )
        if adapter_version is not None:
            details["adapter_version"] = adapter_version

        return _result(
            required=required,
            execution_status=CheckExecutionStatus.COMPLETED,
            outcome=CheckOutcome.PASS,
            summary=_SUMMARY_PASS,
            evidence=[
                _evidence(
                    code="dbt_parse_succeeded",
                    message=(
                        "dbt Core parsed the server-generated project and produced "
                        "the expected model manifest."
                    ),
                    details=details,
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
                    code="dbt_execution_error",
                    message=(
                        "The dbt validation engine could not complete the check."
                    ),
                    details={"adapter_name": ADAPTER_NAME},
                )
            ],
            engine_version=engine_version,
        )
    finally:
        if project is not None:
            project.cleanup()
