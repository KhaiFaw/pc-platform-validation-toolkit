# PC Platform Validation Toolkit

[![CI](https://github.com/KhaiFaw/pc-platform-validation-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/KhaiFaw/pc-platform-validation-toolkit/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![C++20](https://img.shields.io/badge/C%2B%2B-20-00599C?logo=cplusplus&logoColor=white)](cpp/cpuid_probe)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A requirements-based command-line toolkit for collecting sanitized PC inventory, running bounded functional validation, preserving evidence, and comparing compatible runs against an immutable known-good baseline.

## Project status

Milestones 0–11 are implemented. The Python toolkit includes inventory, capability discovery, bounded CPU/memory/storage workloads, telemetry, explicit requirement evaluation, SQLite persistence, JSON/Markdown/HTML reports, conservative baseline comparisons, and a software-only fault-injection demonstration. GitHub Actions verifies portable Python behavior and the C++ decoder on Windows and Ubuntu.

The optional native CPUID probe source is complete but has not been compiled on the original development machine because CMake and a C++20 compiler are unavailable there. Missing native or sensor capabilities degrade to explicit WARN or SKIP evidence.

This is a functional validation and engineering-evidence tool. It is not an unrestricted stress test, overclocking utility, universal benchmark, monitoring replacement, or hardware-certification system.

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

Milestone 11 is the remaining clean acceptance pass: reinstall from the documented setup, build the native probe on a supported compiler, exercise the quick/baseline/demo workflows, review generated artifacts, and record any environment-specific limitations without overstating conclusions.

## License

MIT. See [LICENSE](LICENSE).
