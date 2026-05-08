"""Alert rule evaluation for cron audit results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronaudit.multi import AuditResult


@dataclass
class AlertRule:
    """A single alert rule with a name, condition type, and threshold."""
    name: str
    condition: str          # 'failure_rate', 'min_entries', 'max_entries', 'server_down'
    threshold: float = 0.0
    enabled: bool = True


@dataclass
class AlertEvent:
    """Fired when an AlertRule is triggered."""
    rule_name: str
    condition: str
    actual: float
    threshold: float
    message: str

    def __bool__(self) -> bool:  # noqa: D105
        return True


@dataclass
class AlertReport:
    """Collection of alert events produced by evaluate_rules."""
    events: List[AlertEvent] = field(default_factory=list)
    rules_checked: int = 0

    @property
    def triggered(self) -> int:
        return len(self.events)

    def __bool__(self) -> bool:  # noqa: D105
        return self.triggered > 0


def evaluate_rules(
    results: List[AuditResult],
    rules: List[AlertRule],
) -> AlertReport:
    """Evaluate *rules* against *results* and return an AlertReport."""
    report = AlertReport(rules_checked=len(rules))
    total = len(results)
    if total == 0:
        return report

    failures = sum(1 for r in results if r.error)
    failure_rate = failures / total
    total_entries = sum(len(r.entries) for r in results)

    for rule in rules:
        if not rule.enabled:
            continue
        event: Optional[AlertEvent] = None

        if rule.condition == "failure_rate":
            if failure_rate >= rule.threshold:
                event = AlertEvent(
                    rule_name=rule.name,
                    condition=rule.condition,
                    actual=failure_rate,
                    threshold=rule.threshold,
                    message=(
                        f"Failure rate {failure_rate:.0%} "
                        f">= threshold {rule.threshold:.0%}"
                    ),
                )
        elif rule.condition == "min_entries":
            if total_entries < rule.threshold:
                event = AlertEvent(
                    rule_name=rule.name,
                    condition=rule.condition,
                    actual=float(total_entries),
                    threshold=rule.threshold,
                    message=(
                        f"Total entries {total_entries} "
                        f"< minimum {int(rule.threshold)}"
                    ),
                )
        elif rule.condition == "max_entries":
            if total_entries > rule.threshold:
                event = AlertEvent(
                    rule_name=rule.name,
                    condition=rule.condition,
                    actual=float(total_entries),
                    threshold=rule.threshold,
                    message=(
                        f"Total entries {total_entries} "
                        f"> maximum {int(rule.threshold)}"
                    ),
                )
        elif rule.condition == "server_down":
            if failures >= rule.threshold:
                event = AlertEvent(
                    rule_name=rule.name,
                    condition=rule.condition,
                    actual=float(failures),
                    threshold=rule.threshold,
                    message=(
                        f"{failures} server(s) unreachable, "
                        f"threshold {int(rule.threshold)}"
                    ),
                )

        if event:
            report.events.append(event)

    return report


def format_alert_report(report: AlertReport) -> str:
    """Return a human-readable string for *report*."""
    lines: List[str] = [
        f"Alert Report — {report.rules_checked} rule(s) checked, "
        f"{report.triggered} triggered",
        "-" * 50,
    ]
    if not report.events:
        lines.append("No alerts triggered.")
    else:
        for ev in report.events:
            lines.append(f"[{ev.rule_name}] {ev.message}")
    return "\n".join(lines)
