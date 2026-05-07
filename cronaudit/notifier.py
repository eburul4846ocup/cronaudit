"""Notification module for cronaudit — sends alerts when audits detect issues."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronaudit.multi import AuditResult


@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    email_to: List[str] = field(default_factory=list)
    email_from: str = "cronaudit@localhost"
    smtp_host: str = "localhost"
    smtp_port: int = 25
    min_failed_servers: int = 1
    include_summary: bool = True


@dataclass
class NotificationResult:
    """Result of a notification attempt."""
    sent: bool
    recipient_count: int
    error: Optional[str] = None

    def __bool__(self) -> bool:
        return self.sent


def should_notify(results: List[AuditResult], config: NotificationConfig) -> bool:
    """Return True if the audit results warrant sending a notification."""
    failed = sum(1 for r in results if r.error is not None)
    return failed >= config.min_failed_servers


def build_subject(results: List[AuditResult]) -> str:
    """Build an email subject line summarising audit results."""
    total = len(results)
    failed = sum(1 for r in results if r.error is not None)
    if failed == 0:
        return f"[cronaudit] Audit OK — {total} server(s) checked"
    return f"[cronaudit] Audit ALERT — {failed}/{total} server(s) failed"


def build_body(results: List[AuditResult], include_summary: bool = True) -> str:
    """Build a plain-text email body from audit results."""
    lines: List[str] = ["cronaudit report", "=" * 40, ""]
    for r in results:
        status = "ERROR" if r.error else "OK"
        lines.append(f"  {r.server}: {status}")
        if r.error:
            lines.append(f"    Reason: {r.error}")
        elif include_summary:
            lines.append(f"    Entries: {len(r.entries)}")
    lines.append("")
    return "\n".join(lines)


def send_notification(
    results: List[AuditResult],
    config: NotificationConfig,
    _smtp_factory=None,
) -> NotificationResult:
    """Send an email notification if thresholds are met.

    _smtp_factory is injectable for testing; defaults to smtplib.SMTP.
    """
    if not config.email_to:
        return NotificationResult(sent=False, recipient_count=0, error="No recipients configured")

    if not should_notify(results, config):
        return NotificationResult(sent=False, recipient_count=0)

    subject = build_subject(results)
    body = build_body(results, config.include_summary)
    message = f"From: {config.email_from}\nTo: {', '.join(config.email_to)}\nSubject: {subject}\n\n{body}"

    if _smtp_factory is None:
        import smtplib
        _smtp_factory = smtplib.SMTP

    try:
        with _smtp_factory(config.smtp_host, config.smtp_port) as smtp:
            smtp.sendmail(config.email_from, config.email_to, message)
        return NotificationResult(sent=True, recipient_count=len(config.email_to))
    except Exception as exc:  # noqa: BLE001
        return NotificationResult(sent=False, recipient_count=0, error=str(exc))
