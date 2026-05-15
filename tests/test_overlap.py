"""Tests for cronaudit.overlap."""
import pytest

from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab
from cronaudit.overlap import (
    OverlapPair,
    OverlapReport,
    detect_overlaps,
    format_overlap_report,
)


def _entry(schedule: str, command: str, user: str = "root") -> CronEntry:
    return CronEntry(schedule=schedule, command=command, user=user, comment="")


def _crontab(server: str, entries, error: str = "") -> ServerCrontab:
    return ServerCrontab(server=server, entries=list(entries), error=error)


# ---------------------------------------------------------------------------
# OverlapReport helpers
# ---------------------------------------------------------------------------

def test_overlap_report_bool_false_when_empty():
    assert not OverlapReport()


def test_overlap_report_bool_true_when_pairs():
    pair = OverlapPair(
        server="s1",
        entry_a=_entry("* * * * *", "cmd1"),
        entry_b=_entry("* * * * *", "cmd2"),
    )
    assert OverlapReport(pairs=[pair])


def test_overlap_report_count():
    pairs = [
        OverlapPair("s", _entry("0 * * * *", "a"), _entry("0 * * * *", "b")),
        OverlapPair("s", _entry("0 * * * *", "a"), _entry("0 * * * *", "c")),
    ]
    assert OverlapReport(pairs=pairs).count == 2


# ---------------------------------------------------------------------------
# detect_overlaps
# ---------------------------------------------------------------------------

def test_no_overlaps_when_different_schedules():
    ct = _crontab(
        "srv",
        [
            _entry("0 * * * *", "job_a"),
            _entry("0 2 * * *", "job_b"),
        ],
    )
    report = detect_overlaps([ct])
    assert not report


def test_detects_single_overlap():
    ct = _crontab(
        "srv",
        [
            _entry("0 * * * *", "job_a"),
            _entry("0 * * * *", "job_b"),
            _entry("0 2 * * *", "job_c"),
        ],
    )
    report = detect_overlaps([ct])
    assert report.count == 1
    assert report.pairs[0].server == "srv"


def test_detects_multiple_pairs():
    ct = _crontab(
        "srv",
        [
            _entry("*/5 * * * *", "a"),
            _entry("*/5 * * * *", "b"),
            _entry("*/5 * * * *", "c"),
        ],
    )
    # Three entries → 3 unique pairs
    report = detect_overlaps([ct])
    assert report.count == 3


def test_skips_errored_crontabs():
    ct = _crontab("bad", [_entry("* * * * *", "x"), _entry("* * * * *", "y")], error="timeout")
    report = detect_overlaps([ct])
    assert not report


def test_multiple_servers_independent():
    ct1 = _crontab("s1", [_entry("0 1 * * *", "a"), _entry("0 1 * * *", "b")])
    ct2 = _crontab("s2", [_entry("0 2 * * *", "c"), _entry("0 2 * * *", "d")])
    report = detect_overlaps([ct1, ct2])
    assert report.count == 2
    servers = {p.server for p in report.pairs}
    assert servers == {"s1", "s2"}


# ---------------------------------------------------------------------------
# format_overlap_report
# ---------------------------------------------------------------------------

def test_format_no_overlaps():
    msg = format_overlap_report(OverlapReport())
    assert "No overlapping" in msg


def test_format_shows_pair_info():
    pair = OverlapPair("web1", _entry("0 * * * *", "backup"), _entry("0 * * * *", "sync"))
    report = OverlapReport(pairs=[pair])
    text = format_overlap_report(report)
    assert "web1" in text
    assert "backup" in text
    assert "sync" in text
    assert "1 pair" in text
