"""Cron expression complexity scoring — rates how hard a schedule is to understand."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab


@dataclass
class ComplexityResult:
    entry: CronEntry
    server: str
    score: int
    reasons: List[str] = field(default_factory=list)

    @property
    def level(self) -> str:
        if self.score <= 2:
            return "simple"
        if self.score <= 5:
            return "moderate"
        return "complex"


@dataclass
class ComplexityReport:
    results: List[ComplexityResult] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.results)

    @property
    def complex_count(self) -> int:
        return sum(1 for r in self.results if r.level == "complex")

    @property
    def average_score(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.score for r in self.results) / len(self.results)

    def __bool__(self) -> bool:
        return self.complex_count > 0


def _score_field(value: str, range_max: int) -> tuple[int, List[str]]:
    """Return (score_delta, reasons) for a single cron field."""
    score = 0
    reasons: List[str] = []
    if value == "*":
        return 0, []
    if "," in value:
        score += 1
        reasons.append(f"list value '{value}'")
    if "/" in value:
        score += 1
        reasons.append(f"step value '{value}'")
    if "-" in value:
        score += 1
        reasons.append(f"range value '{value}'")
    return score, reasons


def score_entry(entry: CronEntry, server: str = "") -> ComplexityResult:
    """Compute a complexity score for a single CronEntry."""
    if entry.special:
        return ComplexityResult(entry=entry, server=server, score=0, reasons=[])

    parts = entry.schedule.split()
    if len(parts) != 5:
        return ComplexityResult(entry=entry, server=server, score=0, reasons=[])

    ranges = [59, 23, 31, 12, 7]
    total_score = 0
    all_reasons: List[str] = []
    for value, max_val in zip(parts, ranges):
        delta, reasons = _score_field(value, max_val)
        total_score += delta
        all_reasons.extend(reasons)

    if len(parts[4].split(",")) > 2 or len(parts[2].split(",")) > 2:
        total_score += 1
        all_reasons.append("multiple day constraints")

    return ComplexityResult(
        entry=entry, server=server, score=total_score, reasons=all_reasons
    )


def analyse_complexity(crontabs: List[ServerCrontab]) -> ComplexityReport:
    """Score all entries across multiple ServerCrontab objects."""
    results: List[ComplexityResult] = []
    for crontab in crontabs:
        for entry in crontab.entries:
            results.append(score_entry(entry, server=crontab.server))
    return ComplexityReport(results=results)
