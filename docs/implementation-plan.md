# Implementation plan

The project is built in verified increments. A milestone is complete only when its focused checks pass or a precise prerequisite is documented.

| Milestone | Scope | Exit evidence | Status |
|---|---|---|---|
| 0 | Environment, repository, scope | Toolchain inventory and local limitations recorded | Complete |
| 1 | Packaging, domain models, status semantics, initial documentation | Python 3.12 install plus lint, type, and unit checks | Complete |
| 2 | C++20 CPUID probe and Python adapter | Decoder tests and versioned JSON contract | Source complete; native compile blocked by missing toolchain |
| 3 | Sanitized inventory and capability discovery | `doctor` and `inventory` tests | Complete |
| 4 | Bounded workload engine and safety enforcement | Correctness, timeout, cancellation, and cleanup tests | Complete |
| 5 | Plan loader, runner, telemetry, evaluation | Quick synthetic and functional plans | Complete |
| 6 | SQLite persistence and JSON artifacts | Transactional repository round trips | Complete |
| 7 | Markdown and self-contained HTML reports | Rendered report inspection | Complete |
| 8 | Baselines and regression analysis | Same-platform comparison tests | Complete |
| 9 | Opt-in fault injection | Deterministic failure integration test | Complete |
| 10 | CI and full documentation | Windows/Ubuntu synthetic workflow | Complete locally; remote workflow not yet run |
| 11 | Clean final verification | Isolated install, quality gates, end-to-end workflow, artifact checks, and CI | Complete locally; remote CI verifies native builds |

## Completed MVP scope

Milestones 0–11 form the portfolio-quality MVP. Baselines are immutable and compatibility-gated; comparison policies store absolute and percent differences against explicit thresholds; the software-only failure demo is labelled and report-backed; and SHA-pinned Windows/Ubuntu CI exercises both the portable Python toolkit and native decoder. The local release verifier recreates the documented setup in an isolated environment and exercises the full evidence workflow. The native build remains an explicit local skip on machines without CMake and a C++20 compiler.
