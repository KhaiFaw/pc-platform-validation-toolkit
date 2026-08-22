"""Telemetry collector capability discovery."""

from platval.collectors.capabilities import CollectorCapability, discover_psutil_capabilities
from platval.collectors.sampler import PsutilTelemetrySampler

__all__ = ["CollectorCapability", "PsutilTelemetrySampler", "discover_psutil_capabilities"]
