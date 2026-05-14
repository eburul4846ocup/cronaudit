"""Runner that scores entries from AuditResult objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from cronaudit.multi import AuditResult
from cronaudit.scorer import ScoredEntry, score_entries


@dataclass
class ScoreRunResult:
    server_scores: Dict[str, List[ScoredEntry]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def high_risk_count(self) -> int:
        return sum(
            1
            for scores in self.server_scores.values()
            for s in scores
            if s.risk_level == "high"
        )

    @property
    def total_scored(self) -> int:
        return sum(len(v) for v in self.server_scores.values())

    def summary_line(self) -> str:
        return (
            f"{self.total_scored} entries scored across "
            f"{len(self.server_scores)} server(s); "
            f"{self.high_risk_count} high-risk"
        )


def run_scoring(results: List[AuditResult]) -> ScoreRunResult:
    """Score all entries from a list of AuditResult objects."""
    run = ScoreRunResult()
    for result in results:
        if not result.ok:
            run.errors.append(
                f"{result.server}: {result.error}"
            )
            continue
        scored = score_entries(result.entries)
        run.server_scores[result.server] = scored
    return run
