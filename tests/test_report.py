"""Tests for cronaudit.report module."""

import pytest
from cronaudit.parser import parse_crontab
from cronaudit.report import format_entry, generate_report


SAMPLE_CRONTAB = """
@daily /usr/bin/daily.sh # daily cleanup
0 2 * * * /usr/bin/backup.sh
* * /bad entry
"""


def test_format_entry_valid():
    entries = parse_crontab("0 2 * * * /usr/bin/backup.sh", server="web-01")
    assert len(entries) == 1
    result = format_entry(entries[0])
    assert "web-01" in result
    assert "/usr/bin/backup.sh" in result
    assert "0 2 * * *" in result


def test_format_entry_special():
    entries = parse_crontab("@daily /usr/bin/daily.sh", server="db-01")
    result = format_entry(entries[0])
    assert "@daily" in result
    assert "once a day" in result


def test_format_entry_with_comment():
    entries = parse_crontab("0 5 * * * /bin/report.sh # morning report")
    result = format_entry(entries[0], show_server=False)
    assert "morning report" in result


def test_format_entry_invalid():
    entries = parse_crontab("* * bad line")
    result = format_entry(entries[0], show_server=False)
    assert "INVALID" in result


def test_generate_report_structure():
    entries = parse_crontab(SAMPLE_CRONTAB, server="app-01")
    report = generate_report(entries, title="Test Report")
    assert "Test Report" in report
    assert "app-01" in report
    assert "Total entries" in report
    assert "Valid" in report
    assert "Invalid" in report


def test_generate_report_counts():
    entries = parse_crontab(SAMPLE_CRONTAB, server="app-01")
    report = generate_report(entries)
    assert "Total entries : 3" in report
    assert "Valid         : 2" in report
    assert "Invalid       : 1" in report


def test_generate_report_hide_invalid():
    entries = parse_crontab(SAMPLE_CRONTAB, server="app-01")
    report = generate_report(entries, show_invalid=False)
    assert "INVALID ENTRIES" not in report


def test_generate_report_multiple_servers():
    entries_a = parse_crontab("0 1 * * * /bin/a.sh", server="server-a")
    entries_b = parse_crontab("0 2 * * * /bin/b.sh", server="server-b")
    report = generate_report(entries_a + entries_b)
    assert "server-a" in report
    assert "server-b" in report
    assert "Servers       : 2" in report
