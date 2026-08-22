# Initial development environment

Inspection date: 2026-08-22

The target directory did not exist and was created as a new local Git repository under the configured workspace. The repository deliberately records no username or absolute private path.

## Available

- Windows PowerShell development shell
- Python 3.10.11 through the system Python launcher
- Bundled Python 3.12.13, used to create the project-local `.venv`
- Git 2.55.0 for Windows
- Project and development dependencies installed in `.venv`

## Missing from PATH

- CMake
- Ninja
- MSVC `cl.exe`, Clang, or GCC

The repository targets the required Python version rather than silently accepting the older system interpreter. Native-probe compilation must wait until CMake and a C++20 compiler are available. No compiler or third-party monitoring software was downloaded automatically.

## Milestone 1 verification

- Editable installation: passed
- Unit tests: 11 passed
- Python core coverage: 81.94%
- Ruff lint and formatting: passed after mechanical fixes
- mypy strict checking: passed
- `platval --version` and `platval --help`: passed

## Milestone 2 checkpoint

- Native probe C++20 source and versioned JSON contract: implemented
- Python subprocess adapter and strict response validation: implemented
- Python suite: 16 passed with 83.54% core coverage
- Ruff and strict mypy: passed
- Native configuration, compile, CTest, and real CPUID response: blocked because CMake and a C++20 compiler remain unavailable
- `scripts\build_native.ps1`: fails early with the expected actionable CMake prerequisite message

## Milestone 3 verification

- Sanitized inventory and stable fingerprint: implemented
- psutil capability discovery: implemented
- `platval doctor` and `platval inventory`, including JSON modes: passed
- Test suite: 26 passed with 87% core coverage
- Ruff and strict mypy: passed
- Privacy review: serialized inventory contains no home path or prohibited identifier field names
- Expected limitations: native CPUID detail and trustworthy temperature telemetry remain unavailable

## Milestone 4 verification

- Deterministic CPU hash and floating-point workloads: implemented
- Bounded memory pattern verification: implemented
- Owned-directory temporary-storage round trip and cleanup: implemented
- Repeated-workload robust variability calculation: implemented
- Worker, memory, temporary-file, timeout, and disk-reserve limits: tested
- Pre-cancellation, monotonic timeout, and cancellation-during-write cleanup: tested
- Test suite: 35 passed with 90% core coverage
- Ruff and strict mypy: passed

## Milestone 5 verification

- Strict YAML loader and stable plan hash: implemented
- All specified requirement operators and missing-value behavior: tested
- Independent bounded telemetry sampler: implemented and tested
- Quick plan runner lifecycle, structured results, and raw telemetry: passed
- Deterministic unmet-requirement workflow: produces FAIL and a failed evaluation
- `platval run --plan configs/quick.yaml --json`: passed with expected WARN/SKIP degradation
- Test suite: 54 passed with 88% core coverage
- Ruff and strict mypy: passed

## Milestone 6 verification

- SQLite schema version 1 and foreign-key enforcement: implemented
- Per-run immutable platform snapshots and normalized evidence rows: verified
- Canonical JSON atomic write and SHA-256 metadata: verified
- Repository round trip, listing, and schema incompatibility behavior: tested
- Baseline source deletion protection: tested
- Confirmation-gated deletion with recoverable artifact trash: tested
- Test suite: 59 passed with 86% core coverage
- Ruff and strict mypy: passed
