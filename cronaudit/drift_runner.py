"""Runner that applies drift detection across paired snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from cronaudit.collector import ServerCrontab
from cronaudit.drift import DriftReport, detect_drift


@dataclass
class DriftRunResult:
    reports: Dict[str, DriftReport] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    @property
    def total_drifted(self) -> int:
        return sum(r.count for r in self.reports.values())

    def summary_line(self) -> str:
        servers = len(self.reports)
        return (
            f"Drift detection: {servers} server(s) checked, "
            f"{self.total_drifted} schedule change(s) found."
        )


def run_drift(
    pairs: List[Tuple[ServerCrontab, ServerCrontab]],
) -> DriftRunResult:
    """Run drift detection over a list of (old, new) ServerCrontab pairs.

    Each tuple should contain snapshots for the same server.
    """
    result = DriftRunResult()
    for old_crontab, new_crontab in pairs:
        if old_crontab.server != new_crontab.server:
            result.errors.append(
                f"Server mismatch: {old_crontab.server!r} vs {new_crontab.server!r}"
            )
            continue
        report = detect_drift(
            server=old_crontab.server,
            old_entries=old_crontab.entries,
            new_entries=new_crontab.entries,
        )
        result.reports[old_crontab.server] = report
    return result
