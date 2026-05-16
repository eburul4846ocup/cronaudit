"""Formatters for ComplexityReport — text and JSON output."""
from __future__ import annotations

import json
from typing import List

from cronaudit.complexity import ComplexityReport, ComplexityResult


def _result_to_dict(r: ComplexityResult) -> dict:
    return {
        "server": r.server,
        "schedule": r.entry.schedule,
        "command": r.entry.command,
        "score": r.score,
        "level": r.level,
        "reasons": r.reasons,
    }


def complexity_to_text(report: ComplexityReport) -> str:
    """Render a human-readable complexity report."""
    lines: List[str] = [
        "=== Cron Complexity Report ===",
        f"Entries analysed : {report.count}",
        f"Complex entries  : {report.complex_count}",
        f"Average score    : {report.average_score:.2f}",
        "",
    ]

    complex_results = [r for r in report.results if r.level == "complex"]
    if not complex_results:
        lines.append("No complex entries found.")
        return "\n".join(lines)

    lines.append("Complex entries:")
    for r in sorted(complex_results, key=lambda x: x.score, reverse=True):
        lines.append(f"  [{r.score:2d}] {r.server}  {r.entry.schedule}  {r.entry.command}")
        for reason in r.reasons:
            lines.append(f"        - {reason}")

    return "\n".join(lines)


def complexity_to_json(report: ComplexityReport) -> str:
    """Render complexity report as a JSON string."""
    payload = {
        "summary": {
            "total": report.count,
            "complex": report.complex_count,
            "average_score": round(report.average_score, 2),
        },
        "entries": [_result_to_dict(r) for r in report.results],
    }
    return json.dumps(payload, indent=2)
