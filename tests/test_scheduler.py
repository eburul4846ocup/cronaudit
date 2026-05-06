"""Tests for cronaudit.scheduler."""

import pytest
from cronaudit.scheduler import describe_schedule, ScheduleInfo


def test_describe_daily_special():
    info = describe_schedule("@daily")
    assert info.is_special is True
    assert "midnight" in info.description.lower() or "day" in info.description.lower()
    assert info.expanded == "0 0 * * *"


def test_describe_reboot_has_no_expansion():
    info = describe_schedule("@reboot")
    assert info.is_special is True
    assert info.expanded is None
    assert "reboot" in info.description.lower()


def test_describe_hourly_special():
    info = describe_schedule("@hourly")
    assert info.is_special is True
    assert info.expanded == "0 * * * *"


def test_describe_every_minute():
    info = describe_schedule("* * * * *")
    assert info.is_special is False
    assert "every minute" in info.description.lower()


def test_describe_specific_time():
    info = describe_schedule("30 14 * * *")
    assert "14:30" in info.description


def test_describe_with_dom():
    info = describe_schedule("0 0 1 * *")
    assert "day 1" in info.description


def test_describe_with_month():
    info = describe_schedule("0 0 * 6 *")
    assert "month 6" in info.description


def test_describe_invalid_expression():
    info = describe_schedule("bad expression here")
    assert info.is_special is False
    assert "invalid" in info.description.lower()


def test_describe_returns_schedule_info():
    info = describe_schedule("0 12 * * 1")
    assert isinstance(info, ScheduleInfo)
    assert info.raw == "0 12 * * 1"
