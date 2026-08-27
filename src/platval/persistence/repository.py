"""Transactional SQLite repository with normalized evidence tables."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from pydantic import Field, field_validator

from platval.models.common import DomainModel, require_aware_timestamp
from platval.models.platform import PlatformIdentity
from platval.models.results import RunResult
from platval.models.status import ResultStatus
from platval.models.telemetry import TelemetrySample
from platval.persistence.schema import SCHEMA_SQL, SCHEMA_VERSION
from platval.runner.engine import RunExecution


class PersistenceError(RuntimeError):
    """Base class for local repository failures."""


class SchemaVersionError(PersistenceError):
    """The database schema is newer or otherwise incompatible."""


class RunNotFoundError(PersistenceError):
    """The requested run ID is absent."""


class BaselineSourceError(PersistenceError):
    """A run is protected because a baseline references it."""


class BaselineNotFoundError(PersistenceError):
    """The requested baseline is absent."""


class BaselineExistsError(PersistenceError):
    """A baseline name is already registered and cannot be replaced."""


class ArtifactRecord(DomainModel):
    kind: str = Field(min_length=1, max_length=64)
    relative_path: str = Field(min_length=1, max_length=500)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class RunSummary(DomainModel):
    run_id: str
    plan_name: str
    started_at: datetime
    overall_status: ResultStatus
    platform_fingerprint: str

    _started_at_is_aware = field_validator("started_at")(require_aware_timestamp)


class StoredRun(DomainModel):
    execution: RunExecution
    artifacts: list[ArtifactRecord] = Field(default_factory=list)


class BaselineRecord(DomainModel):
    name: str
    source_run_id: str
    created_at: datetime
    platform_fingerprint: str
    plan_hash: str
    plan_name: str

    _created_at_is_aware = field_validator("created_at")(require_aware_timestamp)


class SQLiteRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path.resolve()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(self.database_path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            yield connection
            connection.commit()
        except sqlite3.Error as exc:
            if connection is not None:
                connection.rollback()
            raise PersistenceError(f"SQLite operation failed ({type(exc).__name__})") from None
        except BaseException:
            if connection is not None:
                connection.rollback()
            raise
        finally:
            if connection is not None:
                connection.close()

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_metadata "
                "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            row = connection.execute(
                "SELECT value FROM schema_metadata WHERE key = 'schema_version'"
            ).fetchone()
            if row is not None:
                try:
                    stored_version = int(row["value"])
                except ValueError:
                    raise SchemaVersionError("database schema version is not an integer") from None
                if stored_version != SCHEMA_VERSION:
                    raise SchemaVersionError(
                        f"database schema {stored_version} is incompatible "
                        f"with schema {SCHEMA_VERSION}"
                    )
            connection.executescript(SCHEMA_SQL)
            if row is None:
                connection.execute(
                    "INSERT INTO schema_metadata(key, value) VALUES ('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )

    def save_execution(
        self, execution: RunExecution, artifacts: list[ArtifactRecord] | None = None
    ) -> None:
        self.initialize()
        run = execution.run
        artifact_rows = artifacts or []
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            platform_cursor = connection.execute(
                """
                INSERT INTO platforms(fingerprint, snapshot_json, captured_at)
                VALUES (?, ?, ?)
                """,
                (
                    execution.platform.sanitized_platform_fingerprint,
                    execution.platform.model_dump_json(),
                    datetime.now(UTC).isoformat(),
                ),
            )
            connection.execute(
                """
                INSERT INTO runs(
                    run_id, plan_name, plan_hash, tool_version, platform_snapshot_id,
                    platform_fingerprint,
                    started_at, ended_at, overall_status, result_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.plan_name,
                    run.plan_hash,
                    run.tool_version,
                    platform_cursor.lastrowid,
                    run.platform_fingerprint,
                    run.started_at.isoformat(),
                    run.ended_at.isoformat(),
                    run.overall_status.value,
                    run.model_dump_json(),
                    datetime.now(UTC).isoformat(),
                ),
            )
            for result in run.test_results:
                connection.execute(
                    """
                    INSERT INTO test_results(
                        run_id, test_id, status, started_at, ended_at, duration_seconds,
                        failure_reason, exception_summary, injected, result_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run.run_id,
                        result.test_id,
                        result.status.value,
                        result.started_at.isoformat(),
                        result.ended_at.isoformat(),
                        result.duration_seconds,
                        result.failure_reason,
                        result.exception_summary,
                        int(result.injected),
                        result.model_dump_json(),
                    ),
                )

                for name, metric in result.measured_values.items():
                    connection.execute(
                        """
                        INSERT INTO metrics(run_id, test_id, name, value_json, unit, source)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            run.run_id,
                            result.test_id,
                            name,
                            json.dumps(metric.value, sort_keys=True),
                            metric.unit,
                            metric.source,
                        ),
                    )
                for index, evaluation in enumerate(result.requirements):
                    connection.execute(
                        """
                        INSERT INTO requirement_evaluations(
                            run_id, test_id, evaluation_index, metric, operator,
                            expected_json, actual_json, unit, passed, explanation
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            run.run_id,
                            result.test_id,
                            index,
                            evaluation.metric,
                            evaluation.operator,
                            json.dumps(evaluation.expected, sort_keys=True),
                            json.dumps(evaluation.actual, sort_keys=True),
                            evaluation.unit,
                            int(evaluation.passed),
                            evaluation.explanation,
                        ),
                    )
            for test_id, samples in execution.telemetry_samples.items():
                for index, sample in enumerate(samples):
                    connection.execute(
                        """
                        INSERT INTO telemetry_samples(
                            run_id, test_id, sample_index, elapsed_seconds, timestamp, sample_json
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            run.run_id,
                            test_id,
                            index,
                            sample.elapsed_seconds,
                            sample.timestamp.isoformat(),
                            sample.model_dump_json(),
                        ),
                    )
            for artifact in artifact_rows:
                connection.execute(
                    """
                    INSERT INTO artifacts(run_id, kind, relative_path, sha256, size_bytes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        run.run_id,
                        artifact.kind,
                        artifact.relative_path,
                        artifact.sha256,
                        artifact.size_bytes,
                    ),
                )

    def add_artifact(self, run_id: str, artifact: ArtifactRecord) -> None:
        """Register one immutable derived artifact for an existing run."""
        self.initialize()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            run_row = connection.execute(
                "SELECT 1 FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if run_row is None:
                raise RunNotFoundError(f"run {run_id!r} was not found")
            connection.execute(
                """
                INSERT INTO artifacts(run_id, kind, relative_path, sha256, size_bytes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    artifact.kind,
                    artifact.relative_path,
                    artifact.sha256,
                    artifact.size_bytes,
                ),
            )

    def get_run(self, run_id: str) -> StoredRun:
        self.initialize()
        with self._connection() as connection:
            row = connection.execute(
                "SELECT result_json, platform_snapshot_id FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if row is None:
                raise RunNotFoundError(f"run {run_id!r} was not found")
            platform_row = connection.execute(
                "SELECT snapshot_json FROM platforms WHERE snapshot_id = ?",
                (row["platform_snapshot_id"],),
            ).fetchone()
            if platform_row is None:
                raise PersistenceError("run references a missing platform snapshot")
            telemetry_rows = connection.execute(
                """
                SELECT test_id, sample_json FROM telemetry_samples
                WHERE run_id = ? ORDER BY test_id, sample_index
                """,
                (run_id,),
            ).fetchall()
            artifact_rows = connection.execute(
                """
                SELECT kind, relative_path, sha256, size_bytes FROM artifacts
                WHERE run_id = ? ORDER BY relative_path
                """,
                (run_id,),
            ).fetchall()

        run_result = RunResult.model_validate_json(row["result_json"])
        telemetry: dict[str, list[TelemetrySample]] = {
            result.test_id: [] for result in run_result.test_results
        }
        for telemetry_row in telemetry_rows:
            telemetry.setdefault(telemetry_row["test_id"], []).append(
                TelemetrySample.model_validate_json(telemetry_row["sample_json"])
            )
        return StoredRun(
            execution=RunExecution(
                run=run_result,
                platform=PlatformIdentity.model_validate_json(platform_row["snapshot_json"]),
                telemetry_samples=telemetry,
            ),
            artifacts=[ArtifactRecord.model_validate(dict(item)) for item in artifact_rows],
        )

    def list_runs(self, *, limit: int = 50) -> list[RunSummary]:
        if limit < 1 or limit > 1000:
            raise ValueError("run list limit must be between 1 and 1000")
        self.initialize()
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT run_id, plan_name, started_at, overall_status, platform_fingerprint
                FROM runs ORDER BY started_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            RunSummary(
                run_id=row["run_id"],
                plan_name=row["plan_name"],
                started_at=datetime.fromisoformat(row["started_at"]),
                overall_status=ResultStatus(row["overall_status"]),
                platform_fingerprint=row["platform_fingerprint"],
            )
            for row in rows
        ]

    def create_baseline(self, name: str, source_run_id: str) -> BaselineRecord:
        """Create an immutable named pointer to a known-good source run."""
        self.initialize()
        created_at = datetime.now(UTC)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT 1 FROM baselines WHERE name = ?", (name,)).fetchone():
                raise BaselineExistsError(f"baseline {name!r} already exists and was not replaced")
            source = connection.execute(
                """
                SELECT platform_fingerprint, plan_hash, plan_name
                FROM runs WHERE run_id = ?
                """,
                (source_run_id,),
            ).fetchone()
            if source is None:
                raise RunNotFoundError(f"run {source_run_id!r} was not found")
            connection.execute(
                "INSERT INTO baselines(name, source_run_id, created_at) VALUES (?, ?, ?)",
                (name, source_run_id, created_at.isoformat()),
            )
        return BaselineRecord(
            name=name,
            source_run_id=source_run_id,
            created_at=created_at,
            platform_fingerprint=source["platform_fingerprint"],
            plan_hash=source["plan_hash"],
            plan_name=source["plan_name"],
        )

    def get_baseline(self, name: str) -> BaselineRecord:
        self.initialize()
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT b.name, b.source_run_id, b.created_at,
                       r.platform_fingerprint, r.plan_hash, r.plan_name
                FROM baselines AS b
                JOIN runs AS r ON r.run_id = b.source_run_id
                WHERE b.name = ?
                """,
                (name,),
            ).fetchone()
        if row is None:
            raise BaselineNotFoundError(f"baseline {name!r} was not found")
        return BaselineRecord.model_validate(dict(row))

    def list_baselines(self) -> list[BaselineRecord]:
        self.initialize()
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT b.name, b.source_run_id, b.created_at,
                       r.platform_fingerprint, r.plan_hash, r.plan_name
                FROM baselines AS b
                JOIN runs AS r ON r.run_id = b.source_run_id
                ORDER BY b.name
                """
            ).fetchall()
        return [BaselineRecord.model_validate(dict(row)) for row in rows]

    def delete_run(self, run_id: str) -> None:
        self.initialize()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            run_row = connection.execute(
                "SELECT platform_snapshot_id FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if run_row is None:
                raise RunNotFoundError(f"run {run_id!r} was not found")
            baseline = connection.execute(
                "SELECT name FROM baselines WHERE source_run_id = ? LIMIT 1", (run_id,)
            ).fetchone()
            if baseline is not None:
                raise BaselineSourceError(
                    f"run is the source of baseline {baseline['name']!r} and was not deleted"
                )
            cursor = connection.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
            if cursor.rowcount != 1:
                raise PersistenceError("run deletion affected an unexpected number of rows")
            connection.execute(
                "DELETE FROM platforms WHERE snapshot_id = ?",
                (run_row["platform_snapshot_id"],),
            )
