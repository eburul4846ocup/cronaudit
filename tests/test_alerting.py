"""Tests for cronaudit.alerting."""
from __future__ import annotations

from cronaudit.alerting import (
    AlertRule,
    AlertReport,
    evaluate_rules,
    format_alert_report,
)
from cronaudit.multi import AuditResult
from cronaudit.parser import CronEntry


def _ok_result(server: str = "host1", entries: int = 3) -> AuditResult:
    fake_entries = [
        CronEntry(
            raw=f"0 * * * * /cmd{i}",
            schedule="0 * * * *",
            command=f"/cmd{i}",
        )
        for i in range(entries)
    ]
    return AuditResult(server=server, entries=fake_entries, error=None)


def _fail_result(server: str = "down1") -> AuditResult:
    return AuditResult(server=server, entries=[], error="Connection refused")


# ---------------------------------------------------------------------------
# evaluate_rules
# ---------------------------------------------------------------------------

def test_no_rules_returns_empty_report():
    report = evaluate_rules([_ok_result()], [])
    assert report.triggered == 0
    assert report.rules_checked == 0


def test_failure_rate_triggered():
    results = [_ok_result(), _fail_result(), _fail_result()]
    rules = [AlertRule(name="high_fail", condition="failure_rate", threshold=0.5)]
    report = evaluate_rules(results, rules)
    assert report.triggered == 1
    assert report.events[0].rule_name == "high_fail"


def test_failure_rate_not_triggered():
    results = [_ok_result(), _ok_result(), _fail_result()]
    rules = [AlertRule(name="r", condition="failure_rate", threshold=0.9)]
    report = evaluate_rules(results, rules)
    assert report.triggered == 0


def test_min_entries_triggered():
    results = [_ok_result(entries=1)]
    rules = [AlertRule(name="too_few", condition="min_entries", threshold=5)]
    report = evaluate_rules(results, rules)
    assert report.triggered == 1
    assert "minimum" in report.events[0].message


def test_max_entries_triggered():
    results = [_ok_result(entries=10)]
    rules = [AlertRule(name="too_many", condition="max_entries", threshold=5)]
    report = evaluate_rules(results, rules)
    assert report.triggered == 1


def test_server_down_triggered():
    results = [_ok_result(), _fail_result(), _fail_result()]
    rules = [AlertRule(name="down", condition="server_down", threshold=2)]
    report = evaluate_rules(results, rules)
    assert report.triggered == 1


def test_disabled_rule_skipped():
    results = [_fail_result(), _fail_result()]
    rules = [
        AlertRule(name="r", condition="failure_rate", threshold=0.1, enabled=False)
    ]
    report = evaluate_rules(results, rules)
    assert report.triggered == 0


def test_empty_results_returns_empty_report():
    rules = [AlertRule(name="r", condition="failure_rate", threshold=0.1)]
    report = evaluate_rules([], rules)
    assert report.triggered == 0


def test_alert_report_bool_true():
    results = [_fail_result()]
    rules = [AlertRule(name="r", condition="failure_rate", threshold=0.5)]
    report = evaluate_rules(results, rules)
    assert bool(report) is True


def test_alert_report_bool_false():
    report = AlertReport(events=[], rules_checked=2)
    assert bool(report) is False


# ---------------------------------------------------------------------------
# format_alert_report
# ---------------------------------------------------------------------------

def test_format_no_alerts():
    report = AlertReport(events=[], rules_checked=3)
    text = format_alert_report(report)
    assert "No alerts triggered" in text
    assert "3 rule(s)" in text


def test_format_with_alerts():
    results = [_fail_result(), _fail_result()]
    rules = [AlertRule(name="critical", condition="failure_rate", threshold=0.5)]
    report = evaluate_rules(results, rules)
    text = format_alert_report(report)
    assert "critical" in text
    assert "triggered" in text
