"""Deterministic bounded CPU and scheduler-stability workloads."""

import hashlib
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from pydantic import Field, model_validator

from platval.models.common import DomainModel
from platval.workloads.control import CancellationToken, WorkloadContext
from platval.workloads.models import WorkloadMeasurement, WorkloadResult
from platval.workloads.safety import MIB, SafetyPolicy, resolve_policy


class IntegerWorkloadConfig(DomainModel):
    workers: int = Field(default=1, ge=1)
    operations: int = Field(default=256, ge=1, le=1_000_000)
    block_size_bytes: int = Field(default=64 * 1024, ge=4096, le=MIB)
    expected_checksum: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def operations_cover_workers(self) -> "IntegerWorkloadConfig":
        if self.operations < self.workers:
            raise ValueError("operations must be at least the worker count")
        return self


class FloatingPointWorkloadConfig(DomainModel):
    iterations: int = Field(default=1_000_000, ge=1, le=20_000_000)
    tolerance: float = Field(default=1e-12, gt=0, le=1e-6)


class StabilityWorkloadConfig(DomainModel):
    repetitions: int = Field(default=5, ge=3, le=20)
    integer: IntegerWorkloadConfig = Field(
        default_factory=lambda: IntegerWorkloadConfig(operations=64, block_size_bytes=16 * 1024)
    )


def _worker_block(worker_index: int, block_size: int) -> bytes:
    seed = hashlib.sha256(f"platval-integer-worker-{worker_index}".encode()).digest()
    return (seed * ((block_size + len(seed) - 1) // len(seed)))[:block_size]


def _hash_worker(
    worker_index: int,
    operations: int,
    block_size: int,
    context: WorkloadContext,
) -> bytes:
    block = _worker_block(worker_index, block_size)
    aggregate = hashlib.sha256()
    for iteration in range(operations):
        context.checkpoint()
        aggregate.update(hashlib.sha256(block + iteration.to_bytes(8, "little")).digest())
    return aggregate.digest()


def _operation_counts(total: int, workers: int) -> list[int]:
    base, remainder = divmod(total, workers)
    return [base + (1 if index < remainder else 0) for index in range(workers)]


def _combine_worker_digests(digests: list[bytes]) -> str:
    aggregate = hashlib.sha256()
    for digest in digests:
        aggregate.update(digest)
    return aggregate.hexdigest()


def _reference_checksum(config: IntegerWorkloadConfig, context: WorkloadContext) -> str:
    digests = [
        _hash_worker(index, count, config.block_size_bytes, context)
        for index, count in enumerate(_operation_counts(config.operations, config.workers))
    ]
    return _combine_worker_digests(digests)


def run_integer_workload(
    config: IntegerWorkloadConfig,
    *,
    timeout_seconds: float,
    policy: SafetyPolicy | None = None,
    token: CancellationToken | None = None,
) -> WorkloadResult:
    """Compare concurrent deterministic hashing with a sequential reference."""
    active_policy = resolve_policy(policy)
    active_policy.require_workers(config.workers)
    active_policy.require_memory(config.workers * config.block_size_bytes)
    active_policy.require_timeout(timeout_seconds)
    context = WorkloadContext.create(timeout_seconds, token)
    context.checkpoint()
    started_at = datetime.now(UTC)
    total_start = time.monotonic()

    expected = config.expected_checksum or _reference_checksum(config, context)
    counts = _operation_counts(config.operations, config.workers)
    measured_start = time.monotonic()
    with ThreadPoolExecutor(max_workers=config.workers, thread_name_prefix="platval-cpu") as pool:
        futures = [
            pool.submit(_hash_worker, index, count, config.block_size_bytes, context)
            for index, count in enumerate(counts)
        ]
        try:
            digests = [future.result() for future in futures]
        except BaseException:
            context.token.cancel()
            raise
    measured_seconds = time.monotonic() - measured_start
    checksum = _combine_worker_digests(digests)
    ended_at = datetime.now(UTC)
    duration = time.monotonic() - total_start
    return WorkloadResult(
        workload="cpu_integer",
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration,
        correct=checksum == expected,
        checksum=checksum,
        measurements={
            "checksum_valid": WorkloadMeasurement(value=checksum == expected),
            "operations": WorkloadMeasurement(value=config.operations, unit="blocks"),
            "workers": WorkloadMeasurement(value=config.workers, unit="workers"),
            "measured_duration": WorkloadMeasurement(value=measured_seconds, unit="seconds"),
            "operations_per_second": WorkloadMeasurement(
                value=config.operations / max(measured_seconds, 1e-12), unit="blocks/s"
            ),
        },
    )


def run_floating_point_workload(
    config: FloatingPointWorkloadConfig,
    *,
    timeout_seconds: float,
    policy: SafetyPolicy | None = None,
    token: CancellationToken | None = None,
) -> WorkloadResult:
    """Evaluate a telescoping series with compensated summation and a closed-form result."""
    active_policy = resolve_policy(policy)
    active_policy.require_timeout(timeout_seconds)
    context = WorkloadContext.create(timeout_seconds, token)
    context.checkpoint()
    started_at = datetime.now(UTC)
    started = time.monotonic()
    total = 0.0
    compensation = 0.0
    for index in range(1, config.iterations + 1):
        if index % 4096 == 0:
            context.checkpoint()
        term = 1.0 / (index * (index + 1))
        adjusted = term - compensation
        updated = total + adjusted
        compensation = (updated - total) - adjusted
        total = updated
    context.checkpoint()
    duration = time.monotonic() - started
    expected = config.iterations / (config.iterations + 1)
    absolute_error = abs(total - expected)
    ended_at = datetime.now(UTC)
    return WorkloadResult(
        workload="cpu_floating_point",
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration,
        correct=absolute_error <= config.tolerance,
        measurements={
            "actual": WorkloadMeasurement(value=total),
            "expected": WorkloadMeasurement(value=expected),
            "absolute_error": WorkloadMeasurement(value=absolute_error),
            "tolerance": WorkloadMeasurement(value=config.tolerance),
            "operations_per_second": WorkloadMeasurement(
                value=config.iterations / max(duration, 1e-12), unit="terms/s"
            ),
        },
        notes=[
            "Floating-point results are evaluated against a local tolerance, "
            "not ranked across platforms."
        ],
    )


def run_stability_workload(
    config: StabilityWorkloadConfig,
    *,
    timeout_seconds: float,
    policy: SafetyPolicy | None = None,
    token: CancellationToken | None = None,
) -> WorkloadResult:
    """Repeat a short workload and report median absolute timing deviation."""
    active_policy = resolve_policy(policy)
    active_policy.require_timeout(timeout_seconds)
    context = WorkloadContext.create(timeout_seconds, token)
    started_at = datetime.now(UTC)
    started = time.monotonic()
    durations: list[float] = []
    expected_checksum = config.integer.expected_checksum
    correct = True
    for _ in range(config.repetitions):
        remaining = context.remaining_seconds()
        current_config = config.integer.model_copy(update={"expected_checksum": expected_checksum})
        result = run_integer_workload(
            current_config,
            timeout_seconds=remaining,
            policy=active_policy,
            token=context.token,
        )
        expected_checksum = result.checksum
        correct = correct and result.correct
        duration_value = result.measurements["measured_duration"].value
        if not isinstance(duration_value, (int, float)):
            raise TypeError("integer workload returned a non-numeric duration")
        durations.append(float(duration_value))
    median_duration = statistics.median(durations)
    mad = statistics.median(abs(value - median_duration) for value in durations)
    robust_variability_percent = 100.0 * mad / max(median_duration, 1e-12)
    ended_at = datetime.now(UTC)
    return WorkloadResult(
        workload="scheduler_stability",
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=time.monotonic() - started,
        correct=correct,
        checksum=expected_checksum,
        measurements={
            "repetitions": WorkloadMeasurement(value=config.repetitions, unit="runs"),
            "median_duration": WorkloadMeasurement(value=median_duration, unit="seconds"),
            "median_absolute_deviation": WorkloadMeasurement(value=mad, unit="seconds"),
            "robust_variability": WorkloadMeasurement(value=robust_variability_percent, unit="%"),
        },
        notes=["High timing variability is evidence for a WARN, not proof of a hardware defect."],
    )
