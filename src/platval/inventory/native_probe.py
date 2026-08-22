"""Validated subprocess boundary for the optional native CPUID probe."""

import json
import os
import shutil
import subprocess
from enum import StrEnum
from pathlib import Path

from pydantic import Field, ValidationError, field_validator

from platval.constants import NATIVE_PROBE_SCHEMA_VERSION
from platval.models.common import DomainModel

_MAX_PROBE_OUTPUT_BYTES = 1_048_576
_DEFAULT_TIMEOUT_SECONDS = 5.0


class NativeProbeStatus(StrEnum):
    AVAILABLE = "available"
    MISSING = "missing"
    INCOMPATIBLE = "incompatible"
    ERROR = "error"


class NativeFeatureSet(DomainModel):
    sse2: bool
    sse41: bool
    sse42: bool
    avx_hardware: bool
    avx2_hardware: bool
    avx_os_enabled: bool
    aes: bool
    vmx: bool
    svm: bool
    virtualization_hardware: bool


class NativeCacheDescriptor(DomainModel):
    level: int = Field(ge=1, le=4)
    kind: str = Field(pattern=r"^(data|instruction|unified)$")
    size_bytes: int = Field(gt=0)
    line_size_bytes: int = Field(gt=0)
    sets: int = Field(gt=0)
    ways: int = Field(gt=0)
    partitions: int = Field(gt=0)


class NativeProbeData(DomainModel):
    schema_version: int
    probe_version: str = Field(min_length=1, max_length=64)
    architecture: str = Field(pattern=r"^(x86|x86_64)$")
    vendor_id: str = Field(min_length=1, max_length=12)
    brand_string: str | None = Field(default=None, max_length=48)
    max_basic_leaf: int = Field(ge=0)
    max_extended_leaf: int = Field(ge=0)
    features: NativeFeatureSet
    caches: list[NativeCacheDescriptor] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def schema_is_compatible(cls, value: int) -> int:
        if value != NATIVE_PROBE_SCHEMA_VERSION:
            raise ValueError(
                f"expected native probe schema {NATIVE_PROBE_SCHEMA_VERSION}, received {value}"
            )
        return value


class NativeProbeOutcome(DomainModel):
    status: NativeProbeStatus
    data: NativeProbeData | None = None
    limitation: str | None = None
    stderr_summary: str | None = None


def locate_native_probe(explicit_path: Path | None = None) -> Path | None:
    """Resolve only an explicit file or the executable search path."""
    if explicit_path is not None:
        candidate = explicit_path.resolve()
        return candidate if candidate.is_file() else None

    executable_name = "cpuid_probe.exe" if os.name == "nt" else "cpuid_probe"
    discovered = shutil.which(executable_name)
    return Path(discovered).resolve() if discovered else None


def _summarize_stderr(stderr: str) -> str | None:
    normalized = " ".join(stderr.split())
    if not normalized:
        return None
    return normalized[:500]


def invoke_native_probe(
    executable: Path | None,
    *,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
) -> NativeProbeOutcome:
    """Invoke and validate the probe without exposing private absolute paths."""
    if executable is None or not executable.is_file():
        return NativeProbeOutcome(
            status=NativeProbeStatus.MISSING,
            limitation="Native CPUID probe is not installed; CPU feature detail is unavailable.",
        )

    try:
        completed = subprocess.run(
            [str(executable), "--json"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return NativeProbeOutcome(
            status=NativeProbeStatus.ERROR,
            limitation=f"Native CPUID probe exceeded its {timeout_seconds:g}-second timeout.",
        )
    except OSError as exc:
        return NativeProbeOutcome(
            status=NativeProbeStatus.ERROR,
            limitation=f"Native CPUID probe could not start ({type(exc).__name__}).",
        )

    stderr_summary = _summarize_stderr(completed.stderr)
    if completed.returncode != 0:
        return NativeProbeOutcome(
            status=NativeProbeStatus.ERROR,
            limitation=f"Native CPUID probe exited with code {completed.returncode}.",
            stderr_summary=stderr_summary,
        )
    if len(completed.stdout.encode("utf-8")) > _MAX_PROBE_OUTPUT_BYTES:
        return NativeProbeOutcome(
            status=NativeProbeStatus.ERROR,
            limitation="Native CPUID probe returned an unexpectedly large response.",
            stderr_summary=stderr_summary,
        )

    try:
        raw = json.loads(completed.stdout)
        data = NativeProbeData.model_validate(raw)
    except (json.JSONDecodeError, ValidationError) as exc:
        return NativeProbeOutcome(
            status=NativeProbeStatus.INCOMPATIBLE,
            limitation=f"Native CPUID probe response failed validation ({type(exc).__name__}).",
            stderr_summary=stderr_summary,
        )

    return NativeProbeOutcome(
        status=NativeProbeStatus.AVAILABLE,
        data=data,
        stderr_summary=stderr_summary,
    )
