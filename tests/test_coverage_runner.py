"""Tests for cronaudit.coverage_runner."""
from __future__ import annotations

from cronaudit.collector import ServerCrontab
from cronaudit.coverage_runner import run_coverage
from cronaudit.parser import CronEntry


def _entry(hour="*", dow="*") -> CronEntry:
    return CronEntry(
        minute="0", hour=hour, dom="*", month="*", dow=dow,
        user="root", command="/bin/job", special=None,
    )


def _crontab(entries, server="srv") -> ServerCrontab:
    sc = ServerCrontab(server=server)
    sc.entries = entries
    return sc


def test_run_coverage_returns_result():
    result = run_coverage([])
    assert result.report is not None
    assert isinstance(result.text, str)
    assert isinstance(result.json_str, str)


def test_run_coverage_ok_false_when_gaps():
    result = run_coverage([])
    assert result.ok is False


def test_run_coverage_ok_true_when_full():
    entries = [_entry(hour=str(h)) for h in range(24)]
    result = run_coverage([_crontab(entries)])
    assert result.ok is True


def test_summary_line_contains_pct():
    result = run_coverage([])
    assert "%" in result.summary_line


def test_summary_line_ok_label_when_no_gaps():
    entries = [_entry(hour=str(h)) for h in range(24)]
    result = run_coverage([_crontab(entries)])
    assert "OK" in result.summary_line


def test_summary_line_gap_count_when_gaps():
    result = run_coverage([])
    assert "gap" in result.summary_line


def test_text_contains_header():
    result = run_coverage([])
    assert "Coverage Report" in result.text


def test_json_contains_grid_key():
    import json
    result = run_coverage([])
    data = json.loads(result.json_str)
    assert "grid" in data
    assert "gaps" in data
    assert "coverage_pct" in data
