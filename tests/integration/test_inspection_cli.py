import json
from pathlib import Path

from typer.testing import CliRunner

from platval.cli import app

runner = CliRunner()


def test_inventory_json_command_is_sanitized(tmp_path: Path) -> None:
    result = runner.invoke(app, ["inventory", "--json", "--storage-path", str(tmp_path)])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["platform"]["logical_processor_count"] > 0
    assert "hostname" not in result.output.lower()
    assert str(Path.home()).lower() not in result.output.lower()


def test_inventory_human_command_reports_fingerprint(tmp_path: Path) -> None:
    result = runner.invoke(app, ["inventory", "--storage-path", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "Sanitized platform inventory" in result.output
    assert "Fingerprint" in result.output


def test_doctor_json_and_human_commands(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    json_result = runner.invoke(app, ["doctor", "--json", "--runtime-dir", str(runtime)])
    assert json_result.exit_code == 0, json_result.output
    payload = json.loads(json_result.output)
    assert payload["overall_status"] in {"PASS", "WARN"}

    human_result = runner.invoke(app, ["doctor", "--runtime-dir", str(runtime)])
    assert human_result.exit_code == 0, human_result.output
    assert "platval doctor" in human_result.output


def test_run_command_returns_structured_json(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run",
            "--plan",
            "configs/quick.yaml",
            "--runtime-dir",
            str(tmp_path / "runtime"),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["execution"]["run"]["overall_status"] in {"PASS", "WARN"}
    assert payload["execution"]["run"]["test_results"]
    assert payload["execution"]["telemetry_samples"]
    assert payload["artifacts"][0]["kind"] == "run_json"

    run_id = payload["execution"]["run"]["run_id"]
    runtime = str(tmp_path / "runtime")
    list_result = runner.invoke(app, ["runs", "list", "--runtime-dir", runtime, "--json"])
    assert list_result.exit_code == 0, list_result.output
    assert json.loads(list_result.output)[0]["run_id"] == run_id

    show_result = runner.invoke(app, ["runs", "show", run_id, "--runtime-dir", runtime, "--json"])
    assert show_result.exit_code == 0, show_result.output
    assert json.loads(show_result.output)["execution"]["run"]["run_id"] == run_id

    delete_result = runner.invoke(
        app, ["runs", "delete", run_id, "--runtime-dir", runtime, "--yes"]
    )
    assert delete_result.exit_code == 0, delete_result.output
    assert "artifacts moved" in delete_result.output
    assert any((tmp_path / "runtime" / "trash").iterdir())
