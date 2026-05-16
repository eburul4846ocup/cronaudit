"""Tests for cronaudit.drift_formatter."""
import json

import pytest

from cronaudit.drift import DriftPair, DriftReport
from cronaudit.drift_formatter import drift_to_json, drift_to_text


def _report_with_pair(
    server: str = "web1",
    command: str = "/bin/job",
    old: str = "0 2 * * *",
    new: str = "0 4 * * *",
    user: str | None = "root",
) -> dict:
    pair = DriftPair(
        server=server, command=command,
        old_schedule=old, new_schedule=new, user=user,
    )
    return {server: DriftReport(pairs=[pair])}


# --- text ---

def test_text_no_drift_message():
    text = drift_to_text({"srv1": DriftReport()})
    assert "No schedule drift" in text


def test_text_contains_header():
    text = drift_to_text(_report_with_pair())
    assert "Drift Report" in text


def test_text_shows_server_name():
    text = drift_to_text(_report_with_pair(server="db1"))
    assert "db1" in text


def test_text_shows_old_and_new_schedule():
    text = drift_to_text(_report_with_pair(old="0 2 * * *", new="0 6 * * *"))
    assert "0 2 * * *" in text
    assert "0 6 * * *" in text


def test_text_shows_command():
    text = drift_to_text(_report_with_pair(command="/usr/bin/sync"))
    assert "/usr/bin/sync" in text


def test_text_shows_total():
    text = drift_to_text(_report_with_pair())
    assert "Total drift events: 1" in text


# --- json ---

def test_json_is_valid():
    text = drift_to_json(_report_with_pair())
    data = json.loads(text)
    assert "drift_report" in data


def test_json_total_drifted():
    data = json.loads(drift_to_json(_report_with_pair()))
    assert data["total_drifted"] == 1


def test_json_pair_fields():
    data = json.loads(drift_to_json(_report_with_pair(server="s1", command="/bin/x")))
    pairs = data["drift_report"]["s1"]
    assert len(pairs) == 1
    assert pairs[0]["command"] == "/bin/x"
    assert "old_schedule" in pairs[0]
    assert "new_schedule" in pairs[0]


def test_json_empty_report():
    data = json.loads(drift_to_json({"srv1": DriftReport()}))
    assert data["total_drifted"] == 0
    assert data["drift_report"]["srv1"] == []
