# Captured evidence

Captured 20 September 2026 in Asia/Kuala_Lumpur; embedded report timestamps are UTC (19 September). Source: published MVP `73c14ff`. No workload implementation changes were made for this capture.

## Measured quick plan

`python -m platval.cli run --plan configs/quick.yaml --runtime-dir <local-evidence-directory> --json`

Environment: Windows 11, Python 3.12, AMD64, 6 physical / 12 logical processors, approximately 31.29 GiB available installed memory as reported by psutil. The optional native probe was not installed. The [Markdown](measured/report.md), [HTML](measured/report.html) and [canonical JSON](measured/run.json) are generated outputs, not illustrations.

Result: seven PASS, one WARN, one SKIP. Read the per-test reasons; unavailable temperature/native capabilities are not zeros or passes. Very short workloads can produce only one telemetry sample; the charts do not establish sustained thermal or load behavior. Durations and throughput are one local observation, not a cross-system benchmark.

## Injected failure

`python -m platval.cli demo failure --runtime-dir <separate-local-evidence-directory>`

The [Markdown](injected/report.md), [HTML](injected/report.html) and [JSON](injected/run.json) label the deliberate checksum mismatch as synthetic/injected. The observed FAIL is the intended result, not a hardware defect.

## Baseline exercise

A baseline was created from the measured run and compared to that same run. This checks storage, lookup and comparison execution only. Independent repeat runs under controlled conditions are still needed for an empirical regression demonstration.

## Sharing and viewing

Reports contain sanitized configuration, numeric resource capacities, UTC timestamps and hashes. They do not contain usernames, hostnames, MAC/IP addresses, device serials or private filesystem paths. Review configuration details before future publication. GitHub does not execute checked-in HTML; download it and open locally. The generated Markdown includes inline SVG charts that GitHub may strip; the HTML and captured PNG previews preserve those charts.
