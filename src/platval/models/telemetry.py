"""Time-series telemetry models; optional readings remain explicitly absent."""

from datetime import datetime

from pydantic import Field, field_validator

from platval.models.common import DomainModel, require_aware_timestamp


class SensorReading(DomainModel):
    name: str = Field(min_length=1, max_length=128)
    value: float
    unit: str = Field(min_length=1, max_length=32)
    source: str = Field(min_length=1, max_length=128)


class TelemetrySample(DomainModel):
    elapsed_seconds: float = Field(ge=0)
    timestamp: datetime
    cpu_utilization_percent: float | None = Field(default=None, ge=0, le=100)
    per_core_utilization_percent: list[float] | None = None
    cpu_frequency_mhz: float | None = Field(default=None, gt=0)
    process_cpu_percent: float | None = Field(default=None, ge=0)
    process_memory_bytes: int | None = Field(default=None, ge=0)
    available_memory_bytes: int | None = Field(default=None, ge=0)
    disk_free_bytes: int | None = Field(default=None, ge=0)
    temperatures: list[SensorReading] = Field(default_factory=list)
    collector_errors: list[str] = Field(default_factory=list)

    _timestamp_is_aware = field_validator("timestamp")(require_aware_timestamp)

    @field_validator("per_core_utilization_percent")
    @classmethod
    def core_utilization_is_percentage(cls, value: list[float] | None) -> list[float] | None:
        if value is not None and any(item < 0 or item > 100 for item in value):
            raise ValueError("per-core utilization values must be between 0 and 100")
        return value
