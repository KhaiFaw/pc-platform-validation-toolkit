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
| 7 | Markdown and self-contained HTML reports | Rendered report inspection | Not started |
| 8 | Baselines and regression analysis | Same-platform comparison tests | Not started |
| 9 | Opt-in fault injection | Deterministic failure integration test | Not started |
| 10 | CI and full documentation | Windows/Ubuntu synthetic workflow | Not started |
| 11 | Clean final verification | Acceptance checklist with captured commands | Not started |

## Immediate continuation point

Milestone 6 is complete with normalized transactional storage and canonical JSON evidence. Continue with Milestone 7 by rendering stored runs into Markdown and self-contained HTML, adding labelled telemetry charts and limitations, registering each derived artifact, and visually inspecting the HTML rather than relying only on string assertions.
