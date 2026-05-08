"""Tests for cronaudit.tagging."""
import pytest

from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab
from cronaudit.tagging import (
    TagRule,
    TaggedEntry,
    apply_rules,
    tag_crontab,
    tag_all,
    collect_tags,
)


def _entry(command: str) -> CronEntry:
    return CronEntry(
        raw="0 * * * * " + command,
        schedule="0 * * * *",
        command=command,
        user="root",
        comment="",
        is_valid=True,
    )


def _crontab(server: str, commands, error="") -> ServerCrontab:
    return ServerCrontab(
        server=server,
        entries=[_entry(c) for c in commands],
        error=error,
    )


RULES = [
    TagRule(tag="backup", pattern="backup"),
    TagRule(tag="deploy", pattern="deploy"),
    TagRule(tag="python", pattern="python"),
]


def test_apply_rules_single_match():
    e = _entry("/usr/bin/backup.sh")
    tags = apply_rules(e, RULES)
    assert tags == {"backup"}


def test_apply_rules_multiple_match():
    e = _entry("python deploy.py")
    tags = apply_rules(e, RULES)
    assert "deploy" in tags
    assert "python" in tags


def test_apply_rules_no_match():
    e = _entry("/bin/cleanup")
    tags = apply_rules(e, RULES)
    assert tags == set()


def test_apply_rules_case_insensitive():
    e = _entry("/scripts/BACKUP_weekly.sh")
    tags = apply_rules(e, RULES)
    assert "backup" in tags


def test_tag_crontab_preserves_server():
    ct = _crontab("web01", ["/usr/bin/backup.sh", "/bin/other"])
    result = tag_crontab(ct, RULES)
    assert result.server == "web01"
    assert len(result.tagged_entries) == 2


def test_tag_crontab_error_propagated():
    ct = _crontab("broken", [], error="SSH timeout")
    result = tag_crontab(ct, RULES)
    assert not result.is_ok
    assert result.error == "SSH timeout"


def test_entries_with_tag():
    ct = _crontab("srv", ["backup_db", "deploy_app", "cleanup"])
    tc = tag_crontab(ct, RULES)
    backup_entries = tc.entries_with_tag("backup")
    assert len(backup_entries) == 1
    assert backup_entries[0].entry.command == "backup_db"


def test_tag_all_multiple_servers():
    crontabs = [
        _crontab("a", ["backup_a"]),
        _crontab("b", ["deploy_b"]),
    ]
    results = tag_all(crontabs, RULES)
    assert len(results) == 2
    assert results[0].server == "a"
    assert results[1].server == "b"


def test_collect_tags_counts():
    crontabs = [
        _crontab("a", ["backup1", "backup2", "deploy1"]),
        _crontab("b", ["backup3"]),
    ]
    tagged = tag_all(crontabs, RULES)
    counts = collect_tags(tagged)
    assert counts["backup"] == 3
    assert counts["deploy"] == 1


def test_collect_tags_empty():
    assert collect_tags([]) == {}


def test_has_tag():
    e = _entry("python backup.py")
    te = TaggedEntry(entry=e, tags=apply_rules(e, RULES))
    assert te.has_tag("python")
    assert te.has_tag("backup")
    assert not te.has_tag("deploy")
