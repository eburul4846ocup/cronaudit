"""Group cron entries by schedule pattern, user, or command prefix."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab


@dataclass
class EntryGroup:
    key: str
    entries: List[tuple[str, CronEntry]] = field(default_factory=list)  # (server, entry)

    @property
    def count(self) -> int:
        return len(self.entries)

    @property
    def servers(self) -> List[str]:
        return sorted({s for s, _ in self.entries})


@dataclass
class GroupingResult:
    groups: Dict[str, EntryGroup] = field(default_factory=dict)
    by: str = "schedule"

    @property
    def group_count(self) -> int:
        return len(self.groups)

    @property
    def total_entries(self) -> int:
        return sum(g.count for g in self.groups.values())


def _schedule_key(entry: CronEntry) -> str:
    if entry.special:
        return entry.special
    return entry.schedule or "unknown"


def _user_key(entry: CronEntry) -> str:
    return entry.user or "(no user)"


def _command_prefix_key(entry: CronEntry, words: int = 1) -> str:
    if not entry.command:
        return "(empty)"
    parts = entry.command.split()
    return " ".join(parts[:words])


def group_by(
    crontabs: List[ServerCrontab],
    by: str = "schedule",
    command_words: int = 1,
) -> GroupingResult:
    """Group entries from multiple servers by the given strategy.

    Args:
        crontabs: list of ServerCrontab objects.
        by: one of 'schedule', 'user', 'command'.
        command_words: number of leading command words to use as key when by='command'.

    Returns:
        GroupingResult with populated groups.
    """
    if by not in ("schedule", "user", "command"):
        raise ValueError(f"Unknown grouping strategy: {by!r}")

    result = GroupingResult(by=by)
    for sc in crontabs:
        if not sc.is_ok():
            continue
        for entry in sc.entries:
            if by == "schedule":
                key = _schedule_key(entry)
            elif by == "user":
                key = _user_key(entry)
            else:
                key = _command_prefix_key(entry, command_words)

            if key not in result.groups:
                result.groups[key] = EntryGroup(key=key)
            result.groups[key].entries.append((sc.server, entry))

    return result
