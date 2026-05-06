"""Crontab entry parser module."""

import re
from dataclasses import dataclass, field
from typing import Optional

CRON_FIELDS = ["minute", "hour", "day_of_month", "month", "day_of_week"]

SPECIAL_STRINGS = {
    "@reboot": "Run once at startup",
    "@yearly": "Run once a year (0 0 1 1 *)",
    "@annually": "Run once a year (0 0 1 1 *)",
    "@monthly": "Run once a month (0 0 1 * *)",
    "@weekly": "Run once a week (0 0 * * 0)",
    "@daily": "Run once a day (0 0 * * *)",
    "@midnight": "Run once a day (0 0 * * *)",
    "@hourly": "Run once an hour (0 * * * *)",
}


@dataclass
class CronEntry:
    raw: str
    user: Optional[str] = None
    server: Optional[str] = None
    schedule: str = ""
    command: str = ""
    is_special: bool = False
    special_description: Optional[str] = None
    fields: dict = field(default_factory=dict)
    comment: Optional[str] = None
    is_valid: bool = True
    error: Optional[str] = None


def parse_line(line: str, user: Optional[str] = None, server: Optional[str] = None) -> Optional[CronEntry]:
    """Parse a single crontab line into a CronEntry."""
    stripped = line.strip()

    if not stripped or stripped.startswith("#"):
        return None

    comment = None
    if " #" in stripped:
        parts = stripped.split(" #", 1)
        stripped = parts[0].strip()
        comment = parts[1].strip()

    entry = CronEntry(raw=line, user=user, server=server, comment=comment)

    # Handle special strings like @reboot, @daily, etc.
    for special, description in SPECIAL_STRINGS.items():
        if stripped.startswith(special):
            entry.is_special = True
            entry.schedule = special
            entry.special_description = description
            entry.command = stripped[len(special):].strip()
            return entry

    tokens = stripped.split()
    if len(tokens) < 6:
        entry.is_valid = False
        entry.error = f"Expected at least 6 fields, got {len(tokens)}"
        return entry

    schedule_tokens = tokens[:5]
    entry.schedule = " ".join(schedule_tokens)
    entry.command = " ".join(tokens[5:])
    entry.fields = dict(zip(CRON_FIELDS, schedule_tokens))

    return entry


def parse_crontab(content: str, user: Optional[str] = None, server: Optional[str] = None) -> list[CronEntry]:
    """Parse full crontab content and return list of CronEntry objects."""
    entries = []
    for line in content.splitlines():
        entry = parse_line(line, user=user, server=server)
        if entry is not None:
            entries.append(entry)
    return entries
