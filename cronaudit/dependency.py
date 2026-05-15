"""Detect cron entries that may have implicit ordering dependencies."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronaudit.collector import ServerCrontab
from cronaudit.parser import CronEntry


@dataclass
class DependencyPair:
    """Two entries suspected to have an ordering dependency."""

    server: str
    first: CronEntry
    second: CronEntry
    reason: str

    def __str__(self) -> str:
        return (
            f"[{self.server}] '{self.first.command}' -> '{self.second.command}': {self.reason}"
        )


@dataclass
class DependencyReport:
    """Aggregated dependency analysis across all servers."""

    pairs: List[DependencyPair] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.pairs)

    def __bool__(self) -> bool:
        return self.count > 0


def _same_schedule(a: CronEntry, b: CronEntry) -> bool:
    """Return True if two entries share the same schedule expression."""
    return a.schedule == b.schedule


def _sequential_minutes(a: CronEntry, b: CronEntry) -> Optional[str]:
    """Return a reason string if entries run in consecutive minutes, else None."""
    parts_a = a.schedule.split()
    parts_b = b.schedule.split()
    if len(parts_a) != 5 or len(parts_b) != 5:
        return None
    try:
        min_a = int(parts_a[0])
        min_b = int(parts_b[0])
    except ValueError:
        return None
    # Same hour, consecutive minutes
    if parts_a[1:] == parts_b[1:] and abs(min_b - min_a) == 1:
        return f"consecutive minutes ({min_a} then {min_b}) on same hour/day pattern"
    return None


def detect_dependencies(crontabs: List[ServerCrontab]) -> DependencyReport:
    """Scan crontabs for entries that may depend on each other's ordering."""
    report = DependencyReport()
    for ct in crontabs:
        entries = ct.entries
        for i, a in enumerate(entries):
            for b in entries[i + 1 :]:
                if _same_schedule(a, b) and a.schedule not in ("@reboot",):
                    report.pairs.append(
                        DependencyPair(
                            server=ct.server,
                            first=a,
                            second=b,
                            reason="identical schedule — execution order undefined",
                        )
                    )
                    continue
                reason = _sequential_minutes(a, b)
                if reason:
                    report.pairs.append(
                        DependencyPair(
                            server=ct.server,
                            first=a,
                            second=b,
                            reason=reason,
                        )
                    )
    return report
