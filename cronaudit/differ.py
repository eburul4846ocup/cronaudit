"""Diff crontab entries between two server snapshots."""

from dataclasses import dataclass, field
from typing import List, Tuple
from cronaudit.collector import ServerCrontab
from cronaudit.parser import CronEntry


@dataclass
class DiffResult:
    server: str
    added: List[CronEntry] = field(default_factory=list)
    removed: List[CronEntry] = field(default_factory=list)
    unchanged: List[CronEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed)


def _entry_key(entry: CronEntry) -> Tuple[str, str, str]:
    """Return a hashable key representing a cron entry."""
    return (entry.schedule, entry.user or "", entry.command)


def diff_crontabs(before: ServerCrontab, after: ServerCrontab) -> DiffResult:
    """Compare two ServerCrontab snapshots and return a DiffResult.

    Args:
        before: The earlier snapshot.
        after:  The later snapshot.

    Returns:
        DiffResult describing added, removed, and unchanged entries.
    """
    server = after.server or before.server or "unknown"
    result = DiffResult(server=server)

    before_map = {_entry_key(e): e for e in before.entries}
    after_map = {_entry_key(e): e for e in after.entries}

    for key, entry in after_map.items():
        if key in before_map:
            result.unchanged.append(entry)
        else:
            result.added.append(entry)

    for key, entry in before_map.items():
        if key not in after_map:
            result.removed.append(entry)

    return result


def format_diff(diff: DiffResult) -> str:
    """Render a DiffResult as a human-readable string."""
    lines: List[str] = [f"=== Diff for {diff.server} ==="]

    if not diff.has_changes:
        lines.append("  No changes detected.")
        return "\n".join(lines)

    for entry in diff.added:
        lines.append(f"  + {entry.schedule}  {entry.command}")

    for entry in diff.removed:
        lines.append(f"  - {entry.schedule}  {entry.command}")

    lines.append(
        f"  Summary: {len(diff.added)} added, "
        f"{len(diff.removed)} removed, "
        f"{len(diff.unchanged)} unchanged."
    )
    return "\n".join(lines)
