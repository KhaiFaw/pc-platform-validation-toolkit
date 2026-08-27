"""Deterministic Markdown and self-contained HTML rendering."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from platval.models.status import ResultStatus
from platval.reporting.view import ReportView

_STATUS_SYMBOLS = {
    ResultStatus.PASS: "✓",
    ResultStatus.FAIL: "✗",
    ResultStatus.WARN: "!",
    ResultStatus.SKIP: "↷",
    ResultStatus.ERROR: "x",
}


def _markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    output.extend(
        "| " + " | ".join(_markdown_escape(value) for value in row) + " |" for row in rows
    )
    return output


def render_markdown(view: ReportView) -> str:
    lines = [
        f"# PC Platform Validation Report — {view.overall_status.value}",
        "",
        "## Run identity",
        "",
        *_markdown_table(
            ["Field", "Value"],
            [
                ["Run ID", view.run_id],
                ["Plan", view.plan_name],
                ["Plan hash", view.plan_hash],
                ["Tool version", view.tool_version],
                ["Started", view.started_at],
                ["Ended", view.ended_at],
            ],
        ),
        "",
        "## Result summary",
        "",
        *_markdown_table(
            ["Status", "Count"],
            [[status, str(count)] for status, count in view.result_counts.items()],
        ),
        "",
        "## Sanitized platform",
        "",
        *_markdown_table(
            ["Field", "Value", "Unit", "Classification", "Source"],
            [
                [
                    value.name,
                    value.display_value,
                    value.unit or "—",
                    value.classification.value,
                    value.source or "—",
                ]
                for value in view.platform_values
            ],
        ),
        "",
    ]
    if view.contains_simulated_data:
        lines.extend(
            [
                "> **Synthetic evidence present.** Injected results are labelled per test "
                "and must not be interpreted as hardware observations.",
                "",
            ]
        )
    for test in view.tests:
        lines.extend(
            [
                f"## {test.test_id} — {_STATUS_SYMBOLS[test.status]} {test.status.value}",
                "",
                f"Duration: {test.duration_seconds:.6f} seconds",
                f"Injected: {'yes' if test.injected else 'no'}",
                "",
            ]
        )
        if test.failure_reason:
            lines.extend([f"Reason: {test.failure_reason}", ""])
        if test.exception_summary:
            lines.extend([f"Exception summary: `{test.exception_summary}`", ""])
        lines.extend(["### Measurements", ""])
        if test.metrics:
            lines.extend(
                _markdown_table(
                    ["Metric", "Value", "Unit", "Classification", "Source"],
                    [
                        [
                            value.name,
                            value.display_value,
                            value.unit or "—",
                            value.classification.value,
                            value.source or "—",
                        ]
                        for value in test.metrics
                    ],
                )
            )
        else:
            lines.append("No workload measurements were recorded.")
        lines.extend(["", "### Requirements", ""])
        if test.requirements:
            lines.extend(
                _markdown_table(
                    [
                        "Result",
                        "Metric",
                        "Operator",
                        "Configured expected",
                        "Measured actual",
                        "Unit",
                    ],
                    [
                        [
                            "PASS" if requirement.passed else "FAIL",
                            requirement.metric,
                            requirement.operator,
                            f"{requirement.expected} [{requirement.expected_classification.value}]",
                            f"{requirement.actual} [{requirement.actual_classification.value}]",
                            requirement.unit or "—",
                        ]
                        for requirement in test.requirements
                    ],
                )
            )
        else:
            lines.append("No explicit requirements were configured.")
        lines.extend(["", "### Telemetry", ""])
        lines.extend(
            _markdown_table(
                ["Derived statistic", "Value", "Unit", "Source"],
                [
                    [value.name, value.display_value, value.unit or "—", value.source or "—"]
                    for value in test.telemetry_values
                ],
            )
        )
        if test.unavailable_telemetry:
            lines.extend(
                [
                    "",
                    "Unavailable telemetry: " + ", ".join(test.unavailable_telemetry) + ".",
                ]
            )
        if test.telemetry_chart_svg:
            lines.extend(["", test.telemetry_chart_svg])
        lines.extend(
            [
                "",
                "Evidence references: "
                + (
                    ", ".join(test.evidence_references)
                    if test.evidence_references
                    else "none recorded"
                ),
                "",
            ]
        )
    lines.extend(["## Warnings", ""])
    lines.extend([f"- {warning}" for warning in view.warnings] or ["- None recorded."])
    lines.extend(["", "## Limitations", ""])
    lines.extend([f"- {limitation}" for limitation in view.limitations] or ["- None recorded."])
    lines.extend(
        [
            "",
            "## Interpretation notes",
            "",
            "- Results are local software observations, not hardware certification.",
            "- A failed test supports further diagnosis but does not alone prove "
            "defective hardware.",
            "- Timing can be influenced by scheduler activity, power policy, background "
            "load, and unavailable thermal data.",
            "- Missing telemetry is reported as unavailable and is never represented "
            "as numeric zero.",
            "",
        ]
    )
    return "\n".join(lines)


def render_html(view: ReportView) -> str:
    template_directory = Path(__file__).resolve().parent / "templates"
    environment = Environment(
        loader=FileSystemLoader(template_directory),
        autoescape=select_autoescape(enabled_extensions=("html", "j2")),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = environment.get_template("report.html.j2")
    return template.render(view=view, status_symbols=_STATUS_SYMBOLS)
