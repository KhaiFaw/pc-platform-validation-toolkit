"""Deterministic report view model derived from stored canonical evidence."""

import html
import statistics
from enum import StrEnum

from pydantic import Field

from platval.models.common import DomainModel, Scalar
from platval.models.status import ResultStatus
from platval.models.telemetry import TelemetrySample
from platval.persistence import StoredRun


class ValueClass(StrEnum):
    MEASURED = "measured"
    CONFIGURED = "configured"
    DERIVED = "derived"
    UNAVAILABLE = "unavailable"
    SIMULATED = "simulated"


class ReportValue(DomainModel):
    name: str
    display_value: str
    unit: str | None = None
    classification: ValueClass
    source: str | None = None


class ReportRequirement(DomainModel):
    metric: str
    operator: str
    expected: str
    actual: str
    unit: str | None = None
    passed: bool
    explanation: str
    expected_classification: ValueClass = ValueClass.CONFIGURED
    actual_classification: ValueClass


class ReportTest(DomainModel):
    test_id: str
    status: ResultStatus
    duration_seconds: float
    failure_reason: str | None = None
    exception_summary: str | None = None
    injected: bool = False
    metrics: list[ReportValue] = Field(default_factory=list)
    requirements: list[ReportRequirement] = Field(default_factory=list)
    telemetry_values: list[ReportValue] = Field(default_factory=list)
    unavailable_telemetry: list[str] = Field(default_factory=list)
    telemetry_chart_svg: str | None = None
    evidence_references: list[str] = Field(default_factory=list)


class ReportView(DomainModel):
    run_id: str
    plan_name: str
    plan_hash: str
    tool_version: str
    started_at: str
    ended_at: str
    overall_status: ResultStatus
    result_counts: dict[str, int]
    platform_values: list[ReportValue]
    tests: list[ReportTest]
    warnings: list[str]
    limitations: list[str]
    contains_simulated_data: bool


_DERIVED_METRICS = {
    "absolute_error",
    "median_absolute_deviation",
    "median_duration",
    "operations_per_second",
    "read_throughput",
    "robust_variability",
    "throughput",
    "write_throughput",
}


def _display(value: Scalar | list[Scalar]) -> str:
    if value is None:
        return "UNAVAILABLE"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return format(value, ".8g")
    if isinstance(value, list):
        return "[" + ", ".join(_display(item) for item in value) + "]"
    return str(value)


def _gib(value: int) -> str:
    return f"{value / (1024**3):.2f}"


def _platform_values(stored: StoredRun) -> list[ReportValue]:
    platform = stored.execution.platform
    return [
        ReportValue(
            name="Operating system",
            display_value=f"{platform.operating_system} {platform.operating_system_version}",
            classification=ValueClass.MEASURED,
            source="inventory",
        ),
        ReportValue(
            name="Architecture",
            display_value=platform.architecture,
            classification=ValueClass.MEASURED,
            source="inventory",
        ),
        ReportValue(
            name="CPU",
            display_value=platform.cpu_brand or "UNAVAILABLE",
            classification=(ValueClass.MEASURED if platform.cpu_brand else ValueClass.UNAVAILABLE),
            source="native probe" if platform.native_probe_version else "operating system",
        ),
        ReportValue(
            name="Processors",
            display_value=(
                f"{platform.physical_processor_count or 'UNAVAILABLE'} physical / "
                f"{platform.logical_processor_count} logical"
            ),
            classification=ValueClass.MEASURED,
            source="psutil",
        ),
        ReportValue(
            name="Memory capacity",
            display_value=_gib(platform.total_memory_bytes),
            unit="GiB",
            classification=ValueClass.MEASURED,
            source="psutil",
        ),
        ReportValue(
            name="Storage capacity",
            display_value=_gib(platform.storage_volume.capacity_bytes),
            unit="GiB",
            classification=ValueClass.MEASURED,
            source="psutil",
        ),
        ReportValue(
            name="Storage free at inventory",
            display_value=_gib(platform.storage_volume.free_bytes),
            unit="GiB",
            classification=ValueClass.MEASURED,
            source="psutil",
        ),
        ReportValue(
            name="Power plan",
            display_value=platform.power_plan_name or "UNAVAILABLE",
            classification=(
                ValueClass.MEASURED if platform.power_plan_name else ValueClass.UNAVAILABLE
            ),
            source="powercfg" if platform.power_plan_name else None,
        ),
        ReportValue(
            name="Native probe",
            display_value=platform.native_probe_version or "UNAVAILABLE",
            classification=(
                ValueClass.MEASURED if platform.native_probe_version else ValueClass.UNAVAILABLE
            ),
            source="cpuid_probe" if platform.native_probe_version else None,
        ),
        ReportValue(
            name="Sanitized fingerprint",
            display_value=platform.sanitized_platform_fingerprint,
            classification=ValueClass.DERIVED,
            source="SHA-256 configuration allowlist",
        ),
    ]


def _telemetry_values(samples: list[TelemetrySample]) -> list[ReportValue]:
    values: list[ReportValue] = [
        ReportValue(
            name="Sample count",
            display_value=str(len(samples)),
            unit="samples",
            classification=ValueClass.DERIVED,
            source="telemetry series",
        )
    ]
    cpu_values = [
        sample.cpu_utilization_percent
        for sample in samples
        if sample.cpu_utilization_percent is not None
    ]
    if cpu_values:
        for name, value in (
            ("CPU utilization minimum", min(cpu_values)),
            ("CPU utilization average", statistics.fmean(cpu_values)),
            ("CPU utilization maximum", max(cpu_values)),
        ):
            values.append(
                ReportValue(
                    name=name,
                    display_value=_display(value),
                    unit="%",
                    classification=ValueClass.DERIVED,
                    source="telemetry series",
                )
            )
    process_memory = [
        sample.process_memory_bytes for sample in samples if sample.process_memory_bytes is not None
    ]
    if process_memory:
        values.append(
            ReportValue(
                name="Peak process memory",
                display_value=f"{max(process_memory) / (1024**2):.2f}",
                unit="MiB",
                classification=ValueClass.DERIVED,
                source="telemetry series",
            )
        )
    temperatures = [reading.value for sample in samples for reading in sample.temperatures]
    if temperatures:
        values.append(
            ReportValue(
                name="Maximum reported temperature",
                display_value=_display(max(temperatures)),
                unit="degC",
                classification=ValueClass.DERIVED,
                source="telemetry series",
            )
        )
    return values


def _cpu_chart(samples: list[TelemetrySample], test_id: str) -> str | None:
    points = [
        (sample.elapsed_seconds, sample.cpu_utilization_percent)
        for sample in samples
        if sample.cpu_utilization_percent is not None
    ]
    if not points:
        return None
    width, height = 720, 230
    left, right, top, bottom = 54, 18, 22, 42
    chart_width = width - left - right
    chart_height = height - top - bottom
    max_elapsed = max(point[0] for point in points) or 1.0

    def coordinates(elapsed: float, utilization: float) -> tuple[float, float]:
        x = left + (elapsed / max_elapsed) * chart_width
        y = top + (1.0 - max(0.0, min(100.0, utilization)) / 100.0) * chart_height
        return x, y

    encoded_points = " ".join(
        f"{x:.2f},{y:.2f}" for x, y in (coordinates(elapsed, value) for elapsed, value in points)
    )
    if len(points) == 1:
        marker_x, marker_y = coordinates(points[0][0], points[0][1])
        series_element = (
            f'<circle cx="{marker_x:.2f}" cy="{marker_y:.2f}" r="4" class="chart-point" />'
        )
    else:
        series_element = f'<polyline points="{encoded_points}" class="chart-line" />'
    grid = []
    for value in (0, 50, 100):
        _, y = coordinates(0, float(value))
        grid.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" y2="{y:.2f}" '
            'class="chart-grid" />'
        )
        grid.append(
            f'<text x="{left - 8}" y="{y + 4:.2f}" text-anchor="end" class="chart-label">'
            f"{value}</text>"
        )
    safe_id = html.escape(test_id)
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-labelledby="chart-title-{safe_id} chart-desc-{safe_id}">'
        f'<title id="chart-title-{safe_id}">{safe_id} CPU utilization</title>'
        f'<desc id="chart-desc-{safe_id}">CPU utilization percent over elapsed seconds.</desc>'
        + "".join(grid)
        + f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" class="chart-axis" />'
        + f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" '
        + f'y2="{height - bottom}" class="chart-axis" />'
        + series_element
        + f'<text x="{width / 2:.1f}" y="{height - 8}" text-anchor="middle" class="chart-label">'
        "Elapsed time (seconds)</text>" + f'<text x="14" y="{height / 2:.1f}" text-anchor="middle" '
        'transform="rotate(-90 14 115)" class="chart-label">CPU utilization (%)</text>'
        + f'<text x="{width - right}" y="{height - bottom + 18}" text-anchor="end" '
        f'class="chart-label">{max_elapsed:.3f}s</text></svg>'
    )


def build_report_view(stored: StoredRun) -> ReportView:
    run = stored.execution.run
    report_tests: list[ReportTest] = []
    for result in run.test_results:
        samples = stored.execution.telemetry_samples.get(result.test_id, [])
        metrics = [
            ReportValue(
                name=name,
                display_value=_display(metric.value),
                unit=metric.unit,
                classification=(
                    ValueClass.SIMULATED
                    if result.injected
                    else (ValueClass.DERIVED if name in _DERIVED_METRICS else ValueClass.MEASURED)
                ),
                source=metric.source,
            )
            for name, metric in sorted(result.measured_values.items())
        ]
        requirements = [
            ReportRequirement(
                metric=evaluation.metric,
                operator=evaluation.operator,
                expected=_display(evaluation.expected),
                actual=_display(evaluation.actual),
                unit=evaluation.unit,
                passed=evaluation.passed,
                explanation=evaluation.explanation,
                actual_classification=(
                    ValueClass.UNAVAILABLE
                    if evaluation.actual is None
                    else (
                        ValueClass.SIMULATED
                        if result.injected
                        else (
                            ValueClass.DERIVED
                            if evaluation.metric in _DERIVED_METRICS
                            else ValueClass.MEASURED
                        )
                    )
                ),
            )
            for evaluation in result.requirements
        ]
        report_tests.append(
            ReportTest(
                test_id=result.test_id,
                status=result.status,
                duration_seconds=result.duration_seconds,
                failure_reason=result.failure_reason,
                exception_summary=result.exception_summary,
                injected=result.injected,
                metrics=metrics,
                requirements=requirements,
                telemetry_values=_telemetry_values(samples),
                unavailable_telemetry=(
                    result.telemetry_summary.unavailable_metrics
                    if result.telemetry_summary is not None
                    else []
                ),
                telemetry_chart_svg=_cpu_chart(samples, result.test_id),
                evidence_references=result.evidence_references,
            )
        )
    return ReportView(
        run_id=run.run_id,
        plan_name=run.plan_name,
        plan_hash=run.plan_hash,
        tool_version=run.tool_version,
        started_at=run.started_at.isoformat(),
        ended_at=run.ended_at.isoformat(),
        overall_status=run.overall_status,
        result_counts={status.value: run.result_counts.get(status, 0) for status in ResultStatus},
        platform_values=_platform_values(stored),
        tests=report_tests,
        warnings=run.warnings,
        limitations=run.limitations,
        contains_simulated_data=any(result.injected for result in run.test_results),
    )
