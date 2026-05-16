"""Formatters for HeatmapReport: text (ASCII grid) and JSON."""
from __future__ import annotations

import json
from typing import List

from cronaudit.heatmap import DAYS, HOURS, HeatmapReport

_SHADES = " ░▒▓█"


def _shade(value: int, peak: int) -> str:
    if peak == 0 or value == 0:
        return _SHADES[0]
    idx = max(1, round(value / peak * (len(_SHADES) - 1)))
    return _SHADES[idx]


def heatmap_to_text(report: HeatmapReport) -> str:
    """Render the heatmap as an ASCII block grid."""
    lines: List[str] = []
    lines.append("Schedule Heatmap (day × hour)")
    lines.append("=" * 60)
    # Header row
    hour_labels = "".join(f"{h:>2}" for h in HOURS)
    lines.append(f"     {hour_labels}")
    lines.append(f"     {'--' * len(HOURS)}")
    peak = report.peak
    for d_idx, day in enumerate(DAYS):
        row = "".join(
            f" {_shade(report.grid[d_idx][h], peak)} " for h in HOURS
        )
        lines.append(f"{day} |{row}|")
    lines.append("")
    lines.append(f"Total entries : {report.total_entries}")
    lines.append(f"Skipped       : {report.skipped_entries}")
    lines.append(f"Peak cell     : {peak}")
    return "\n".join(lines)


def heatmap_to_json(report: HeatmapReport) -> str:
    """Serialise the heatmap report to a JSON string."""
    grid_serialisable = {
        DAYS[d]: {str(h): report.grid[d][h] for h in HOURS}
        for d in range(7)
    }
    payload = {
        "total_entries": report.total_entries,
        "skipped_entries": report.skipped_entries,
        "peak": report.peak,
        "grid": grid_serialisable,
    }
    return json.dumps(payload, indent=2)
