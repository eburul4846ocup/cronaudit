"""Tests for cronaudit.complexity and cronaudit.complexity_formatter."""
import json
import pytest

from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab
from cronaudit.complexity import (
    score_entry,
    analyse_complexity,
    ComplexityReport,
    ComplexityResult,
)
from cronaudit.complexity_formatter import complexity_to_text, complexity_to_json


def _entry(schedule: str, command: str = "cmd", special: bool = False) -> CronEntry:
    return CronEntry(
        schedule=schedule,
        command=command,
        user=None,
        comment=None,
        special=special,
    )


def _crontab(server: str, entries) -> ServerCrontab:
    sc = ServerCrontab(server=server)
    sc.entries = list(entries)
    return sc


# --- score_entry ---

def test_simple_wildcard_entry_scores_zero():
    result = score_entry(_entry("* * * * *"), server="host1")
    assert result.score == 0
    assert result.level == "simple"


def test_step_value_adds_score():
    result = score_entry(_entry("*/5 * * * *"), server="host1")
    assert result.score >= 1
    assert "step" in " ".join(result.reasons)


def test_list_value_adds_score():
    result = score_entry(_entry("0 9,17 * * *"), server="host1")
    assert result.score >= 1
    assert any("list" in r for r in result.reasons)


def test_range_value_adds_score():
    result = score_entry(_entry("0 8-18 * * *"), server="host1")
    assert result.score >= 1
    assert any("range" in r for r in result.reasons)


def test_combined_fields_accumulate_score():
    result = score_entry(_entry("*/10 8-18 1,15 * 1-5"), server="host1")
    assert result.score >= 4
    assert result.level in ("moderate", "complex")


def test_special_entry_scores_zero():
    result = score_entry(_entry("@daily", special=True), server="host1")
    assert result.score == 0
    assert result.level == "simple"


def test_server_stored_in_result():
    result = score_entry(_entry("* * * * *"), server="myserver")
    assert result.server == "myserver"


# --- analyse_complexity ---

def test_analyse_empty_returns_empty_report():
    report = analyse_complexity([])
    assert report.count == 0
    assert report.average_score == 0.0
    assert not report


def test_analyse_counts_all_entries():
    ct = _crontab("srv", [_entry("* * * * *"), _entry("*/5 * * * *")])
    report = analyse_complexity([ct])
    assert report.count == 2


def test_analyse_complex_count():
    entries = [
        _entry("* * * * *"),
        _entry("*/5 8-18 1,15 * 1-5"),  # complex
        _entry("0 0 * * *"),
    ]
    ct = _crontab("srv", entries)
    report = analyse_complexity([ct])
    assert report.complex_count >= 1


def test_bool_true_when_complex_entries_exist():
    ct = _crontab("srv", [_entry("*/5 8-18 1,15 * 1-5")])
    report = analyse_complexity([ct])
    assert bool(report) is True


def test_bool_false_when_no_complex_entries():
    ct = _crontab("srv", [_entry("* * * * *")])
    report = analyse_complexity([ct])
    assert bool(report) is False


# --- formatters ---

def test_text_contains_header():
    report = analyse_complexity([])
    text = complexity_to_text(report)
    assert "Complexity Report" in text


def test_text_shows_no_complex_message_when_clean():
    ct = _crontab("srv", [_entry("0 0 * * *")])
    report = analyse_complexity([ct])
    text = complexity_to_text(report)
    assert "No complex entries found" in text


def test_text_lists_complex_entries():
    ct = _crontab("srv", [_entry("*/5 8-18 1,15 * 1-5", "backup.sh")])
    report = analyse_complexity([ct])
    text = complexity_to_text(report)
    assert "backup.sh" in text


def test_json_output_valid():
    ct = _crontab("srv", [_entry("*/5 * * * *", "job")])
    report = analyse_complexity([ct])
    data = json.loads(complexity_to_json(report))
    assert "summary" in data
    assert "entries" in data
    assert data["summary"]["total"] == 1


def test_json_entry_has_expected_keys():
    ct = _crontab("srv", [_entry("0 * * * *", "hourly")])
    report = analyse_complexity([ct])
    data = json.loads(complexity_to_json(report))
    entry = data["entries"][0]
    for key in ("server", "schedule", "command", "score", "level", "reasons"):
        assert key in entry
