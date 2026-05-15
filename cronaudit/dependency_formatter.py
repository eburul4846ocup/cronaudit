"""Format DependencyReport as text or JSON."""
from __future__ import annotations

import json
from typing import List

from cronaudit.dependency import DependencyReport


def dependency_to_text(report: DependencyReport) -> str:
    """Render a DependencyReport as a human-readable text block."""
    lines: List[str] = []
    lines.append("=== Dependency Analysis ===")
    if not report:
        lines.append("No potential dependency issues detected.")
        return "\n".join(lines)

    lines.append(f"Found {report.count} potential dependency pair(s):\n")
    for i, pair in enumerate(report.pairs, start=1):
        lines.append(f"  {i}. Server : {pair.server}")
        lines.append(f"     Entry A: [{pair.first.schedule}] {pair.first.command}")
        lines.append(f"     Entry B: [{pair.second.schedule}] {pair.second.command}")
        lines.append(f"     Reason : {pair.reason}")
        lines.append("")
    return "\n".join(lines).rstrip()


def dependency_to_json(report: DependencyReport) -> str:
    """Render a DependencyReport as a JSON string."""
    data = {
        "dependency_pair_count": report.count,
        "pairs": [
            {
                "server": p.server,
                "entry_a": {"schedule": p.first.schedule, "command": p.first.command, "user": p.first.user},
                "entry_b": {"schedule": p.second.schedule, "command": p.second.command, "user": p.second.user},
                "reason": p.reason,
            }
            for p in report.pairs
        ],
    }
    return json.dumps(data, indent=2)
