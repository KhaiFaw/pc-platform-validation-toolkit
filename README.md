# PC Platform Validation Toolkit

[![CI](https://github.com/KhaiFaw/pc-platform-validation-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/KhaiFaw/pc-platform-validation-toolkit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A requirements-based command-line toolkit for collecting sanitized PC inventory, running bounded functional validation, preserving evidence, and comparing compatible runs against an immutable known-good baseline.

**Status:** functional MVP, `0.1.0.dev0`. Current reports distinguish measured results, unavailable capabilities and deliberately injected failures.

<img src="docs/images/architecture.png" width="640" alt="YAML plans and inventory feed bounded workloads, immutable reports and compatible baseline comparisons">

[Independent native-enabled sessions](examples/independent-sessions/README.md) · [Injected-failure report](examples/injected/report.md) · [Verification](docs/final-verification.md) · [Portfolio](https://github.com/KhaiFaw)

## Project status

Milestones 0–11 are implemented. The Python toolkit includes inventory, capability discovery, bounded CPU/memory/storage workloads, telemetry, explicit requirement evaluation, SQLite persistence, JSON/Markdown/HTML reports, conservative baseline comparisons, and a software-only fault-injection demonstration. GitHub Actions verifies portable Python behavior and the C++ decoder on Windows and Ubuntu.

Version `0.1.0.dev0` is a functional MVP, not a stable release. On 30 September 2026, local verification passed 80 tests, lint, formatting and strict typing. Two separately executed native-enabled quick plans each returned eight PASS and one WARN; temperature evidence remains unavailable. Their compatible timing comparison returned FAIL because a sub-millisecond measurement crossed a configured threshold; this is retained as evidence, not presented as a hardware diagnosis.

The optional native CPUID probe now builds and runs locally: CMake 4.4.3, LLVM/MinGW Clang 23.1.2, Release build, decoder CTest and real Python schema integration passed. The toolchain was used from portable workspace folders without system installation. Missing native or sensor capabilities still degrade to explicit WARN or SKIP evidence.

This is a functional validation and engineering-evidence tool. It is not an unrestricted stress test, overclocking utility, universal benchmark, monitoring replacement, or hardware-certification system.

## Engineering problem and contributions

The useful question is whether an explicit requirement holds under a repeatable, resource-bounded test—and whether the evidence can explain a failure later. The project-specific code defines typed plans/results, lifecycle and safety controls, requirement evaluation, immutable artifacts, baseline compatibility and a labelled failure demonstration.

Typer provides the CLI, Pydantic validates models, psutil provides portable observations, Jinja2 renders reports and SQLite stores local history. The optional C++ probe decodes processor information. These dependencies are credited as infrastructure, not claimed as original implementations.

## Current evidence

The [paired capture](examples/independent-sessions/README.md) preserves both real runs, their immutable baseline, comparison, power/background-load context, package-origin check, native-binary hash and source-file hashes. The runs have different UUIDs and matching platform/plan identities. They are short functional samples on a normal interactive desktop, not a controlled benchmark or thermal validation.

![Actual quick-plan HTML report: WARN, with seven passes, one warning and one skip](docs/images/measured-report.png)

[Open the historical measured Markdown report](examples/measured/report.md), or download and open the [self-contained HTML](examples/measured/report.html) locally. This 20 September capture used Windows 11, Python 3.12, the checked-in quick plan and no native probe. It is preserved as historical functional/report evidence; recapture its baseline before interpreting timing against the corrected high-resolution timer.

![Actual injected-failure HTML report with synthetic evidence labelled](docs/images/injected-report.png)

The [injected report](examples/injected/report.md) deliberately fails a checksum requirement. It proves the software failure/reporting path, not a faulty CPU. [Capture notes](examples/CAPTURE_NOTES.md) distinguish measured observations, missing capabilities and the baseline self-comparison.

## Architecture

```text
YAML plan -> runner -> bounded workloads -> requirement evaluation
                |              |
          inventory/probe   telemetry sampler
                |              |
                +-> canonical result -> SQLite + immutable artifacts
                                           |
                              reports / baselines / comparison
```

Collectors report observations and unavailable capabilities; evaluators assign outcomes only against explicit requirements. Reports are projections of persisted evidence and never rerun workloads. See [architecture.md](docs/architecture.md) and the short records in [docs/decisions](docs/decisions).

## Quick start

Python 3.12 or newer is required.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

platval doctor
platval inventory
platval run --plan configs/quick.yaml
platval runs list
```

To build the optional native probe after installing CMake and a supported C++20 compiler:

```powershell
.\scripts\build_native.ps1
platval doctor --native-probe cpp\cpuid_probe\build\Release\cpuid_probe.exe
```

Single-configuration generators place the executable at `cpp\cpuid_probe\build\cpuid_probe.exe`. Portable LLVM/MinGW builds can explicitly select `-Generator 'MinGW Makefiles'`, `-CxxCompiler <compiler.exe>` and `-MakeProgram <mingw32-make.exe>` without changing system settings. Keep the compiler's runtime DLL directory on the current shell's PATH. See [the native-session procedure](docs/independent-sessions.md).

## Evidence and baseline workflow

```powershell
platval report <run-id> --format html
platval report <run-id> --format markdown
platval report <run-id> --format json

platval baseline create --from-run <run-id> --name known-good
platval baseline list
platval baseline show known-good
platval compare --baseline known-good --run <later-run-id>
```

Baselines are tied to a sanitized platform fingerprint and plan hash and are never silently replaced. Numeric conclusions are withheld when either identity differs. Registered metrics use conservative 10% warning and 20% failure defaults, configurable per comparison. Functional correctness always takes priority over performance changes.

Use [the paired-session capture script](scripts/capture_sessions.ps1) to preserve two independent quick-plan executions and their sanitized context. Self-comparisons are explicitly warned; changed recorded power plans are also flagged. Baselines captured before the high-resolution timing fix must be recaptured, even though the MVP version and plan hash are unchanged.

## Safe failure demonstration

```powershell
platval demo failure
```

The demo deliberately supplies an incorrect expected checksum to one small bounded CPU workload. It is disabled during normal plans, changes no hardware or operating-system state, and labels the result and reports as injected synthetic evidence. The command succeeds when the intended FAIL evidence and reports are produced.

## Verification

```powershell
pytest
ruff format --check src tests
ruff check src tests
mypy src tests
.\scripts\verify.ps1 -UseExistingEnvironment
```

The clean verification script can instead create an isolated environment when invoked with a Python 3.12 executable through `-PythonPath`. CMake verification is performed when available and reported as an explicit local skip otherwise. CI excludes `hardware` and `extended` tests because hosted-runner sensors and performance are not representative; it still builds and tests the native decoder.

See the [final verification record](docs/final-verification.md) for the acceptance scope and evidence, and [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change.

## Safety, privacy, and interpretation

- Workloads have explicit duration, worker, memory, and temporary-storage limits.
- Storage validation writes only beneath an owned temporary directory and cleans it up.
- Inventory excludes usernames, hostnames, serial numbers, network addresses, and product identifiers by default.
- Unavailable sensors are represented as unavailable, never numeric zero.
- The toolkit never changes voltage, frequency, firmware, power limits, or security settings.
- Timing differences can reflect scheduling, background load, caching, power policy, or thermal state and do not prove causation.

Read [safety.md](docs/safety.md), [results-guide.md](docs/results-guide.md), and [test-strategy.md](docs/test-strategy.md) before interpreting results.

## Documentation

- [Requirements and verification map](docs/requirements.md)
- [Implementation milestones](docs/implementation-plan.md)
- [Environment and verified checkpoints](docs/environment.md)
- [Native-probe contract](docs/native-probe-contract.md)
- [CI design](docs/ci.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Clearly labelled sample evidence](examples/README.md)

## Roadmap

The MVP acceptance path and local native integration have been exercised; earlier published source passed the Windows/Ubuntu CI matrix. Next: collect longer repeated sessions under controlled power/background conditions, add AMD extended-cache decoding, and establish a release policy. Two short interactive-desktop captures do not establish sustained stability. Timing variation alone cannot identify a hardware cause.

## Repository guide

| Path | Responsibility |
|---|---|
| `src/platval/runner/` | Plan loading, lifecycle and result assembly |
| `src/platval/workloads/` | Bounded CPU, memory and storage work |
| `src/platval/evaluation/` | Explicit requirement outcomes |
| `src/platval/persistence/` | SQLite and immutable artifacts |
| `src/platval/reporting/` | Views, templates and derived reports |
| `src/platval/baselines/` | Compatibility and comparisons |
| `cpp/cpuid_probe/` | Optional native probe and decoder tests |
| `tests/` | Unit and integration checks |

Architectural trade-offs are recorded in [the decision log](docs/decisions/): subprocess isolation, local SQLite, static offline reports, capability-based sensors and bounded validation.

## License

MIT. See [LICENSE](LICENSE).
