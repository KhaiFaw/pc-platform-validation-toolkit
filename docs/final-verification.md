# Final verification record

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
