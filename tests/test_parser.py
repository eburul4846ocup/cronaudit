"""Tests for cronaudit.parser module."""

import pytest
from cronaudit.parser import parse_line, parse_crontab, CronEntry


def test_parse_standard_entry():
    line = "0 2 * * * /usr/bin/backup.sh"
    entry = parse_line(line)
    assert entry is not None
    assert entry.is_valid
    assert entry.schedule == "0 2 * * *"
    assert entry.command == "/usr/bin/backup.sh"
    assert not entry.is_special


def test_parse_special_at_daily():
    line = "@daily /usr/bin/cleanup.sh"
    entry = parse_line(line)
    assert entry is not None
    assert entry.is_special
    assert entry.schedule == "@daily"
    assert "once a day" in entry.special_description
    assert entry.command == "/usr/bin/cleanup.sh"


def test_parse_special_at_reboot():
    line = "@reboot /usr/local/bin/start_agent.sh"
    entry = parse_line(line)
    assert entry is not None
    assert entry.is_special
    assert entry.schedule == "@reboot"


def test_parse_comment_line_returns_none():
    assert parse_line("# this is a comment") is None
    assert parse_line("") is None
    assert parse_line("   ") is None


def test_parse_inline_comment():
    line = "30 6 * * 1 /usr/bin/report.sh # weekly report"
    entry = parse_line(line)
    assert entry is not None
    assert entry.comment == "weekly report"
    assert entry.command == "/usr/bin/report.sh"


def test_parse_invalid_entry_too_few_fields():
    line = "* * /usr/bin/something"
    entry = parse_line(line)
    assert entry is not None
    assert not entry.is_valid
    assert entry.error is not None


def test_parse_with_user_and_server():
    line = "0 0 * * * /bin/true"
    entry = parse_line(line, user="root", server="web-01")
    assert entry.user == "root"
    assert entry.server == "web-01"


def test_parse_crontab_multiple_lines():
    content = """
# System crontab
@daily /usr/bin/daily_task.sh
0 3 * * * /usr/bin/nightly.sh
# another comment
* * * * * /usr/bin/minutely.sh
"""
    entries = parse_crontab(content, server="srv-01")
    assert len(entries) == 3
    assert all(e.server == "srv-01" for e in entries)


def test_parse_crontab_fields_mapping():
    line = "5 4 1 1 0 /usr/bin/newyear.sh"
    entry = parse_line(line)
    assert entry.fields["minute"] == "5"
    assert entry.fields["hour"] == "4"
    assert entry.fields["day_of_month"] == "1"
    assert entry.fields["month"] == "1"
    assert entry.fields["day_of_week"] == "0"
