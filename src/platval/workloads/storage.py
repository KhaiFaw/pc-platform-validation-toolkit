"""Owned-directory temporary-storage round-trip verification."""

import hashlib
import os
import shutil
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil
from pydantic import Field

from platval.models.common import DomainModel
from platval.workloads.control import CancellationToken, WorkloadContext
from platval.workloads.errors import SafetyLimitError
from platval.workloads.models import WorkloadMeasurement, WorkloadResult
from platval.workloads.safety import MIB, SafetyPolicy, resolve_policy


class StorageWorkloadConfig(DomainModel):
    size_bytes: int = Field(default=64 * MIB, ge=4096, le=1024 * MIB)
    block_size_bytes: int = Field(default=MIB, ge=4096, le=8 * MIB)


def _deterministic_block(index: int, size: int) -> bytes:
    seed = hashlib.sha256(f"platval-storage-block-{index}".encode()).digest()
    return (seed * ((size + len(seed) - 1) // len(seed)))[:size]


def run_storage_workload(
    config: StorageWorkloadConfig,
    *,
    temporary_root: Path,
    timeout_seconds: float,
    policy: SafetyPolicy | None = None,
    token: CancellationToken | None = None,
) -> WorkloadResult:
    """Write, flush, read, and remove one deterministic file in an owned directory."""
    active_policy = resolve_policy(policy)
    active_policy.require_timeout(timeout_seconds)
    active_policy.require_temporary_file(config.size_bytes)
    root = temporary_root.resolve()
    if not root.is_dir():
        raise ValueError("temporary root must be an existing directory")
    free_bytes = psutil.disk_usage(str(root)).free
    required_bytes = config.size_bytes + active_policy.minimum_disk_reserve_bytes
    if free_bytes < required_bytes:
        raise SafetyLimitError(
            "insufficient free space after preserving the configured disk reserve"
        )

    context = WorkloadContext.create(timeout_seconds, token)
    context.checkpoint()
    started_at = datetime.now(UTC)
    started = time.monotonic()
    test_directory: Path | None = None
    write_seconds = 0.0
    read_seconds = 0.0
    expected_checksum = ""
    actual_checksum = ""
    try:
        test_directory = Path(tempfile.mkdtemp(prefix="platval-storage-", dir=root))
        test_file = test_directory / "round-trip.bin"
        expected_hasher = hashlib.sha256()
        write_started = time.monotonic()
        with test_file.open("xb") as handle:
            remaining = config.size_bytes
            index = 0
            while remaining:
                context.checkpoint()
                length = min(config.block_size_bytes, remaining)
                block = _deterministic_block(index, length)
                handle.write(block)
                expected_hasher.update(block)
                remaining -= length
                index += 1
            handle.flush()
            os.fsync(handle.fileno())
        write_seconds = time.monotonic() - write_started
        expected_checksum = expected_hasher.hexdigest()

        actual_hasher = hashlib.sha256()
        read_started = time.monotonic()
        with test_file.open("rb") as handle:
            while True:
                context.checkpoint()
                block = handle.read(config.block_size_bytes)
                if not block:
                    break
                actual_hasher.update(block)
        read_seconds = time.monotonic() - read_started
        actual_checksum = actual_hasher.hexdigest()
    finally:
        if test_directory is not None:
            shutil.rmtree(test_directory)

    duration = time.monotonic() - started
    ended_at = datetime.now(UTC)
    return WorkloadResult(
        workload="temporary_storage_round_trip",
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration,
        correct=actual_checksum == expected_checksum,
        checksum=actual_checksum,
        measurements={
            "checksum_valid": WorkloadMeasurement(value=actual_checksum == expected_checksum),
            "file_size": WorkloadMeasurement(value=config.size_bytes, unit="bytes"),
            "write_throughput": WorkloadMeasurement(
                value=config.size_bytes / max(write_seconds, 1e-12), unit="bytes/s"
            ),
            "read_throughput": WorkloadMeasurement(
                value=config.size_bytes / max(read_seconds, 1e-12), unit="bytes/s"
            ),
        },
        notes=["This is a local functional sample, not a universal storage benchmark."],
    )
