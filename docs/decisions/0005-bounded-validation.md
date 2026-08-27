# ADR-0005: Bounded validation instead of unrestricted stress testing

## Status

Accepted

## Decision

Use finite functional workloads governed by a central safety policy, monotonic deadlines, cooperative cancellation, resource ceilings, and owned temporary storage. Do not implement voltage, frequency, firmware, raw-disk, power-limit, or security-setting controls.

## Consequences

Runs provide reproducible application-visible evidence with lower operational risk, but they cannot replace specialized thermal, electrical, endurance, or hardware-certification testing. Performance observations remain local and must not be presented as universal rankings.
