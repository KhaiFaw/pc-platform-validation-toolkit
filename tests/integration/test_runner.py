from pathlib import Path

from platval.models.plan import TestPlan as PlanModel
from platval.models.status import ResultStatus
from platval.runner import load_test_plan, run_validation_plan


def test_quick_plan_completes_with_structured_results(tmp_path: Path) -> None:
    plan = load_test_plan(Path("configs/quick.yaml"))
    execution = run_validation_plan(plan, runtime_directory=tmp_path / "runtime")
    statuses = {result.test_id: result.status for result in execution.run.test_results}
    assert execution.run.overall_status in {ResultStatus.PASS, ResultStatus.WARN}
    assert len(execution.run.test_results) == len(plan.tests)
    assert statuses["INV-001"] is ResultStatus.PASS
    assert statuses["CPU-001"] is ResultStatus.PASS
    assert statuses["MEM-001"] is ResultStatus.PASS
    assert statuses["STO-001"] is ResultStatus.PASS
    assert statuses["TEL-001"] in {ResultStatus.PASS, ResultStatus.WARN}
    assert statuses["CFG-001"] in {ResultStatus.PASS, ResultStatus.SKIP}
    assert all(samples for samples in execution.telemetry_samples.values())
    assert list((tmp_path / "runtime" / "tmp").iterdir()) == []


def test_unmet_requirement_produces_fail_status(tmp_path: Path) -> None:
    plan = PlanModel.model_validate(
        {
            "name": "deterministic-requirement-failure",
            "sampling_interval_seconds": 0.05,
            "tests": [
                {
                    "id": "INV-001",
                    "name": "Impossible logical count",
                    "category": "inventory",
                    "timeout_seconds": 2,
                    "requirements": [
                        {
                            "metric": "logical_cpu_count",
                            "operator": "less_than",
                            "expected": 0,
                        }
                    ],
                }
            ],
        }
    )
    execution = run_validation_plan(plan, runtime_directory=tmp_path / "runtime")
    result = execution.run.test_results[0]
    assert result.status is ResultStatus.FAIL
    assert result.requirements[0].passed is False
    assert execution.run.overall_status is ResultStatus.FAIL
