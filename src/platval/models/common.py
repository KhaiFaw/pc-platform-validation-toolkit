"""Common validation helpers for domain models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

type Scalar = bool | int | float | str | None
type ExpectedValue = Scalar | list[Scalar]


class DomainModel(BaseModel):
    """Base model that rejects misspelled or unplanned input fields."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def require_aware_timestamp(value: datetime) -> datetime:
    """Reject local timestamps whose UTC relationship cannot be reconstructed."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return value
