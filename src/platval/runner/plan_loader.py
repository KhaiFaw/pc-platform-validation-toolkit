"""Bounded YAML loading and canonical plan hashing."""

import hashlib
import json
from pathlib import Path

import yaml
from pydantic import ValidationError

from platval.models.plan import TestPlan

_MAX_PLAN_BYTES = 1024 * 1024


class PlanLoadError(ValueError):
    """A test plan could not be read or validated."""


def _validation_message(error: ValidationError) -> str:
    details: list[str] = []
    for item in error.errors(include_url=False):
        location = ".".join(str(part) for part in item["loc"])
        details.append(f"{location or '<root>'}: {item['msg']}")
    return "; ".join(details)


def load_test_plan(path: Path) -> TestPlan:
    """Load one safe YAML document with a strict size and schema boundary."""
    try:
        size = path.stat().st_size
        if size > _MAX_PLAN_BYTES:
            raise PlanLoadError("test plan exceeds the 1 MiB size limit")
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PlanLoadError(f"test plan could not be read ({type(exc).__name__})") from None
    try:
        raw = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        location = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        raise PlanLoadError(f"invalid YAML{location}") from None
    if not isinstance(raw, dict):
        raise PlanLoadError("test plan root must be a mapping")
    try:
        return TestPlan.model_validate(raw)
    except ValidationError as exc:
        raise PlanLoadError(_validation_message(exc)) from None


def canonical_plan_hash(plan: TestPlan) -> str:
    encoded = json.dumps(
        plan.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
