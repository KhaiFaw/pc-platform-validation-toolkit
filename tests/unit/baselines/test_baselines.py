import uuid
from pathlib import Path

import pytest

from platval.baselines import ComparisonOutcome, compare_run, create_baseline
from platval.models.plan import TestPlan as PlanModel
from platval.persistence import BaselineExistsError, SQLiteRepository, persist_execution
from platval.runner import run_validation_plan
from platval.runner.engine import RunExecution


def make_execution(tmp_path: Path) -> RunExecution:
    plan = PlanModel.model_validate(
        {
            "name": "baseline-test",
            "sampling_interval_seconds": 0.05,
            "tests": [
                {
                    "id": "CPU-001",
                    "name": "Integer",
                    "category": "cpu",
                    "timeout_seconds": 2,
                    "parameters": {"workload_size": 8, "block_size_bytes": 4096},
                }
            ],
        }
    )
    return run_validation_plan(plan, runtime_directory=tmp_path / str(uuid.uuid4()))


def with_throughput(execution: RunExecution, value: float) -> RunExecution:
    changed = execution.model_copy(deep=True)
    changed.run.run_id = str(uuid.uuid4())
    metric = changed.run.test_results[0].measured_values["operations_per_second"]
    metric.value = value
    return changed


def test_baseline_is_immutable_and_comparison_classifies_regression(tmp_path: Path) -> None:
    runtime = tmp_path / "store"
    source = with_throughput(make_execution(tmp_path), 100.0)
    current = with_throughput(source, 75.0)
    persist_execution(source, runtime_directory=runtime)
    persist_execution(current, runtime_directory=runtime)

    baseline = create_baseline("known-good", source.run.run_id, runtime_directory=runtime)
    assert baseline.platform_fingerprint == source.run.platform_fingerprint
    with pytest.raises(BaselineExistsError, match="not replaced"):
        create_baseline("known-good", current.run.run_id, runtime_directory=runtime)

    report = compare_run("known-good", current.run.run_id, runtime_directory=runtime)
    comparison = next(item for item in report.comparisons if item.metric == "operations_per_second")
    assert comparison.absolute_difference == -25.0
    assert comparison.percent_difference == -25.0
    assert comparison.outcome is ComparisonOutcome.FAIL
    assert report.overall_status.value == "FAIL"

    unchanged = compare_run(
        "known-good",
        source.run.run_id,
        runtime_directory=runtime,
        warning_threshold_percent=0,
        failure_threshold_percent=20,
    )
    same_metric = next(
        item for item in unchanged.comparisons if item.metric == "operations_per_second"
    )
    assert same_metric.outcome is ComparisonOutcome.UNCHANGED
    assert unchanged.overall_status.value == "WARN"
    assert any("self-comparison" in warning for warning in unchanged.warnings)


def test_incompatible_platform_withholds_numeric_comparison(tmp_path: Path) -> None:
    runtime = tmp_path / "store"
    source = with_throughput(make_execution(tmp_path), 100.0)
    current = with_throughput(source, 80.0)
    current.run.platform_fingerprint = "b" * 64
    persist_execution(source, runtime_directory=runtime)
    persist_execution(current, runtime_directory=runtime)
    create_baseline("known-good", source.run.run_id, runtime_directory=runtime)

    report = compare_run("known-good", current.run.run_id, runtime_directory=runtime)
    assert report.platform_compatible is False
    assert report.comparisons == []
    assert any("withheld" in warning for warning in report.warnings)
    assert SQLiteRepository(runtime / "platval.db").list_baselines() == [report.baseline]


def test_independent_runs_do_not_emit_self_comparison_warning(tmp_path: Path) -> None:
    runtime = tmp_path / "store"
    source = with_throughput(make_execution(tmp_path), 100.0)
    current = with_throughput(source, 100.0)
    persist_execution(source, runtime_directory=runtime)
    persist_execution(current, runtime_directory=runtime)
    create_baseline("known-good", source.run.run_id, runtime_directory=runtime)

    report = compare_run("known-good", current.run.run_id, runtime_directory=runtime)
    assert report.baseline.source_run_id != report.run_id
    assert not any("self-comparison" in warning for warning in report.warnings)


def test_power_plan_change_is_explicit_even_on_compatible_platform(tmp_path: Path) -> None:
    runtime = tmp_path / "store"
    source = with_throughput(make_execution(tmp_path), 100.0)
    current = with_throughput(source, 100.0)
    source.platform.power_plan_name = "Balanced"
    current.platform.power_plan_name = "Power saver"
    persist_execution(source, runtime_directory=runtime)
    persist_execution(current, runtime_directory=runtime)
    create_baseline("known-good", source.run.run_id, runtime_directory=runtime)

    report = compare_run("known-good", current.run.run_id, runtime_directory=runtime)
    assert report.platform_compatible is True
    assert report.overall_status.value == "WARN"
    assert any("power plans differ" in warning for warning in report.warnings)


@pytest.mark.parametrize(
    ("warning", "failure"),
    [(float("nan"), 20.0), (10.0, float("nan")), (float("inf"), 20.0), (10.0, float("inf"))],
)
def test_comparison_rejects_nonfinite_thresholds(
    tmp_path: Path, warning: float, failure: float
) -> None:
    with pytest.raises(ValueError, match="finite values"):
        compare_run(
            "known-good",
            str(uuid.uuid4()),
            runtime_directory=tmp_path,
            warning_threshold_percent=warning,
            failure_threshold_percent=failure,
        )
