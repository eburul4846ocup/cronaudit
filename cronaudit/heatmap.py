"""Heatmap module: builds a schedule frequency heatmap across hours and weekdays."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from cronaudit.collector import ServerCrontab
from cronaudit.parser import CronEntry

# Axes
HOURS = list(range(24))
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_DAY_INDEX = {name: i for i, name in enumerate(DAYS)}


@dataclass
class HeatmapReport:
    """Frequency counts keyed by (day_index, hour)."""
    # grid[day][hour] = count
    grid: Dict[int, Dict[int, int]] = field(
        default_factory=lambda: {d: {h: 0 for h in HOURS} for d in range(7)}
    )
    total_entries: int = 0
    skipped_entries: int = 0

    @property
    def peak(self) -> int:
        """Maximum count in any single cell."""
        return max(
            self.grid[d][h] for d in range(7) for h in HOURS
        )


def _expand_field(field_val: str, lo: int, hi: int) -> List[int]:
    """Expand a cron field string to a list of matching integers."""
    if field_val == "*":
        return list(range(lo, hi + 1))
    results: List[int] = []
    for part in field_val.split(","):
        if "/" in part:
            base, step_str = part.split("/", 1)
            step = int(step_str)
            start = lo if base == "*" else int(base.split("-")[0])
            end = hi if base == "*" else (int(base.split("-")[1]) if "-" in base else start)
            results.extend(range(start, end + 1, step))
        elif "-" in part:
            a, b = part.split("-", 1)
            results.extend(range(int(a), int(b) + 1))
        else:
            results.append(int(part))
    return results


def _increment_entry(grid: Dict[int, Dict[int, int]], entry: CronEntry) -> bool:
    """Increment grid cells for a single CronEntry. Returns False if skipped."""
    if entry.special or not entry.schedule:
        return False
    parts = entry.schedule.split()
    if len(parts) != 5:
        return False
    _, hour_f, _, _, dow_f = parts
    try:
        hours = _expand_field(hour_f, 0, 23)
        dows = _expand_field(dow_f, 0, 6)  # 0=Sun in cron, remap below
    except (ValueError, IndexError):
        return False
    # cron dow: 0 or 7 = Sunday; remap to Mon=0 .. Sun=6
    remapped = [(d % 7 + 6) % 7 for d in dows]
    for d in remapped:
        for h in hours:
            grid[d][h] += 1
    return True


def build_heatmap(crontabs: List[ServerCrontab]) -> HeatmapReport:
    """Build a HeatmapReport from a list of ServerCrontab objects."""
    report = HeatmapReport()
    for crontab in crontabs:
        for entry in crontab.entries:
            report.total_entries += 1
            if not _increment_entry(report.grid, entry):
                report.skipped_entries += 1
    return report
