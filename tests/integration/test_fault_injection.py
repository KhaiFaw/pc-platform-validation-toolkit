import json
from pathlib import Path

from typer.testing import CliRunner

from platval.cli import app
from platval.models.status import ResultStatus
from platval.runner import load_test_plan, run_validation_plan


def test_failure_plan_is_opt_in_labelled_and_deterministic(tmp_path: Path) -> None:
    plan = load_test_plan(Path("configs/failure-demo.yaml"))
    execution = run_validation_plan(plan, runtime_directory=tmp_path / "plan")
    result = execution.run.test_results[0]

    assert execution.run.overall_status is ResultStatus.FAIL
    assert result.status is ResultStatus.FAIL
    assert result.injected is True
    assert result.measured_values["checksum_valid"].value is False
    assert "injected checksum mismatch" in (result.failure_reason or "")
    assert result.evidence_references == ["fault-injection:checksum_mismatch"]
    assert any("not hardware evidence" in item for item in execution.run.warnings)


def test_demo_failure_cli_generates_labelled_reports(tmp_path: Path) -> None:
    runtime = tmp_path / "demo"
    result = CliRunner().invoke(
        app,
        ["demo", "failure", "--runtime-dir", str(runtime), "--json"],
    )
    assert result.exit_code == 0, result.output
    stored = json.loads(result.output)
    test_result = stored["execution"]["run"]["test_results"][0]
    assert stored["execution"]["run"]["overall_status"] == "FAIL"
    assert test_result["injected"] is True
    assert {item["kind"] for item in stored["artifacts"]} == {
        "run_json",
        "report_html",
        "report_markdown",
    }
    html_artifact = next(item for item in stored["artifacts"] if item["kind"] == "report_html")
    html = (runtime / html_artifact["relative_path"]).read_text(encoding="utf-8")
    assert "Synthetic evidence present" in html
    assert "Injected yes" in html
    assert "fault-injection:checksum_mismatch" in html
