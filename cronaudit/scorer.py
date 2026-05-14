"""Entry risk scoring — assigns a numeric risk score to cron entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronaudit.parser import CronEntry

# Commands that raise the risk level
_HIGH_RISK_PATTERNS = [
    "rm ", "dd ", "mkfs", "chmod 777", "wget ", "curl ",
    "bash -c", "sh -c", "eval ", "> /dev/",
]

_MEDIUM_RISK_PATTERNS = [
    "sudo ", "su ", "python", "ruby", "perl", "node",
    "mysql", "psql", "mongodump",
]


@dataclass
class ScoredEntry:
    entry: CronEntry
    score: int
    reasons: List[str] = field(default_factory=list)

    @property
    def risk_level(self) -> str:
        if self.score >= 70:
            return "high"
        if self.score >= 40:
            return "medium"
        return "low"


def score_entry(entry: CronEntry) -> ScoredEntry:
    """Return a ScoredEntry with a 0-100 risk score."""
    score = 0
    reasons: List[str] = []

    if not entry.valid:
        score += 30
        reasons.append("invalid cron expression")

    cmd = (entry.command or "").lower()

    for pat in _HIGH_RISK_PATTERNS:
        if pat in cmd:
            score += 25
            reasons.append(f"high-risk pattern: '{pat.strip()}'")
            break

    for pat in _MEDIUM_RISK_PATTERNS:
        if pat in cmd:
            score += 15
            reasons.append(f"medium-risk pattern: '{pat.strip()}'")
            break

    if entry.schedule == "@reboot":
        score += 20
        reasons.append("runs at reboot")

    if entry.user and entry.user == "root":
        score += 10
        reasons.append("runs as root")

    return ScoredEntry(entry=entry, score=min(score, 100), reasons=reasons)


def score_entries(entries: List[CronEntry]) -> List[ScoredEntry]:
    """Score a list of entries, sorted highest risk first."""
    scored = [score_entry(e) for e in entries]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored
