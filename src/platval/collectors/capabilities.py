"""Portable telemetry capability discovery without starting a sampler."""

from collections.abc import Callable

import psutil
from pydantic import Field

from platval.models.common import DomainModel


class CollectorCapability(DomainModel):
    metric: str = Field(min_length=1, max_length=128)
    available: bool
    source: str = Field(min_length=1, max_length=64)
    unit: str | None = Field(default=None, max_length=32)
    limitation: str | None = Field(default=None, max_length=500)


def _call_is_available(function: Callable[[], object]) -> bool:
    try:
        return function() is not None
    except (AttributeError, NotImplementedError, OSError, RuntimeError):
        return False


def _temperature_is_available() -> bool:
    function = getattr(psutil, "sensors_temperatures", None)
    if function is None:
        return False
    try:
        readings = function()
    except (AttributeError, NotImplementedError, OSError, RuntimeError):
        return False
    return any(entries for entries in readings.values())


def discover_psutil_capabilities() -> list[CollectorCapability]:
    """Report what the portable collector can measure on this platform."""
    frequency_available = _call_is_available(psutil.cpu_freq)
    temperature_available = _temperature_is_available()
    return [
        CollectorCapability(metric="cpu_utilization", available=True, source="psutil", unit="%"),
        CollectorCapability(
            metric="per_core_utilization", available=True, source="psutil", unit="%"
        ),
        CollectorCapability(
            metric="cpu_frequency",
            available=frequency_available,
            source="psutil",
            unit="MHz",
            limitation=None if frequency_available else "CPU frequency is not exposed by psutil.",
        ),
        CollectorCapability(metric="process_cpu", available=True, source="psutil", unit="%"),
        CollectorCapability(metric="process_memory", available=True, source="psutil", unit="bytes"),
        CollectorCapability(
            metric="available_memory", available=True, source="psutil", unit="bytes"
        ),
        CollectorCapability(metric="disk_free", available=True, source="psutil", unit="bytes"),
        CollectorCapability(
            metric="temperature",
            available=temperature_available,
            source="psutil",
            unit="degC",
            limitation=(
                None
                if temperature_available
                else (
                    "A trustworthy temperature source is unavailable; "
                    "runtime limits remain conservative."
                )
            ),
        ),
    ]
