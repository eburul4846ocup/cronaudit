"""Tests for cronaudit.summarizer."""
import pytest
from cronaudit.parser import CronEntry
from cronaudit.multi import AuditResult
from cronaudit.summarizer import summarize, format_summary


def _entry(schedule: str, command: str) -> CronEntry:
    return CronEntry(schedule=schedule, command=command, raw=f"{schedule} {command}")


def _result(server: str, entries=None, error=None) -> AuditResult:
    return AuditResult(server=server, entries=entries or [], error=error)


def test_summary_counts_servers():
    results = [
        _result("host1", [_entry("* * * * *", "/bin/a")]),
        _result("host2", [], error="unreachable"),
    ]
    s = summarize(results)
    assert s.total_servers == 2
    assert s.successful_servers == 1
    assert s.failed_servers == 1


def test_summary_counts_entries():
    results = [
        _result("host1", [
            _entry("0 * * * *", "/usr/bin/backup"),
            _entry("@daily", "/usr/bin/cleanup"),
        ]),
        _result("host2", [_entry("5 4 * * *", "/usr/bin/report")]),
    ]
    s = summarize(results)
    assert s.total_entries == 3
    assert s.entries_per_server["host1"] == 2
    assert s.entries_per_server["host2"] == 1


def test_summary_schedule_type_split():
    results = [
        _result("srv", [
            _entry("@reboot", "/bin/start"),
            _entry("@daily", "/bin/clean"),
            _entry("0 0 * * *", "/bin/nightly"),
        ])
    ]
    s = summarize(results)
    assert s.special_schedule_count == 2
    assert s.standard_schedule_count == 1


def test_summary_top_commands():
    results = [
        _result("srv", [
            _entry("* * * * *", "/bin/foo arg1"),
            _entry("* * * * *", "/bin/foo arg2"),
            _entry("* * * * *", "/bin/bar"),
        ])
    ]
    s = summarize(results)
    cmds = dict(s.top_commands)
    assert cmds["/bin/foo"] == 2
    assert cmds["/bin/bar"] == 1


def test_summary_empty_results():
    s = summarize([])
    assert s.total_servers == 0
    assert s.total_entries == 0
    assert s.top_commands == []


def test_format_summary_contains_key_fields():
    results = [
        _result("alpha", [_entry("@daily", "/bin/x")]),
        _result("beta", [], error="timeout"),
    ]
    s = summarize(results)
    text = format_summary(s)
    assert "Servers" in text
    assert "alpha" in text
    assert "beta" in text
    assert "Entries" in text


def test_format_summary_top_commands_section():
    results = [
        _result("s", [
            _entry("0 * * * *", "/usr/bin/python script.py"),
            _entry("0 * * * *", "/usr/bin/python other.py"),
        ])
    ]
    s = summarize(results)
    text = format_summary(s)
    assert "Top commands" in text
    assert "/usr/bin/python" in text
