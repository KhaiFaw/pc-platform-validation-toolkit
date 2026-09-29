# PC Platform Validation Report — WARN

## Run identity

| Field | Value |
| --- | --- |
| Run ID | b6434d3c-f080-4d3f-aa98-d2b5e4254274 |
| Plan | quick-validation |
| Plan hash | fb9a4cd47ff07fb05917c10bc102168578b0418be998f0c1fe20b02e7d33f8ac |
| Tool version | 0.1.0.dev0 |
| Started | 2026-09-29T21:54:47.678320+00:00 |
| Ended | 2026-09-29T21:54:47.794320+00:00 |

## Result summary

| Status | Count |
| --- | --- |
| PASS | 8 |
| FAIL | 0 |
| WARN | 1 |
| SKIP | 0 |
| ERROR | 0 |

## Sanitized platform

| Field | Value | Unit | Classification | Source |
| --- | --- | --- | --- | --- |
| Operating system | Windows 11 | — | measured | inventory |
| Architecture | x86_64 | — | measured | inventory |
| CPU | AMD Ryzen 5 7500F 6-Core Processor | — | measured | native probe |
| Processors | 6 physical / 12 logical | — | measured | psutil |
| Memory capacity | 31.29 | GiB | measured | psutil |
| Storage capacity | 952.83 | GiB | measured | psutil |
| Storage free at inventory | 480.68 | GiB | measured | psutil |
| Power plan | Ultimate Performance | — | measured | powercfg |
| Native probe | 0.1.0 | — | measured | cpuid_probe |
| Sanitized fingerprint | ab272582381d2dc3c80106850dc88d177df1c5a5d37c79a2c819d9eb749adb61 | — | derived | SHA-256 configuration allowlist |

## INV-001 — ✓ PASS

Duration: 0.000932 seconds
Injected: no

### Measurements

| Metric | Value | Unit | Classification | Source |
| --- | --- | --- | --- | --- |
| architecture | x86_64 | — | measured | inventory |
| logical_cpu_count | 12 | processors | measured | inventory |
| physical_cpu_count | 6 | processors | measured | inventory |
| storage_free_bytes | 516125507584 | bytes | measured | inventory |
| total_memory_bytes | 33594245120 | bytes | measured | inventory |

### Requirements

| Result | Metric | Operator | Configured expected | Measured actual | Unit |
| --- | --- | --- | --- | --- | --- |
| PASS | logical_cpu_count | greater_than | 0 [configured] | 12 [measured] | — |
| PASS | total_memory_bytes | greater_than | 0 [configured] | 33594245120 [measured] | — |

### Telemetry

| Derived statistic | Value | Unit | Source |
| --- | --- | --- | --- |
| Sample count | 1 | samples | telemetry series |
| CPU utilization minimum | 0 | % | telemetry series |
| CPU utilization average | 0 | % | telemetry series |
| CPU utilization maximum | 0 | % | telemetry series |
| Peak process memory | 45.15 | MiB | telemetry series |

Unavailable telemetry: temperature.

<svg viewBox="0 0 720 230" role="img" aria-labelledby="chart-title-INV-001 chart-desc-INV-001"><title id="chart-title-INV-001">INV-001 CPU utilization</title><desc id="chart-desc-INV-001">CPU utilization percent over elapsed seconds.</desc><line x1="54" y1="188.00" x2="702" y2="188.00" class="chart-grid" /><text x="46" y="192.00" text-anchor="end" class="chart-label">0</text><line x1="54" y1="105.00" x2="702" y2="105.00" class="chart-grid" /><text x="46" y="109.00" text-anchor="end" class="chart-label">50</text><line x1="54" y1="22.00" x2="702" y2="22.00" class="chart-grid" /><text x="46" y="26.00" text-anchor="end" class="chart-label">100</text><line x1="54" y1="22" x2="54" y2="188" class="chart-axis" /><line x1="54" y1="188" x2="702" y2="188" class="chart-axis" /><circle cx="54.00" cy="188.00" r="4" class="chart-point" /><text x="360.0" y="222" text-anchor="middle" class="chart-label">Elapsed time (seconds)</text><text x="14" y="115.0" text-anchor="middle" transform="rotate(-90 14 115)" class="chart-label">CPU utilization (%)</text><text x="702" y="206" text-anchor="end" class="chart-label">1.000s</text></svg>

Evidence references: none recorded

## CPU-001 — ✓ PASS

Duration: 0.002410 seconds
Injected: no

### Measurements

| Metric | Value | Unit | Classification | Source |
| --- | --- | --- | --- | --- |
| checksum_valid | true | — | measured | cpu_integer |
| measured_duration | 0.00092360005 | seconds | measured | cpu_integer |
| operations | 64 | blocks | measured | cpu_integer |
| operations_per_second | 69294.063 | blocks/s | derived | cpu_integer |
| workers | 1 | workers | measured | cpu_integer |

### Requirements

| Result | Metric | Operator | Configured expected | Measured actual | Unit |
| --- | --- | --- | --- | --- | --- |
| PASS | checksum_valid | equals | true [configured] | true [measured] | — |

### Telemetry

| Derived statistic | Value | Unit | Source |
| --- | --- | --- | --- |
| Sample count | 1 | samples | telemetry series |
| CPU utilization minimum | 0 | % | telemetry series |
| CPU utilization average | 0 | % | telemetry series |
| CPU utilization maximum | 0 | % | telemetry series |
| Peak process memory | 45.19 | MiB | telemetry series |

Unavailable telemetry: temperature.

<svg viewBox="0 0 720 230" role="img" aria-labelledby="chart-title-CPU-001 chart-desc-CPU-001"><title id="chart-title-CPU-001">CPU-001 CPU utilization</title><desc id="chart-desc-CPU-001">CPU utilization percent over elapsed seconds.</desc><line x1="54" y1="188.00" x2="702" y2="188.00" class="chart-grid" /><text x="46" y="192.00" text-anchor="end" class="chart-label">0</text><line x1="54" y1="105.00" x2="702" y2="105.00" class="chart-grid" /><text x="46" y="109.00" text-anchor="end" class="chart-label">50</text><line x1="54" y1="22.00" x2="702" y2="22.00" class="chart-grid" /><text x="46" y="26.00" text-anchor="end" class="chart-label">100</text><line x1="54" y1="22" x2="54" y2="188" class="chart-axis" /><line x1="54" y1="188" x2="702" y2="188" class="chart-axis" /><circle cx="54.00" cy="188.00" r="4" class="chart-point" /><text x="360.0" y="222" text-anchor="middle" class="chart-label">Elapsed time (seconds)</text><text x="14" y="115.0" text-anchor="middle" transform="rotate(-90 14 115)" class="chart-label">CPU utilization (%)</text><text x="702" y="206" text-anchor="end" class="chart-label">1.000s</text></svg>

Evidence references: none recorded

## CPU-002 — ✓ PASS

Duration: 0.012481 seconds
Injected: no

### Measurements

| Metric | Value | Unit | Classification | Source |
| --- | --- | --- | --- | --- |
| absolute_error | 1.110223e-16 | — | derived | cpu_floating_point |
| actual | 0.99999 | — | measured | cpu_floating_point |
| expected | 0.99999 | — | measured | cpu_floating_point |
| operations_per_second | 8588630.3 | terms/s | derived | cpu_floating_point |
| tolerance | 1e-12 | — | measured | cpu_floating_point |

### Requirements

| Result | Metric | Operator | Configured expected | Measured actual | Unit |
| --- | --- | --- | --- | --- | --- |
| PASS | absolute_error | less_than_or_equal | 1e-12 [configured] | 1.110223e-16 [derived] | — |

### Telemetry

| Derived statistic | Value | Unit | Source |
| --- | --- | --- | --- |
| Sample count | 1 | samples | telemetry series |
| CPU utilization minimum | 0 | % | telemetry series |
| CPU utilization average | 0 | % | telemetry series |
| CPU utilization maximum | 0 | % | telemetry series |
| Peak process memory | 45.22 | MiB | telemetry series |

Unavailable telemetry: temperature.

<svg viewBox="0 0 720 230" role="img" aria-labelledby="chart-title-CPU-002 chart-desc-CPU-002"><title id="chart-title-CPU-002">CPU-002 CPU utilization</title><desc id="chart-desc-CPU-002">CPU utilization percent over elapsed seconds.</desc><line x1="54" y1="188.00" x2="702" y2="188.00" class="chart-grid" /><text x="46" y="192.00" text-anchor="end" class="chart-label">0</text><line x1="54" y1="105.00" x2="702" y2="105.00" class="chart-grid" /><text x="46" y="109.00" text-anchor="end" class="chart-label">50</text><line x1="54" y1="22.00" x2="702" y2="22.00" class="chart-grid" /><text x="46" y="26.00" text-anchor="end" class="chart-label">100</text><line x1="54" y1="22" x2="54" y2="188" class="chart-axis" /><line x1="54" y1="188" x2="702" y2="188" class="chart-axis" /><circle cx="702.00" cy="188.00" r="4" class="chart-point" /><text x="360.0" y="222" text-anchor="middle" class="chart-label">Elapsed time (seconds)</text><text x="14" y="115.0" text-anchor="middle" transform="rotate(-90 14 115)" class="chart-label">CPU utilization (%)</text><text x="702" y="206" text-anchor="end" class="chart-label">0.015s</text></svg>

Evidence references: none recorded

## CPU-003 — ✓ PASS

Duration: 0.002086 seconds
Injected: no

### Measurements

| Metric | Value | Unit | Classification | Source |
| --- | --- | --- | --- | --- |
| checksum_valid | true | — | measured | cpu_integer |
| measured_duration | 0.00069979997 | seconds | measured | cpu_integer |
| operations | 64 | blocks | measured | cpu_integer |
| operations_per_second | 91454.705 | blocks/s | derived | cpu_integer |
| workers | 2 | workers | measured | cpu_integer |

### Requirements

| Result | Metric | Operator | Configured expected | Measured actual | Unit |
| --- | --- | --- | --- | --- | --- |
| PASS | checksum_valid | equals | true [configured] | true [measured] | — |

### Telemetry

| Derived statistic | Value | Unit | Source |
| --- | --- | --- | --- |
| Sample count | 1 | samples | telemetry series |
| CPU utilization minimum | 0 | % | telemetry series |
| CPU utilization average | 0 | % | telemetry series |
| CPU utilization maximum | 0 | % | telemetry series |
| Peak process memory | 45.23 | MiB | telemetry series |

Unavailable telemetry: temperature.

<svg viewBox="0 0 720 230" role="img" aria-labelledby="chart-title-CPU-003 chart-desc-CPU-003"><title id="chart-title-CPU-003">CPU-003 CPU utilization</title><desc id="chart-desc-CPU-003">CPU utilization percent over elapsed seconds.</desc><line x1="54" y1="188.00" x2="702" y2="188.00" class="chart-grid" /><text x="46" y="192.00" text-anchor="end" class="chart-label">0</text><line x1="54" y1="105.00" x2="702" y2="105.00" class="chart-grid" /><text x="46" y="109.00" text-anchor="end" class="chart-label">50</text><line x1="54" y1="22.00" x2="702" y2="22.00" class="chart-grid" /><text x="46" y="26.00" text-anchor="end" class="chart-label">100</text><line x1="54" y1="22" x2="54" y2="188" class="chart-axis" /><line x1="54" y1="188" x2="702" y2="188" class="chart-axis" /><circle cx="54.00" cy="188.00" r="4" class="chart-point" /><text x="360.0" y="222" text-anchor="middle" class="chart-label">Elapsed time (seconds)</text><text x="14" y="115.0" text-anchor="middle" transform="rotate(-90 14 115)" class="chart-label">CPU utilization (%)</text><text x="702" y="206" text-anchor="end" class="chart-label">1.000s</text></svg>

Evidence references: none recorded

## MEM-001 — ✓ PASS

Duration: 0.016755 seconds
Injected: no

### Measurements

| Metric | Value | Unit | Classification | Source |
| --- | --- | --- | --- | --- |
| allocation | 8388608 | bytes | measured | memory_pattern |
| checksum_valid | true | — | measured | memory_pattern |
| processed_bytes | 25165824 | bytes | measured | memory_pattern |
| throughput | 1.6039403e+09 | bytes/s | derived | memory_pattern |

### Requirements

| Result | Metric | Operator | Configured expected | Measured actual | Unit |
| --- | --- | --- | --- | --- | --- |
| PASS | checksum_valid | equals | true [configured] | true [measured] | — |

### Telemetry

| Derived statistic | Value | Unit | Source |
| --- | --- | --- | --- |
| Sample count | 1 | samples | telemetry series |
| CPU utilization minimum | 0 | % | telemetry series |
| CPU utilization average | 0 | % | telemetry series |
| CPU utilization maximum | 0 | % | telemetry series |
| Peak process memory | 45.28 | MiB | telemetry series |

Unavailable telemetry: temperature.

<svg viewBox="0 0 720 230" role="img" aria-labelledby="chart-title-MEM-001 chart-desc-MEM-001"><title id="chart-title-MEM-001">MEM-001 CPU utilization</title><desc id="chart-desc-MEM-001">CPU utilization percent over elapsed seconds.</desc><line x1="54" y1="188.00" x2="702" y2="188.00" class="chart-grid" /><text x="46" y="192.00" text-anchor="end" class="chart-label">0</text><line x1="54" y1="105.00" x2="702" y2="105.00" class="chart-grid" /><text x="46" y="109.00" text-anchor="end" class="chart-label">50</text><line x1="54" y1="22.00" x2="702" y2="22.00" class="chart-grid" /><text x="46" y="26.00" text-anchor="end" class="chart-label">100</text><line x1="54" y1="22" x2="54" y2="188" class="chart-axis" /><line x1="54" y1="188" x2="702" y2="188" class="chart-axis" /><circle cx="54.00" cy="188.00" r="4" class="chart-point" /><text x="360.0" y="222" text-anchor="middle" class="chart-label">Elapsed time (seconds)</text><text x="14" y="115.0" text-anchor="middle" transform="rotate(-90 14 115)" class="chart-label">CPU utilization (%)</text><text x="702" y="206" text-anchor="end" class="chart-label">1.000s</text></svg>

Evidence references: none recorded

## STO-001 — ✓ PASS

Duration: 0.015604 seconds
Injected: no

### Measurements

| Metric | Value | Unit | Classification | Source |
| --- | --- | --- | --- | --- |
| checksum_valid | true | — | measured | temporary_storage_round_trip |
| file_size | 4194304 | bytes | measured | temporary_storage_round_trip |
| read_throughput | 5.5927037e+08 | bytes/s | derived | temporary_storage_round_trip |
| write_throughput | 7.8889236e+08 | bytes/s | derived | temporary_storage_round_trip |

### Requirements

| Result | Metric | Operator | Configured expected | Measured actual | Unit |
| --- | --- | --- | --- | --- | --- |
| PASS | checksum_valid | equals | true [configured] | true [measured] | — |

### Telemetry

| Derived statistic | Value | Unit | Source |
| --- | --- | --- | --- |
| Sample count | 1 | samples | telemetry series |
| CPU utilization minimum | 0 | % | telemetry series |
| CPU utilization average | 0 | % | telemetry series |
| CPU utilization maximum | 0 | % | telemetry series |
| Peak process memory | 45.29 | MiB | telemetry series |

Unavailable telemetry: temperature.

<svg viewBox="0 0 720 230" role="img" aria-labelledby="chart-title-STO-001 chart-desc-STO-001"><title id="chart-title-STO-001">STO-001 CPU utilization</title><desc id="chart-desc-STO-001">CPU utilization percent over elapsed seconds.</desc><line x1="54" y1="188.00" x2="702" y2="188.00" class="chart-grid" /><text x="46" y="192.00" text-anchor="end" class="chart-label">0</text><line x1="54" y1="105.00" x2="702" y2="105.00" class="chart-grid" /><text x="46" y="109.00" text-anchor="end" class="chart-label">50</text><line x1="54" y1="22.00" x2="702" y2="22.00" class="chart-grid" /><text x="46" y="26.00" text-anchor="end" class="chart-label">100</text><line x1="54" y1="22" x2="54" y2="188" class="chart-axis" /><line x1="54" y1="188" x2="702" y2="188" class="chart-axis" /><circle cx="54.00" cy="188.00" r="4" class="chart-point" /><text x="360.0" y="222" text-anchor="middle" class="chart-label">Elapsed time (seconds)</text><text x="14" y="115.0" text-anchor="middle" transform="rotate(-90 14 115)" class="chart-label">CPU utilization (%)</text><text x="702" y="206" text-anchor="end" class="chart-label">1.000s</text></svg>

Evidence references: none recorded

## TEL-001 — ! WARN

Duration: 0.000957 seconds
Injected: no

Reason: temperature telemetry is unavailable

### Measurements

| Metric | Value | Unit | Classification | Source |
| --- | --- | --- | --- | --- |
| available_memory_available | true | — | measured | psutil |
| cpu_frequency_available | true | — | measured | psutil |
| cpu_utilization_available | true | — | measured | psutil |
| disk_free_available | true | — | measured | psutil |
| per_core_utilization_available | true | — | measured | psutil |
| process_cpu_available | true | — | measured | psutil |
| process_memory_available | true | — | measured | psutil |
| temperature_available | false | — | measured | psutil |

### Requirements

No explicit requirements were configured.

### Telemetry

| Derived statistic | Value | Unit | Source |
| --- | --- | --- | --- |
| Sample count | 1 | samples | telemetry series |
| CPU utilization minimum | 0 | % | telemetry series |
| CPU utilization average | 0 | % | telemetry series |
| CPU utilization maximum | 0 | % | telemetry series |
| Peak process memory | 45.34 | MiB | telemetry series |

Unavailable telemetry: temperature.

<svg viewBox="0 0 720 230" role="img" aria-labelledby="chart-title-TEL-001 chart-desc-TEL-001"><title id="chart-title-TEL-001">TEL-001 CPU utilization</title><desc id="chart-desc-TEL-001">CPU utilization percent over elapsed seconds.</desc><line x1="54" y1="188.00" x2="702" y2="188.00" class="chart-grid" /><text x="46" y="192.00" text-anchor="end" class="chart-label">0</text><line x1="54" y1="105.00" x2="702" y2="105.00" class="chart-grid" /><text x="46" y="109.00" text-anchor="end" class="chart-label">50</text><line x1="54" y1="22.00" x2="702" y2="22.00" class="chart-grid" /><text x="46" y="26.00" text-anchor="end" class="chart-label">100</text><line x1="54" y1="22" x2="54" y2="188" class="chart-axis" /><line x1="54" y1="188" x2="702" y2="188" class="chart-axis" /><circle cx="54.00" cy="188.00" r="4" class="chart-point" /><text x="360.0" y="222" text-anchor="middle" class="chart-label">Elapsed time (seconds)</text><text x="14" y="115.0" text-anchor="middle" transform="rotate(-90 14 115)" class="chart-label">CPU utilization (%)</text><text x="702" y="206" text-anchor="end" class="chart-label">1.000s</text></svg>

Evidence references: none recorded

## STB-001 — ✓ PASS

Duration: 0.002286 seconds
Injected: no

### Measurements

| Metric | Value | Unit | Classification | Source |
| --- | --- | --- | --- | --- |
| median_absolute_deviation | 5.7999277e-06 | seconds | derived | scheduler_stability |
| median_duration | 0.00037459994 | seconds | derived | scheduler_stability |
| repetitions | 3 | runs | measured | scheduler_stability |
| robust_variability | 1.5482992 | % | derived | scheduler_stability |

### Requirements

No explicit requirements were configured.

### Telemetry

| Derived statistic | Value | Unit | Source |
| --- | --- | --- | --- |
| Sample count | 1 | samples | telemetry series |
| CPU utilization minimum | 0 | % | telemetry series |
| CPU utilization average | 0 | % | telemetry series |
| CPU utilization maximum | 0 | % | telemetry series |
| Peak process memory | 45.35 | MiB | telemetry series |

Unavailable telemetry: temperature.

<svg viewBox="0 0 720 230" role="img" aria-labelledby="chart-title-STB-001 chart-desc-STB-001"><title id="chart-title-STB-001">STB-001 CPU utilization</title><desc id="chart-desc-STB-001">CPU utilization percent over elapsed seconds.</desc><line x1="54" y1="188.00" x2="702" y2="188.00" class="chart-grid" /><text x="46" y="192.00" text-anchor="end" class="chart-label">0</text><line x1="54" y1="105.00" x2="702" y2="105.00" class="chart-grid" /><text x="46" y="109.00" text-anchor="end" class="chart-label">50</text><line x1="54" y1="22.00" x2="702" y2="22.00" class="chart-grid" /><text x="46" y="26.00" text-anchor="end" class="chart-label">100</text><line x1="54" y1="22" x2="54" y2="188" class="chart-axis" /><line x1="54" y1="188" x2="702" y2="188" class="chart-axis" /><circle cx="54.00" cy="188.00" r="4" class="chart-point" /><text x="360.0" y="222" text-anchor="middle" class="chart-label">Elapsed time (seconds)</text><text x="14" y="115.0" text-anchor="middle" transform="rotate(-90 14 115)" class="chart-label">CPU utilization (%)</text><text x="702" y="206" text-anchor="end" class="chart-label">1.000s</text></svg>

Evidence references: none recorded

## CFG-001 — ✓ PASS

Duration: 0.000696 seconds
Injected: no

### Measurements

| Metric | Value | Unit | Classification | Source |
| --- | --- | --- | --- | --- |
| cpu.aes | true | — | measured | native_cpuid_probe |
| cpu.avx2_hardware | true | — | measured | native_cpuid_probe |
| cpu.avx_hardware | true | — | measured | native_cpuid_probe |
| cpu.avx_os_enabled | true | — | measured | native_cpuid_probe |
| cpu.sse2 | true | — | measured | native_cpuid_probe |
| cpu.sse41 | true | — | measured | native_cpuid_probe |
| cpu.sse42 | true | — | measured | native_cpuid_probe |
| cpu.virtualization_hardware | false | — | measured | native_cpuid_probe |

### Requirements

| Result | Metric | Operator | Configured expected | Measured actual | Unit |
| --- | --- | --- | --- | --- | --- |
| PASS | cpu.sse2 | equals | true [configured] | true [measured] | — |

### Telemetry

| Derived statistic | Value | Unit | Source |
| --- | --- | --- | --- |
| Sample count | 1 | samples | telemetry series |
| CPU utilization minimum | 0 | % | telemetry series |
| CPU utilization average | 0 | % | telemetry series |
| CPU utilization maximum | 0 | % | telemetry series |
| Peak process memory | 45.35 | MiB | telemetry series |

Unavailable telemetry: temperature.

<svg viewBox="0 0 720 230" role="img" aria-labelledby="chart-title-CFG-001 chart-desc-CFG-001"><title id="chart-title-CFG-001">CFG-001 CPU utilization</title><desc id="chart-desc-CFG-001">CPU utilization percent over elapsed seconds.</desc><line x1="54" y1="188.00" x2="702" y2="188.00" class="chart-grid" /><text x="46" y="192.00" text-anchor="end" class="chart-label">0</text><line x1="54" y1="105.00" x2="702" y2="105.00" class="chart-grid" /><text x="46" y="109.00" text-anchor="end" class="chart-label">50</text><line x1="54" y1="22.00" x2="702" y2="22.00" class="chart-grid" /><text x="46" y="26.00" text-anchor="end" class="chart-label">100</text><line x1="54" y1="22" x2="54" y2="188" class="chart-axis" /><line x1="54" y1="188" x2="702" y2="188" class="chart-axis" /><circle cx="54.00" cy="188.00" r="4" class="chart-point" /><text x="360.0" y="222" text-anchor="middle" class="chart-label">Elapsed time (seconds)</text><text x="14" y="115.0" text-anchor="middle" transform="rotate(-90 14 115)" class="chart-label">CPU utilization (%)</text><text x="702" y="206" text-anchor="end" class="chart-label">1.000s</text></svg>

Evidence references: none recorded

## Warnings

- A trustworthy temperature source is unavailable; runtime limits remain conservative.

## Limitations

- A trustworthy temperature source is unavailable; runtime limits remain conservative.

## Interpretation notes

- Results are local software observations, not hardware certification.
- A failed test supports further diagnosis but does not alone prove defective hardware.
- Timing can be influenced by scheduler activity, power policy, background load, and unavailable thermal data.
- Missing telemetry is reported as unavailable and is never represented as numeric zero.
