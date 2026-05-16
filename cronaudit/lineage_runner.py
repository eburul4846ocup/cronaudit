"""Runner that applies lineage detection across paired server snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from cronaudit.collector import ServerCrontab
from cronaudit.lineage import LineageReport, detect_lineage


@dataclass
class LineageRunResult:
    reports: Dict[str, LineageReport] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def total_renames(self) -> int:
        return sum(r.count for r in self.reports.values())

    def summary_line(self) -> str:
        servers = len(self.reports)
        renames = self.total_renames
        return f"{servers} server(s) compared, {renames} likely rename(s) detected"


def run_lineage(
    pairs: List[Tuple[ServerCrontab, ServerCrontab]],
    threshold: float = 0.72,
) -> LineageRunResult:
    """Run lineage detection over a list of (old, new) ServerCrontab pairs."""
    result = LineageRunResult()
    for old, new in pairs:
        if old.server != new.server:
            result.errors.append(
                f"Server mismatch: {old.server!r} vs {new.server!r}"
            )
            continue
        try:
            report = detect_lineage(old, new, threshold=threshold)
            result.reports[old.server] = report
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"{old.server}: {exc}")
    return result
