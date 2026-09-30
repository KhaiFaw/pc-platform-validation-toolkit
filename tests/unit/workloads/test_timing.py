import time
from pathlib import Path

import pytest

from platval.workloads import (
    FloatingPointWorkloadConfig,
    IntegerWorkloadConfig,
    MemoryWorkloadConfig,
    StabilityWorkloadConfig,
    StorageWorkloadConfig,
    run_floating_point_workload,
    run_integer_workload,
    run_memory_workload,
    run_stability_workload,
    run_storage_workload,
)
from platval.workloads.timing import rate_per_second


@pytest.mark.parametrize("duration", [0.0, -0.1, float("nan"), float("inf")])
def test_unmeasurable_rate_is_unavailable_not_epsilon_derived(duration: float) -> None:
    assert rate_per_second(64, duration) is None


def test_finite_rate_preserves_actual_duration() -> None:
    assert rate_per_second(64, 0.002) == 32_000.0
    assert rate_per_second(0, 0.002) == 0.0
    assert rate_per_second(float("inf"), 0.002) is None


def test_short_workloads_do_not_depend_on_coarse_deadline_clock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Python 3.12 Windows monotonic() may not tick during a sub-15.625 ms test.
    monkeypatch.setattr(time, "monotonic", lambda: 100.0)
    integer = run_integer_workload(
        IntegerWorkloadConfig(operations=4, block_size_bytes=4096), timeout_seconds=5
    )
    floating = run_floating_point_workload(
        FloatingPointWorkloadConfig(iterations=1000), timeout_seconds=5
    )
    memory = run_memory_workload(MemoryWorkloadConfig(allocation_bytes=4096), timeout_seconds=5)
    storage = run_storage_workload(
        StorageWorkloadConfig(size_bytes=4096, block_size_bytes=4096),
        temporary_root=tmp_path,
        timeout_seconds=5,
    )
    stability = run_stability_workload(
        StabilityWorkloadConfig(integer=IntegerWorkloadConfig(operations=4, block_size_bytes=4096)),
        timeout_seconds=5,
    )
    for result, metrics in (
        (integer, ["operations_per_second", "measured_duration"]),
        (floating, ["operations_per_second"]),
        (memory, ["throughput"]),
        (storage, ["read_throughput", "write_throughput"]),
        (stability, ["median_duration"]),
    ):
        assert result.correct is True
        assert result.duration_seconds > 0
        for name in metrics:
            value = result.measurements[name].value
            assert isinstance(value, (float, int)) and value > 0


def test_zero_high_resolution_duration_does_not_create_extreme_rate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(time, "perf_counter", lambda: 100.0)
    result = run_integer_workload(
        IntegerWorkloadConfig(operations=4, block_size_bytes=4096), timeout_seconds=5
    )
    assert result.correct is True
    assert result.measurements["measured_duration"].value == 0.0
    assert result.measurements["operations_per_second"].value is None
