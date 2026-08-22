"""Canonical JSON artifacts and recoverable run deletion."""

import hashlib
import os
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from platval.persistence.repository import ArtifactRecord, SQLiteRepository, StoredRun
from platval.runner.engine import RunExecution


class ArtifactError(RuntimeError):
    """Artifact paths or filesystem operations violated the local store contract."""


def _validated_run_id(run_id: str) -> str:
    try:
        parsed = uuid.UUID(run_id)
    except ValueError:
        raise ArtifactError("run ID is not a canonical UUID") from None
    canonical = str(parsed)
    if canonical != run_id:
        raise ArtifactError("run ID is not a canonical UUID")
    return canonical


def _run_directory(runtime_directory: Path, run_id: str) -> Path:
    safe_id = _validated_run_id(run_id)
    runs_root = (runtime_directory.resolve() / "runs").resolve()
    candidate = (runs_root / safe_id).resolve()
    if candidate.parent != runs_root:
        raise ArtifactError("resolved run directory escaped the runtime runs directory")
    return candidate


def persist_execution(
    execution: RunExecution,
    *,
    runtime_directory: Path,
    repository: SQLiteRepository | None = None,
) -> ArtifactRecord:
    """Write canonical JSON atomically, then commit normalized database evidence."""
    runtime = runtime_directory.resolve()
    run_directory = _run_directory(runtime, execution.run.run_id)
    if run_directory.exists():
        raise ArtifactError("run artifact directory already exists; refusing to overwrite it")
    run_directory.mkdir(parents=True)
    artifact_path = run_directory / "run.json"
    temporary_path = run_directory / "run.json.tmp"
    payload = (execution.model_dump_json(indent=2) + "\n").encode("utf-8")
    try:
        with temporary_path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, artifact_path)
        relative_path = artifact_path.relative_to(runtime).as_posix()
        artifact = ArtifactRecord(
            kind="run_json",
            relative_path=relative_path,
            sha256=hashlib.sha256(payload).hexdigest(),
            size_bytes=len(payload),
        )
        active_repository = repository or SQLiteRepository(runtime / "platval.db")
        active_repository.save_execution(execution, [artifact])
        return artifact
    except BaseException:
        if run_directory.exists():
            shutil.rmtree(run_directory)
        raise


def load_stored_run(run_id: str, *, runtime_directory: Path) -> StoredRun:
    repository = SQLiteRepository(runtime_directory.resolve() / "platval.db")
    return repository.get_run(run_id)


def delete_run_recoverably(run_id: str, *, runtime_directory: Path) -> Path | None:
    """Delete normalized rows and move owned artifacts into local trash."""
    runtime = runtime_directory.resolve()
    source = _run_directory(runtime, run_id)
    repository = SQLiteRepository(runtime / "platval.db")
    repository.delete_run(run_id)
    if not source.exists():
        return None
    trash_root = (runtime / "trash").resolve()
    trash_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    destination = (trash_root / f"{run_id}-{stamp}").resolve()
    if destination.parent != trash_root:
        raise ArtifactError("resolved trash path escaped the runtime trash directory")
    shutil.move(str(source), str(destination))
    return destination
