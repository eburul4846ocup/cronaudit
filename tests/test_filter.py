"""Tests for cronaudit.filter module."""

import pytest
from cronaudit.parser import CronEntry
from cronaudit.multi import AuditResult
from cronaudit.filter import (
    FilterCriteria,
    filter_results,
    search_command,
    filter_by_server,
)


def _entry(command: str, user: str = "root", schedule: str = "* * * * *", comment: str = "") -> CronEntry:
    return CronEntry(
        raw_schedule=schedule,
        user=user,
        command=command,
        comment=comment,
        is_valid=True,
    )


def _result(server: str, entries, error=None) -> AuditResult:
    return AuditResult(server=server, entries=list(entries), error=error)


def test_filter_by_command_contains():
    results = [_result("web1", [_entry("/usr/bin/backup"), _entry("/usr/bin/cleanup")])]
    out = filter_results(results, FilterCriteria(command_contains="backup"))
    assert len(out[0].entries) == 1
    assert "backup" in out[0].entries[0].command


def test_filter_by_user():
    results = [_result("db1", [_entry("/bin/cmd", user="deploy"), _entry("/bin/cmd", user="root")])]
    out = filter_results(results, FilterCriteria(user="deploy"))
    assert len(out[0].entries) == 1
    assert out[0].entries[0].user == "deploy"


def test_filter_by_server_name():
    results = [
        _result("web1", [_entry("/bin/a")]),
        _result("db1", [_entry("/bin/b")]),
    ]
    out = filter_by_server(results, "web")
    servers = [r.server for r in out]
    assert "web1" in servers
    assert "db1" not in servers


def test_filter_has_comment_true():
    results = [_result("s1", [
        _entry("/bin/a", comment="nightly"),
        _entry("/bin/b", comment=""),
    ])]
    out = filter_results(results, FilterCriteria(has_comment=True))
    assert len(out[0].entries) == 1
    assert out[0].entries[0].comment == "nightly"


def test_filter_has_comment_false():
    results = [_result("s1", [
        _entry("/bin/a", comment="nightly"),
        _entry("/bin/b", comment=""),
    ])]
    out = filter_results(results, FilterCriteria(has_comment=False))
    assert len(out[0].entries) == 1
    assert out[0].entries[0].command == "/bin/b"


def test_search_command_convenience():
    results = [_result("srv", [_entry("/opt/deploy.sh"), _entry("/opt/clean.sh")])]
    out = search_command(results, "deploy")
    assert len(out[0].entries) == 1


def test_error_result_passes_through():
    results = [_result("broken", [], error="SSH timeout")]
    out = filter_results(results, FilterCriteria(command_contains="anything"))
    assert out[0].error == "SSH timeout"


def test_no_criteria_returns_all():
    results = [_result("s1", [_entry("/a"), _entry("/b"), _entry("/c")])]
    out = filter_results(results, FilterCriteria())
    assert len(out[0].entries) == 3
