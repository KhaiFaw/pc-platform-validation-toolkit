"""Expected workload control and safety failures."""


class WorkloadError(RuntimeError):
    """Base class for workload failures handled by the future runner."""


class SafetyLimitError(WorkloadError):
    """A requested resource would exceed the active safety policy."""


class WorkloadCancelled(WorkloadError):
    """The caller requested cooperative cancellation."""


class WorkloadTimeout(WorkloadError):
    """The workload exceeded its monotonic deadline."""
