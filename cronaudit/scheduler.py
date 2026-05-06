"""Utilities for describing and evaluating cron schedule expressions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Map of @special aliases to their cron equivalents
SPECIAL_ALIASES: dict[str, str] = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}

HUMAN_DESCRIPTIONS: dict[str, str] = {
    "@yearly": "Once a year (Jan 1 at midnight)",
    "@annually": "Once a year (Jan 1 at midnight)",
    "@monthly": "Once a month (1st at midnight)",
    "@weekly": "Once a week (Sunday at midnight)",
    "@daily": "Once a day at midnight",
    "@midnight": "Once a day at midnight",
    "@hourly": "Once an hour at minute 0",
    "@reboot": "At system reboot",
}


@dataclass
class ScheduleInfo:
    raw: str
    is_special: bool
    description: str
    expanded: Optional[str] = None


def describe_schedule(expression: str) -> ScheduleInfo:
    """Return a human-readable description for a cron schedule expression."""
    expr = expression.strip()

    if expr in HUMAN_DESCRIPTIONS:
        expanded = SPECIAL_ALIASES.get(expr)
        return ScheduleInfo(
            raw=expr,
            is_special=True,
            description=HUMAN_DESCRIPTIONS[expr],
            expanded=expanded,
        )

    parts = expr.split()
    if len(parts) != 5:
        return ScheduleInfo(raw=expr, is_special=False, description="Invalid expression")

    description = _describe_standard(parts)
    return ScheduleInfo(raw=expr, is_special=False, description=description)


def _describe_standard(parts: list[str]) -> str:
    """Build a plain-English description from the five cron fields."""
    minute, hour, dom, month, dow = parts

    if all(p == "*" for p in parts):
        return "Every minute"

    time_str = _time_str(minute, hour)
    day_str = _day_str(dom, dow, month)
    return f"{time_str}{day_str}".strip()


def _time_str(minute: str, hour: str) -> str:
    if hour == "*" and minute == "*":
        return "Every minute"
    if hour == "*":
        return f"At minute {minute} of every hour"
    if minute == "*":
        return f"Every minute during hour {hour}"
    try:
        dt = datetime(2000, 1, 1, int(hour), int(minute))
        return f"At {dt.strftime('%H:%M')}"
    except ValueError:
        return f"At {hour}:{minute}"


def _day_str(dom: str, dow: str, month: str) -> str:
    parts = []
    if dom != "*":
        parts.append(f" on day {dom} of the month")
    if dow != "*":
        parts.append(f" on weekday {dow}")
    if month != "*":
        parts.append(f" in month {month}")
    return ",".join(parts)
