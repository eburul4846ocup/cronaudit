"""Track command lineage — detect renamed or moved commands across snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import List, Optional

from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab

_SIMILARITY_THRESHOLD = 0.72


@dataclass
class LineagePair:
    server: str
    old_command: str
    new_command: str
    similarity: float
    schedule_changed: bool

    def __str__(self) -> str:
        arrow = "~>" if self.schedule_changed else "->"
        return (
            f"[{self.server}] {self.old_command!r} {arrow} {self.new_command!r} "
            f"(similarity={self.similarity:.0%})"
        )


@dataclass
class LineageReport:
    pairs: List[LineagePair] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.pairs)

    def __bool__(self) -> bool:
        return bool(self.pairs)


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _entry_key(entry: CronEntry) -> str:
    return entry.schedule


def detect_lineage(
    old: ServerCrontab,
    new: ServerCrontab,
    threshold: float = _SIMILARITY_THRESHOLD,
) -> LineageReport:
    """Compare two snapshots of the same server and find likely renamed commands."""
    old_commands = {e.command for e in old.entries}
    new_commands = {e.command for e in new.entries}

    removed = old_commands - new_commands
    added = new_commands - old_commands

    old_map = {e.command: e for e in old.entries if e.command in removed}
    new_map = {e.command: e for e in new.entries if e.command in added}

    pairs: List[LineagePair] = []
    matched_new: set = set()

    for old_cmd, old_entry in old_map.items():
        best_score = 0.0
        best_new: Optional[CronEntry] = None
        for new_cmd, new_entry in new_map.items():
            if new_cmd in matched_new:
                continue
            score = _similarity(old_cmd, new_cmd)
            if score > best_score:
                best_score = score
                best_new = new_entry
        if best_new is not None and best_score >= threshold:
            matched_new.add(best_new.command)
            pairs.append(
                LineagePair(
                    server=old.server,
                    old_command=old_cmd,
                    new_command=best_new.command,
                    similarity=best_score,
                    schedule_changed=(old_entry.schedule != best_new.schedule),
                )
            )

    return LineageReport(pairs=pairs)
