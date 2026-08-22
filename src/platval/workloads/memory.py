"""Bounded deterministic application-visible memory verification."""

import hashlib
import time
from datetime import UTC, datetime

import psutil
from pydantic import Field

from platval.models.common import DomainModel
from platval.workloads.control import CancellationToken, WorkloadContext
from platval.workloads.models import WorkloadMeasurement, WorkloadResult
from platval.workloads.safety import MIB, SafetyPolicy, resolve_policy

_DEFAULT_MAX_ALLOCATION = 256 * MIB
_PATTERN = bytes((index * 131 + 17) & 0xFF for index in range(256))
_TRANSFORM_TABLE = bytes(index ^ 0xA5 for index in range(256))


class MemoryWorkloadConfig(DomainModel):
    allocation_bytes: int | None = Field(default=None, ge=4096)
    chunk_size_bytes: int = Field(default=MIB, ge=4096, le=8 * MIB)


def default_memory_allocation(policy: SafetyPolicy | None = None) -> int:
    """Use the lesser of 256 MiB, 10% available memory, and the policy limit."""
    active_policy = resolve_policy(policy)
    available = psutil.virtual_memory().available
    return max(4096, min(_DEFAULT_MAX_ALLOCATION, available // 10, active_policy.max_memory_bytes))


def _pattern_chunk(size: int, *, transformed: bool) -> bytes:
    source = _PATTERN.translate(_TRANSFORM_TABLE) if transformed else _PATTERN
    return (source * ((size + len(source) - 1) // len(source)))[:size]


def run_memory_workload(
    config: MemoryWorkloadConfig,
    *,
    timeout_seconds: float,
    policy: SafetyPolicy | None = None,
    token: CancellationToken | None = None,
) -> WorkloadResult:
    """Fill, transform, and checksum one bounded byte buffer."""
    active_policy = resolve_policy(policy)
    active_policy.require_timeout(timeout_seconds)
    allocation = config.allocation_bytes or default_memory_allocation(active_policy)
    active_policy.require_memory(allocation)
    context = WorkloadContext.create(timeout_seconds, token)
    context.checkpoint()
    started_at = datetime.now(UTC)
    started = time.monotonic()
    buffer = bytearray(allocation)
    chunk_size = min(config.chunk_size_bytes, allocation)
    source_chunk = _pattern_chunk(chunk_size, transformed=False)

    for offset in range(0, allocation, chunk_size):
        context.checkpoint()
        length = min(chunk_size, allocation - offset)
        buffer[offset : offset + length] = source_chunk[:length]

    expected_hasher = hashlib.sha256()
    transformed_chunk = _pattern_chunk(chunk_size, transformed=True)
    for offset in range(0, allocation, chunk_size):
        context.checkpoint()
        length = min(chunk_size, allocation - offset)
        buffer[offset : offset + length] = buffer[offset : offset + length].translate(
            _TRANSFORM_TABLE
        )
        expected_hasher.update(transformed_chunk[:length])

    actual_hasher = hashlib.sha256()
    view = memoryview(buffer)
    for offset in range(0, allocation, chunk_size):
        context.checkpoint()
        actual_hasher.update(view[offset : offset + min(chunk_size, allocation - offset)])
    actual_checksum = actual_hasher.hexdigest()
    expected_checksum = expected_hasher.hexdigest()
    duration = time.monotonic() - started
    ended_at = datetime.now(UTC)
    view.release()
    return WorkloadResult(
        workload="memory_pattern",
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration,
        correct=actual_checksum == expected_checksum,
        checksum=actual_checksum,
        measurements={
            "checksum_valid": WorkloadMeasurement(value=actual_checksum == expected_checksum),
            "allocation": WorkloadMeasurement(value=allocation, unit="bytes"),
            "processed_bytes": WorkloadMeasurement(value=allocation * 3, unit="bytes"),
            "throughput": WorkloadMeasurement(
                value=(allocation * 3) / max(duration, 1e-12), unit="bytes/s"
            ),
        },
        notes=["This verifies application-visible memory, not physical DRAM in isolation."],
    )
