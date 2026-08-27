# Architecture

## Boundaries

The application accepts a versioned YAML test plan, validates it into typed domain models, and executes each definition through a runner. Workloads produce measurements; collectors independently produce time-series evidence; evaluators compare measurements with explicit requirements. A canonical run result is then persisted and rendered into JSON, Markdown, and HTML artifacts.

```text
YAML plan -> plan loader -> validation runner -> canonical run result
                              |     |     |             |
                         inventory  |  evaluator     repository
                              native probe            reporters
                                    |
                            workload + telemetry
```

Data collection and requirement evaluation are deliberately separate: a collector reports observations and limitations, while an evaluator decides whether a named requirement passed. This prevents missing telemetry from being converted into a false numeric value.

## Native boundary

The C++ CPUID probe will be a versioned subprocess that emits JSON on standard output and diagnostics on standard error. Python validates the response. The application remains useful with reduced capability when the executable is missing or incompatible. See [ADR-0001](decisions/0001-native-probe-subprocess.md).

## Operating-system adapters

Platform-specific inventory and sensor logic will live behind capability-discovering interfaces. Core plan, result, evaluation, persistence, and reporting code will not import Windows-specific modules.

The Milestone 3 inventory collector uses portable `platform` and `psutil` data, with a narrowly scoped `powercfg /getactivescheme` adapter on Windows. The subprocess has a fixed argument list and timeout. Inventory stores the plan's display name but no command path, user identifier, or raw diagnostic output.

## Workload boundary

Milestone 4 workloads accept validated configuration, a central safety policy, a monotonic timeout, and an optional shared cancellation token. They return measurements and correctness evidence but do not assign PASS or FAIL; requirement evaluation remains a runner responsibility. Cooperative checkpoints occur between bounded chunks, so cancellation never depends on forcibly terminating a thread.

The concurrent CPU workload hashes blocks larger than Python's GIL-release threshold through `hashlib`, allowing bounded worker threads without unmanaged child processes. Memory verification uses one main buffer and chunked in-place transformation. Storage validation creates exactly one owned directory beneath the selected temporary root and removes that directory in a `finally` block.

## Runner and telemetry lifecycle

The runner loads one size-bounded YAML document into strict models and hashes its canonical JSON representation. It inventories the platform once, then dispatches stable test IDs to bounded workload adapters. Each enabled test owns a child cancellation token linked to the run token, so a test timeout cannot accidentally cancel unrelated tests while run-level cancellation still propagates.

A psutil sampler runs on a separate bounded thread during each enabled test. It samples immediately, uses monotonic elapsed time, caps stored samples at 10,000, and joins before the test result is finalized. Optional sensor failures are recorded on samples. Raw samples remain alongside the canonical result in `RunExecution` and are persisted transactionally.

Workload correctness is evaluated before configured requirements. Missing metrics remain `None`, never zero. Explicitly unmet requirements produce FAIL, invalid operand types produce ERROR, unavailable optional capabilities produce SKIP or WARN, and high stability variation is a soft WARN.

## Persistence and artifacts

SQLite schema version 1 stores an immutable platform snapshot per run plus normalized test results, metrics, requirement evaluations, telemetry samples, and artifact metadata. Foreign keys are enabled on every connection and writes use explicit immediate transactions. SQL remains confined to the persistence package. Connections close deterministically and SQLite failures are translated into concise repository errors.

The artifact service writes `runs/<run-id>/run.json.tmp`, flushes and synchronizes it, then atomically replaces it with `run.json` before committing matching database metadata. A database failure removes only the newly owned artifact directory. The canonical JSON hash is stored in the artifacts table rather than recursively embedding its own digest.

Run deletion is confirmation-gated at the CLI. Database rows cascade only after checking baseline references; the owned artifact directory is moved into `.platval/trash/` instead of being irreversibly erased. Platform snapshots are per-run because transient evidence such as free space and power plan may differ even when the stable platform fingerprint is unchanged.

## Reporting boundary

Reports are pure projections of stored canonical evidence; report generation never reruns inventory or workloads. A typed view model labels observations as measured, configured, derived, unavailable, or simulated before format-specific rendering. Requirement tables keep configured expectations beside measured actual values, and missing telemetry remains explicit.

Markdown and HTML use the same view. HTML contains all CSS and accessible SVG charts inline and has no scripts, external fonts, CDN assets, or server dependency. Derived report files are atomically created inside the owning run directory, hashed, and registered in SQLite. Existing files are never overwritten. JSON reporting returns the original canonical `run.json` artifact rather than producing a duplicate. See [ADR-0003](decisions/0003-static-offline-reports.md).

## Baselines and regression

A baseline is an immutable database pointer to its source run. Repository joins expose the source platform fingerprint and plan hash without duplicating canonical evidence. Comparisons load both stored executions and withhold numeric conclusions unless those identities match. Only registered numeric metrics with a known direction are compared; boolean correctness is left to normal result status.

The comparator records baseline/current values, signed absolute and percent differences, metric direction, thresholds, and classification. Median-based stability metrics are used when the workload provides them. Functional FAIL or ERROR outranks performance classification, zero baselines cannot produce a percentage, and explanatory warnings avoid causal claims.

## Fault-injection boundary

Fault injection is an explicit typed plan field and defaults to absent. The implemented mode changes only the expected checksum supplied to a small deterministic CPU workload. It does not alter the computation, machine configuration, or operating system. The runner labels the result, evidence reference, and run warning; all report formats preserve the synthetic distinction. `platval demo failure` constructs this plan internally so installed packages do not depend on a repository-relative config file.

## Verification boundary

The local PowerShell verifier can use the project environment or create an isolated one, performs Python quality gates, conditionally verifies native code when CMake exists, and generates a synthetic failure report. CI enforces the native build on GitHub-hosted Windows and Ubuntu but excludes hardware and extended tests because hosted telemetry and timing are not representative evidence.

## Data handling

The canonical result models reject unknown fields. Timestamps require UTC offsets; elapsed sampling uses a monotonic clock. A platform fingerprint hashes stable non-sensitive configuration values. It deliberately excludes free disk space, sensor availability, and other transient capabilities. Runtime data lives in ignored `.platval/` storage and temporary workloads will be confined to an owned temporary directory.
