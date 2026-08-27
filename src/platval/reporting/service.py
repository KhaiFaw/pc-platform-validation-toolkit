"""Load canonical evidence and create immutable local report artifacts."""

from enum import StrEnum
from pathlib import Path

from platval.models.common import DomainModel
from platval.persistence import ArtifactRecord, load_stored_run, write_derived_artifact
from platval.reporting.renderers import render_html, render_markdown
from platval.reporting.view import build_report_view


class ReportFormat(StrEnum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class GeneratedReport(DomainModel):
    format: ReportFormat
    path: Path
    artifact: ArtifactRecord
    reused: bool = False


_REPORT_FILES = {
    ReportFormat.MARKDOWN: ("report.md", "report_markdown"),
    ReportFormat.HTML: ("report.html", "report_html"),
}


def generate_report(
    run_id: str, *, runtime_directory: Path, report_format: ReportFormat
) -> GeneratedReport:
    """Generate a report from stored evidence, or locate canonical JSON."""
    runtime = runtime_directory.resolve()
    stored = load_stored_run(run_id, runtime_directory=runtime)
    if report_format is ReportFormat.JSON:
        artifact = next(
            (item for item in stored.artifacts if item.kind == "run_json"),
            None,
        )
        if artifact is None:
            raise ValueError("stored run has no canonical JSON artifact")
        path = runtime / Path(artifact.relative_path)
        if not path.is_file():
            raise ValueError("canonical JSON artifact is missing from disk")
        return GeneratedReport(
            format=report_format,
            path=path,
            artifact=artifact,
            reused=True,
        )

    view = build_report_view(stored)
    filename, kind = _REPORT_FILES[report_format]
    content = render_html(view) if report_format is ReportFormat.HTML else render_markdown(view)
    artifact = write_derived_artifact(
        run_id,
        runtime_directory=runtime,
        filename=filename,
        kind=kind,
        content=content,
    )
    return GeneratedReport(
        format=report_format,
        path=runtime / Path(artifact.relative_path),
        artifact=artifact,
    )
