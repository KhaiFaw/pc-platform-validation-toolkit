# Test strategy

## Levels

Unit tests cover strict models, plan loading, operator boundaries, fingerprints, capability handling, workload correctness, safety limits, statistics, and subprocess degradation. Integration tests exercise inspection commands, the complete quick plan, telemetry collection, cleanup, and an explicitly unmet requirement. Native decoder tests are present in C++ but remain uncompiled until the local C++ toolchain is available.

Default tests use small bounded resources and no privileged hardware access. Hardware-dependent tests will use the `hardware` marker; longer tests use `extended`. CI must run synthetic and portable tests without assuming temperature sensors, a native probe, or a particular CPU feature.

## Status semantics

- `PASS`: workload correctness and all explicit requirements passed.
- `FAIL`: correctness failed or an explicit requirement was not met.
- `WARN`: evidence is incomplete or a soft variability threshold was exceeded.
- `SKIP`: a disabled test or unavailable optional capability prevented execution.
- `ERROR`: configuration, timeout, or execution failed before a valid conclusion.

ERROR takes precedence over FAIL, then WARN, PASS, and SKIP. PASS mixed with optional SKIP remains PASS; reports still expose skipped counts.

## Measurement limits

Performance measurements are local observations. Background load, scheduler activity, power policy, thermal state, storage caching, and unavailable sensors can affect results. Stability uses median duration and median absolute deviation; high variation is initially a warning. Baseline comparison will use conservative thresholds and will not imply causation.

## Fault injection

The current integration suite safely demonstrates an impossible requirement. Milestone 9 will add explicitly labelled opt-in fault-injection paths for checksum, telemetry, schema, and timeout behavior. Synthetic evidence must never be presented as a real hardware result.
