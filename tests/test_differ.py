"""Tests for cronaudit.differ module."""

import pytest
from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab
from cronaudit.differ import DiffResult, diff_crontabs, format_diff


def _entry(schedule: str, command: str, user: str = None) -> CronEntry:
    return CronEntry(schedule=schedule, command=command, user=user)


def _snapshot(server: str, entries) -> ServerCrontab:
    sc = ServerCrontab(server=server)
    sc.entries = entries
    return sc


def test_diff_no_changes():
    entry = _entry("0 * * * *", "/bin/backup")
    before = _snapshot("web1", [entry])
    after = _snapshot("web1", [entry])
    result = diff_crontabs(before, after)
    assert not result.has_changes
    assert len(result.unchanged) == 1
    assert result.added == []
    assert result.removed == []


def test_diff_added_entry():
    old = _entry("0 * * * *", "/bin/backup")
    new = _entry("@daily", "/bin/cleanup")
    before = _snapshot("web1", [old])
    after = _snapshot("web1", [old, new])
    result = diff_crontabs(before, after)
    assert result.has_changes
    assert len(result.added) == 1
    assert result.added[0].command == "/bin/cleanup"
    assert result.removed == []


def test_diff_removed_entry():
    old = _entry("0 * * * *", "/bin/backup")
    before = _snapshot("web1", [old])
    after = _snapshot("web1", [])
    result = diff_crontabs(before, after)
    assert result.has_changes
    assert result.removed[0].command == "/bin/backup"
    assert result.added == []


def test_diff_added_and_removed():
    old = _entry("0 * * * *", "/bin/backup")
    new = _entry("@daily", "/bin/cleanup")
    before = _snapshot("db1", [old])
    after = _snapshot("db1", [new])
    result = diff_crontabs(before, after)
    assert len(result.added) == 1
    assert len(result.removed) == 1
    assert len(result.unchanged) == 0


def test_diff_uses_after_server_name():
    before = _snapshot("old-host", [])
    after = _snapshot("new-host", [])
    result = diff_crontabs(before, after)
    assert result.server == "new-host"


def test_format_diff_no_changes():
    before = _snapshot("web1", [])
    after = _snapshot("web1", [])
    result = diff_crontabs(before, after)
    text = format_diff(result)
    assert "No changes" in text
    assert "web1" in text


def test_format_diff_shows_plus_minus():
    old = _entry("0 * * * *", "/bin/backup")
    new = _entry("@daily", "/bin/cleanup")
    before = _snapshot("web1", [old])
    after = _snapshot("web1", [new])
    result = diff_crontabs(before, after)
    text = format_diff(result)
    assert "+ @daily" in text
    assert "- 0 * * * *" in text


def test_format_diff_summary_line():
    old = _entry("0 * * * *", "/bin/backup")
    new = _entry("@daily", "/bin/cleanup")
    before = _snapshot("web1", [old])
    after = _snapshot("web1", [new])
    result = diff_crontabs(before, after)
    text = format_diff(result)
    assert "1 added" in text
    assert "1 removed" in text
