from pathlib import Path

import pytest

from platval.runner.plan_loader import PlanLoadError, canonical_plan_hash, load_test_plan


def test_repository_plans_load_and_hash_stably() -> None:
    quick = load_test_plan(Path("configs/quick.yaml"))
    standard = load_test_plan(Path("configs/standard.yaml"))
    assert quick.name == "quick-validation"
    assert standard.name == "standard-validation"
    assert canonical_plan_hash(quick) == canonical_plan_hash(
        load_test_plan(Path("configs/quick.yaml"))
    )
    assert len(canonical_plan_hash(quick)) == 64


def test_loader_reports_field_location(tmp_path: Path) -> None:
    plan = tmp_path / "invalid.yaml"
    plan.write_text(
        """schema_version: 1
name: invalid
tests:
  - id: CPU-001
    name: Example
    category: cpu
    timeout_seconds: 5
    interations: 2
""",
        encoding="utf-8",
    )
    with pytest.raises(PlanLoadError, match=r"tests\.0\.interations"):
        load_test_plan(plan)


def test_loader_rejects_unknown_schema_and_non_mapping(tmp_path: Path) -> None:
    wrong_schema = tmp_path / "schema.yaml"
    wrong_schema.write_text("schema_version: 99\nname: wrong\ntests: []\n", encoding="utf-8")
    with pytest.raises(PlanLoadError, match="expected plan schema"):
        load_test_plan(wrong_schema)

    sequence = tmp_path / "sequence.yaml"
    sequence.write_text("- not\n- a\n- mapping\n", encoding="utf-8")
    with pytest.raises(PlanLoadError, match="root must be a mapping"):
        load_test_plan(sequence)


def test_loader_reports_malformed_yaml(tmp_path: Path) -> None:
    plan = tmp_path / "malformed.yaml"
    plan.write_text("name: [unterminated", encoding="utf-8")
    with pytest.raises(PlanLoadError, match="invalid YAML at line"):
        load_test_plan(plan)
