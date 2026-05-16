"""Tests for cronaudit.coverage."""
from __future__ import annotations

import pytest

from cronaudit.collector import ServerCrontab
from cronaudit.coverage import (
    CoverageGap,
    CoverageReport,
    _expand_field,
    build_coverage,
)
from cronaudit.parser import CronEntry


def _entry(
    minute="0",
    hour="*",
    dom="*",
    month="*",
    dow="*",
    user="root",
    command="/bin/true",
    special=None,
) -> CronEntry:
    return CronEntry(
        minute=minute,
        hour=hour,
        dom=dom,
        month=month,
        dow=dow,
        user=user,
        command=command,
        special=special,
    )


def _crontab(entries, server="srv1") -> ServerCrontab:
    sc = ServerCrontab(server=server)
    sc.entries = entries
    return sc


# --- _expand_field ---

def test_expand_star():
    assert _expand_field("*", 0, 6) == list(range(7))


def test_expand_single_value():
    assert _expand_field("5", 0, 23) == [5]


def test_expand_range():
    assert _expand_field("2-4", 0, 23) == [2, 3, 4]


def test_expand_step():
    assert _expand_field("*/6", 0, 23) == [0, 6, 12, 18]


def test_expand_list():
    assert _expand_field("1,3,5", 0, 6) == [1, 3, 5]


# --- CoverageReport properties ---

def test_empty_crontabs_all_gaps():
    report = build_coverage([])
    assert report.covered_hours == 0
    assert report.coverage_pct == 0.0
    assert len(report.gaps) == 7  # one gap per day covering all 24 hours


def test_specific_hour_marks_all_days():
    """A wildcard DOW entry at hour 3 should mark hour 3 for every day."""
    entry = _entry(minute="0", hour="3", dow="*")
    report = build_coverage([_crontab([entry])])
    for day in range(7):
        assert report.grid[day][3] is True
    # Other hours remain uncovered
    assert report.grid[0][4] is False


def test_specific_dow_only_marks_that_day():
    """DOW=1 (Tuesday) entry should only mark Tuesday."""
    entry = _entry(minute="0", hour="10", dow="1")
    report = build_coverage([_crontab([entry])])
    assert report.grid[1][10] is True
    assert report.grid[0][10] is False
    assert report.grid[2][10] is False


def test_full_coverage_no_gaps():
    """Entries covering every hour of every day produce no gaps."""
    entries = [_entry(minute="0", hour=str(h), dow="*") for h in range(24)]
    report = build_coverage([_crontab(entries)])
    assert report.covered_hours == 168
    assert report.gaps == []
    assert bool(report) is True


def test_special_at_daily_marks_midnight():
    entry = _entry(special="@daily")
    report = build_coverage([_crontab([entry])])
    for day in range(7):
        assert report.grid[day][0] is True


def test_special_at_reboot_skipped():
    """@reboot entries cannot be mapped to a time slot and are ignored."""
    entry = _entry(special="@reboot")
    report = build_coverage([_crontab([entry])])
    assert report.covered_hours == 0


def test_bool_false_when_gaps():
    report = build_coverage([])
    assert bool(report) is False


def test_coverage_gap_str_range():
    gap = CoverageGap(day=0, start_hour=2, end_hour=5)
    assert str(gap) == "Mon 02:00-05:59"


def test_coverage_gap_str_single():
    gap = CoverageGap(day=6, start_hour=14, end_hour=14)
    assert str(gap) == "Sun 14:00"


def test_multiple_servers_merged():
    """Entries from two servers should both contribute to the grid."""
    e1 = _entry(minute="0", hour="8", dow="0")  # Monday 08:00
    e2 = _entry(minute="0", hour="20", dow="3")  # Thursday 20:00
    report = build_coverage([_crontab([e1], "srv1"), _crontab([e2], "srv2")])
    assert report.grid[0][8] is True
    assert report.grid[3][20] is True
    assert report.grid[0][20] is False
