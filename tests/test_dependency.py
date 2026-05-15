"""Tests for cronaudit.dependency and cronaudit.dependency_runner."""
import pytest

from cronaudit.collector import ServerCrontab
from cronaudit.dependency import (
    DependencyPair,
    DependencyReport,
    detect_dependencies,
    _same_schedule,
    _sequential_minutes,
)
from cronaudit.dependency_runner import run_dependency_check
from cronaudit.parser import CronEntry


def _entry(schedule: str, command: str, user: str = "root") -> CronEntry:
    return CronEntry(schedule=schedule, command=command, user=user, raw=f"{schedule} {user} {command}")


def _crontab(server: str, entries) -> ServerCrontab:
    ct = ServerCrontab(server=server)
    ct.entries = list(entries)
    return ct


# --- _same_schedule ---

def test_same_schedule_true():
    a = _entry("0 2 * * *", "backup.sh")
    b = _entry("0 2 * * *", "cleanup.sh")
    assert _same_schedule(a, b) is True


def test_same_schedule_false():
    a = _entry("0 2 * * *", "backup.sh")
    b = _entry("0 3 * * *", "cleanup.sh")
    assert _same_schedule(a, b) is False


# --- _sequential_minutes ---

def test_sequential_minutes_detects_consecutive():
    a = _entry("0 2 * * *", "step1.sh")
    b = _entry("1 2 * * *", "step2.sh")
    reason = _sequential_minutes(a, b)
    assert reason is not None
    assert "consecutive" in reason


def test_sequential_minutes_ignores_same_minute():
    a = _entry("5 2 * * *", "a.sh")
    b = _entry("5 2 * * *", "b.sh")
    assert _sequential_minutes(a, b) is None


def test_sequential_minutes_ignores_special():
    a = _entry("@daily", "a.sh")
    b = _entry("@daily", "b.sh")
    assert _sequential_minutes(a, b) is None


# --- detect_dependencies ---

def test_detect_identical_schedule_flags_pair():
    ct = _crontab("srv1", [
        _entry("0 2 * * *", "job_a.sh"),
        _entry("0 2 * * *", "job_b.sh"),
    ])
    report = detect_dependencies([ct])
    assert report.count == 1
    assert "undefined" in report.pairs[0].reason


def test_detect_consecutive_minutes_flags_pair():
    ct = _crontab("srv1", [
        _entry("10 4 * * *", "first.sh"),
        _entry("11 4 * * *", "second.sh"),
    ])
    report = detect_dependencies([ct])
    assert report.count == 1
    assert "consecutive" in report.pairs[0].reason


def test_detect_no_issues_returns_empty():
    ct = _crontab("srv1", [
        _entry("0 1 * * *", "morning.sh"),
        _entry("0 13 * * *", "afternoon.sh"),
    ])
    report = detect_dependencies([ct])
    assert report.count == 0
    assert not bool(report)


def test_detect_reboot_not_flagged_as_identical():
    ct = _crontab("srv1", [
        _entry("@reboot", "init_a.sh"),
        _entry("@reboot", "init_b.sh"),
    ])
    report = detect_dependencies([ct])
    # @reboot entries are excluded from identical-schedule check
    assert report.count == 0


def test_detect_across_multiple_servers():
    ct1 = _crontab("web1", [_entry("5 3 * * *", "x.sh"), _entry("5 3 * * *", "y.sh")])
    ct2 = _crontab("web2", [_entry("0 6 * * *", "z.sh")])
    report = detect_dependencies([ct1, ct2])
    assert report.count == 1
    assert report.pairs[0].server == "web1"


# --- DependencyReport helpers ---

def test_report_str_representation():
    a = _entry("0 2 * * *", "a.sh")
    b = _entry("0 2 * * *", "b.sh")
    pair = DependencyPair(server="s", first=a, second=b, reason="test reason")
    assert "a.sh" in str(pair)
    assert "b.sh" in str(pair)
    assert "test reason" in str(pair)


# --- run_dependency_check ---

def test_runner_ok_when_no_issues():
    ct = _crontab("clean", [_entry("0 1 * * *", "a.sh")])
    result = run_dependency_check([ct])
    assert result.ok is True
    assert "No dependency" in result.summary_line


def test_runner_not_ok_when_issues():
    ct = _crontab("srv", [
        _entry("0 2 * * *", "x.sh"),
        _entry("0 2 * * *", "y.sh"),
    ])
    result = run_dependency_check([ct])
    assert result.ok is False
    assert "1" in result.summary_line


def test_runner_server_count():
    crontabs = [_crontab(f"s{i}", []) for i in range(3)]
    result = run_dependency_check(crontabs)
    assert result.server_count == 3
