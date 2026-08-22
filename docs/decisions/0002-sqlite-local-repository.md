# ADR-0002: Use SQLite for local result persistence

Status: Accepted

## Context

Validation runs contain related platform snapshots, test outcomes, metrics, requirements, telemetry, and artifact metadata. They need transactional integrity and queryable history, but the MVP is a single-user local command-line tool and must not require a server or account.

## Decision

Use Python's standard `sqlite3` module with an explicitly versioned schema, foreign keys on every connection, normalized evidence tables, and one immutable platform snapshot per run. Keep SQL inside the persistence package. Store large or human-readable artifacts as files and retain only relative paths, hashes, and sizes in SQLite.

## Consequences

Setup remains local and reproducible while multi-table writes are atomic. Schema evolution requires reviewed migrations, and SQLite is not intended for concurrent remote lab agents. File and database updates cannot share one transaction, so the artifact service writes atomically first, rolls back newly owned files after database failure, and never silently overwrites an existing run directory.
