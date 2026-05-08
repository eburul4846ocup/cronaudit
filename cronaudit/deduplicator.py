"""Detect and remove duplicate cron entries within or across servers."""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab


@dataclass
class DuplicateGroup:
    """A group of entries that are considered duplicates."""
    key: str
    entries: List[Tuple[str, CronEntry]] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.entries)

    @property
    def servers(self) -> List[str]:
        return [server for server, _ in self.entries]


@dataclass
class DeduplicationResult:
    """Result of a deduplication pass over one or more server crontabs."""
    groups: List[DuplicateGroup] = field(default_factory=list)
    total_entries: int = 0
    unique_entries: int = 0

    @property
    def duplicate_count(self) -> int:
        return sum(g.count - 1 for g in self.groups)

    @property
    def has_duplicates(self) -> bool:
        return len(self.groups) > 0


def _entry_key(entry: CronEntry, include_user: bool = True) -> str:
    """Build a normalised key for comparison."""
    schedule = entry.schedule.strip()
    command = entry.command.strip()
    user = (entry.user or "").strip() if include_user else ""
    return f"{schedule}|{user}|{command}"


def find_duplicates(
    crontabs: List[ServerCrontab],
    cross_server: bool = True,
    include_user: bool = True,
) -> DeduplicationResult:
    """Find duplicate entries across (or within) a list of ServerCrontab objects."""
    seen: Dict[str, List[Tuple[str, CronEntry]]] = {}
    total = 0

    for sc in crontabs:
        for entry in sc.entries:
            if not entry.is_valid:
                continue
            total += 1
            key = _entry_key(entry, include_user=include_user)
            scope_key = key if cross_server else f"{sc.server}::{key}"
            seen.setdefault(scope_key, []).append((sc.server, entry))

    groups = [
        DuplicateGroup(key=k, entries=v)
        for k, v in seen.items()
        if len(v) > 1
    ]

    unique = sum(1 for v in seen.values() if len(v) == 1)
    return DeduplicationResult(
        groups=groups,
        total_entries=total,
        unique_entries=unique,
    )


def format_duplicates(result: DeduplicationResult) -> str:
    """Return a human-readable summary of duplicate groups."""
    if not result.has_duplicates:
        return "No duplicate cron entries found."
    lines = [
        f"Found {len(result.groups)} duplicate group(s) "
        f"({result.duplicate_count} redundant entries):",
    ]
    for i, group in enumerate(result.groups, 1):
        lines.append(f"\n  [{i}] {group.key}")
        for server, entry in group.entries:
            lines.append(f"      {server}: {entry.schedule} {entry.command}")
    return "\n".join(lines)
