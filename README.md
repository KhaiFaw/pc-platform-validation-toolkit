# PC Platform Validation Toolkit

A requirements-based command-line toolkit for collecting sanitized PC inventory and running bounded, reproducible validation workloads.

## Project status

The repository is under active development. Sanitized inventory, bounded workloads, versioned plans, telemetry, requirement evaluation, validation runs, transactional SQLite persistence, and canonical JSON evidence are implemented. The optional native CPUID probe source is present but has not yet been compiled on the development machine because CMake and a C++20 compiler are unavailable. Markdown/HTML reports and baselines are not implemented yet.

The primary target is Windows 11 on x86-64. Operating-system-specific collection will remain behind adapters so Linux support can be added without changing the runner or result model.

## Engineering problem

The toolkit is intended to determine whether repeatable software tests can identify platform configuration changes, functional failures, and meaningful regressions while retaining evidence for debugging. It is a bounded functional validation tool, not an unrestricted stress test or a hardware-certification system.

## Safety and privacy principles

- Workloads will have explicit time, worker, memory, and temporary-storage limits.
- Unavailable sensors will be reported as unavailable, never as zero.
- Inventory excludes usernames, hostnames, serial numbers, network addresses, and product identifiers by default.
- The toolkit will not change voltage, frequency, firmware, power limits, or operating-system security settings.

## Development setup

Python 3.12 or newer is required.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
mypy
platval --version
platval doctor
platval inventory
platval run --plan configs/quick.yaml
platval runs list
platval runs show <run-id>
platval runs delete <run-id>
```

Inspection, run, list, and show commands support `--json`. Use `--native-probe <path>` after building the optional probe. Inventory output excludes usernames, hostnames, serial numbers, network addresses, product identifiers, and private filesystem paths. Runs are stored under ignored `.platval/` data. Deletion requires confirmation and moves artifacts to recoverable local trash.

See [docs/implementation-plan.md](docs/implementation-plan.md) for current milestones and [docs/environment.md](docs/environment.md) for prerequisites discovered on the first development machine.

Workload boundaries and interpretation limits are documented in [docs/safety.md](docs/safety.md).

## License

MIT. See [LICENSE](LICENSE).
