"""Format drift reports as text or JSON."""
from __future__ import annotations

import json
from typing import Dict

from cronaudit.drift import DriftPair, DriftReport


def _pair_to_dict(pair: DriftPair) -> dict:
    return {
        "server": pair.server,
        "command": pair.command,
        "user": pair.user,
        "old_schedule": pair.old_schedule,
        "new_schedule": pair.new_schedule,
    }


def drift_to_text(reports: Dict[str, DriftReport]) -> str:
    lines = ["=== Schedule Drift Report ==="]
    total = sum(r.count for r in reports.values())
    if total == 0:
        lines.append("No schedule drift detected.")
        return "\n".join(lines)

    for server, report in sorted(reports.items()):
        if not report:
            continue
        lines.append(f"\nServer: {server}")
        lines.append("-" * 40)
        for pair in report.pairs:
            user_part = f" [{pair.user}]" if pair.user else ""
            lines.append(f"  Command : {pair.command}{user_part}")
            lines.append(f"  Before  : {pair.old_schedule}")
            lines.append(f"  After   : {pair.new_schedule}")
            lines.append("")

    lines.append(f"Total drift events: {total}")
    return "\n".join(lines)


def drift_to_json(reports: Dict[str, DriftReport]) -> str:
    data = {
        "drift_report": {
            server: [_pair_to_dict(p) for p in report.pairs]
            for server, report in sorted(reports.items())
        },
        "total_drifted": sum(r.count for r in reports.values()),
    }
    return json.dumps(data, indent=2)
