"""Bounded deterministic validation workloads."""

from platval.workloads.control import CancellationToken
from platval.workloads.cpu import (
    FloatingPointWorkloadConfig,
    IntegerWorkloadConfig,
    StabilityWorkloadConfig,
    run_floating_point_workload,
    run_integer_workload,
    run_stability_workload,
)
from platval.workloads.errors import SafetyLimitError, WorkloadCancelled, WorkloadTimeout
from platval.workloads.memory import MemoryWorkloadConfig, run_memory_workload
from platval.workloads.safety import SafetyPolicy
from platval.workloads.storage import StorageWorkloadConfig, run_storage_workload

__all__ = [
    "CancellationToken",
    "FloatingPointWorkloadConfig",
    "IntegerWorkloadConfig",
    "MemoryWorkloadConfig",
    "SafetyLimitError",
    "SafetyPolicy",
    "StabilityWorkloadConfig",
    "StorageWorkloadConfig",
    "WorkloadCancelled",
    "WorkloadTimeout",
    "run_floating_point_workload",
    "run_integer_workload",
    "run_memory_workload",
    "run_stability_workload",
    "run_storage_workload",
]
