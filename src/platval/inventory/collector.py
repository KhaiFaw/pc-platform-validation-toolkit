"""Sanitized, portable platform inventory collection."""

import platform
import re
import subprocess
from pathlib import Path

import psutil
from pydantic import Field

from platval.collectors import CollectorCapability, discover_psutil_capabilities
from platval.constants import TOOL_VERSION
from platval.inventory.native_probe import (
    NativeProbeStatus,
    invoke_native_probe,
    locate_native_probe,
)
from platval.models.common import DomainModel
from platval.models.platform import (
    CacheDescriptor,
    PlatformIdentity,
    StorageVolume,
    sanitized_platform_fingerprint,
)


class InventorySnapshot(DomainModel):
    platform: PlatformIdentity
    capabilities: list[CollectorCapability]
    limitations: list[str] = Field(default_factory=list)


def _parse_power_plan(output: str) -> str | None:
    match = re.search(r"\(([^()]+)\)\s*$", output.strip())
    return match.group(1).strip() if match else None


def _windows_power_plan() -> str | None:
    if platform.system() != "Windows":
        return None
    try:
        completed = subprocess.run(
            ["powercfg", "/getactivescheme"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return _parse_power_plan(completed.stdout)


def _filesystem_for(path: Path) -> str | None:
    resolved_path = path.resolve()
    best_match: tuple[int, str] | None = None
    try:
        for partition in psutil.disk_partitions(all=False):
            mountpoint = Path(partition.mountpoint).resolve()
            try:
                resolved_path.relative_to(mountpoint)
            except ValueError:
                continue
            score = len(mountpoint.parts)
            if partition.fstype and (best_match is None or score > best_match[0]):
                best_match = (score, partition.fstype)
    except (OSError, RuntimeError):
        return None
    return best_match[1] if best_match is not None else None


def collect_platform_inventory(
    *,
    storage_path: Path | None = None,
    native_probe_path: Path | None = None,
) -> InventorySnapshot:
    """Collect only validation-relevant configuration and capability data."""
    selected_path = (storage_path or Path.cwd()).resolve()
    if not selected_path.is_dir():
        raise ValueError("storage path must be an existing directory")

    capabilities = discover_psutil_capabilities()
    limitations = [
        capability.limitation
        for capability in capabilities
        if not capability.available and capability.limitation is not None
    ]
    probe = invoke_native_probe(locate_native_probe(native_probe_path))
    if probe.limitation:
        limitations.append(probe.limitation)

    native = probe.data if probe.status is NativeProbeStatus.AVAILABLE else None
    disk = psutil.disk_usage(str(selected_path))
    memory = psutil.virtual_memory()
    power_plan = _windows_power_plan()
    if platform.system() == "Windows" and power_plan is None:
        limitations.append("The active Windows power plan could not be determined.")

    caches = (
        [
            CacheDescriptor(
                level=cache.level,
                kind=cache.kind,
                size_bytes=cache.size_bytes,
                line_size_bytes=cache.line_size_bytes,
            )
            for cache in native.caches
        ]
        if native is not None
        else []
    )
    cpu_brand_fallback = platform.processor().strip() or None
    logical_count = psutil.cpu_count(logical=True) or 1
    physical_count = psutil.cpu_count(logical=False)
    capability_flags = {
        "native_cpuid_probe": native is not None,
        **{f"telemetry.{item.metric}": item.available for item in capabilities},
    }
    if native is not None:
        capability_flags.update(
            {
                "cpu.sse2": native.features.sse2,
                "cpu.sse41": native.features.sse41,
                "cpu.sse42": native.features.sse42,
                "cpu.avx_hardware": native.features.avx_hardware,
                "cpu.avx2_hardware": native.features.avx2_hardware,
                "cpu.avx_os_enabled": native.features.avx_os_enabled,
                "cpu.aes": native.features.aes,
                "cpu.virtualization_hardware": native.features.virtualization_hardware,
            }
        )

    payload = {
        "tool_version": TOOL_VERSION,
        "operating_system": platform.system(),
        "operating_system_version": platform.release(),
        "operating_system_build": platform.version(),
        "python_version": platform.python_version(),
        "architecture": native.architecture if native is not None else platform.machine(),
        "cpu_vendor": native.vendor_id if native is not None else None,
        "cpu_brand": native.brand_string if native is not None else cpu_brand_fallback,
        "logical_processor_count": logical_count,
        "physical_processor_count": physical_count,
        "caches": caches,
        "total_memory_bytes": memory.total,
        "storage_volume": StorageVolume(
            filesystem=_filesystem_for(selected_path),
            capacity_bytes=disk.total,
            free_bytes=disk.free,
        ),
        "power_plan_name": power_plan,
        "native_probe_version": native.probe_version if native is not None else None,
        "capability_flags": capability_flags,
    }
    fingerprint = sanitized_platform_fingerprint(payload)
    identity = PlatformIdentity(
        **payload,
        sanitized_platform_fingerprint=fingerprint,
    )
    return InventorySnapshot(
        platform=identity,
        capabilities=capabilities,
        limitations=list(dict.fromkeys(limitations)),
    )
