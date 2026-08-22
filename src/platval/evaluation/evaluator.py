"""Small explicit requirement-operator implementation."""

from collections.abc import Mapping

from platval.models.common import Scalar
from platval.models.plan import Requirement, RequirementOperator
from platval.models.results import RequirementEvaluation


class EvaluationError(ValueError):
    """A requirement has incompatible operand types."""


def _numeric(value: Scalar, label: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvaluationError(f"{label} must be numeric")
    return value


def _expected_scalar(value: Scalar | list[Scalar]) -> Scalar:
    if isinstance(value, list):
        raise EvaluationError("expected value must be scalar for this operator")
    return value


def evaluate_requirement(
    requirement: Requirement, metrics: Mapping[str, Scalar]
) -> RequirementEvaluation:
    """Evaluate one requirement without coercing absent values to zero."""
    actual = metrics.get(requirement.metric)
    expected = requirement.expected
    operator = requirement.operator

    if operator is RequirementOperator.PRESENT:
        passed = actual is not None
    elif actual is None:
        passed = False
    elif operator is RequirementOperator.EQUALS:
        passed = actual == expected
    elif operator is RequirementOperator.NOT_EQUALS:
        passed = actual != expected
    elif operator is RequirementOperator.GREATER_THAN:
        passed = _numeric(actual, "actual") > _numeric(_expected_scalar(expected), "expected")
    elif operator is RequirementOperator.GREATER_THAN_OR_EQUAL:
        passed = _numeric(actual, "actual") >= _numeric(_expected_scalar(expected), "expected")
    elif operator is RequirementOperator.LESS_THAN:
        passed = _numeric(actual, "actual") < _numeric(_expected_scalar(expected), "expected")
    elif operator is RequirementOperator.LESS_THAN_OR_EQUAL:
        passed = _numeric(actual, "actual") <= _numeric(_expected_scalar(expected), "expected")
    elif operator is RequirementOperator.BETWEEN:
        if not isinstance(expected, list) or len(expected) != 2:
            raise EvaluationError("between requires two numeric boundaries")
        lower = _numeric(expected[0], "lower boundary")
        upper = _numeric(expected[1], "upper boundary")
        if lower > upper:
            raise EvaluationError("between boundaries must be ordered")
        numeric_actual = _numeric(actual, "actual")
        passed = lower <= numeric_actual <= upper
    elif operator is RequirementOperator.CONTAINS:
        if not isinstance(actual, str) or not isinstance(expected, str):
            raise EvaluationError("contains requires string operands")
        passed = expected in actual
    else:
        raise EvaluationError(f"unsupported operator: {operator}")

    if actual is None:
        explanation = f"metric {requirement.metric!r} is unavailable"
    else:
        explanation = (
            f"actual value {actual!r} satisfied {operator.value} {expected!r}"
            if passed
            else f"actual value {actual!r} did not satisfy {operator.value} {expected!r}"
        )
    return RequirementEvaluation(
        metric=requirement.metric,
        operator=operator.value,
        expected=expected,
        actual=actual,
        unit=requirement.unit,
        passed=passed,
        explanation=explanation,
    )
