# Native-enabled independent quick sessions

Captured 30 September 2026, Asia/Kuala_Lumpur. Embedded timestamps are UTC, 29 September. Implementation source: `b9e74768613ad0925f76a142df59d40802a5c606`; the source was clean and its hashes were unchanged across the two processes.

## Results and context

| Observation | Baseline session | Repeat session |
|---|---|---|
| Run UUID | `fc5a7b5e-2b68-4c46-9dec-23e104abf602` | `b6434d3c-f080-4d3f-aa98-d2b5e4254274` |
| Started, UTC | 21:54:28.858528 | 21:54:47.678320 |
| Functional result | 8 PASS, 1 WARN, 0 FAIL/ERROR | 8 PASS, 1 WARN, 0 FAIL/ERROR |
| Active power plan | Ultimate Performance | Ultimate Performance |
| Pre-run CPU, 2-second sample | 10.2% | 6.3% |
| Process count before run | 375 | 374 |
| Native probe | 0.1.0, schema validated | Same binary and version |
| Temperature | Unavailable | Unavailable |

Both sessions ran on the same Windows 11 / Python 3.12.14 desktop, with an AMD Ryzen 5 7500F, six physical / twelve logical processors and 31.29 GiB installed memory exposed by psutil. Background applications were left running; no load or power-policy change was deliberately injected. A 15-second pause separated the commands, but this did not establish thermal equilibrium. Battery/AC observations were unavailable, not assumed from the desktop configuration.

The immutable [baseline](baseline.json) points to the first run. The [comparison](comparison.json) references the second UUID; platform fingerprint and plan hash match. The result is **FAIL** at the recorded 10% WARN / 20% FAIL thresholds: CPU-001 measured duration increased by approximately 22.82%. Other warnings include approximately 18.58% lower CPU-001 rate, 16.92% higher STB-001 median duration and 11.19% lower storage write rate. These are sub-millisecond or very short functional samples affected by scheduling, caching and normal desktop activity. They do not establish a hardware regression, defect, sustained performance or thermal stability.

This capture was retained as produced, including threshold crossings. Earlier diagnostic/provenance iterations also produced WARN or FAIL comparisons and remain in ignored local runtime folders; no successful benchmark claim is selected from those iterations.

## Evidence files

- Baseline: [Markdown](baseline-session/report.md), [HTML](baseline-session/report.html), [canonical JSON](baseline-session/run.json).
- Repeat: [Markdown](repeat-session/report.md), [HTML](repeat-session/report.html), [canonical JSON](repeat-session/run.json).
- [Sanitized context](context.json) records timestamps, load, power plan, timer details and a package-origin boolean; no process names or private paths.
- [Source manifest](source-manifest.json) records repository-relative file hashes, exact implementation commit and native binary SHA-256.
- [Capability diagnostics](doctor.json) distinguish a passing native adapter from unavailable temperature telemetry.

The native executable SHA-256 is `dc45e960a21194bec9da228404db7043ddd13d4484baceddfcafa5246d6a122a`. Build: CMake 4.4.3, portable LLVM/MinGW Clang 23.1.2, MinGW Makefiles, Release; decoder CTest passed. The existing decoder does not yet fall back to AMD extended-cache leaves, so the observed empty cache list is not a claim that the processor lacks caches. CPUID feature bits are exposed observations, not assertions about firmware or hypervisor policy.

GitHub does not execute these HTML files; download and open them locally. Markdown charts may be sanitized by GitHub. The [repeatable procedure](../../docs/independent-sessions.md) explains how to recapture without overwriting evidence.
