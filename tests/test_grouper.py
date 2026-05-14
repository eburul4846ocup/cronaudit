"""Tests for cronaudit.grouper."""
import pytest
from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab
from cronaudit.grouper import group_by, EntryGroup, GroupingResult


def _entry(schedule="0 * * * *", command="/bin/foo", user="root", special=None):
    return CronEntry(
        schedule=schedule,
        command=command,
        user=user,
        special=special,
        comment=None,
        raw="",
        valid=True,
    )


def _crontab(server, entries, error=None):
    sc = ServerCrontab(server=server, entries=entries, error=error)
    return sc


def test_group_by_schedule_basic():
    crontabs = [
        _crontab("web1", [_entry("0 * * * *", "/bin/a"), _entry("0 0 * * *", "/bin/b")]),
        _crontab("web2", [_entry("0 * * * *", "/bin/c")]),
    ]
    result = group_by(crontabs, by="schedule")
    assert result.group_count == 2
    assert result.groups["0 * * * *"].count == 2
    assert result.groups["0 0 * * *"].count == 1


def test_group_by_user():
    crontabs = [
        _crontab("srv1", [_entry(user="root"), _entry(user="deploy")]),
        _crontab("srv2", [_entry(user="root")]),
    ]
    result = group_by(crontabs, by="user")
    assert "root" in result.groups
    assert result.groups["root"].count == 2
    assert result.groups["deploy"].count == 1


def test_group_by_command_prefix():
    crontabs = [
        _crontab("s1", [_entry(command="/usr/bin/python script.py"), _entry(command="/usr/bin/bash run.sh")]),
        _crontab("s2", [_entry(command="/usr/bin/python other.py")]),
    ]
    result = group_by(crontabs, by="command", command_words=1)
    assert "/usr/bin/python" in result.groups
    assert result.groups["/usr/bin/python"].count == 2


def test_group_skips_errored_crontabs():
    crontabs = [
        _crontab("ok", [_entry()]),
        _crontab("bad", [], error="SSH timeout"),
    ]
    result = group_by(crontabs, by="schedule")
    servers_in_groups = {s for g in result.groups.values() for s, _ in g.entries}
    assert "bad" not in servers_in_groups
    assert "ok" in servers_in_groups


def test_group_special_schedule_key():
    crontabs = [
        _crontab("s1", [_entry(schedule=None, special="@daily")]),
    ]
    result = group_by(crontabs, by="schedule")
    assert "@daily" in result.groups


def test_invalid_strategy_raises():
    with pytest.raises(ValueError, match="Unknown grouping strategy"):
        group_by([], by="invalid")


def test_total_entries():
    crontabs = [
        _crontab("a", [_entry(), _entry(), _entry()]),
        _crontab("b", [_entry()]),
    ]
    result = group_by(crontabs, by="schedule")
    assert result.total_entries == 4
