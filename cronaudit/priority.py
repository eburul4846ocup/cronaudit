"""Assigns execution priority tiers to cron entries based on schedule frequency and command patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab

# Priority tiers (lower number = higher priority / more critical)
CRITICAL = 1
HIGH = 2
MEDIUM = 3
LOW = 4

_CRITICAL_PATTERNS = ("backup", "dump", "restore", "db", "database", "mysql", "pg_dump")
_HIGH_PATTERNS = ("deploy", "sync", "rsync", "import", "export", "migrate")
_LOW_PATTERNS = ("log", "clean", "tmp", "cache", "rotate", "prune")


@dataclass
class PrioritizedEntry:
    entry: CronEntry
    server: str
    priority: int
    reason: str

    @property
    def tier_name(self) -> str:
        return {CRITICAL: "critical", HIGH: "high", MEDIUM: "medium", LOW: "low"}.get(
            self.priority, "unknown"
        )


@dataclass
class PriorityReport:
    server: str
    entries: List[PrioritizedEntry] = field(default_factory=list)

    @property
    def critical(self) -> List[PrioritizedEntry]:
        return [e for e in self.entries if e.priority == CRITICAL]

    @property
    def high(self) -> List[PrioritizedEntry]:
        return [e for e in self.entries if e.priority == HIGH]

    @property
    def count(self) -> int:
        return len(self.entries)


def _assign_priority(entry: CronEntry) -> tuple[int, str]:
    """Return (priority, reason) for a single entry."""
    cmd_lower = entry.command.lower()

    for pat in _CRITICAL_PATTERNS:
        if pat in cmd_lower:
            return CRITICAL, f"command contains '{pat}'"

    for pat in _HIGH_PATTERNS:
        if pat in cmd_lower:
            return HIGH, f"command contains '{pat}'"

    # Frequent schedules elevate priority
    if entry.special in ("@reboot",):
        return HIGH, "runs at reboot"

    if entry.special in ("@hourly", "@daily", "@midnight"):
        return MEDIUM, f"special schedule {entry.special}"

    if not entry.special and entry.minute not in (None, "*") and entry.hour not in (None, "*"):
        return MEDIUM, "runs at specific time"

    for pat in _LOW_PATTERNS:
        if pat in cmd_lower:
            return LOW, f"command contains '{pat}'"

    return LOW, "default"


def prioritize_crontab(crontab: ServerCrontab) -> PriorityReport:
    """Assign priorities to all valid entries in a ServerCrontab."""
    report = PriorityReport(server=crontab.server)
    for entry in crontab.entries:
        if not entry.valid:
            continue
        priority, reason = _assign_priority(entry)
        report.entries.append(
            PrioritizedEntry(entry=entry, server=crontab.server, priority=priority, reason=reason)
        )
    return report
