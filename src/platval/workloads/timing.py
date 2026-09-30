"""Timing arithmetic that never invents a duration for an unmeasurable sample."""

import math


def rate_per_second(amount: int | float, duration_seconds: float) -> float | None:
    """Return unavailable rather than an epsilon-derived extreme rate."""
    if duration_seconds <= 0 or not math.isfinite(duration_seconds):
        return None
    rate = amount / duration_seconds
    return rate if math.isfinite(rate) else None
