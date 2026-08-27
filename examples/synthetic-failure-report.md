# PC Platform Validation Report — FAIL

## Run identity

| Field | Value |
| --- | --- |
| Run ID | 4ebd370b-284c-48d4-9566-4690a5f165ee |
| Plan | synthetic-failure-demo |
| Plan hash | 4cf96042777ea34c303cd0799e6cd59afaf82243b5b39b1cbb7233332448a0bc |
| Tool version | 0.1.0.dev0 |
| Started | 2026-08-27T17:27:00.056476+00:00 |
| Ended | 2026-08-27T17:27:00.125476+00:00 |

## Result summary

| Status | Count |
| --- | --- |
| PASS | 0 |
| FAIL | 1 |
| WARN | 0 |
| SKIP | 0 |
| ERROR | 0 |

## Sanitized platform

| Field | Value | Unit | Classification | Source |
| --- | --- | --- | --- | --- |
| Operating system | Windows 11 | — | measured | inventory |
| Architecture | AMD64 | — | measured | inventory |
| CPU | AMD64 Family 25 Model 97 Stepping 2, AuthenticAMD | — | measured | operating system |
| Processors | 6 physical / 12 logical | — | measured | psutil |
| Memory capacity | 31.29 | GiB | measured | psutil |
| Storage capacity | 952.83 | GiB | measured | psutil |
| Storage free at inventory | 319.48 | GiB | measured | psutil |
| Power plan | Ultimate Performance | — | measured | powercfg |
| Native probe | UNAVAILABLE | — | unavailable | — |
| Sanitized fingerprint | 348c4b1169323bada4c7ae3046ffd4c72369a71b9f3f08142e1f8e92acff9a91 | — | derived | SHA-256 configuration allowlist |

> **Synthetic evidence present.** Injected results are labelled per test and must not be interpreted as hardware observations.

## CPU-001 — ✗ FAIL

Duration: 0.000000 seconds
Injected: yes

Reason: opt-in injected checksum mismatch produced the expected failure

### Measurements

| Metric | Value | Unit | Classification | Source |
| --- | --- | --- | --- | --- |
| checksum_valid | false | — | simulated | cpu_integer |
| measured_duration | 0 | seconds | simulated | cpu_integer |
| operations | 16 | blocks | simulated | cpu_integer |
| operations_per_second | 1.6e+13 | blocks/s | simulated | cpu_integer |
| workers | 1 | workers | simulated | cpu_integer |

### Requirements

| Result | Metric | Operator | Configured expected | Measured actual | Unit |
| --- | --- | --- | --- | --- | --- |
| FAIL | checksum_valid | equals | true [configured] | false [simulated] | — |

### Telemetry

| Derived statistic | Value | Unit | Source |
| --- | --- | --- | --- |
| Sample count | 1 | samples | telemetry series |
| CPU utilization minimum | 0 | % | telemetry series |
| CPU utilization average | 0 | % | telemetry series |
| CPU utilization maximum | 0 | % | telemetry series |
| Peak process memory | 46.52 | MiB | telemetry series |

Unavailable telemetry: temperature.

<svg viewBox="0 0 720 230" role="img" aria-labelledby="chart-title-CPU-001 chart-desc-CPU-001"><title id="chart-title-CPU-001">CPU-001 CPU utilization</title><desc id="chart-desc-CPU-001">CPU utilization percent over elapsed seconds.</desc><line x1="54" y1="188.00" x2="702" y2="188.00" class="chart-grid" /><text x="46" y="192.00" text-anchor="end" class="chart-label">0</text><line x1="54" y1="105.00" x2="702" y2="105.00" class="chart-grid" /><text x="46" y="109.00" text-anchor="end" class="chart-label">50</text><line x1="54" y1="22.00" x2="702" y2="22.00" class="chart-grid" /><text x="46" y="26.00" text-anchor="end" class="chart-label">100</text><line x1="54" y1="22" x2="54" y2="188" class="chart-axis" /><line x1="54" y1="188" x2="702" y2="188" class="chart-axis" /><circle cx="54.00" cy="188.00" r="4" class="chart-point" /><text x="360.0" y="222" text-anchor="middle" class="chart-label">Elapsed time (seconds)</text><text x="14" y="115.0" text-anchor="middle" transform="rotate(-90 14 115)" class="chart-label">CPU utilization (%)</text><text x="702" y="206" text-anchor="end" class="chart-label">1.000s</text></svg>

Evidence references: fault-injection:checksum_mismatch

## Warnings

- A trustworthy temperature source is unavailable; runtime limits remain conservative.
- Native CPUID probe is not installed; CPU feature detail is unavailable.
- Synthetic fault injection was enabled; injected results are not hardware evidence.

## Limitations

- A trustworthy temperature source is unavailable; runtime limits remain conservative.
- Native CPUID probe is not installed; CPU feature detail is unavailable.

## Interpretation notes

- Results are local software observations, not hardware certification.
- A failed test supports further diagnosis but does not alone prove defective hardware.
- Timing can be influenced by scheduler activity, power policy, background load, and unavailable thermal data.
- Missing telemetry is reported as unavailable and is never represented as numeric zero.
