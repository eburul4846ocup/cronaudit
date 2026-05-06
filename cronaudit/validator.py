"""Validation helpers for cron schedule fields."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "dom": (1, 31),
    "month": (1, 12),
    "dow": (0, 7),
}

SPECIAL_KEYWORDS = {
    "@reboot", "@yearly", "@annually", "@monthly",
    "@weekly", "@daily", "@midnight", "@hourly",
}


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid


def validate_expression(expression: str) -> ValidationResult:
    """Validate a full cron schedule expression."""
    expr = expression.strip()

    if expr in SPECIAL_KEYWORDS:
        return ValidationResult(valid=True)

    parts = expr.split()
    if len(parts) != 5:
        return ValidationResult(
            valid=False,
            errors=[f"Expected 5 fields, got {len(parts)}: '{expr}'"],
        )

    field_names = ["minute", "hour", "dom", "month", "dow"]
    errors: list[str] = []
    for name, value in zip(field_names, parts):
        errs = _validate_field(name, value)
        errors.extend(errs)

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def _validate_field(name: str, value: str) -> list[str]:
    """Validate a single cron field value."""
    lo, hi = FIELD_RANGES[name]
    errors: list[str] = []

    if value == "*":
        return []

    # Handle step values: */2 or 1-5/2
    step_part = None
    if "/" in value:
        base, _, step_part = value.partition("/")
        if not step_part.isdigit():
            errors.append(f"{name}: invalid step '{step_part}'")
            return errors
        value = base

    # Handle ranges
    if "-" in value:
        start, _, end = value.partition("-")
        for v in (start, end):
            err = _check_numeric(name, v, lo, hi)
            if err:
                errors.append(err)
        return errors

    # Handle lists
    for item in value.split(","):
        err = _check_numeric(name, item, lo, hi)
        if err:
            errors.append(err)

    return errors


def _check_numeric(name: str, value: str, lo: int, hi: int) -> str | None:
    if not value.isdigit():
        return f"{name}: non-numeric value '{value}'"
    n = int(value)
    if not (lo <= n <= hi):
        return f"{name}: value {n} out of range [{lo}-{hi}]"
    return None
