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

Performance measurements are local observations. Background load, scheduler activity, power policy, thermal state, storage caching, and unavailable sensors can affect results. Stability uses median duration and median absolute deviation; high variation is initially a warning. Baseline comparisons require matching platform fingerprints and plan hashes, use registered metric directions, and default to 10% warning and 20% failure thresholds. Zero baselines and incompatible identities do not produce a misleading percentage.

## Fault injection

The integration suite exercises both an impossible requirement and the explicit checksum fault mode. Injection is absent by default, supported only on bounded integer tests, and labelled in structured results, evidence references, warnings, and reports. `platval demo failure` returns success only after producing the intended FAIL evidence and immutable reports; the FAIL is not presented as a hardware result.

## Continuous integration

Windows and Ubuntu jobs run formatting, linting, strict typing, and portable tests with coverage, then build and test the native decoder. `hardware` and `extended` tests are excluded because hosted machines cannot provide representative sensor or performance evidence. The synthetic failure demo supplies a safe generated report artifact without requiring secrets.
