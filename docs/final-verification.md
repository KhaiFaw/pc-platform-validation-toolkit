# Final verification record

## Local native and independent-session verification — 30 September 2026

Implementation commit `b9e7476` adds high-resolution duration measurement, unavailable zero-duration rates, a WARN for unmeasurable stability, baseline self-comparison/power-policy warnings and finite-threshold validation. The existing Python 3.12.14 development environment passed **80 tests**, **83.73% combined statement/branch coverage**, Ruff lint/format checks and strict mypy across 59 files. These are local results, not a claim that this new branch has run remotely.

The optional native source compiled in Release with portable CMake 4.4.3 and LLVM/MinGW Clang 23.1.2, using MinGW Makefiles. CTest passed 1/1 decoder executable; actual CPUID output validated through the Python adapter as AVAILABLE, schema 1, version 0.1.0. No native source change was needed. AMD extended-cache decoding remains an explicit limitation; trustworthy temperature and battery/AC observations remain unavailable.

The [retained pair](../examples/independent-sessions/README.md) executes the checked-in quick plan twice, 15 seconds apart, using the same binary and clean implementation source. Each plan returned 8 PASS and 1 WARN. The baseline/current UUIDs differ; plan hashes and platform fingerprints match. The comparison returned FAIL at the recorded timing threshold, which is retained and explained rather than presented as a hardware defect or filtered into a performance-success claim. Context, exact binary hash, package-origin check and source hashes are preserved.

The updated acceptance script passed Python gates, local native build/CTest, native-enabled diagnostics, bounded plans, all report formats, an independent second-run comparison and the labelled synthetic failure demo. It displayed a short-run comparison FAIL without treating brief interactive-desktop timing as a benchmark gate; functional failures still abort verification. Verification's owned `.tmp/verification` directory was removed by its checked cleanup path. Generated paired evidence was separately retained; prior diagnostic iterations remain in ignored runtime folders.

See the [capture procedure](independent-sessions.md) for provenance, limitations and legacy-baseline recapture requirements. Historical pre-fix timing baselines should not be used with the corrected clock, even when their version/plan hashes match.

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

At the original milestone acceptance, the Windows development machine did not have CMake or a C++20 compiler and the optional native step was skipped. The 30 September follow-up above adds real local native build/integration evidence using portable tools. GitHub Actions also configures, builds and runs CTest on Windows and Ubuntu; the new maintenance branch's remote result must be verified after publication.

No result from this toolkit constitutes hardware certification. Missing sensors remain explicit, hosted CI performance is not treated as a benchmark, and the included failure report is clearly labelled synthetic.
