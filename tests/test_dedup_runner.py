"""Tests for cronaudit.dedup_runner."""
import os
import pytest
from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab
from cronaudit.dedup_runner import DedupRunConfig, DedupRunResult, run_deduplication


def _entry(schedule: str, command: str) -> CronEntry:
    return CronEntry(
        schedule=schedule,
        command=command,
        user="root",
        comment="",
        is_valid=True,
        raw=f"{schedule} {command}",
    )


def _crontab(server: str, entries) -> ServerCrontab:
    sc = ServerCrontab(server=server)
    sc.entries = entries
    return sc


# ---------------------------------------------------------------------------
# DedupRunConfig defaults
# ---------------------------------------------------------------------------

def test_config_defaults():
    cfg = DedupRunConfig()
    assert cfg.cross_server is True
    assert cfg.include_user is True
    assert cfg.output_path is None


# ---------------------------------------------------------------------------
# run_deduplication — basic behaviour
# ---------------------------------------------------------------------------

def test_run_no_duplicates_ok():
    ct = _crontab("srv1", [_entry("0 * * * *", "/bin/a")])
    result = run_deduplication([ct])
    assert result.ok
    assert not result.dedup.has_duplicates


def test_run_detects_duplicates_across_servers():
    e = _entry("@daily", "/usr/bin/cleanup")
    ct1 = _crontab("web1", [e])
    ct2 = _crontab("web2", [e])
    result = run_deduplication([ct1, ct2])
    assert result.ok
    assert result.dedup.has_duplicates
    assert result.dedup.duplicate_count == 1


def test_run_cross_server_false_config():
    e = _entry("@daily", "/usr/bin/cleanup")
    ct1 = _crontab("web1", [e])
    ct2 = _crontab("web2", [e])
    cfg = DedupRunConfig(cross_server=False)
    result = run_deduplication([ct1, ct2], config=cfg)
    assert result.ok
    assert not result.dedup.has_duplicates


def test_run_empty_crontabs():
    result = run_deduplication([])
    assert result.ok
    assert result.dedup.total_entries == 0


# ---------------------------------------------------------------------------
# summary_line
# ---------------------------------------------------------------------------

def test_summary_line_contains_counts():
    e = _entry("0 1 * * *", "/bin/x")
    ct1 = _crontab("s1", [e])
    ct2 = _crontab("s2", [e])
    result = run_deduplication([ct1, ct2])
    line = result.summary_line
    assert "Total entries" in line
    assert "Duplicates" in line


# ---------------------------------------------------------------------------
# output_path — writes report file
# ---------------------------------------------------------------------------

def test_run_writes_report_file(tmp_path):
    out = str(tmp_path / "dedup_report.txt")
    e = _entry("@hourly", "/bin/y")
    ct1 = _crontab("s1", [e])
    ct2 = _crontab("s2", [e])
    cfg = DedupRunConfig(output_path=out)
    result = run_deduplication([ct1, ct2], config=cfg)
    assert result.ok
    assert result.written_to == out
    assert os.path.exists(out)
    content = open(out).read()
    assert "/bin/y" in content


def test_run_bad_output_path_returns_error():
    e = _entry("* * * * *", "/bin/z")
    ct = _crontab("s1", [e])
    cfg = DedupRunConfig(output_path="/nonexistent_dir/report.txt")
    result = run_deduplication([ct], config=cfg)
    assert not result.ok
    assert result.error is not None
