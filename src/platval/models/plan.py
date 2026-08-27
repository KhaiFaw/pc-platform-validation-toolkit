"""Versioned YAML test-plan domain model."""

from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from platval.constants import PLAN_SCHEMA_VERSION
from platval.models.common import DomainModel, ExpectedValue, Scalar


class RequirementOperator(StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    BETWEEN = "between"
    PRESENT = "present"
    CONTAINS = "contains"


class TestCategory(StrEnum):
    INVENTORY = "inventory"
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    TELEMETRY = "telemetry"
    STABILITY = "stability"
    CONFIGURATION = "configuration"
    REGRESSION = "regression"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class FaultInjection(StrEnum):
    CHECKSUM_MISMATCH = "checksum_mismatch"


class Requirement(DomainModel):
    metric: str = Field(min_length=1, max_length=128)
    operator: RequirementOperator
    expected: ExpectedValue = None
    unit: str | None = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def validate_expected_shape(self) -> "Requirement":
        if self.operator is RequirementOperator.BETWEEN:
            if not isinstance(self.expected, list) or len(self.expected) != 2:
                raise ValueError("between requires exactly two expected boundary values")
        elif self.operator is RequirementOperator.PRESENT:
            if self.expected is not None:
                raise ValueError("present does not accept an expected value")
        elif self.expected is None:
            raise ValueError(f"{self.operator.value} requires an expected value")
        return self


class SafetyLimits(DomainModel):
    max_workers: int | None = Field(default=None, gt=0)
    max_memory_bytes: int | None = Field(default=None, gt=0)
    max_temporary_file_bytes: int | None = Field(default=None, gt=0)
    thermal_stop_celsius: float | None = Field(default=None, gt=0, le=125)


class TestDefinition(DomainModel):
    id: str = Field(pattern=r"^[A-Z]{3}-\d{3}$")
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=1000)
    category: TestCategory
    enabled: bool = True
    timeout_seconds: float = Field(gt=0, le=3600)
    iterations: int = Field(default=1, ge=1, le=1000)
    parameters: dict[str, Scalar] = Field(default_factory=dict)
    requirements: list[Requirement] = Field(default_factory=list)
    severity: Severity = Severity.WARNING
    tags: list[str] = Field(default_factory=list)
    safety_limits: SafetyLimits = Field(default_factory=SafetyLimits)
    fault_injection: FaultInjection | None = None

    @model_validator(mode="after")
    def fault_is_supported_by_test(self) -> "TestDefinition":
        if self.fault_injection is not None and not self.enabled:
            raise ValueError("fault injection cannot be configured on a disabled test")
        if self.fault_injection is not None and self.id not in {"CPU-001", "CPU-003"}:
            raise ValueError("checksum fault injection is supported only by CPU-001 or CPU-003")
        return self


class TestPlan(DomainModel):
    schema_version: int = PLAN_SCHEMA_VERSION
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=1000)
    sampling_interval_seconds: float = Field(default=1.0, ge=0.05, le=60)
    extended: bool = False
    tests: list[TestDefinition] = Field(min_length=1)

    @field_validator("schema_version")
    @classmethod
    def schema_is_supported(cls, value: int) -> int:
        if value != PLAN_SCHEMA_VERSION:
            raise ValueError(f"expected plan schema {PLAN_SCHEMA_VERSION}, received {value}")
        return value

    @model_validator(mode="after")
    def test_ids_are_unique(self) -> "TestPlan":
        ids = [test.id for test in self.tests]
        if len(ids) != len(set(ids)):
            raise ValueError("test IDs must be unique within a plan")
        return self
