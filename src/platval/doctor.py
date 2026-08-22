"""Local prerequisite and capability diagnostics."""

import importlib.util
import sys
import tempfile
from enum import StrEnum
from pathlib import Path

import psutil
from pydantic import Field

from platval.collectors import CollectorCapability, discover_psutil_capabilities
from platval.inventory.native_probe import (
    NativeProbeStatus,
    invoke_native_probe,
    locate_native_probe,
)
from platval.models.common import DomainModel

_MINIMUM_TEMPORARY_FREE_BYTES = 128 * 1024 * 1024
_REQUIRED_IMPORTS = ("jinja2", "psutil", "pydantic", "yaml", "rich", "typer")


class DoctorStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class DoctorCheck(DomainModel):
    name: str = Field(min_length=1, max_length=128)
    status: DoctorStatus
    detail: str = Field(min_length=1, max_length=500)


class DoctorReport(DomainModel):
    overall_status: DoctorStatus
    checks: list[DoctorCheck]
    capabilities: list[CollectorCapability]


def _overall_status(checks: list[DoctorCheck]) -> DoctorStatus:
    if any(check.status is DoctorStatus.FAIL for check in checks):
        return DoctorStatus.FAIL
    if any(check.status is DoctorStatus.WARN for check in checks):
        return DoctorStatus.WARN
    return DoctorStatus.PASS


def _runtime_checks(runtime_directory: Path) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    try:
        runtime_directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=runtime_directory) as handle:
            handle.write(b"platval-doctor")
            handle.flush()
        checks.append(
            DoctorCheck(
                name="runtime directory",
                status=DoctorStatus.PASS,
                detail="Runtime directory is writable.",
            )
        )
    except OSError as exc:
        checks.append(
            DoctorCheck(
                name="runtime directory",
                status=DoctorStatus.FAIL,
                detail=f"Runtime directory is not writable ({type(exc).__name__}).",
            )
        )
        return checks

    try:
        free_bytes = psutil.disk_usage(str(runtime_directory)).free
        adequate = free_bytes >= _MINIMUM_TEMPORARY_FREE_BYTES
        checks.append(
            DoctorCheck(
                name="temporary disk space",
                status=DoctorStatus.PASS if adequate else DoctorStatus.FAIL,
                detail=(
                    "Temporary disk space meets the 128 MiB minimum."
                    if adequate
                    else "Less than 128 MiB is free for bounded temporary validation."
                ),
            )
        )
    except OSError as exc:
        checks.append(
            DoctorCheck(
                name="temporary disk space",
                status=DoctorStatus.FAIL,
                detail=f"Temporary disk space could not be checked ({type(exc).__name__}).",
            )
        )
    return checks


def run_doctor(*, runtime_directory: Path, native_probe_path: Path | None = None) -> DoctorReport:
    """Check required local facilities without running validation workloads."""
    checks: list[DoctorCheck] = []
    supported_python = sys.version_info >= (3, 12)
    checks.append(
        DoctorCheck(
            name="Python version",
            status=DoctorStatus.PASS if supported_python else DoctorStatus.FAIL,
            detail=(
                f"Python {sys.version_info.major}.{sys.version_info.minor} is supported."
                if supported_python
                else "Python 3.12 or newer is required."
            ),
        )
    )

    missing = [name for name in _REQUIRED_IMPORTS if importlib.util.find_spec(name) is None]
    checks.append(
        DoctorCheck(
            name="Python dependencies",
            status=DoctorStatus.FAIL if missing else DoctorStatus.PASS,
            detail=(
                f"Missing required imports: {', '.join(missing)}."
                if missing
                else "All required Python imports are available."
            ),
        )
    )
    checks.extend(_runtime_checks(runtime_directory.resolve()))

    probe = invoke_native_probe(locate_native_probe(native_probe_path))
    checks.append(
        DoctorCheck(
            name="native CPUID probe",
            status=(
                DoctorStatus.PASS
                if probe.status is NativeProbeStatus.AVAILABLE
                else DoctorStatus.WARN
            ),
            detail=(
                f"Native probe {probe.data.probe_version} is compatible."
                if probe.data is not None
                else (probe.limitation or "Native CPUID detail is unavailable.")
            ),
        )
    )

    capabilities = discover_psutil_capabilities()
    temperature = next(item for item in capabilities if item.metric == "temperature")
    checks.append(
        DoctorCheck(
            name="temperature telemetry",
            status=DoctorStatus.PASS if temperature.available else DoctorStatus.WARN,
            detail=(
                "A temperature source is available."
                if temperature.available
                else (temperature.limitation or "Temperature telemetry is unavailable.")
            ),
        )
    )
    return DoctorReport(
        overall_status=_overall_status(checks),
        checks=checks,
        capabilities=capabilities,
    )
