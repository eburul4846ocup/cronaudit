"""Tests for cronaudit.baseline."""
import pytest

from cronaudit.baseline import (
    BaselineDiff,
    BaselineReport,
    compare_to_baseline,
    format_baseline_report,
)
from cronaudit.multi import AuditResult
from cronaudit.parser import CronEntry


def _entry(schedule: str, command: str, user: str = "root") -> CronEntry:
    return CronEntry(schedule=schedule, command=command, user=user, raw=f"{schedule} {command}")


def _result(server: str, entries: list) -> AuditResult:
    return AuditResult(server=server, entries=entries, error=None)


# --- BaselineDiff ---

def test_baseline_diff_has_changes_when_added():
    diff = BaselineDiff(server="srv1", added=[_entry("* * * * *", "cmd")], removed=[])
    assert diff.has_changes is True


def test_baseline_diff_has_changes_when_removed():
    diff = BaselineDiff(server="srv1", added=[], removed=[_entry("* * * * *", "cmd")])
    assert diff.has_changes is True


def test_baseline_diff_no_changes():
    diff = BaselineDiff(server="srv1", added=[], removed=[])
    assert diff.has_changes is False


# --- BaselineReport ---

def test_baseline_report_clean_when_no_diffs():
    report = BaselineReport(diffs=[], servers_checked=2)
    assert report.clean is True
    assert report.changed_servers == 0


def test_baseline_report_not_clean_when_diff():
    diff = BaselineDiff(server="srv1", added=[_entry("@daily", "/bin/x")], removed=[])
    report = BaselineReport(diffs=[diff], servers_checked=1)
    assert report.clean is False
    assert report.changed_servers == 1
    assert report.total_added == 1
    assert report.total_removed == 0


# --- compare_to_baseline ---

def test_no_changes_returns_clean_report():
    entry = _entry("0 * * * *", "/usr/bin/backup")
    current = [_result("host1", [entry])]
    baseline = [_result("host1", [entry])]
    report = compare_to_baseline(current, baseline, label="v1")
    assert report.clean is True
    assert report.servers_checked == 1
    assert report.baseline_label == "v1"


def test_added_entry_detected():
    old_entry = _entry("0 * * * *", "/usr/bin/backup")
    new_entry = _entry("@daily", "/usr/bin/cleanup")
    current = [_result("host1", [old_entry, new_entry])]
    baseline = [_result("host1", [old_entry])]
    report = compare_to_baseline(current, baseline)
    assert report.total_added == 1
    assert report.total_removed == 0
    assert report.changed_servers == 1


def test_removed_entry_detected():
    old_entry = _entry("0 * * * *", "/usr/bin/backup")
    current = [_result("host1", [])]
    baseline = [_result("host1", [old_entry])]
    report = compare_to_baseline(current, baseline)
    assert report.total_removed == 1
    assert report.total_added == 0


def test_new_server_in_current_shows_all_added():
    entry = _entry("* * * * *", "cmd")
    current = [_result("new-host", [entry])]
    baseline = []
    report = compare_to_baseline(current, baseline)
    assert report.total_added == 1
    assert report.servers_checked == 1


def test_server_missing_from_current_shows_all_removed():
    entry = _entry("* * * * *", "cmd")
    current = []
    baseline = [_result("old-host", [entry])]
    report = compare_to_baseline(current, baseline)
    assert report.total_removed == 1


# --- format_baseline_report ---

def test_format_report_contains_header():
    report = BaselineReport(diffs=[], servers_checked=3, baseline_label="snap-1")
    text = format_baseline_report(report)
    assert "Baseline Comparison" in text
    assert "snap-1" in text
    assert "3" in text


def test_format_report_shows_added_and_removed():
    added = _entry("@daily", "/bin/new")
    removed = _entry("0 5 * * *", "/bin/old")
    diff = BaselineDiff(server="srv", added=[added], removed=[removed])
    report = BaselineReport(diffs=[diff], servers_checked=1)
    text = format_baseline_report(report)
    assert "+ @daily" in text
    assert "- 0 5 * * *" in text
    assert "srv" in text
