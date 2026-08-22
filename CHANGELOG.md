# Changelog

All notable changes will be documented here. The project has not made a stable release.

## Unreleased

### Added

- Initial Python packaging and command entry point.
- Validated platform, plan, telemetry, test-result, and run-result models.
- Explicit result-status aggregation semantics.
- Sanitized platform fingerprint calculation.
- Initial architecture, requirements, environment, and implementation-plan documents.
- C++20 CPUID probe source with compiler-intrinsic access, decoding, JSON serialization, and synthetic decoder tests.
- Strict Python schema and bounded subprocess adapter for native-probe capability degradation.
- Native-probe build script and versioned contract documentation.
- Sanitized portable platform inventory with stable, non-sensitive configuration fingerprints.
- psutil telemetry capability discovery with explicit unavailable-temperature handling.
- `platval doctor` and `platval inventory` commands with human-readable and JSON output.
- Cooperative monotonic timeout and cancellation controls with a central safety policy.
- Deterministic integer/hash, floating-point, memory, temporary-storage, and stability workloads.
- Storage cleanup and resource-boundary tests, including cancellation during a write.
- Strict, size-bounded YAML plan loading and canonical plan hashing.
- Explicit requirement operators with missing-value and type-error handling.
- Independent bounded psutil telemetry sampling during each enabled test.
- Validation runner lifecycle and `platval run --plan` with structured JSON output and meaningful exit codes.
- Conservative quick and standard validation plans.
- SQLite schema version 1 with normalized runs, platform snapshots, tests, metrics, requirements, telemetry, artifacts, and baseline references.
- Atomic canonical `run.json` artifacts with SHA-256 metadata.
- Persisted run listing, inspection, and confirmation-gated recoverable deletion.
