"""Tests for cronaudit.notifier."""

from unittest.mock import MagicMock, patch
from cronaudit.notifier import (
    NotificationConfig,
    NotificationResult,
    should_notify,
    build_subject,
    build_body,
    send_notification,
)
from cronaudit.multi import AuditResult
from cronaudit.parser import CronEntry


def _ok_result(server: str = "web1") -> AuditResult:
    entry = CronEntry(
        raw="* * * * * root /bin/true",
        schedule="* * * * *",
        user="root",
        command="/bin/true",
    )
    return AuditResult(server=server, entries=[entry], error=None)


def _fail_result(server: str = "db1") -> AuditResult:
    return AuditResult(server=server, entries=[], error="Connection refused")


# --- should_notify ---

def test_should_notify_when_enough_failures():
    config = NotificationConfig(email_to=["ops@example.com"], min_failed_servers=1)
    assert should_notify([_ok_result(), _fail_result()], config) is True


def test_should_not_notify_when_all_ok():
    config = NotificationConfig(email_to=["ops@example.com"], min_failed_servers=1)
    assert should_notify([_ok_result(), _ok_result()], config) is False


def test_should_not_notify_below_threshold():
    config = NotificationConfig(email_to=["ops@example.com"], min_failed_servers=2)
    assert should_notify([_ok_result(), _fail_result()], config) is False


# --- build_subject ---

def test_build_subject_all_ok():
    subject = build_subject([_ok_result(), _ok_result()])
    assert "OK" in subject
    assert "2" in subject


def test_build_subject_with_failures():
    subject = build_subject([_ok_result(), _fail_result()])
    assert "ALERT" in subject
    assert "1/2" in subject


# --- build_body ---

def test_build_body_contains_server_names():
    body = build_body([_ok_result("web1"), _fail_result("db1")])
    assert "web1" in body
    assert "db1" in body


def test_build_body_shows_error_reason():
    body = build_body([_fail_result()])
    assert "Connection refused" in body


def test_build_body_shows_entry_count_when_summary_enabled():
    body = build_body([_ok_result()], include_summary=True)
    assert "Entries:" in body


def test_build_body_hides_entry_count_when_summary_disabled():
    body = build_body([_ok_result()], include_summary=False)
    assert "Entries:" not in body


# --- send_notification ---

def test_send_notification_no_recipients():
    config = NotificationConfig(email_to=[])
    result = send_notification([_fail_result()], config)
    assert result.sent is False
    assert "No recipients" in (result.error or "")


def test_send_notification_below_threshold_not_sent():
    config = NotificationConfig(email_to=["ops@example.com"], min_failed_servers=5)
    result = send_notification([_fail_result()], config)
    assert result.sent is False
    assert result.error is None


def test_send_notification_success():
    config = NotificationConfig(email_to=["ops@example.com", "dev@example.com"])
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = lambda s: s
    mock_smtp.__exit__ = MagicMock(return_value=False)
    factory = MagicMock(return_value=mock_smtp)

    result = send_notification([_fail_result()], config, _smtp_factory=factory)
    assert result.sent is True
    assert result.recipient_count == 2
    mock_smtp.sendmail.assert_called_once()


def test_send_notification_smtp_error():
    config = NotificationConfig(email_to=["ops@example.com"])
    factory = MagicMock(side_effect=OSError("Connection refused"))
    result = send_notification([_fail_result()], config, _smtp_factory=factory)
    assert result.sent is False
    assert result.error is not None


def test_notification_result_bool_true():
    assert bool(NotificationResult(sent=True, recipient_count=1)) is True


def test_notification_result_bool_false():
    assert bool(NotificationResult(sent=False, recipient_count=0)) is False
