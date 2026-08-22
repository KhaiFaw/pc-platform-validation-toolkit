"""Canonical test and run result models."""

from collections import Counter
from datetime import datetime

from pydantic import Field, field_validator, model_validator

from platval.constants import RESULT_SCHEMA_VERSION
from platval.models.common import DomainModel, Scalar, require_aware_timestamp
from platval.models.status import ResultStatus


def aggregate_status(statuses: list[ResultStatus]) -> ResultStatus:
    """Return the most consequential state while treating SKIP as non-failure."""
    if not statuses:
        return ResultStatus.SKIP
    for candidate in (ResultStatus.ERROR, ResultStatus.FAIL, ResultStatus.WARN):
        if candidate in statuses:
            return candidate
    if ResultStatus.PASS in statuses:
        return ResultStatus.PASS
    return ResultStatus.SKIP


class MetricValue(DomainModel):
    value: Scalar
    unit: str | None = Field(default=None, max_length=32)
    source: str = Field(min_length=1, max_length=128)


class RequirementEvaluation(DomainModel):
    metric: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    expected: Scalar | list[Scalar] = None
    actual: Scalar = None
    unit: str | None = None
    passed: bool
    explanation: str = Field(min_length=1)


class TelemetrySummary(DomainModel):
    sample_count: int = Field(ge=0)
    available_metrics: list[str] = Field(default_factory=list)
    unavailable_metrics: list[str] = Field(default_factory=list)
    collector_error_count: int = Field(default=0, ge=0)


class TestResult(DomainModel):
    test_id: str = Field(pattern=r"^[A-Z]{3}-\d{3}$")
    started_at: datetime
    ended_at: datetime
    duration_seconds: float = Field(ge=0)
    status: ResultStatus
    measured_values: dict[str, MetricValue] = Field(default_factory=dict)
    requirements: list[RequirementEvaluation] = Field(default_factory=list)
    failure_reason: str | None = None
    evidence_references: list[str] = Field(default_factory=list)
    exception_summary: str | None = None
    telemetry_summary: TelemetrySummary | None = None
    injected: bool = False

    _started_at_is_aware = field_validator("started_at")(require_aware_timestamp)
    _ended_at_is_aware = field_validator("ended_at")(require_aware_timestamp)

    @model_validator(mode="after")
    def end_follows_start(self) -> "TestResult":
        if self.ended_at < self.started_at:
            raise ValueError("ended_at must not precede started_at")
        return self


class ArtifactReference(DomainModel):
    kind: str = Field(min_length=1, max_length=64)
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class RunResult(DomainModel):
    schema_version: int = RESULT_SCHEMA_VERSION
    run_id: str = Field(min_length=1, max_length=64)
    plan_name: str = Field(min_length=1)
    plan_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    tool_version: str = Field(min_length=1)
    platform_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    started_at: datetime
    ended_at: datetime
    overall_status: ResultStatus
    result_counts: dict[ResultStatus, int]
    test_results: list[TestResult]
    artifact_manifest: list[ArtifactReference] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    _started_at_is_aware = field_validator("started_at")(require_aware_timestamp)
    _ended_at_is_aware = field_validator("ended_at")(require_aware_timestamp)

    @model_validator(mode="after")
    def summary_matches_results(self) -> "RunResult":
        if self.ended_at < self.started_at:
            raise ValueError("ended_at must not precede started_at")
        statuses = [result.status for result in self.test_results]
        if self.overall_status is not aggregate_status(statuses):
            raise ValueError("overall_status does not match test result statuses")
        expected_counts = dict(Counter(statuses))
        supplied_counts = {status: count for status, count in self.result_counts.items() if count}
        if supplied_counts != expected_counts:
            raise ValueError("result_counts does not match test results")
        return self
