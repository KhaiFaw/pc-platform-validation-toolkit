import hashlib
import sqlite3
from pathlib import Path

import pytest

from platval.models.plan import TestPlan as PlanModel
from platval.persistence import (
    ArtifactError,
    BaselineSourceError,
    RunNotFoundError,
    SchemaVersionError,
    SQLiteRepository,
    delete_run_recoverably,
    persist_execution,
)
from platval.runner import run_validation_plan


def make_execution(tmp_path: Path):  # type: ignore[no-untyped-def]
    plan = PlanModel.model_validate(
        {
            "name": "persistence-test",
            "sampling_interval_seconds": 0.05,
            "tests": [
                {
                    "id": "INV-001",
                    "name": "Inventory",
                    "category": "inventory",
                    "timeout_seconds": 2,
                    "requirements": [
                        {
                            "metric": "logical_cpu_count",
                            "operator": "greater_than",
                            "expected": 0,
                        }
                    ],
                }
            ],
        }
    )
    return run_validation_plan(plan, runtime_directory=tmp_path / "execution-runtime")


def test_persisted_execution_round_trips_and_normalizes(tmp_path: Path) -> None:
    execution = make_execution(tmp_path)
    runtime = tmp_path / "store"
    artifact = persist_execution(execution, runtime_directory=runtime)
    repository = SQLiteRepository(runtime / "platval.db")
    stored = repository.get_run(execution.run.run_id)

    artifact_path = runtime / artifact.relative_path
    assert artifact_path.is_file()
    assert hashlib.sha256(artifact_path.read_bytes()).hexdigest() == artifact.sha256
    assert stored.execution.model_dump(mode="json") == execution.model_dump(mode="json")
    assert stored.artifacts == [artifact]
    assert repository.list_runs()[0].run_id == execution.run.run_id

    with sqlite3.connect(runtime / "platval.db") as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "platforms",
                "runs",
                "test_results",
                "metrics",
                "requirement_evaluations",
                "telemetry_samples",
                "artifacts",
            )
        }
    assert counts["platforms"] == 1
    assert counts["runs"] == 1
    assert counts["test_results"] == 1
    assert counts["metrics"] > 0
    assert counts["requirement_evaluations"] == 1
    assert counts["telemetry_samples"] > 0
    assert counts["artifacts"] == 1


def test_artifact_store_refuses_overwrite(tmp_path: Path) -> None:
    execution = make_execution(tmp_path)
    runtime = tmp_path / "store"
    persist_execution(execution, runtime_directory=runtime)
    with pytest.raises(ArtifactError, match="refusing to overwrite"):
        persist_execution(execution, runtime_directory=runtime)


def test_recoverable_delete_removes_rows_and_moves_artifacts(tmp_path: Path) -> None:
    execution = make_execution(tmp_path)
    runtime = tmp_path / "store"
    artifact = persist_execution(execution, runtime_directory=runtime)
    original = runtime / artifact.relative_path
    archived = delete_run_recoverably(execution.run.run_id, runtime_directory=runtime)
    assert archived is not None
    assert archived.is_dir()
    assert not original.exists()
    assert (archived / "run.json").is_file()
    with pytest.raises(RunNotFoundError):
        SQLiteRepository(runtime / "platval.db").get_run(execution.run.run_id)


def test_baseline_source_is_protected_from_deletion(tmp_path: Path) -> None:
    execution = make_execution(tmp_path)
    runtime = tmp_path / "store"
    persist_execution(execution, runtime_directory=runtime)
    with sqlite3.connect(runtime / "platval.db") as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "INSERT INTO baselines(name, source_run_id, created_at) VALUES (?, ?, ?)",
            ("known-good", execution.run.run_id, execution.run.ended_at.isoformat()),
        )
    with pytest.raises(BaselineSourceError, match="known-good"):
        SQLiteRepository(runtime / "platval.db").delete_run(execution.run.run_id)


def test_incompatible_schema_is_rejected(tmp_path: Path) -> None:
    database = tmp_path / "platval.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE schema_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO schema_metadata(key, value) VALUES ('schema_version', '99')"
        )
    with pytest.raises(SchemaVersionError, match="incompatible"):
        SQLiteRepository(database).initialize()
