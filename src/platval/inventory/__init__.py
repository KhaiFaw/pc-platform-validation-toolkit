"""Platform inventory adapters."""

from platval.inventory.collector import InventorySnapshot, collect_platform_inventory
from platval.inventory.native_probe import (
    NativeProbeData,
    NativeProbeOutcome,
    NativeProbeStatus,
    invoke_native_probe,
    locate_native_probe,
)

__all__ = [
    "InventorySnapshot",
    "NativeProbeData",
    "NativeProbeOutcome",
    "NativeProbeStatus",
    "collect_platform_inventory",
    "invoke_native_probe",
    "locate_native_probe",
]
