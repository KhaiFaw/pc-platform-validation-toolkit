"""Validation runner lifecycle from typed plan to canonical structured result."""

import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from pydantic import Field

from platval.collectors import PsutilTelemetrySampler
from platval.constants import TOOL_VERSION
from platval.evaluation import EvaluationError, evaluate_requirement
from platval.inventory import InventorySnapshot, collect_platform_inventory
from platval.models.common import DomainModel, Scalar
from platval.models.plan import TestDefinition, TestPlan
from platval.models.platform import PlatformIdentity
from platval.models.results import (
    MetricValue,
    RunResult,
    TelemetrySummary,
    TestResult,
    aggregate_status,
)
from platval.models.status import ResultStatus
from platval.models.telemetry import TelemetrySample
from platval.runner.plan_loader import canonical_plan_hash
from platval.workloads import (
    CancellationToken,
    FloatingPointWorkloadConfig,
    IntegerWorkloadConfig,
    MemoryWorkloadConfig,
    SafetyPolicy,
    StabilityWorkloadConfig,
    StorageWorkloadConfig,
    WorkloadCancelled,
    WorkloadTimeout,
    run_floating_point_workload,
    run_integer_workload,
    run_memory_workload,
    run_stability_workload,
    run_storage_workload,
)
from platval.workloads.models import WorkloadResult


class RunExecution(DomainModel):
    run: RunResult
    platform: PlatformIdentity
    telemetry_samples: dict[str, list[TelemetrySample]] = Field(default_factory=dict)


@dataclass(slots=True)
class _CaseExecution:
    correct: bool = True
    measurements: dict[str, MetricValue] = field(default_factory=dict)
    status_hint: ResultStatus = ResultStatus.PASS
    reason: str | None = None


def _parameter(test: TestDefinition, name: str, default: Scalar) -> Scalar:
    return test.parameters.get(name, default)


def _int_parameter(test: TestDefinition, name: str, default: int) -> int:
    value = _parameter(test, name, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"parameter {name!r} must be an integer")
    return value


def _float_parameter(test: TestDefinition, name: str, default: float) -> float:
    value = _parameter(test, name, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"parameter {name!r} must be numeric")
    return float(value)


def _string_parameter(test: TestDefinition, name: str) -> str | None:
    value = _parameter(test, name, None)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"parameter {name!r} must be a string")
    return value


def _case_policy(test: TestDefinition, detected: SafetyPolicy) -> SafetyPolicy:
    limits = test.safety_limits
    return SafetyPolicy(
        max_workers=min(detected.max_workers, limits.max_workers or detected.max_workers),
        max_memory_bytes=min(
            detected.max_memory_bytes, limits.max_memory_bytes or detected.max_memory_bytes
        ),
        max_temporary_file_bytes=min(
            detected.max_temporary_file_bytes,
            limits.max_temporary_file_bytes or detected.max_temporary_file_bytes,
        ),
        max_duration_seconds=min(detected.max_duration_seconds, test.timeout_seconds),
        minimum_disk_reserve_bytes=detected.minimum_disk_reserve_bytes,
    )


def _workload_case(result: WorkloadResult) -> _CaseExecution:
    return _CaseExecution(
        correct=result.correct,
        measurements={
            name: MetricValue(
                value=measurement.value, unit=measurement.unit, source=result.workload
            )
            for name, measurement in result.measurements.items()
        },
        reason=None if result.correct else "workload correctness verification failed",
    )


def _inventory_case(snapshot: InventorySnapshot) -> _CaseExecution:
    platform = snapshot.platform
    return _CaseExecution(
        measurements={
            "logical_cpu_count": MetricValue(
                value=platform.logical_processor_count, unit="processors", source="inventory"
            ),
            "physical_cpu_count": MetricValue(
                value=platform.physical_processor_count, unit="processors", source="inventory"
            ),
            "total_memory_bytes": MetricValue(
                value=platform.total_memory_bytes, unit="bytes", source="inventory"
            ),
            "storage_free_bytes": MetricValue(
                value=platform.storage_volume.free_bytes, unit="bytes", source="inventory"
            ),
            "architecture": MetricValue(value=platform.architecture, source="inventory"),
        }
    )


def _telemetry_case(snapshot: InventorySnapshot) -> _CaseExecution:
    measurements = {
        f"{capability.metric}_available": MetricValue(
            value=capability.available, source=capability.source
        )
        for capability in snapshot.capabilities
    }
    temperature_available = bool(measurements["temperature_available"].value)
    return _CaseExecution(
        measurements=measurements,
        status_hint=ResultStatus.PASS if temperature_available else ResultStatus.WARN,
        reason=None if temperature_available else "temperature telemetry is unavailable",
    )


def _configuration_case(snapshot: InventorySnapshot) -> _CaseExecution:
    if not snapshot.platform.capability_flags.get("native_cpuid_probe", False):
        return _CaseExecution(
            status_hint=ResultStatus.SKIP,
            reason="native CPUID probe is unavailable; CPU feature requirements were not evaluated",
        )
    return _CaseExecution(
        measurements={
            name: MetricValue(value=value, source="native_cpuid_probe")
            for name, value in snapshot.platform.capability_flags.items()
            if name.startswith("cpu.")
        }
    )


def _execute_case(
    test: TestDefinition,
    *,
    snapshot: InventorySnapshot,
    storage_root: Path,
    policy: SafetyPolicy,
    token: CancellationToken,
) -> _CaseExecution:
    if test.id == "INV-001":
        return _inventory_case(snapshot)
    if test.id in {"CPU-001", "CPU-003"}:
        workers_default = 1 if test.id == "CPU-001" else min(2, policy.max_workers)
        result = run_integer_workload(
            IntegerWorkloadConfig(
                workers=_int_parameter(test, "workers", workers_default),
                operations=_int_parameter(test, "workload_size", 256),
                block_size_bytes=_int_parameter(test, "block_size_bytes", 64 * 1024),
                expected_checksum=_string_parameter(test, "expected_checksum"),
            ),
            timeout_seconds=test.timeout_seconds,
            policy=policy,
            token=token,
        )
        return _workload_case(result)
    if test.id == "CPU-002":
        return _workload_case(
            run_floating_point_workload(
                FloatingPointWorkloadConfig(
                    iterations=_int_parameter(test, "iterations", 1_000_000),
                    tolerance=_float_parameter(test, "tolerance", 1e-12),
                ),
                timeout_seconds=test.timeout_seconds,
                policy=policy,
                token=token,
            )
        )
    if test.id == "MEM-001":
        allocation = _parameter(test, "allocation_bytes", None)
        if allocation is not None and (
            isinstance(allocation, bool) or not isinstance(allocation, int)
        ):
            raise ValueError("parameter 'allocation_bytes' must be an integer")
        return _workload_case(
            run_memory_workload(
                MemoryWorkloadConfig(allocation_bytes=allocation),
                timeout_seconds=test.timeout_seconds,
                policy=policy,
                token=token,
            )
        )
    if test.id == "STO-001":
        return _workload_case(
            run_storage_workload(
                StorageWorkloadConfig(
                    size_bytes=_int_parameter(test, "size_bytes", 64 * 1024 * 1024),
                    block_size_bytes=_int_parameter(test, "block_size_bytes", 1024 * 1024),
                ),
                temporary_root=storage_root,
                timeout_seconds=test.timeout_seconds,
                policy=policy,
                token=token,
            )
        )
    if test.id == "TEL-001":
        return _telemetry_case(snapshot)
    if test.id == "STB-001":
        case = _workload_case(
            run_stability_workload(
                StabilityWorkloadConfig(
                    repetitions=_int_parameter(test, "repetitions", 5),
                    integer=IntegerWorkloadConfig(
                        workers=_int_parameter(test, "workers", 1),
                        operations=_int_parameter(test, "workload_size", 64),
                        block_size_bytes=_int_parameter(test, "block_size_bytes", 16 * 1024),
                    ),
                ),
                timeout_seconds=test.timeout_seconds,
                policy=policy,
                token=token,
            )
        )
        variability = case.measurements["robust_variability"].value
        threshold = _float_parameter(test, "warn_variability_percent", 50.0)
        if isinstance(variability, (int, float)) and variability > threshold:
            case.status_hint = ResultStatus.WARN
            case.reason = "timing variability exceeded the configured soft threshold"
        return case
    if test.id == "CFG-001":
        return _configuration_case(snapshot)
    if test.id == "REG-001":
        return _CaseExecution(
            status_hint=ResultStatus.SKIP,
            reason="baseline comparison is not available until Milestone 8",
        )
    return _CaseExecution(
        status_hint=ResultStatus.SKIP,
        reason=f"no workload implementation is registered for {test.id}",
    )


def _telemetry_summary(samples: list[TelemetrySample]) -> TelemetrySummary:
    availability = {
        "cpu_utilization": any(sample.cpu_utilization_percent is not None for sample in samples),
        "per_core_utilization": any(
            sample.per_core_utilization_percent is not None for sample in samples
        ),
        "cpu_frequency": any(sample.cpu_frequency_mhz is not None for sample in samples),
        "process_cpu": any(sample.process_cpu_percent is not None for sample in samples),
        "process_memory": any(sample.process_memory_bytes is not None for sample in samples),
        "available_memory": any(sample.available_memory_bytes is not None for sample in samples),
        "disk_free": any(sample.disk_free_bytes is not None for sample in samples),
        "temperature": any(bool(sample.temperatures) for sample in samples),
    }
    available = [name for name, is_available in availability.items() if is_available]
    return TelemetrySummary(
        sample_count=len(samples),
        available_metrics=available,
        unavailable_metrics=[name for name in availability if name not in available],
        collector_error_count=sum(len(sample.collector_errors) for sample in samples),
    )


def _run_test(
    test: TestDefinition,
    *,
    snapshot: InventorySnapshot,
    storage_path: Path,
    temporary_root: Path,
    sampling_interval_seconds: float,
    detected_policy: SafetyPolicy,
    run_token: CancellationToken,
) -> tuple[TestResult, list[TelemetrySample]]:
    started_at = datetime.now(UTC)
    started = time.monotonic()
    if not test.enabled:
        ended_at = datetime.now(UTC)
        return (
            TestResult(
                test_id=test.id,
                started_at=started_at,
                ended_at=ended_at,
                duration_seconds=time.monotonic() - started,
                status=ResultStatus.SKIP,
                failure_reason="test is disabled in the plan",
                telemetry_summary=_telemetry_summary([]),
            ),
            [],
        )

    sampler = PsutilTelemetrySampler(
        interval_seconds=sampling_interval_seconds,
        storage_path=storage_path,
        max_samples=min(10_000, max(1, int(test.timeout_seconds / sampling_interval_seconds) + 2)),
    )
    sampler.start()
    case = _CaseExecution()
    exception_summary: str | None = None
    child_token = CancellationToken(parent=run_token)
    try:
        case = _execute_case(
            test,
            snapshot=snapshot,
            storage_root=temporary_root,
            policy=_case_policy(test, detected_policy),
            token=child_token,
        )
    except WorkloadCancelled:
        raise
    except WorkloadTimeout as exc:
        case = _CaseExecution(status_hint=ResultStatus.ERROR, correct=False, reason=str(exc))
        exception_summary = type(exc).__name__
    except (OSError, ValueError, RuntimeError) as exc:
        case = _CaseExecution(
            status_hint=ResultStatus.ERROR,
            correct=False,
            reason="test execution failed before producing valid measurements",
        )
        exception_summary = f"{type(exc).__name__}: {exc}"
    finally:
        samples = sampler.stop()

    evaluations = []
    status = case.status_hint
    if status not in {ResultStatus.SKIP, ResultStatus.ERROR}:
        metric_values = {name: measurement.value for name, measurement in case.measurements.items()}
        try:
            evaluations = [
                evaluate_requirement(requirement, metric_values)
                for requirement in test.requirements
            ]
        except EvaluationError as exc:
            status = ResultStatus.ERROR
            case.reason = "requirement evaluation configuration is invalid"
            exception_summary = f"{type(exc).__name__}: {exc}"
        else:
            if not case.correct or any(not evaluation.passed for evaluation in evaluations):
                status = ResultStatus.FAIL
                case.reason = case.reason or "one or more explicit requirements were not met"

    ended_at = datetime.now(UTC)
    return (
        TestResult(
            test_id=test.id,
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=time.monotonic() - started,
            status=status,
            measured_values=case.measurements,
            requirements=evaluations,
            failure_reason=case.reason,
            exception_summary=exception_summary,
            telemetry_summary=_telemetry_summary(samples),
        ),
        samples,
    )


def run_validation_plan(
    plan: TestPlan,
    *,
    runtime_directory: Path,
    storage_path: Path | None = None,
    native_probe_path: Path | None = None,
    token: CancellationToken | None = None,
) -> RunExecution:
    """Execute a validated plan and retain structured results plus raw telemetry."""
    active_token = token or CancellationToken()
    runtime_directory.mkdir(parents=True, exist_ok=True)
    if storage_path is not None and not storage_path.is_dir():
        raise ValueError("storage path must be an existing directory")
    selected_storage = (storage_path or runtime_directory).resolve()
    temporary_root = runtime_directory / "tmp"
    temporary_root.mkdir(parents=True, exist_ok=True)
    run_started_at = datetime.now(UTC)
    snapshot = collect_platform_inventory(
        storage_path=selected_storage, native_probe_path=native_probe_path
    )
    detected_policy = SafetyPolicy.detected()
    results: list[TestResult] = []
    telemetry: dict[str, list[TelemetrySample]] = {}
    for test in plan.tests:
        if active_token.cancelled:
            raise WorkloadCancelled("validation run cancellation was requested")
        result, samples = _run_test(
            test,
            snapshot=snapshot,
            storage_path=selected_storage,
            temporary_root=temporary_root,
            sampling_interval_seconds=plan.sampling_interval_seconds,
            detected_policy=detected_policy,
            run_token=active_token,
        )
        results.append(result)
        telemetry[test.id] = samples
    run_ended_at = datetime.now(UTC)
    statuses = [result.status for result in results]
    return RunExecution(
        run=RunResult(
            run_id=str(uuid.uuid4()),
            plan_name=plan.name,
            plan_hash=canonical_plan_hash(plan),
            tool_version=TOOL_VERSION,
            platform_fingerprint=snapshot.platform.sanitized_platform_fingerprint,
            started_at=run_started_at,
            ended_at=run_ended_at,
            overall_status=aggregate_status(statuses),
            result_counts=dict(Counter(statuses)),
            test_results=results,
            warnings=snapshot.limitations,
            limitations=snapshot.limitations,
        ),
        platform=snapshot.platform,
        telemetry_samples=telemetry,
    )
