"""Detect overlapping cron schedules — entries likely to run simultaneously."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab


@dataclass
class OverlapPair:
    server: str
    entry_a: CronEntry
    entry_b: CronEntry

    def __str__(self) -> str:
        return (
            f"[{self.server}] '{self.entry_a.command}' "
            f"overlaps with '{self.entry_b.command}' "
            f"(schedule: {self.entry_a.schedule})"
        )


@dataclass
class OverlapReport:
    pairs: List[OverlapPair] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.pairs)

    def __bool__(self) -> bool:
        return self.count > 0


def _normalise_schedule(schedule: str) -> str:
    """Return a canonical schedule string for comparison."""
    return " ".join(schedule.strip().split())


def _schedules_match(a: CronEntry, b: CronEntry) -> bool:
    """Return True when two entries share an identical schedule."""
    if a is b:
        return False
    return _normalise_schedule(a.schedule) == _normalise_schedule(b.schedule)


def _pairs_from_entries(
    entries: List[CronEntry],
) -> List[Tuple[CronEntry, CronEntry]]:
    """Return all unique pairs of entries that share a schedule."""
    pairs: List[Tuple[CronEntry, CronEntry]] = []
    for i, ea in enumerate(entries):
        for eb in entries[i + 1 :]:
            if _schedules_match(ea, eb):
                pairs.append((ea, eb))
    return pairs


def detect_overlaps(crontabs: List[ServerCrontab]) -> OverlapReport:
    """Scan *crontabs* and return an :class:`OverlapReport` of matching schedules."""
    report = OverlapReport()
    for ct in crontabs:
        if not ct.is_ok:
            continue
        for ea, eb in _pairs_from_entries(ct.entries):
            report.pairs.append(OverlapPair(server=ct.server, entry_a=ea, entry_b=eb))
    return report


def format_overlap_report(report: OverlapReport) -> str:
    """Return a human-readable summary of overlapping entries."""
    if not report:
        return "No overlapping schedules detected."
    lines = [f"Overlapping schedules detected: {report.count} pair(s)", ""]
    for pair in report.pairs:
        lines.append(f"  {pair}")
    return "\n".join(lines)
