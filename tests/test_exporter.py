"""Tests for cronaudit.exporter."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from cronaudit.exporter import ExportOptions, ExportSummary, export_results
from cronaudit.multi import AuditResult
from cronaudit.collector import ServerCrontab
from cronaudit.parser import CronEntry


def _make_entry(cmd: str = "/bin/true") -> CronEntry:
    return CronEntry(
        raw="* * * * * " + cmd,
        schedule="* * * * *",
        command=cmd,
        user=None,
        comment=None,
        is_valid=True,
    )


def _make_result(server: str = "host1") -> AuditResult:
    sc = ServerCrontab(server=server, entries=[_make_entry()], error=None)
    return AuditResult(server=server, crontab=sc)


# ---------------------------------------------------------------------------
# ExportOptions defaults
# ---------------------------------------------------------------------------

def test_export_options_default_formats():
    opts = ExportOptions()
    assert opts.formats == ["text"]


def test_export_options_custom():
    opts = ExportOptions(output_dir="/tmp", base_name="report", formats=["json", "csv"])
    assert "json" in opts.formats
    assert opts.base_name == "report"


# ---------------------------------------------------------------------------
# export_results — happy path
# ---------------------------------------------------------------------------

def test_export_creates_text_file(tmp_path):
    opts = ExportOptions(output_dir=str(tmp_path), formats=["text"])
    summary = export_results([_make_result()], options=opts)
    assert len(summary.written) == 1
    assert summary.written[0].endswith(".txt")
    assert Path(summary.written[0]).exists()


def test_export_creates_json_file(tmp_path):
    opts = ExportOptions(output_dir=str(tmp_path), formats=["json"])
    summary = export_results([_make_result()], options=opts)
    content = Path(summary.written[0]).read_text()
    data = json.loads(content)
    assert isinstance(data, list)


def test_export_creates_csv_file(tmp_path):
    opts = ExportOptions(output_dir=str(tmp_path), formats=["csv"])
    summary = export_results([_make_result()], options=opts)
    content = Path(summary.written[0]).read_text()
    assert "server" in content.lower() or "command" in content.lower()


def test_export_multiple_formats(tmp_path):
    opts = ExportOptions(output_dir=str(tmp_path), formats=["text", "json", "csv"])
    summary = export_results([_make_result()], options=opts)
    assert len(summary.written) == 3


def test_export_unknown_format_skipped(tmp_path):
    opts = ExportOptions(output_dir=str(tmp_path), formats=["xml"])
    summary = export_results([_make_result()], options=opts)
    assert "xml" in summary.skipped
    assert len(summary.written) == 0


def test_export_no_overwrite_skips_existing(tmp_path):
    opts = ExportOptions(output_dir=str(tmp_path), formats=["text"])
    export_results([_make_result()], options=opts)
    summary2 = export_results([_make_result()], options=opts, overwrite=False)
    assert len(summary2.skipped) == 1
    assert len(summary2.written) == 0


def test_export_summary_bool_true(tmp_path):
    opts = ExportOptions(output_dir=str(tmp_path), formats=["text"])
    summary = export_results([_make_result()], options=opts)
    assert bool(summary) is True


def test_export_summary_bool_false(tmp_path):
    opts = ExportOptions(output_dir=str(tmp_path), formats=["xml"])
    summary = export_results([_make_result()], options=opts)
    assert bool(summary) is False


def test_export_creates_output_dir(tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    opts = ExportOptions(output_dir=str(nested), formats=["text"])
    export_results([_make_result()], options=opts)
    assert nested.is_dir()
