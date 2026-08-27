"""Typed baseline comparison evidence."""

from enum import StrEnum

from pydantic import Field

from platval.models.common import DomainModel
from platval.models.status import ResultStatus
from platval.persistence import BaselineRecord


class MetricDirection(StrEnum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class ComparisonOutcome(StrEnum):
    IMPROVED = "IMPROVED"
    UNCHANGED = "UNCHANGED"
    WARN = "WARN"
    FAIL = "FAIL"
    UNAVAILABLE = "UNAVAILABLE"


class MetricComparison(DomainModel):
    test_id: str
    metric: str
    unit: str | None = None
    direction: MetricDirection
    baseline_value: float
    current_value: float
    absolute_difference: float
    percent_difference: float | None = None
    warning_threshold_percent: float = Field(ge=0)
    failure_threshold_percent: float = Field(ge=0)
    outcome: ComparisonOutcome


class ComparisonReport(DomainModel):
    baseline: BaselineRecord
    run_id: str
    platform_compatible: bool
    plan_compatible: bool
    overall_status: ResultStatus
    warning_threshold_percent: float
    failure_threshold_percent: float
    comparisons: list[MetricComparison] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    interpretation: str
