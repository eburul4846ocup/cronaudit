"""Tests for cronaudit.lineage and cronaudit.lineage_runner."""
import pytest

from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab
from cronaudit.lineage import detect_lineage, LineagePair
from cronaudit.lineage_runner import run_lineage


def _entry(command: str, schedule: str = "0 2 * * *", user: str = "root") -> CronEntry:
    return CronEntry(schedule=schedule, command=command, user=user, raw=f"{schedule} {user} {command}")


def _crontab(server: str, entries) -> ServerCrontab:
    sc = ServerCrontab(server=server)
    sc.entries = list(entries)
    return sc


# --- detect_lineage ---

def test_no_changes_returns_empty_report():
    e = _entry("/usr/bin/backup.sh")
    old = _crontab("srv1", [e])
    new = _crontab("srv1", [e])
    report = detect_lineage(old, new)
    assert report.count == 0
    assert not report


def test_renamed_command_detected():
    old = _crontab("srv1", [_entry("/usr/bin/backup.sh")])
    new = _crontab("srv1", [_entry("/usr/bin/backup_new.sh")])
    report = detect_lineage(old, new)
    assert report.count == 1
    pair = report.pairs[0]
    assert pair.old_command == "/usr/bin/backup.sh"
    assert pair.new_command == "/usr/bin/backup_new.sh"
    assert pair.similarity > 0.7


def test_schedule_changed_flag_set():
    old = _crontab("srv1", [_entry("/opt/run.sh", schedule="0 2 * * *")])
    new = _crontab("srv1", [_entry("/opt/run_v2.sh", schedule="0 3 * * *")])
    report = detect_lineage(old, new)
    assert report.count == 1
    assert report.pairs[0].schedule_changed is True


def test_schedule_unchanged_flag_not_set():
    old = _crontab("srv1", [_entry("/opt/run.sh", schedule="0 2 * * *")])
    new = _crontab("srv1", [_entry("/opt/run_v2.sh", schedule="0 2 * * *")])
    report = detect_lineage(old, new)
    assert report.count == 1
    assert report.pairs[0].schedule_changed is False


def test_unrelated_command_not_matched():
    old = _crontab("srv1", [_entry("/usr/bin/backup.sh")])
    new = _crontab("srv1", [_entry("/usr/bin/zzzzzz_completely_different")])
    report = detect_lineage(old, new, threshold=0.9)
    assert report.count == 0


def test_lineage_pair_str_contains_arrow():
    pair = LineagePair(
        server="srv1",
        old_command="/opt/a.sh",
        new_command="/opt/b.sh",
        similarity=0.85,
        schedule_changed=False,
    )
    s = str(pair)
    assert "->" in s
    assert "85%" in s


def test_lineage_pair_str_schedule_changed_uses_tilde_arrow():
    pair = LineagePair(
        server="srv1",
        old_command="/opt/a.sh",
        new_command="/opt/b.sh",
        similarity=0.85,
        schedule_changed=True,
    )
    assert "~>" in str(pair)


# --- run_lineage ---

def test_run_lineage_server_mismatch_adds_error():
    old = _crontab("srv1", [])
    new = _crontab("srv2", [])
    result = run_lineage([(old, new)])
    assert not result.ok
    assert len(result.errors) == 1


def test_run_lineage_summary_line():
    old = _crontab("srv1", [_entry("/usr/bin/backup.sh")])
    new = _crontab("srv1", [_entry("/usr/bin/backup_v2.sh")])
    result = run_lineage([(old, new)])
    line = result.summary_line()
    assert "1 server" in line


def test_run_lineage_total_renames():
    old = _crontab("srv1", [_entry("/usr/bin/backup.sh")])
    new = _crontab("srv1", [_entry("/usr/bin/backup_v2.sh")])
    result = run_lineage([(old, new)])
    assert result.total_renames == 1
