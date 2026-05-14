"""Anomaly detection for cron entries based on heuristic rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from cronaudit.collector import ServerCrontab
from cronaudit.parser import CronEntry

# Schedules that run very frequently and may warrant attention
_HIGH_FREQUENCY_SPECIALS = {"@minutely", "@secondly"}
_SUSPICIOUS_COMMANDS = ["curl", "wget", "bash -c", "sh -c", "python -c", "eval", "base64"]


@dataclass
class AnomalyFlag:
    server: str
    entry: CronEntry
    reason: str

    def __str__(self) -> str:
        cmd = (self.entry.command or "")[:60]
        return f"[{self.server}] {self.reason} — {cmd}"


@dataclass
class AnomalyReport:
    flags: List[AnomalyFlag] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.flags)

    def __bool__(self) -> bool:
        return self.count > 0

    def by_server(self, server: str) -> List[AnomalyFlag]:
        return [f for f in self.flags if f.server == server]


def _is_high_frequency(entry: CronEntry) -> bool:
    """Return True if the schedule fires every minute or more often."""
    if entry.special and entry.special in _HIGH_FREQUENCY_SPECIALS:
        return True
    if entry.special:
        return False
    # standard five-field: minute == "*" and no step means every minute
    fields = (entry.minute, entry.hour, entry.day_of_month, entry.month, entry.day_of_week)
    if all(f is not None for f in fields):
        return entry.minute == "*" and entry.hour == "*"
    return False


def _has_suspicious_command(entry: CronEntry) -> str | None:
    """Return the matched suspicious token or None."""
    cmd = entry.command or ""
    for token in _SUSPICIOUS_COMMANDS:
        if token in cmd:
            return token
    return None


def _runs_as_root(entry: CronEntry) -> bool:
    return (entry.user or "").strip() == "root"


def detect_anomalies(crontabs: Sequence[ServerCrontab]) -> AnomalyReport:
    """Scan *crontabs* and return an AnomalyReport with flagged entries."""
    report = AnomalyReport()
    for ct in crontabs:
        if not ct.is_ok():
            continue
        for entry in ct.entries:
            if _is_high_frequency(entry):
                report.flags.append(
                    AnomalyFlag(ct.server, entry, "High-frequency schedule (every minute or more)")
                )
            token = _has_suspicious_command(entry)
            if token:
                report.flags.append(
                    AnomalyFlag(ct.server, entry, f"Suspicious command token: '{token}'")
                )
            if _runs_as_root(entry) and _has_suspicious_command(entry):
                report.flags.append(
                    AnomalyFlag(ct.server, entry, "Suspicious command running as root")
                )
    return report
