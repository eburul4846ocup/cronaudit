"""Tests for cronaudit.group_runner."""
from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab
from cronaudit.group_runner import GroupRunConfig, GroupRunResult, run_grouping


def _entry(schedule="0 * * * *", command="/bin/task", user="root"):
    return CronEntry(
        schedule=schedule, command=command, user=user,
        special=None, comment=None, raw="", valid=True,
    )


def _crontab(server, entries, error=None):
    return ServerCrontab(server=server, entries=entries, error=error)


def test_run_grouping_defaults_ok():
    crontabs = [_crontab("srv1", [_entry()])]
    res = run_grouping(crontabs)
    assert res.ok
    assert res.result is not None
    assert res.result.group_count >= 1


def test_run_grouping_summary_line():
    crontabs = [_crontab("srv1", [_entry(), _entry("0 0 * * *", "/bin/other")])]
    res = run_grouping(crontabs, GroupRunConfig(by="schedule"))
    line = res.summary_line()
    assert "schedule" in line
    assert "2 groups" in line


def test_run_grouping_min_group_size_filters():
    crontabs = [
        _crontab("s1", [_entry("0 * * * *"), _entry("0 * * * *")]),
        _crontab("s2", [_entry("5 4 * * *")]),
    ]
    cfg = GroupRunConfig(by="schedule", min_group_size=2)
    res = run_grouping(crontabs, cfg)
    assert res.ok
    assert "5 4 * * *" not in res.result.groups
    assert "0 * * * *" in res.result.groups


def test_run_grouping_invalid_strategy_returns_error():
    crontabs = [_crontab("s1", [_entry()])]
    cfg = GroupRunConfig(by="nonsense")
    res = run_grouping(crontabs, cfg)
    assert not res.ok
    assert res.error is not None
    assert "nonsense" in res.summary_line()


def test_run_grouping_empty_crontabs():
    res = run_grouping([])
    assert res.ok
    assert res.result.group_count == 0
    assert res.result.total_entries == 0
