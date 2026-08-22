"""Cooperative cancellation and monotonic workload deadlines."""

import threading
import time
from dataclasses import dataclass

from platval.workloads.errors import WorkloadCancelled, WorkloadTimeout


class CancellationToken:
    """Thread-safe cancellation signal shared by workload workers."""

    def __init__(self, parent: "CancellationToken | None" = None) -> None:
        self._event = threading.Event()
        self._parent = parent

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set() or (self._parent is not None and self._parent.cancelled)


@dataclass(frozen=True, slots=True)
class WorkloadContext:
    token: CancellationToken
    deadline_monotonic: float

    @classmethod
    def create(
        cls, timeout_seconds: float, token: CancellationToken | None = None
    ) -> "WorkloadContext":
        return cls(
            token=token or CancellationToken(),
            deadline_monotonic=time.monotonic() + timeout_seconds,
        )

    def checkpoint(self) -> None:
        if self.token.cancelled:
            raise WorkloadCancelled("workload cancellation was requested")
        if time.monotonic() >= self.deadline_monotonic:
            self.token.cancel()
            raise WorkloadTimeout("workload exceeded its monotonic deadline")

    def remaining_seconds(self) -> float:
        self.checkpoint()
        return max(0.0, self.deadline_monotonic - time.monotonic())
