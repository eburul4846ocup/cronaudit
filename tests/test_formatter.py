"""Tests for cronaudit.formatter module."""

import json
import csv
import io

import pytest

from cronaudit.formatter import to_text, to_json, to_csv
from cronaudit.collector import ServerCrontab
from cronaudit.parser import CronEntry
from cronaudit.multi import AuditResult


def _make_entry(schedule: str, command: str, comment: str = "") -> CronEntry:
    raw = f"{schedule} {command}"
    return CronEntry(schedule=schedule, command=command, comment=comment, raw=raw)


def _make_result() -> AuditResult:
    ok_sc = ServerCrontab(server="web01")
    ok_sc.entries = [
        _make_entry("0 * * * *", "/usr/bin/backup.sh", "nightly backup"),
        _make_entry("@daily", "/usr/bin/cleanup.sh"),
    ]

    err_sc = ServerCrontab(server="db01", error="Connection refused")

    return AuditResult(server_crontabs=[ok_sc, err_sc])


# --- to_text ---

def test_to_text_contains_header():
    result = _make_result()
    output = to_text(result)
    assert "CRON AUDIT REPORT" in output


def test_to_text_summary_counts():
    result = _make_result()
    output = to_text(result)
    assert "Servers audited : 2" in output
    assert "Successful      : 1" in output
    assert "Failed          : 1" in output
    assert "Total entries   : 2" in output


def test_to_text_shows_server_entries():
    result = _make_result()
    output = to_text(result)
    assert "web01" in output
    assert "/usr/bin/backup.sh" in output
    assert "@daily" in output


def test_to_text_shows_error_server():
    result = _make_result()
    output = to_text(result)
    assert "[ERROR] db01" in output
    assert "Connection refused" in output


# --- to_json ---

def test_to_json_is_valid_json():
    result = _make_result()
    output = to_json(result)
    data = json.loads(output)  # should not raise
    assert "summary" in data
    assert "servers" in data


def test_to_json_summary_values():
    result = _make_result()
    data = json.loads(to_json(result))
    assert data["summary"]["total_servers"] == 2
    assert data["summary"]["successful"] == 1
    assert data["summary"]["failed"] == 1
    assert data["summary"]["total_entries"] == 2


def test_to_json_entry_fields():
    result = _make_result()
    data = json.loads(to_json(result))
    web01 = next(s for s in data["servers"] if s["server"] == "web01")
    assert len(web01["entries"]) == 2
    assert web01["entries"][0]["schedule"] == "0 * * * *"
    assert web01["entries"][0]["command"] == "/usr/bin/backup.sh"


# --- to_csv ---

def test_to_csv_has_header_row():
    result = _make_result()
    rows = list(csv.reader(io.StringIO(to_csv(result))))
    assert rows[0] == ["server", "schedule", "command", "comment", "error"]


def test_to_csv_entry_rows():
    result = _make_result()
    rows = list(csv.reader(io.StringIO(to_csv(result))))
    servers = [r[0] for r in rows[1:]]
    assert "web01" in servers
    assert "db01" in servers


def test_to_csv_error_row_has_error_column():
    result = _make_result()
    rows = list(csv.reader(io.StringIO(to_csv(result))))
    db01_row = next(r for r in rows if r[0] == "db01")
    assert db01_row[4] == "Connection refused"
