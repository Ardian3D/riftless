"""Server-controlled temporary dbt project builder (phase F6.4).

Creates a minimal dbt project and DuckDB profile under a temporary directory.
Caller never supplies paths, profiles, packages, or macros.
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

PROJECT_NAME = "riftless_validation"
PROFILE_NAME = "riftless_validation"
ADAPTER_NAME = "duckdb"
MATERIALIZATION = "view"


@dataclass(frozen=True)
class ControlledDbtProject:
    """Paths for one isolated temporary dbt project."""

    root_dir: Path
    project_dir: Path
    profiles_dir: Path
    models_dir: Path
    target_dir: Path
    log_dir: Path
    model_name: str
    model_sql_path: Path

    def allowed_project_files(self) -> set[Path]:
        """Expected allowlisted file paths under the project (not directories)."""
        return {
            self.project_dir / "dbt_project.yml",
            self.models_dir / f"{self.model_name}.sql",
            self.profiles_dir / "profiles.yml",
        }

    def cleanup(self) -> None:
        """Remove the entire temporary root if it still exists."""
        if self.root_dir.exists():
            shutil.rmtree(self.root_dir, ignore_errors=True)


def create_controlled_dbt_project(*, model_name: str, model_sql: str) -> ControlledDbtProject:
    """Create a new temporary controlled dbt project for one check.

    Layout::

        <root>/
          project/
            dbt_project.yml
            models/<model_name>.sql
            target/
            logs/
          profiles/
            profiles.yml
    """
    root = Path(tempfile.mkdtemp(prefix="riftless_dbt_"))
    try:
        project_dir = root / "project"
        profiles_dir = root / "profiles"
        models_dir = project_dir / "models"
        target_dir = project_dir / "target"
        log_dir = project_dir / "logs"
        for path in (models_dir, target_dir, log_dir, profiles_dir):
            path.mkdir(parents=True, exist_ok=True)

        dbt_project = (
            f"name: {PROJECT_NAME}\n"
            f"version: '1.0.0'\n"
            f"config-version: 2\n"
            f"profile: {PROFILE_NAME}\n"
            f"model-paths: ['models']\n"
            f"target-path: 'target'\n"
            f"log-path: 'logs'\n"
            f"clean-targets: ['target', 'logs']\n"
            f"models:\n"
            f"  {PROJECT_NAME}:\n"
            f"    +materialized: {MATERIALIZATION}\n"
        )
        (project_dir / "dbt_project.yml").write_text(dbt_project, encoding="utf-8")

        # Isolated DuckDB target — in-memory only; no user database path.
        profiles = (
            f"{PROFILE_NAME}:\n"
            f"  target: parse\n"
            f"  outputs:\n"
            f"    parse:\n"
            f"      type: {ADAPTER_NAME}\n"
            f"      path: ':memory:'\n"
            f"      threads: 1\n"
        )
        (profiles_dir / "profiles.yml").write_text(profiles, encoding="utf-8")

        model_path = models_dir / f"{model_name}.sql"
        # Write model SQL exactly as supplied (already validated as plain SQL).
        model_path.write_text(model_sql, encoding="utf-8", newline="\n")

        # Hard guarantees: no packages / macros / seeds scaffolding.
        forbidden = [
            project_dir / "packages.yml",
            project_dir / "dependencies.yml",
            project_dir / "macros",
            project_dir / "seeds",
            project_dir / "snapshots",
            project_dir / "analyses",
            project_dir / "tests",
        ]
        for path in forbidden:
            if path.exists():
                raise RuntimeError("controlled project contains forbidden path")

        return ControlledDbtProject(
            root_dir=root,
            project_dir=project_dir,
            profiles_dir=profiles_dir,
            models_dir=models_dir,
            target_dir=target_dir,
            log_dir=log_dir,
            model_name=model_name,
            model_sql_path=model_path,
        )
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
