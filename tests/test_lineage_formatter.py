"""Tests for cronaudit.lineage_formatter."""
import json

from cronaudit.lineage import LineagePair, LineageReport
from cronaudit.lineage_formatter import lineage_to_text, lineage_to_json


def _report_with_pair(schedule_changed: bool = False) -> LineageReport:
    pair = LineagePair(
        server="srv1",
        old_command="/opt/old.sh",
        new_command="/opt/new.sh",
        similarity=0.88,
        schedule_changed=schedule_changed,
    )
    return LineageReport(pairs=[pair])


def test_text_contains_header():
    text = lineage_to_text({"srv1": _report_with_pair()})
    assert "Lineage Report" in text


def test_text_shows_server_name():
    text = lineage_to_text({"srv1": _report_with_pair()})
    assert "srv1" in text


def test_text_shows_commands():
    text = lineage_to_text({"srv1": _report_with_pair()})
    assert "/opt/old.sh" in text
    assert "/opt/new.sh" in text


def test_text_shows_schedule_changed_tag():
    text = lineage_to_text({"srv1": _report_with_pair(schedule_changed=True)})
    assert "schedule changed" in text


def test_text_no_renames_message():
    text = lineage_to_text({"srv1": LineageReport(pairs=[])})
    assert "No renames" in text


def test_text_empty_dict():
    text = lineage_to_text({})
    assert "no data" in text.lower()


def test_json_is_valid():
    raw = lineage_to_json({"srv1": _report_with_pair()})
    data = json.loads(raw)
    assert isinstance(data, list)
    assert data[0]["server"] == "srv1"


def test_json_rename_fields():
    raw = lineage_to_json({"srv1": _report_with_pair()})
    data = json.loads(raw)
    rename = data[0]["renames"][0]
    assert rename["old_command"] == "/opt/old.sh"
    assert rename["new_command"] == "/opt/new.sh"
    assert "similarity" in rename
    assert "schedule_changed" in rename


def test_json_empty_reports():
    raw = lineage_to_json({})
    assert json.loads(raw) == []
