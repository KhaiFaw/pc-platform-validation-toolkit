# ADR-0004: Capability-based optional sensors

## Status

Accepted

## Decision

Discover telemetry capabilities at runtime and model every optional reading as nullable evidence with an explicit source. A missing or failed sensor produces a documented WARN or SKIP where appropriate; it is never guessed, replaced with zero, or satisfied by automatically installing monitoring software.

## Consequences

The toolkit remains portable and honest about environmental limits. Plans cannot assume temperature or frequency support, and reports must preserve unavailable fields. New sensor adapters can be added without changing result semantics.
