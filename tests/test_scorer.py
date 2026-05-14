"""Tests for cronaudit.scorer and cronaudit.score_runner."""
import pytest

from cronaudit.parser import CronEntry
from cronaudit.multi import AuditResult
from cronaudit.scorer import score_entry, score_entries, ScoredEntry
from cronaudit.score_runner import run_scoring, ScoreRunResult


def _entry(
    command="/usr/bin/backup.sh",
    schedule="0 2 * * *",
    user="deploy",
    valid=True,
) -> CronEntry:
    return CronEntry(
        schedule=schedule,
        command=command,
        user=user,
        comment=None,
        valid=valid,
    )


def _result(server="web1", entries=None, error=None) -> AuditResult:
    return AuditResult(
        server=server,
        entries=entries or [],
        error=error,
    )


# --- scorer ---

def test_low_risk_benign_entry():
    s = score_entry(_entry())
    assert s.risk_level == "low"
    assert s.score < 40


def test_high_risk_rm_command():
    s = score_entry(_entry(command="rm -rf /tmp/old"))
    assert s.risk_level == "high"
    assert any("rm" in r for r in s.reasons)


def test_reboot_adds_score():
    s = score_entry(_entry(schedule="@reboot"))
    assert s.score >= 20
    assert any("reboot" in r for r in s.reasons)


def test_root_user_adds_score():
    s = score_entry(_entry(user="root"))
    assert s.score >= 10
    assert any("root" in r for r in s.reasons)


def test_invalid_entry_adds_score():
    s = score_entry(_entry(valid=False))
    assert s.score >= 30
    assert any("invalid" in r for r in s.reasons)


def test_score_capped_at_100():
    e = _entry(command="sudo rm -rf /", user="root", schedule="@reboot", valid=False)
    s = score_entry(e)
    assert s.score <= 100


def test_score_entries_sorted_descending():
    entries = [
        _entry(command="/safe/script.sh"),
        _entry(command="wget http://example.com/payload"),
        _entry(command="rm -rf /var/old"),
    ]
    scored = score_entries(entries)
    scores = [s.score for s in scored]
    assert scores == sorted(scores, reverse=True)


# --- score_runner ---

def test_run_scoring_ok():
    entries = [_entry(), _entry(command="curl http://example.com")]
    results = [_result(entries=entries)]
    run = run_scoring(results)
    assert run.ok
    assert run.total_scored == 2
    assert "web1" in run.server_scores


def test_run_scoring_skips_error_result():
    results = [_result(server="bad", error="connection refused")]
    run = run_scoring(results)
    assert not run.ok
    assert "bad" not in run.server_scores
    assert run.total_scored == 0


def test_run_scoring_high_risk_count():
    entries = [
        _entry(command="rm -rf /tmp"),
        _entry(command="/usr/bin/safe.sh"),
    ]
    run = run_scoring([_result(entries=entries)])
    assert run.high_risk_count >= 1


def test_summary_line_format():
    run = run_scoring([_result(entries=[_entry()])])
    line = run.summary_line()
    assert "scored" in line
    assert "server" in line
    assert "high-risk" in line
