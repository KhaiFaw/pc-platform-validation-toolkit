"""Central resource limits enforced before every workload begins."""

import os

import psutil
from pydantic import Field

from platval.models.common import DomainModel
from platval.workloads.errors import SafetyLimitError

MIB = 1024 * 1024


class SafetyPolicy(DomainModel):
    max_workers: int = Field(gt=0)
    max_memory_bytes: int = Field(gt=0)
    max_temporary_file_bytes: int = Field(gt=0)
    max_duration_seconds: float = Field(gt=0, le=3600)
    minimum_disk_reserve_bytes: int = Field(default=64 * MIB, ge=0)

    @classmethod
    def detected(cls) -> "SafetyPolicy":
        available = psutil.virtual_memory().available
        logical_processors = psutil.cpu_count(logical=True) or os.cpu_count() or 1
        return cls(
            max_workers=logical_processors,
            max_memory_bytes=max(MIB, min(512 * MIB, available // 4)),
            max_temporary_file_bytes=256 * MIB,
            max_duration_seconds=300.0,
        )

    def require_workers(self, workers: int) -> None:
        if workers > self.max_workers:
            raise SafetyLimitError(
                f"requested {workers} workers exceeds the safety limit of {self.max_workers}"
            )

    def require_memory(self, allocation_bytes: int) -> None:
        if allocation_bytes > self.max_memory_bytes:
            raise SafetyLimitError(
                f"requested memory exceeds the {self.max_memory_bytes}-byte safety limit"
            )

    def require_temporary_file(self, size_bytes: int) -> None:
        if size_bytes > self.max_temporary_file_bytes:
            raise SafetyLimitError(
                "requested temporary file exceeds the "
                f"{self.max_temporary_file_bytes}-byte safety limit"
            )

    def require_timeout(self, timeout_seconds: float) -> None:
        if timeout_seconds <= 0:
            raise SafetyLimitError("workload timeout must be greater than zero")
        if timeout_seconds > self.max_duration_seconds:
            raise SafetyLimitError(
                f"requested timeout exceeds the {self.max_duration_seconds:g}-second safety limit"
            )


def resolve_policy(policy: SafetyPolicy | None) -> SafetyPolicy:
    return policy if policy is not None else SafetyPolicy.detected()
