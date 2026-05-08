"""Tests for cronaudit.deduplicator."""
import pytest
from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab
from cronaudit.deduplicator import (
    find_duplicates,
    format_duplicates,
    DeduplicationResult,
    DuplicateGroup,
    _entry_key,
)


def _entry(schedule: str, command: str, user: str = "root", valid: bool = True) -> CronEntry:
    return CronEntry(
        schedule=schedule,
        command=command,
        user=user,
        comment="",
        is_valid=valid,
        raw=f"{schedule} {command}",
    )


def _crontab(server: str, entries) -> ServerCrontab:
    sc = ServerCrontab(server=server)
    sc.entries = entries
    return sc


# ---------------------------------------------------------------------------
# _entry_key
# ---------------------------------------------------------------------------

def test_entry_key_includes_user_by_default():
    e = _entry("0 * * * *", "/bin/foo", user="deploy")
    assert "deploy" in _entry_key(e)


def test_entry_key_excludes_user_when_flag_off():
    e = _entry("0 * * * *", "/bin/foo", user="deploy")
    assert "deploy" not in _entry_key(e, include_user=False)


# ---------------------------------------------------------------------------
# find_duplicates — no duplicates
# ---------------------------------------------------------------------------

def test_no_duplicates_returns_empty_groups():
    ct = _crontab("srv1", [
        _entry("0 * * * *", "/bin/a"),
        _entry("5 * * * *", "/bin/b"),
    ])
    result = find_duplicates([ct])
    assert not result.has_duplicates
    assert result.duplicate_count == 0


def test_total_entries_counted():
    ct = _crontab("srv1", [
        _entry("0 * * * *", "/bin/a"),
        _entry("5 * * * *", "/bin/b"),
    ])
    result = find_duplicates([ct])
    assert result.total_entries == 2


# ---------------------------------------------------------------------------
# find_duplicates — with duplicates
# ---------------------------------------------------------------------------

def test_same_entry_two_servers_detected():
    e = _entry("0 1 * * *", "/usr/bin/backup")
    ct1 = _crontab("srv1", [e])
    ct2 = _crontab("srv2", [e])
    result = find_duplicates([ct1, ct2])
    assert result.has_duplicates
    assert len(result.groups) == 1
    assert result.groups[0].count == 2
    assert set(result.groups[0].servers) == {"srv1", "srv2"}


def test_duplicate_within_single_server():
    e = _entry("@daily", "/bin/clean")
    ct = _crontab("srv1", [e, e])
    result = find_duplicates([ct])
    assert result.has_duplicates
    assert result.duplicate_count == 1


def test_invalid_entries_are_skipped():
    bad = _entry("bad", "/bin/x", valid=False)
    good = _entry("0 * * * *", "/bin/x")
    ct1 = _crontab("srv1", [bad, good])
    ct2 = _crontab("srv2", [good])
    result = find_duplicates([ct1, ct2])
    # only 'good' entries counted — two occurrences = one duplicate group
    assert result.total_entries == 2
    assert result.has_duplicates


def test_cross_server_false_does_not_merge_across_servers():
    e = _entry("0 2 * * *", "/bin/sync")
    ct1 = _crontab("srv1", [e])
    ct2 = _crontab("srv2", [e])
    result = find_duplicates([ct1, ct2], cross_server=False)
    assert not result.has_duplicates


# ---------------------------------------------------------------------------
# format_duplicates
# ---------------------------------------------------------------------------

def test_format_no_duplicates_message():
    result = DeduplicationResult(groups=[], total_entries=3, unique_entries=3)
    assert "No duplicate" in format_duplicates(result)


def test_format_shows_group_info():
    e = _entry("0 * * * *", "/bin/foo")
    group = DuplicateGroup(key="0 * * * *|root|/bin/foo", entries=[("a", e), ("b", e)])
    result = DeduplicationResult(groups=[group], total_entries=2, unique_entries=0)
    text = format_duplicates(result)
    assert "/bin/foo" in text
    assert "srv" in text or "a" in text
