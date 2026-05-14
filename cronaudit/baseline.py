"""Baseline comparison: compare current audit results against a saved baseline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronaudit.multi import AuditResult
from cronaudit.parser import CronEntry


@dataclass
class BaselineDiff:
    server: str
    added: List[CronEntry] = field(default_factory=list)
    removed: List[CronEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed)


@dataclass
class BaselineReport:
    diffs: List[BaselineDiff] = field(default_factory=list)
    servers_checked: int = 0
    baseline_label: str = ""

    @property
    def changed_servers(self) -> int:
        return sum(1 for d in self.diffs if d.has_changes)

    @property
    def total_added(self) -> int:
        return sum(len(d.added) for d in self.diffs)

    @property
    def total_removed(self) -> int:
        return sum(len(d.removed) for d in self.diffs)

    @property
    def clean(self) -> bool:
        return self.changed_servers == 0


def _entry_key(entry: CronEntry) -> str:
    return f"{entry.schedule}|{entry.user or ''}|{entry.command}"


def compare_to_baseline(
    current: List[AuditResult],
    baseline: List[AuditResult],
    label: str = "",
) -> BaselineReport:
    """Compare current audit results against baseline audit results."""
    baseline_map: dict[str, List[CronEntry]] = {
        r.server: r.entries for r in baseline
    }
    current_map: dict[str, List[CronEntry]] = {
        r.server: r.entries for r in current
    }

    diffs: List[BaselineDiff] = []
    all_servers = set(baseline_map) | set(current_map)

    for server in sorted(all_servers):
        base_keys = {_entry_key(e): e for e in baseline_map.get(server, [])}
        curr_keys = {_entry_key(e): e for e in current_map.get(server, [])}

        added = [curr_keys[k] for k in curr_keys if k not in base_keys]
        removed = [base_keys[k] for k in base_keys if k not in curr_keys]

        diffs.append(BaselineDiff(server=server, added=added, removed=removed))

    return BaselineReport(
        diffs=diffs,
        servers_checked=len(all_servers),
        baseline_label=label,
    )


def format_baseline_report(report: BaselineReport) -> str:
    """Render a BaselineReport as a human-readable string."""
    lines: List[str] = []
    label = f" [{report.baseline_label}]" if report.baseline_label else ""
    lines.append(f"Baseline Comparison{label}")
    lines.append(f"Servers checked : {report.servers_checked}")
    lines.append(f"Changed servers : {report.changed_servers}")
    lines.append(f"Entries added   : {report.total_added}")
    lines.append(f"Entries removed : {report.total_removed}")

    for diff in report.diffs:
        if not diff.has_changes:
            continue
        lines.append(f"\n  {diff.server}:")
        for e in diff.added:
            lines.append(f"    + {e.schedule}  {e.command}")
        for e in diff.removed:
            lines.append(f"    - {e.schedule}  {e.command}")

    return "\n".join(lines)
