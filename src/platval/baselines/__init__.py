"""Known-good baseline lifecycle and regression analysis."""

from platval.baselines.models import (
    ComparisonOutcome,
    ComparisonReport,
    MetricComparison,
    MetricDirection,
)
from platval.baselines.service import (
    compare_run,
    create_baseline,
    get_baseline,
    list_baselines,
)

__all__ = [
    "ComparisonOutcome",
    "ComparisonReport",
    "MetricComparison",
    "MetricDirection",
    "compare_run",
    "create_baseline",
    "get_baseline",
    "list_baselines",
]
