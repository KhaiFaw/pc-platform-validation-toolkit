# Contributing

Thanks for helping improve the PC Platform Validation Toolkit. Changes should preserve its core contract: bounded workloads, sanitized evidence, explicit requirements, and honest handling of unavailable capabilities.

## Development setup

Use Python 3.12 or newer on Windows or Ubuntu:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
.\scripts\verify.ps1 -UseExistingEnvironment
```

On Ubuntu, create and activate a virtual environment with `python3.12 -m venv .venv`, then run the individual commands from the verification section in the README.

## Change expectations

- Add or update tests for behavioral changes.
- Keep workloads bounded and cancellation-aware.
- Never collect hostnames, usernames, serial numbers, network addresses, or other identifying data by default.
- Treat missing sensors or optional native components as explicit unavailable evidence.
- Do not present synthetic or injected results as hardware evidence.
- Update requirements, safety notes, and examples when user-visible behavior changes.

Before opening a pull request, run formatting, linting, strict typing, portable tests, and the end-to-end verifier. Native changes must also pass CMake build and CTest. See [SECURITY.md](SECURITY.md) for private vulnerability reports.
