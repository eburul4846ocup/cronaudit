"""Runner that applies dependency detection to a list of ServerCrontab objects."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from cronaudit.collector import ServerCrontab
from cronaudit.dependency import DependencyReport, detect_dependencies


@dataclass
class DependencyRunResult:
    report: DependencyReport
    server_count: int

    @property
    def ok(self) -> bool:
        """True when no dependency pairs were detected."""
        return not bool(self.report)

    @property
    def summary_line(self) -> str:
        pairs = self.report.count
        servers = self.server_count
        if pairs == 0:
            return f"No dependency issues found across {servers} server(s)."
        return (
            f"{pairs} potential dependency pair(s) detected across {servers} server(s)."
        )


def run_dependency_check(crontabs: List[ServerCrontab]) -> DependencyRunResult:
    """Run dependency detection and return a structured result."""
    report = detect_dependencies(crontabs)
    return DependencyRunResult(report=report, server_count=len(crontabs))
