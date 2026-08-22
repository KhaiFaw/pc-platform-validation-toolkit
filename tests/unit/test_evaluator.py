import pytest

from platval.evaluation import EvaluationError, evaluate_requirement
from platval.models.plan import Requirement


@pytest.mark.parametrize(
    ("operator", "actual", "expected", "passed"),
    [
        ("equals", 4, 4, True),
        ("not_equals", "x", "y", True),
        ("greater_than", 5, 4, True),
        ("greater_than_or_equal", 4, 4, True),
        ("less_than", 3, 4, True),
        ("less_than_or_equal", 4, 4, True),
        ("between", 4, [3, 5], True),
        ("contains", "x86_64", "x86", True),
    ],
)
def test_requirement_operators(
    operator: str, actual: int | str, expected: object, passed: bool
) -> None:
    requirement = Requirement.model_validate(
        {"metric": "value", "operator": operator, "expected": expected}
    )
    evaluation = evaluate_requirement(requirement, {"value": actual})
    assert evaluation.passed is passed
    assert "satisfied" in evaluation.explanation


def test_present_and_missing_metrics_remain_explicit() -> None:
    present = evaluate_requirement(
        Requirement(metric="temperature", operator="present"), {"temperature": None}
    )
    comparison = evaluate_requirement(
        Requirement(metric="frequency", operator="greater_than", expected=0), {}
    )
    assert present.passed is False
    assert comparison.passed is False
    assert "unavailable" in comparison.explanation


def test_invalid_operand_types_raise_configuration_error() -> None:
    requirement = Requirement(metric="value", operator="greater_than", expected="fast")
    with pytest.raises(EvaluationError, match="expected must be numeric"):
        evaluate_requirement(requirement, {"value": 10})

    reversed_bounds = Requirement(metric="value", operator="between", expected=[5, 3])
    with pytest.raises(EvaluationError, match="ordered"):
        evaluate_requirement(reversed_bounds, {"value": 4})
