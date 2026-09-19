# Final verification record

## Portfolio verification — 20 September 2026

Base commit `73c14ff`, with local documentation/evidence additions. A new isolated Python 3.12 environment installed the documented `.[dev]` dependencies. Results: 66 tests passed, 83.65% combined statement/branch coverage under the existing coverage configuration, Ruff lint and formatting passed, and mypy passed for 57 files. The coverage percentage is this run's result, not a maintained badge or branch-only percentage.

The quick plan produced 7 PASS, 1 WARN, 1 SKIP and no failures/errors. Native probe and temperature telemetry were unavailable. JSON, Markdown and HTML reports were generated; baseline creation and a same-run comparison succeeded; the opt-in demo generated labelled FAIL evidence. See [capture notes](../examples/CAPTURE_NOTES.md). A same-run comparison exercises persistence and comparison plumbing, not regression sensitivity across independent sessions.

No local CMake/C++20 toolchain was available, so no local native build is claimed. [Published CI run 33099625839](https://github.com/KhaiFaw/pc-platform-validation-toolkit/actions/runs/33099625839) passed Windows and Ubuntu for the unchanged native source at `73c14ff`. The documentation changes have not been pushed or remotely tested.

## Repeatable acceptance procedure

Milestone 11 closes the portfolio-quality MVP with a clean, repeatable acceptance path. The repository verifier creates an isolated Python environment by default, installs the package and development tools, and then checks:

- formatting, linting, strict typing, and portable automated tests;
- the optional native build and decoder tests when CMake is available;
- environment capability diagnostics and graceful degradation;
- a bounded quick validation plan and persisted SQLite evidence;
- canonical JSON plus generated Markdown and self-contained HTML reports;
- immutable baseline creation and a compatible comparison;
- existence of every expected report artifact; and
- the labelled, deterministic software-only failure demonstration.

Run the same acceptance path from the repository root:

```powershell
.\scripts\verify.ps1 -PythonPath py
```

If `py` does not resolve directly as an executable in your shell, pass an absolute Python 3.12 executable path. An already prepared project environment can be checked with:

```powershell
.\scripts\verify.ps1 -UseExistingEnvironment
```

The verifier owns only `.tmp/verification`, refuses to reuse an existing directory at that location, validates the resolved cleanup boundary, and removes its evidence on completion. Tests separately cover timeout, cancellation, and temporary-workload cleanup.

The original Windows development machine does not have CMake or a C++20 compiler, so local verification records that optional step as skipped. The GitHub Actions matrix is the native build evidence: it configures, builds, and runs CTest on both Windows and Ubuntu while also repeating the portable quality gates and generating downloadable synthetic report evidence.

No result from this toolkit constitutes hardware certification. Missing sensors remain explicit, hosted CI performance is not treated as a benchmark, and the included failure report is clearly labelled synthetic.
