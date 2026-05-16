"""Tests for cronaudit.priority module."""

import pytest

from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab
from cronaudit.priority import (
    CRITICAL,
    HIGH,
    MEDIUM,
    LOW,
    PrioritizedEntry,
    PriorityReport,
    prioritize_crontab,
    _assign_priority,
)


def _entry(command: str, special: str = "", minute: str = "0", hour: str = "*") -> CronEntry:
    return CronEntry(
        raw=f"0 * * * * {command}",
        minute=minute,
        hour=hour,
        day_of_month="*",
        month="*",
        day_of_week="*",
        command=command,
        special=special,
        valid=True,
    )


def _crontab(server: str, entries: list) -> ServerCrontab:
    return ServerCrontab(server=server, entries=entries)


# --- _assign_priority ---

def test_critical_for_backup_command():
    e = _entry("/usr/local/bin/backup.sh")
    priority, reason = _assign_priority(e)
    assert priority == CRITICAL
    assert "backup" in reason


def test_critical_for_pg_dump():
    e = _entry("pg_dump mydb > /tmp/mydb.sql")
    priority, reason = _assign_priority(e)
    assert priority == CRITICAL


def test_high_for_deploy_command():
    e = _entry("/scripts/deploy.sh")
    priority, reason = _assign_priority(e)
    assert priority == HIGH


def test_high_for_reboot_special():
    e = _entry("/bin/init_service.sh", special="@reboot")
    priority, reason = _assign_priority(e)
    assert priority == HIGH
    assert "reboot" in reason


def test_medium_for_daily_special():
    e = _entry("/usr/bin/report.sh", special="@daily")
    priority, reason = _assign_priority(e)
    assert priority == MEDIUM


def test_medium_for_specific_time():
    e = _entry("/usr/bin/task.sh", minute="30", hour="3")
    priority, reason = _assign_priority(e)
    assert priority == MEDIUM


def test_low_for_log_cleanup():
    e = _entry("/usr/bin/clean_logs.sh")
    priority, reason = _assign_priority(e)
    assert priority == LOW


def test_low_default():
    e = _entry("/usr/bin/misc_task.sh")
    priority, reason = _assign_priority(e)
    assert priority == LOW
    assert reason == "default"


# --- PrioritizedEntry.tier_name ---

def test_tier_name_critical():
    e = _entry("/bin/backup")
    pe = PrioritizedEntry(entry=e, server="srv1", priority=CRITICAL, reason="test")
    assert pe.tier_name == "critical"


def test_tier_name_low():
    e = _entry("/bin/task")
    pe = PrioritizedEntry(entry=e, server="srv1", priority=LOW, reason="default")
    assert pe.tier_name == "low"


# --- prioritize_crontab ---

def test_prioritize_skips_invalid_entries():
    invalid = CronEntry(
        raw="bad line", minute=None, hour=None, day_of_month=None,
        month=None, day_of_week=None, command="", special="", valid=False,
    )
    ct = _crontab("srv1", [invalid])
    report = prioritize_crontab(ct)
    assert report.count == 0


def test_prioritize_returns_correct_server():
    ct = _crontab("web01", [_entry("/bin/backup.sh")])
    report = prioritize_crontab(ct)
    assert report.server == "web01"


def test_prioritize_critical_and_low_split():
    entries = [
        _entry("/usr/bin/backup_db.sh"),
        _entry("/usr/bin/clean_tmp.sh"),
    ]
    ct = _crontab("srv1", entries)
    report = prioritize_crontab(ct)
    assert len(report.critical) == 1
    assert len(report.high) == 0
    assert report.count == 2


def test_prioritize_report_high_includes_deploy():
    ct = _crontab("srv2", [_entry("/opt/deploy.sh")])
    report = prioritize_crontab(ct)
    assert len(report.high) == 1
