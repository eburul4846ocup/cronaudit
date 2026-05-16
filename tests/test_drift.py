"""Tests for cronaudit.drift and cronaudit.drift_runner."""
import pytest

from cronaudit.collector import ServerCrontab
from cronaudit.drift import DriftPair, DriftReport, detect_drift
from cronaudit.drift_runner import DriftRunResult, run_drift
from cronaudit.parser import CronEntry


def _entry(
    command: str,
    minute: str = "0",
    hour: str = "*",
    user: str = "root",
    special: str | None = None,
) -> CronEntry:
    return CronEntry(
        minute=minute,
        hour=hour,
        day_of_month="*",
        month="*",
        day_of_week="*",
        user=user,
        command=command,
        special=special,
        raw=f"{minute} {hour} * * * {user} {command}",
    )


def _crontab(server: str, entries) -> ServerCrontab:
    sc = ServerCrontab(server=server)
    sc.entries = list(entries)
    return sc


# --- detect_drift ---

def test_no_drift_returns_empty_report():
    old = [_entry("/usr/bin/backup", minute="0", hour="2")]
    new = [_entry("/usr/bin/backup", minute="0", hour="2")]
    report = detect_drift("srv1", old, new)
    assert report.count == 0
    assert not report


def test_changed_hour_detected():
    old = [_entry("/usr/bin/backup", minute="0", hour="2")]
    new = [_entry("/usr/bin/backup", minute="0", hour="4")]
    report = detect_drift("srv1", old, new)
    assert report.count == 1
    pair = report.pairs[0]
    assert pair.command == "/usr/bin/backup"
    assert pair.old_schedule == "0 2 * * *"
    assert pair.new_schedule == "0 4 * * *"
    assert pair.server == "srv1"


def test_new_entry_not_flagged_as_drift():
    old = []
    new = [_entry("/usr/bin/new_job", minute="5", hour="3")]
    report = detect_drift("srv1", old, new)
    assert report.count == 0


def test_removed_entry_not_flagged_as_drift():
    old = [_entry("/usr/bin/old_job", minute="5", hour="3")]
    new = []
    report = detect_drift("srv1", old, new)
    assert report.count == 0


def test_special_schedule_drift_detected():
    old = [_entry("/usr/bin/sync", special="@daily")]
    new = [_entry("/usr/bin/sync", special="@hourly")]
    report = detect_drift("srv1", old, new)
    assert report.count == 1
    assert report.pairs[0].old_schedule == "@daily"
    assert report.pairs[0].new_schedule == "@hourly"


def test_drift_pair_str():
    pair = DriftPair(
        server="web1",
        command="/bin/job",
        old_schedule="0 2 * * *",
        new_schedule="0 4 * * *",
        user="deploy",
    )
    s = str(pair)
    assert "web1" in s
    assert "/bin/job" in s
    assert "deploy" in s


# --- run_drift ---

def test_run_drift_ok_no_changes():
    old = _crontab("srv1", [_entry("/bin/a", minute="0", hour="1")])
    new = _crontab("srv1", [_entry("/bin/a", minute="0", hour="1")])
    result = run_drift([(old, new)])
    assert result.ok
    assert result.total_drifted == 0


def test_run_drift_detects_change():
    old = _crontab("srv1", [_entry("/bin/a", minute="0", hour="1")])
    new = _crontab("srv1", [_entry("/bin/a", minute="0", hour="6")])
    result = run_drift([(old, new)])
    assert result.total_drifted == 1


def test_run_drift_server_mismatch_records_error():
    old = _crontab("srv1", [])
    new = _crontab("srv2", [])
    result = run_drift([(old, new)])
    assert not result.ok
    assert len(result.errors) == 1


def test_run_drift_summary_line():
    old = _crontab("srv1", [_entry("/bin/a", hour="1")])
    new = _crontab("srv1", [_entry("/bin/a", hour="3")])
    result = run_drift([(old, new)])
    summary = result.summary_line()
    assert "1 server" in summary
    assert "1 schedule change" in summary
