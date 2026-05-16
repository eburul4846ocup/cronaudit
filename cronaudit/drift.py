"""Detect schedule drift: entries whose timing has shifted across snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronaudit.parser import CronEntry


@dataclass
class DriftPair:
    server: str
    command: str
    old_schedule: str
    new_schedule: str
    user: Optional[str] = None

    def __str__(self) -> str:
        user_part = f" (user={self.user})" if self.user else ""
        return (
            f"[{self.server}] {self.command}{user_part}: "
            f"{self.old_schedule!r} -> {self.new_schedule!r}"
        )


@dataclass
class DriftReport:
    pairs: List[DriftPair] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.pairs)

    def __bool__(self) -> bool:
        return self.count > 0


def _schedule_str(entry: CronEntry) -> str:
    """Return a canonical schedule string for comparison."""
    if entry.special:
        return entry.special
    return " ".join([
        entry.minute or "*",
        entry.hour or "*",
        entry.day_of_month or "*",
        entry.month or "*",
        entry.day_of_week or "*",
    ])


def _entry_key(entry: CronEntry) -> tuple:
    return (entry.command, entry.user)


def detect_drift(
    server: str,
    old_entries: List[CronEntry],
    new_entries: List[CronEntry],
) -> DriftReport:
    """Compare two lists of entries for the same server and report schedule changes."""
    old_map = {_entry_key(e): e for e in old_entries}
    new_map = {_entry_key(e): e for e in new_entries}

    pairs: List[DriftPair] = []
    for key, new_entry in new_map.items():
        old_entry = old_map.get(key)
        if old_entry is None:
            continue
        old_sched = _schedule_str(old_entry)
        new_sched = _schedule_str(new_entry)
        if old_sched != new_sched:
            pairs.append(DriftPair(
                server=server,
                command=new_entry.command,
                old_schedule=old_sched,
                new_schedule=new_sched,
                user=new_entry.user,
            ))

    return DriftReport(pairs=pairs)
