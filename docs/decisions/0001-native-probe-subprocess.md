# ADR-0001: Keep the native CPUID probe behind a subprocess boundary

Status: Accepted

## Context

CPUID decoding benefits from C++ compiler intrinsics, while orchestration, configuration, persistence, and reporting are easier to test in Python. A Python extension would tightly couple interpreter and compiler versions and make degraded operation harder.

## Decision

Build `cpuid_probe` as a small standalone C++20 executable with a versioned JSON response. Python invokes it with a timeout, validates its schema, summarizes standard-error diagnostics, and treats absence or incompatibility as a documented missing capability.

## Consequences

The boundary is easy to inspect and replace, and synthetic responses can test decoding integration. Process startup has a small cost and both sides must maintain compatible schema versions. The probe must never emit identifying data beyond the documented contract.
