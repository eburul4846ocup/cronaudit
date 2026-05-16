"""Text and JSON formatters for lineage reports."""
from __future__ import annotations

import json
from typing import Dict

from cronaudit.lineage import LineageReport


def _report_to_dict(server: str, report: LineageReport) -> dict:
    return {
        "server": server,
        "renames": [
            {
                "old_command": p.old_command,
                "new_command": p.new_command,
                "similarity": round(p.similarity, 4),
                "schedule_changed": p.schedule_changed,
            }
            for p in report.pairs
        ],
    }


def lineage_to_text(reports: Dict[str, LineageReport]) -> str:
    lines = ["=== Lineage Report ==="]
    if not reports:
        lines.append("  (no data)")
        return "\n".join(lines)
    for server, report in reports.items():
        lines.append(f"\n[{server}]")
        if not report:
            lines.append("  No renames detected.")
            continue
        for pair in report.pairs:
            tag = " [schedule changed]" if pair.schedule_changed else ""
            lines.append(
                f"  {pair.old_command!r}"
                f"  ->  {pair.new_command!r}"
                f"  (sim={pair.similarity:.0%}){tag}"
            )
    return "\n".join(lines)


def lineage_to_json(reports: Dict[str, LineageReport]) -> str:
    data = [_report_to_dict(server, report) for server, report in reports.items()]
    return json.dumps(data, indent=2)
