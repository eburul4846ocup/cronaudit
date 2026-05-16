"""Text and JSON formatters for CoverageReport."""
from __future__ import annotations

import json
from typing import Any, Dict

from cronaudit.coverage import CoverageReport

_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def coverage_to_text(report: CoverageReport) -> str:
    """Render a human-readable coverage summary."""
    lines = [
        "=== Cron Coverage Report ===",
        f"Covered: {report.covered_hours}/{report.total_hours} hours "
        f"({report.coverage_pct}%)",
    ]

    # Mini heatmap header
    lines.append("")
    lines.append("Hour:  " + " ".join(f"{h:02d}" for h in range(24)))
    for di, day in enumerate(_DAYS):
        row = " ".join("##" if report.grid[di][h] else "  " for h in range(24))
        lines.append(f"{day}:  {row}")

    if report.gaps:
        lines.append("")
        lines.append(f"Gaps ({len(report.gaps)} windows with no scheduled jobs):")
        for gap in report.gaps:
            lines.append(f"  - {gap}")
    else:
        lines.append("")
        lines.append("No gaps detected — all hours have at least one scheduled job.")

    return "\n".join(lines)


def coverage_to_json(report: CoverageReport) -> str:
    """Render coverage report as a JSON string."""
    payload: Dict[str, Any] = {
        "covered_hours": report.covered_hours,
        "total_hours": report.total_hours,
        "coverage_pct": report.coverage_pct,
        "grid": {
            _DAYS[di]: [int(report.grid[di][h]) for h in range(24)]
            for di in range(7)
        },
        "gaps": [
            {"day": _DAYS[g.day], "start_hour": g.start_hour, "end_hour": g.end_hour}
            for g in report.gaps
        ],
    }
    return json.dumps(payload, indent=2)
