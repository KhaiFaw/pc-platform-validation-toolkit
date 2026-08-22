from pathlib import Path

import pytest

from platval.workloads import (
    CancellationToken,
    FloatingPointWorkloadConfig,
    IntegerWorkloadConfig,
    MemoryWorkloadConfig,
    SafetyLimitError,
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
from platval.workloads.safety import MIB


@pytest.fixture
def small_policy() -> SafetyPolicy:
    return SafetyPolicy(
        max_workers=4,
        max_memory_bytes=8 * MIB,
        max_temporary_file_bytes=8 * MIB,
        max_duration_seconds=10,
        minimum_disk_reserve_bytes=0,
    )


def test_integer_single_and_multi_worker_are_deterministic(small_policy: SafetyPolicy) -> None:
    single = run_integer_workload(
        IntegerWorkloadConfig(workers=1, operations=16, block_size_bytes=4096),
        timeout_seconds=5,
        policy=small_policy,
    )
    multi_config = IntegerWorkloadConfig(workers=2, operations=16, block_size_bytes=4096)
    first_multi = run_integer_workload(multi_config, timeout_seconds=5, policy=small_policy)
    second_multi = run_integer_workload(
        multi_config.model_copy(update={"expected_checksum": first_multi.checksum}),
        timeout_seconds=5,
        policy=small_policy,
    )
    assert single.correct is True
    assert first_multi.correct is True
    assert second_multi.correct is True
    assert second_multi.checksum == first_multi.checksum
    assert first_multi.measurements["workers"].value == 2


def test_integer_detects_expected_checksum_mismatch(small_policy: SafetyPolicy) -> None:
    result = run_integer_workload(
        IntegerWorkloadConfig(
            workers=1,
            operations=4,
            block_size_bytes=4096,
            expected_checksum="0" * 64,
        ),
        timeout_seconds=5,
        policy=small_policy,
    )
    assert result.correct is False
    assert result.measurements["checksum_valid"].value is False


def test_floating_point_matches_closed_form(small_policy: SafetyPolicy) -> None:
    result = run_floating_point_workload(
        FloatingPointWorkloadConfig(iterations=50_000),
        timeout_seconds=5,
        policy=small_policy,
    )
    assert result.correct is True
    absolute_error = result.measurements["absolute_error"].value
    assert isinstance(absolute_error, (int, float))
    assert float(absolute_error) <= 1e-12


def test_memory_pattern_round_trip(small_policy: SafetyPolicy) -> None:
    result = run_memory_workload(
        MemoryWorkloadConfig(allocation_bytes=MIB, chunk_size_bytes=64 * 1024),
        timeout_seconds=5,
        policy=small_policy,
    )
    assert result.correct is True
    assert result.measurements["allocation"].value == MIB
    assert result.measurements["processed_bytes"].value == 3 * MIB


def test_storage_round_trip_cleans_owned_directory(
    tmp_path: Path, small_policy: SafetyPolicy
) -> None:
    result = run_storage_workload(
        StorageWorkloadConfig(size_bytes=512 * 1024, block_size_bytes=64 * 1024),
        temporary_root=tmp_path,
        timeout_seconds=5,
        policy=small_policy,
    )
    assert result.correct is True
    assert list(tmp_path.iterdir()) == []


def test_storage_cleanup_runs_after_cancellation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, small_policy: SafetyPolicy
) -> None:
    from platval.workloads import storage

    token = CancellationToken()
    original = storage._deterministic_block
    calls = 0

    def cancel_after_first_block(index: int, size: int) -> bytes:
        nonlocal calls
        calls += 1
        block = original(index, size)
        if calls == 1:
            token.cancel()
        return block

    monkeypatch.setattr(storage, "_deterministic_block", cancel_after_first_block)
    with pytest.raises(WorkloadCancelled):
        run_storage_workload(
            StorageWorkloadConfig(size_bytes=256 * 1024, block_size_bytes=64 * 1024),
            temporary_root=tmp_path,
            timeout_seconds=5,
            policy=small_policy,
            token=token,
        )
    assert list(tmp_path.iterdir()) == []


def test_stability_reports_robust_variability(small_policy: SafetyPolicy) -> None:
    result = run_stability_workload(
        StabilityWorkloadConfig(
            repetitions=3,
            integer=IntegerWorkloadConfig(workers=1, operations=8, block_size_bytes=4096),
        ),
        timeout_seconds=5,
        policy=small_policy,
    )
    assert result.correct is True
    assert result.measurements["repetitions"].value == 3
    variability = result.measurements["robust_variability"].value
    assert isinstance(variability, (int, float))
    assert float(variability) >= 0


def test_safety_limits_reject_oversized_requests(
    small_policy: SafetyPolicy, tmp_path: Path
) -> None:
    with pytest.raises(SafetyLimitError, match="workers"):
        run_integer_workload(
            IntegerWorkloadConfig(workers=5, operations=5, block_size_bytes=4096),
            timeout_seconds=5,
            policy=small_policy,
        )
    with pytest.raises(SafetyLimitError, match="memory"):
        run_memory_workload(
            MemoryWorkloadConfig(allocation_bytes=9 * MIB),
            timeout_seconds=5,
            policy=small_policy,
        )
    with pytest.raises(SafetyLimitError, match="temporary file"):
        run_storage_workload(
            StorageWorkloadConfig(size_bytes=9 * MIB),
            temporary_root=tmp_path,
            timeout_seconds=5,
            policy=small_policy,
        )
    with pytest.raises(SafetyLimitError, match="timeout"):
        run_floating_point_workload(
            FloatingPointWorkloadConfig(iterations=1),
            timeout_seconds=11,
            policy=small_policy,
        )
    with pytest.raises(SafetyLimitError, match="greater than zero"):
        run_floating_point_workload(
            FloatingPointWorkloadConfig(iterations=1),
            timeout_seconds=0,
            policy=small_policy,
        )


def test_pre_cancelled_and_expired_workloads_stop(small_policy: SafetyPolicy) -> None:
    token = CancellationToken()
    token.cancel()
    with pytest.raises(WorkloadCancelled):
        run_integer_workload(
            IntegerWorkloadConfig(operations=4, block_size_bytes=4096),
            timeout_seconds=5,
            policy=small_policy,
            token=token,
        )
    with pytest.raises(WorkloadTimeout):
        run_floating_point_workload(
            FloatingPointWorkloadConfig(iterations=20_000_000),
            timeout_seconds=1e-9,
            policy=small_policy,
        )
