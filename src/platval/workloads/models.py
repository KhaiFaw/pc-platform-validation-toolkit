"""Canonical successful workload output before requirement evaluation."""

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from platval.models.common import DomainModel, Scalar, require_aware_timestamp


class WorkloadMeasurement(DomainModel):
    value: Scalar
    unit: str | None = Field(default=None, max_length=32)


class WorkloadResult(DomainModel):
    workload: str = Field(min_length=1, max_length=64)
    started_at: datetime
    ended_at: datetime
    duration_seconds: float = Field(ge=0)
    correct: bool
    checksum: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    measurements: dict[str, WorkloadMeasurement] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)

    _started_at_is_aware = field_validator("started_at")(require_aware_timestamp)
    _ended_at_is_aware = field_validator("ended_at")(require_aware_timestamp)

    @model_validator(mode="after")
    def end_follows_start(self) -> "WorkloadResult":
        if self.ended_at < self.started_at:
            raise ValueError("ended_at must not precede started_at")
        return self
