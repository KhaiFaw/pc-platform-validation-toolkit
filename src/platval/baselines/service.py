"""Immutable baseline lifecycle and conservative regression comparisons."""

import re
from dataclasses import dataclass
from pathlib import Path

from platval.baselines.models import (
    ComparisonOutcome,
    ComparisonReport,
    MetricComparison,
    MetricDirection,
)
from platval.models.status import ResultStatus
from platval.persistence import BaselineRecord, SQLiteRepository, StoredRun


@dataclass(frozen=True, slots=True)
class _MetricPolicy:
    direction: MetricDirection


_POLICIES = {
    "absolute_error": _MetricPolicy(MetricDirection.LOWER_IS_BETTER),
    "measured_duration": _MetricPolicy(MetricDirection.LOWER_IS_BETTER),
    "median_absolute_deviation": _MetricPolicy(MetricDirection.LOWER_IS_BETTER),
    "median_duration": _MetricPolicy(MetricDirection.LOWER_IS_BETTER),
    "operations_per_second": _MetricPolicy(MetricDirection.HIGHER_IS_BETTER),
    "read_throughput": _MetricPolicy(MetricDirection.HIGHER_IS_BETTER),
    "robust_variability": _MetricPolicy(MetricDirection.LOWER_IS_BETTER),
    "throughput": _MetricPolicy(MetricDirection.HIGHER_IS_BETTER),
    "write_throughput": _MetricPolicy(MetricDirection.HIGHER_IS_BETTER),
}
_BASELINE_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def _repository(runtime_directory: Path) -> SQLiteRepository:
    return SQLiteRepository(runtime_directory.resolve() / "platval.db")


def create_baseline(name: str, source_run_id: str, *, runtime_directory: Path) -> BaselineRecord:
    if _BASELINE_NAME.fullmatch(name) is None:
        raise ValueError(
            "baseline name must start with a lowercase letter or digit and use only "
            "lowercase letters, digits, dots, underscores, or hyphens"
        )
    repository = _repository(runtime_directory)
    stored = repository.get_run(source_run_id)
    if stored.execution.run.overall_status in {ResultStatus.FAIL, ResultStatus.ERROR}:
        raise ValueError("a failed or errored run cannot be registered as known-good")
    return repository.create_baseline(name, source_run_id)


def list_baselines(*, runtime_directory: Path) -> list[BaselineRecord]:
    return _repository(runtime_directory).list_baselines()


def get_baseline(name: str, *, runtime_directory: Path) -> BaselineRecord:
    return _repository(runtime_directory).get_baseline(name)


def _numeric_metrics(stored: StoredRun) -> dict[tuple[str, str], tuple[float, str | None]]:
    metrics: dict[tuple[str, str], tuple[float, str | None]] = {}
    for result in stored.execution.run.test_results:
        for name, metric in result.measured_values.items():
            value = metric.value
            if (
                name in _POLICIES
                and not isinstance(value, bool)
                and isinstance(value, (int, float))
            ):
                metrics[(result.test_id, name)] = (float(value), metric.unit)
    return metrics


def _outcome(
    baseline_value: float,
    current_value: float,
    direction: MetricDirection,
    warning_threshold_percent: float,
    failure_threshold_percent: float,
) -> tuple[float | None, ComparisonOutcome]:
    if baseline_value == 0:
        if current_value == 0:
            return None, ComparisonOutcome.UNCHANGED
        return None, ComparisonOutcome.UNAVAILABLE
    percent_difference = ((current_value - baseline_value) / abs(baseline_value)) * 100
    adverse_change = (
        -percent_difference if direction is MetricDirection.HIGHER_IS_BETTER else percent_difference
    )
    if adverse_change == 0:
        outcome = ComparisonOutcome.UNCHANGED
    elif adverse_change >= failure_threshold_percent:
        outcome = ComparisonOutcome.FAIL
    elif adverse_change >= warning_threshold_percent:
        outcome = ComparisonOutcome.WARN
    elif adverse_change <= -warning_threshold_percent:
        outcome = ComparisonOutcome.IMPROVED
    else:
        outcome = ComparisonOutcome.UNCHANGED
    return percent_difference, outcome


def compare_run(
    baseline_name: str,
    run_id: str,
    *,
    runtime_directory: Path,
    warning_threshold_percent: float = 10.0,
    failure_threshold_percent: float = 20.0,
) -> ComparisonReport:
    if warning_threshold_percent < 0 or failure_threshold_percent <= warning_threshold_percent:
        raise ValueError("thresholds require 0 <= warning < failure")
    repository = _repository(runtime_directory)
    baseline = repository.get_baseline(baseline_name)
    source = repository.get_run(baseline.source_run_id)
    current = repository.get_run(run_id)
    platform_compatible = (
        baseline.platform_fingerprint == current.execution.run.platform_fingerprint
    )
    plan_compatible = baseline.plan_hash == current.execution.run.plan_hash
    warnings: list[str] = []
    if not platform_compatible:
        warnings.append(
            "Platform fingerprints differ; numeric regression conclusions were withheld."
        )
    if not plan_compatible:
        warnings.append("Plan hashes differ; numeric regression conclusions were withheld.")
    comparisons: list[MetricComparison] = []
    if platform_compatible and plan_compatible:
        baseline_metrics = _numeric_metrics(source)
        current_metrics = _numeric_metrics(current)
        for key in sorted(baseline_metrics.keys() & current_metrics.keys()):
            baseline_value, baseline_unit = baseline_metrics[key]
            current_value, current_unit = current_metrics[key]
            if baseline_unit != current_unit:
                warnings.append(f"{key[0]} {key[1]} units differ; that metric was not compared.")
                continue
            policy = _POLICIES[key[1]]
            percent_difference, outcome = _outcome(
                baseline_value,
                current_value,
                policy.direction,
                warning_threshold_percent,
                failure_threshold_percent,
            )
            comparisons.append(
                MetricComparison(
                    test_id=key[0],
                    metric=key[1],
                    unit=baseline_unit,
                    direction=policy.direction,
                    baseline_value=baseline_value,
                    current_value=current_value,
                    absolute_difference=current_value - baseline_value,
                    percent_difference=percent_difference,
                    warning_threshold_percent=warning_threshold_percent,
                    failure_threshold_percent=failure_threshold_percent,
                    outcome=outcome,
                )
            )
        if not comparisons:
            warnings.append("No compatible registered performance metrics were available.")
    if any("temperature" in item.lower() for item in current.execution.run.limitations):
        warnings.append(
            "Temperature evidence is unavailable; thermal conditions cannot be excluded."
        )

    current_status = current.execution.run.overall_status
    if current_status is ResultStatus.ERROR:
        overall_status = ResultStatus.ERROR
    elif current_status is ResultStatus.FAIL:
        overall_status = ResultStatus.FAIL
    elif not platform_compatible or not plan_compatible:
        overall_status = ResultStatus.WARN
    elif any(item.outcome is ComparisonOutcome.FAIL for item in comparisons):
        overall_status = ResultStatus.FAIL
    elif (
        current_status is ResultStatus.WARN
        or warnings
        or any(
            item.outcome in {ComparisonOutcome.WARN, ComparisonOutcome.UNAVAILABLE}
            for item in comparisons
        )
    ):
        overall_status = ResultStatus.WARN
    else:
        overall_status = ResultStatus.PASS
    return ComparisonReport(
        baseline=baseline,
        run_id=run_id,
        platform_compatible=platform_compatible,
        plan_compatible=plan_compatible,
        overall_status=overall_status,
        warning_threshold_percent=warning_threshold_percent,
        failure_threshold_percent=failure_threshold_percent,
        comparisons=comparisons,
        warnings=warnings,
        interpretation=(
            "Performance differences are correlations, not proof of a hardware cause; "
            "background load, scheduling, power policy, caching, and thermal state may contribute."
        ),
    )
