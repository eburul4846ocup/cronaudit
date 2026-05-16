"""Coverage analysis: identify time windows with no scheduled jobs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from cronaudit.collector import ServerCrontab
from cronaudit.parser import CronEntry


@dataclass
class CoverageGap:
    """A contiguous hour-of-week window with no scheduled entries."""
    day: int        # 0=Monday ... 6=Sunday
    start_hour: int
    end_hour: int   # inclusive

    def __str__(self) -> str:
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        label = days[self.day] if 0 <= self.day < 7 else f"day{self.day}"
        if self.start_hour == self.end_hour:
            return f"{label} {self.start_hour:02d}:00"
        return f"{label} {self.start_hour:02d}:00-{self.end_hour:02d}:59"


@dataclass
class CoverageReport:
    """Result of coverage analysis across all collected crontabs."""
    # 7 days x 24 hours boolean grid: True means at least one job fires
    grid: List[List[bool]] = field(
        default_factory=lambda: [[False] * 24 for _ in range(7)]
    )
    gaps: List[CoverageGap] = field(default_factory=list)

    @property
    def covered_hours(self) -> int:
        return sum(1 for d in self.grid for h in d if h)

    @property
    def total_hours(self) -> int:
        return 7 * 24

    @property
    def coverage_pct(self) -> float:
        return round(100.0 * self.covered_hours / self.total_hours, 1)

    def __bool__(self) -> bool:
        return len(self.gaps) == 0


def _expand_field(field_str: str, min_val: int, max_val: int) -> List[int]:
    """Expand a cron field string into a list of matching integers."""
    results: set[int] = set()
    for part in field_str.split(","):
        if part == "*":
            results.update(range(min_val, max_val + 1))
        elif "/" in part:
            base, step = part.split("/", 1)
            start = min_val if base == "*" else int(base)
            results.update(range(start, max_val + 1, int(step)))
        elif "-" in part:
            lo, hi = part.split("-", 1)
            results.update(range(int(lo), int(hi) + 1))
        else:
            results.add(int(part))
    return sorted(results)


def build_coverage(crontabs: Sequence[ServerCrontab]) -> CoverageReport:
    """Build a coverage report from a collection of ServerCrontab objects."""
    report = CoverageReport()

    for sc in crontabs:
        for entry in sc.entries:
            if not isinstance(entry, CronEntry) or entry.special:
                # Special entries like @reboot don't map to a time slot
                if entry.special in ("@hourly",):
                    for day in range(7):
                        for hour in range(24):
                            report.grid[day][hour] = True
                elif entry.special in ("@daily", "@midnight"):
                    for day in range(7):
                        report.grid[day][0] = True
                continue
            try:
                hours = _expand_field(entry.hour, 0, 23)
                days_of_week = _expand_field(entry.dow, 0, 6)
            except (ValueError, AttributeError):
                continue
            for dow in days_of_week:
                for h in hours:
                    report.grid[dow % 7][h] = True

    # Identify contiguous gaps
    for day in range(7):
        gap_start: int | None = None
        for hour in range(24):
            if not report.grid[day][hour]:
                if gap_start is None:
                    gap_start = hour
            else:
                if gap_start is not None:
                    report.gaps.append(CoverageGap(day, gap_start, hour - 1))
                    gap_start = None
        if gap_start is not None:
            report.gaps.append(CoverageGap(day, gap_start, 23))

    return report
