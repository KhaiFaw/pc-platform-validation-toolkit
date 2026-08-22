"""SQLite schema version 1."""

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS platforms (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint TEXT NOT NULL,
    snapshot_json TEXT NOT NULL,
    captured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    plan_name TEXT NOT NULL,
    plan_hash TEXT NOT NULL,
    tool_version TEXT NOT NULL,
    platform_snapshot_id INTEGER NOT NULL REFERENCES platforms(snapshot_id),
    platform_fingerprint TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL,
    overall_status TEXT NOT NULL CHECK (overall_status IN ('PASS','FAIL','WARN','SKIP','ERROR')),
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS test_results (
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    test_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PASS','FAIL','WARN','SKIP','ERROR')),
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    failure_reason TEXT,
    exception_summary TEXT,
    injected INTEGER NOT NULL CHECK (injected IN (0,1)),
    result_json TEXT NOT NULL,
    PRIMARY KEY (run_id, test_id)
);

CREATE TABLE IF NOT EXISTS metrics (
    run_id TEXT NOT NULL,
    test_id TEXT NOT NULL,
    name TEXT NOT NULL,
    value_json TEXT NOT NULL,
    unit TEXT,
    source TEXT NOT NULL,
    PRIMARY KEY (run_id, test_id, name),
    FOREIGN KEY (run_id, test_id) REFERENCES test_results(run_id, test_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS requirement_evaluations (
    run_id TEXT NOT NULL,
    test_id TEXT NOT NULL,
    evaluation_index INTEGER NOT NULL,
    metric TEXT NOT NULL,
    operator TEXT NOT NULL,
    expected_json TEXT NOT NULL,
    actual_json TEXT NOT NULL,
    unit TEXT,
    passed INTEGER NOT NULL CHECK (passed IN (0,1)),
    explanation TEXT NOT NULL,
    PRIMARY KEY (run_id, test_id, evaluation_index),
    FOREIGN KEY (run_id, test_id) REFERENCES test_results(run_id, test_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS telemetry_samples (
    run_id TEXT NOT NULL,
    test_id TEXT NOT NULL,
    sample_index INTEGER NOT NULL,
    elapsed_seconds REAL NOT NULL,
    timestamp TEXT NOT NULL,
    sample_json TEXT NOT NULL,
    PRIMARY KEY (run_id, test_id, sample_index),
    FOREIGN KEY (run_id, test_id) REFERENCES test_results(run_id, test_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS artifacts (
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    PRIMARY KEY (run_id, relative_path)
);

CREATE TABLE IF NOT EXISTS baselines (
    name TEXT PRIMARY KEY,
    source_run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_platforms_fingerprint ON platforms(fingerprint);
CREATE INDEX IF NOT EXISTS idx_tests_status ON test_results(status);
CREATE INDEX IF NOT EXISTS idx_telemetry_run_test ON telemetry_samples(run_id, test_id);
"""
