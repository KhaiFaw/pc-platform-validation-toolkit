from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from platval.models.plan import Requirement
from platval.models.plan import TestPlan as PlanModel
from platval.models.platform import sanitized_platform_fingerprint
from platval.models.results import TestResult as ResultModel
from platval.models.results import aggregate_status
from platval.models.status import ResultStatus
from platval.models.telemetry import TelemetrySample


def test_status_aggregation_prioritizes_execution_error() -> None:
    statuses = [ResultStatus.PASS, ResultStatus.FAIL, ResultStatus.ERROR]
    assert aggregate_status(statuses) is ResultStatus.ERROR


def test_status_aggregation_allows_pass_with_skipped_capability() -> None:
    assert aggregate_status([ResultStatus.PASS, ResultStatus.SKIP]) is ResultStatus.PASS


def test_status_aggregation_of_no_results_is_skip() -> None:
    assert aggregate_status([]) is ResultStatus.SKIP


def test_fingerprint_is_stable_and_ignores_sensitive_extras() -> None:
    safe = {
        "operating_system": "Windows",
        "architecture": "AMD64",
        "logical_processor_count": 8,
        "capability_flags": {"native_probe": False},
    }
    first = sanitized_platform_fingerprint({**safe, "hostname": "private-one"})
    second = sanitized_platform_fingerprint({**safe, "hostname": "private-two"})
    assert first == second
    assert len(first) == 64


def test_fingerprint_ignores_transient_free_space_and_capability_changes() -> None:
    stable = {
        "operating_system": "Windows",
        "operating_system_version": "11",
        "architecture": "AMD64",
        "logical_processor_count": 8,
        "physical_processor_count": 4,
        "total_memory_bytes": 16 * 1024**3,
        "storage_volume": {"filesystem": "NTFS", "capacity_bytes": 1000, "free_bytes": 700},
        "capability_flags": {"temperature": False},
    }
    changed_runtime = {
        **stable,
        "storage_volume": {"filesystem": "NTFS", "capacity_bytes": 1000, "free_bytes": 200},
        "capability_flags": {"temperature": True},
    }
    assert sanitized_platform_fingerprint(stable) == sanitized_platform_fingerprint(changed_runtime)


def test_between_requirement_requires_two_boundaries() -> None:
    with pytest.raises(ValidationError, match="exactly two"):
        Requirement(metric="duration", operator="between", expected=[1])


def test_present_requirement_rejects_expected_value() -> None:
    with pytest.raises(ValidationError, match="does not accept"):
        Requirement(metric="temperature", operator="present", expected=True)


def test_plan_rejects_duplicate_test_ids() -> None:
    test = {
        "id": "CPU-001",
        "name": "Integer correctness",
        "category": "cpu",
        "timeout_seconds": 10,
    }
    with pytest.raises(ValidationError, match="must be unique"):
        PlanModel(name="duplicate", tests=[test, test])


def test_plan_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        PlanModel(
            name="typo",
            tests=[
                {
                    "id": "CPU-001",
                    "name": "Integer correctness",
                    "category": "cpu",
                    "timeout_seconds": 10,
                    "interations": 2,
                }
            ],
        )


def test_telemetry_preserves_missing_reading_as_none() -> None:
    sample = TelemetrySample(elapsed_seconds=0, timestamp=datetime.now(UTC))
    assert sample.cpu_frequency_mhz is None
    assert sample.temperatures == []


def test_telemetry_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="UTC offset"):
        TelemetrySample(elapsed_seconds=0, timestamp=datetime.now())


def test_result_end_must_follow_start() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError, match="must not precede"):
        ResultModel(
            test_id="CPU-001",
            started_at=now,
            ended_at=datetime(2020, 1, 1, tzinfo=UTC),
            duration_seconds=0,
            status=ResultStatus.ERROR,
        )
