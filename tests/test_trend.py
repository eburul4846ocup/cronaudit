"""Tests for cronaudit.trend module."""
import pytest
from cronaudit.trend import (
    TrendPoint,
    TrendReport,
    build_trend_point,
    build_trend,
    format_trend,
)


def _snap(label, servers=2, entries=10, failed=0):
    return {
        "label": label,
        "server_count": servers,
        "entry_count": entries,
        "failed_servers": failed,
    }


def test_build_trend_point_fields():
    p = build_trend_point("2024-01", _snap("2024-01", servers=3, entries=15, failed=1))
    assert p.label == "2024-01"
    assert p.server_count == 3
    assert p.entry_count == 15
    assert p.failed_servers == 1


def test_build_trend_empty_list():
    report = build_trend([])
    assert report.points == []
    assert report.latest is None
    assert report.earliest is None


def test_build_trend_skips_missing_label():
    snaps = [_snap("a"), {"server_count": 1, "entry_count": 5, "failed_servers": 0}]
    report = build_trend(snaps)
    assert len(report.points) == 1
    assert report.points[0].label == "a"


def test_entry_delta_positive():
    report = build_trend([_snap("t1", entries=5), _snap("t2", entries=12)])
    assert report.entry_delta() == 7


def test_entry_delta_negative():
    report = build_trend([_snap("t1", entries=20), _snap("t2", entries=8)])
    assert report.entry_delta() == -12


def test_entry_delta_single_point_returns_none():
    report = build_trend([_snap("t1", entries=10)])
    assert report.entry_delta() is None


def test_server_delta():
    report = build_trend([_snap("t1", servers=2), _snap("t2", servers=5)])
    assert report.server_delta() == 3


def test_latest_and_earliest():
    snaps = [_snap("first"), _snap("middle"), _snap("last")]
    report = build_trend(snaps)
    assert report.earliest.label == "first"
    assert report.latest.label == "last"


def test_format_trend_no_data():
    result = format_trend(TrendReport())
    assert "No trend data" in result


def test_format_trend_contains_labels():
    report = build_trend([_snap("2024-01", entries=5), _snap("2024-02", entries=9)])
    text = format_trend(report)
    assert "2024-01" in text
    assert "2024-02" in text


def test_format_trend_shows_delta():
    report = build_trend([_snap("t1", entries=5), _snap("t2", entries=9)])
    text = format_trend(report)
    assert "+4" in text


def test_format_trend_negative_delta():
    report = build_trend([_snap("t1", entries=10), _snap("t2", entries=6)])
    text = format_trend(report)
    assert "-4" in text
