"""Tests for cronaudit.heatmap and cronaudit.heatmap_formatter."""
import json

import pytest

from cronaudit.collector import ServerCrontab
from cronaudit.heatmap import DAYS, HOURS, HeatmapReport, build_heatmap
from cronaudit.heatmap_formatter import heatmap_to_json, heatmap_to_text
from cronaudit.parser import CronEntry


def _entry(schedule: str, command: str = "cmd", special: bool = False) -> CronEntry:
    return CronEntry(
        schedule=schedule,
        command=command,
        user="root",
        special=special,
        comment=None,
        raw=schedule + " " + command,
    )


def _crontab(entries, server: str = "srv1") -> ServerCrontab:
    return ServerCrontab(server=server, entries=entries, error=None)


# ---------------------------------------------------------------------------
# build_heatmap
# ---------------------------------------------------------------------------

def test_empty_crontabs_returns_zero_grid():
    report = build_heatmap([])
    assert report.total_entries == 0
    assert report.peak == 0


def test_special_entry_is_skipped():
    ct = _crontab([_entry("@daily", special=True)])
    report = build_heatmap([ct])
    assert report.total_entries == 1
    assert report.skipped_entries == 1
    assert report.peak == 0


def test_specific_hour_increments_all_days():
    # "* 3 * * *" fires every minute of hour 3 on every day
    ct = _crontab([_entry("* 3 * * *")])
    report = build_heatmap([ct])
    for d in range(7):
        assert report.grid[d][3] == 1
    assert report.grid[0][4] == 0


def test_specific_dow_increments_one_day():
    # "* 10 * * 1" fires on Monday (dow=1) at hour 10
    ct = _crontab([_entry("* 10 * * 1")])
    report = build_heatmap([ct])
    monday_idx = (1 % 7 + 6) % 7  # = 0 (Mon=0 in our remap)
    assert report.grid[monday_idx][10] == 1
    for d in range(7):
        if d != monday_idx:
            assert report.grid[d][10] == 0


def test_multiple_servers_accumulate():
    e = _entry("* 6 * * *")
    ct1 = _crontab([e], server="s1")
    ct2 = _crontab([e], server="s2")
    report = build_heatmap([ct1, ct2])
    for d in range(7):
        assert report.grid[d][6] == 2


def test_peak_reflects_maximum_cell():
    e1 = _entry("* 8 * * *")
    e2 = _entry("* 8 * * *")
    ct = _crontab([e1, e2])
    report = build_heatmap([ct])
    assert report.peak == 2


def test_invalid_schedule_skipped():
    ct = _crontab([_entry("not a cron")])
    report = build_heatmap([ct])
    assert report.skipped_entries == 1


# ---------------------------------------------------------------------------
# heatmap_to_text
# ---------------------------------------------------------------------------

def test_text_contains_day_labels():
    report = build_heatmap([])
    text = heatmap_to_text(report)
    for day in DAYS:
        assert day in text


def test_text_contains_totals():
    ct = _crontab([_entry("* 0 * * *")])
    report = build_heatmap([ct])
    text = heatmap_to_text(report)
    assert "Total entries" in text
    assert "1" in text


# ---------------------------------------------------------------------------
# heatmap_to_json
# ---------------------------------------------------------------------------

def test_json_structure():
    ct = _crontab([_entry("* 12 * * *")])
    report = build_heatmap([ct])
    data = json.loads(heatmap_to_json(report))
    assert "grid" in data
    assert "peak" in data
    assert set(data["grid"].keys()) == set(DAYS)
    assert data["total_entries"] == 1


def test_json_grid_values_are_ints():
    report = build_heatmap([])
    data = json.loads(heatmap_to_json(report))
    for day in DAYS:
        for h in range(24):
            assert isinstance(data["grid"][day][str(h)], int)
