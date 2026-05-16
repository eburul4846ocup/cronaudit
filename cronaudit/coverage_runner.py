"""High-level runner that wires coverage analysis into the pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from cronaudit.collector import ServerCrontab
from cronaudit.coverage import CoverageReport, build_coverage
from cronaudit.coverage_formatter import coverage_to_json, coverage_to_text


@dataclass
class CoverageRunResult:
    report: CoverageReport
    text: str
    json_str: str

    @property
    def ok(self) -> bool:
        """True when there are no coverage gaps."""
        return bool(self.report)

    @property
    def summary_line(self) -> str:
        pct = self.report.coverage_pct
        gaps = len(self.report.gaps)
        status = "OK" if self.ok else f"{gaps} gap(s)"
        return f"Coverage: {pct}% [{status}]"


def run_coverage(crontabs: Sequence[ServerCrontab]) -> CoverageRunResult:
    """Run coverage analysis and return a fully formatted result."""
    report = build_coverage(crontabs)
    return CoverageRunResult(
        report=report,
        text=coverage_to_text(report),
        json_str=coverage_to_json(report),
    )
