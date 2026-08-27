"""Static reports derived from canonical stored validation evidence."""

from platval.reporting.renderers import render_html, render_markdown
from platval.reporting.service import GeneratedReport, ReportFormat, generate_report
from platval.reporting.view import ReportView, ValueClass, build_report_view

__all__ = [
    "GeneratedReport",
    "ReportFormat",
    "ReportView",
    "ValueClass",
    "build_report_view",
    "generate_report",
    "render_html",
    "render_markdown",
]
