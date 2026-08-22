"""Validated domain models and status semantics."""

from platval.models.plan import Requirement, TestDefinition, TestPlan
from platval.models.platform import PlatformIdentity, sanitized_platform_fingerprint
from platval.models.results import RunResult, TestResult, aggregate_status
from platval.models.status import ResultStatus
from platval.models.telemetry import TelemetrySample

__all__ = [
    "PlatformIdentity",
    "Requirement",
    "ResultStatus",
    "RunResult",
    "TelemetrySample",
    "TestDefinition",
    "TestPlan",
    "TestResult",
    "aggregate_status",
    "sanitized_platform_fingerprint",
]
