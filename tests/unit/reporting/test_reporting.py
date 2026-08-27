import hashlib
from pathlib import Path

import pytest

from platval.models.plan import TestPlan as PlanModel
from platval.persistence import ArtifactError, SQLiteRepository, persist_execution
from platval.reporting import (
    ReportFormat,
    ValueClass,
    build_report_view,
    generate_report,
    render_html,
    render_markdown,
)
from platval.runner import run_validation_plan
from platval.runner.engine import RunExecution


def make_execution(tmp_path: Path) -> RunExecution:
    plan = PlanModel.model_validate(
        {
            "name": "report-test",
            "sampling_interval_seconds": 0.05,
            "tests": [
                {
                    "id": "INV-001",
                    "name": "Inventory",
                    "category": "inventory",
                    "timeout_seconds": 2,
                    "requirements": [
                        {
                            "metric": "logical_cpu_count",
                            "operator": "greater_than",
                            "expected": 0,
                        }
                    ],
                }
            ],
        }
    )
    return run_validation_plan(plan, runtime_directory=tmp_path / "execution")


def test_view_and_renderers_label_evidence_classes(tmp_path: Path) -> None:
    execution = make_execution(tmp_path)
    runtime = tmp_path / "store"
    persist_execution(execution, runtime_directory=runtime)
    stored = SQLiteRepository(runtime / "platval.db").get_run(execution.run.run_id)
    view = build_report_view(stored)

    assert any(item.classification is ValueClass.MEASURED for item in view.platform_values)
    assert any(item.classification is ValueClass.DERIVED for item in view.platform_values)
    assert any(item.classification is ValueClass.UNAVAILABLE for item in view.platform_values)
    assert view.tests[0].requirements[0].expected == "0"
    assert view.tests[0].requirements[0].expected_classification is ValueClass.CONFIGURED
    assert view.tests[0].requirements[0].actual_classification is ValueClass.MEASURED
    assert view.tests[0].telemetry_chart_svg is not None

    markdown = render_markdown(view)
    html = render_html(view)
    assert "Configured expected" in markdown
    assert "Measured actual" in markdown
    assert "<svg" in markdown
    assert html.startswith("<!doctype html>")
    assert "Configured expected" in html
    assert 'role="img"' in html
    assert "Elapsed time (seconds)" in html
    assert "CPU utilization (%)" in html
    assert "{height-bottom}" not in html
    assert 'class="chart-point"' in html
    assert "https://" not in html
    assert "http://" not in html
    assert "<script" not in html.lower()


def test_generated_reports_are_hashed_registered_and_immutable(tmp_path: Path) -> None:
    execution = make_execution(tmp_path)
    runtime = tmp_path / "store"
    canonical = persist_execution(execution, runtime_directory=runtime)

    html_report = generate_report(
        execution.run.run_id,
        runtime_directory=runtime,
        report_format=ReportFormat.HTML,
    )
    markdown_report = generate_report(
        execution.run.run_id,
        runtime_directory=runtime,
        report_format=ReportFormat.MARKDOWN,
    )
    json_report = generate_report(
        execution.run.run_id,
        runtime_directory=runtime,
        report_format=ReportFormat.JSON,
    )

    assert html_report.path.is_file()
    assert markdown_report.path.is_file()
    assert hashlib.sha256(html_report.path.read_bytes()).hexdigest() == html_report.artifact.sha256
    assert json_report.artifact == canonical
    assert json_report.reused is True
    stored = SQLiteRepository(runtime / "platval.db").get_run(execution.run.run_id)
    assert {item.kind for item in stored.artifacts} == {
        "run_json",
        "report_html",
        "report_markdown",
    }
    with pytest.raises(ArtifactError, match="refusing to overwrite"):
        generate_report(
            execution.run.run_id,
            runtime_directory=runtime,
            report_format=ReportFormat.HTML,
        )
