"""High-level helper: load config, run audit results through alert rules."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from cronaudit.alert_config import load_alert_rules
from cronaudit.alerting import AlertReport, evaluate_rules, format_alert_report
from cronaudit.multi import AuditResult


@dataclass
class AlertRunResult:
    """Combined outcome of loading rules + evaluating them."""
    report: AlertReport
    config_errors: List[str]
    text: str

    @property
    def ok(self) -> bool:
        """True when no config errors and no alerts triggered."""
        return not self.config_errors and not self.report


def run_alerts(
    results: List[AuditResult],
    config: Dict[str, Any],
) -> AlertRunResult:
    """Load alert rules from *config*, evaluate against *results*.

    Always returns an AlertRunResult even if the config is invalid so
    callers can surface errors without raising.
    """
    rules, config_errors = load_alert_rules(config)
    report = evaluate_rules(results, rules)
    text_lines: List[str] = []

    if config_errors:
        text_lines.append("Configuration errors:")
        for err in config_errors:
            text_lines.append(f"  - {err}")
        text_lines.append("")

    text_lines.append(format_alert_report(report))

    return AlertRunResult(
        report=report,
        config_errors=config_errors,
        text="\n".join(text_lines),
    )
