"""High-level runner that integrates anomaly detection into the audit pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from cronaudit.collector import ServerCrontab
from cronaudit.anomaly import AnomalyReport, detect_anomalies


@dataclass
class AnomalyRunResult:
    report: AnomalyReport
    servers_scanned: int
    errors: List[str]

    @property
    def ok(self) -> bool:
        """True when no anomalies were detected."""
        return not self.report

    @property
    def summary_line(self) -> str:
        if self.ok:
            return (
                f"No anomalies detected across {self.servers_scanned} server(s)."
            )
        return (
            f"{self.report.count} anomaly flag(s) found across "
            f"{self.servers_scanned} server(s)."
        )


def run_anomaly_detection(
    crontabs: Sequence[ServerCrontab],
) -> AnomalyRunResult:
    """Run anomaly detection over *crontabs* and return a structured result."""
    errors: List[str] = []
    valid: List[ServerCrontab] = []

    for ct in crontabs:
        if ct.is_ok():
            valid.append(ct)
        else:
            errors.append(f"{ct.server}: {ct.error}")

    report = detect_anomalies(valid)
    return AnomalyRunResult(
        report=report,
        servers_scanned=len(crontabs),
        errors=errors,
    )
