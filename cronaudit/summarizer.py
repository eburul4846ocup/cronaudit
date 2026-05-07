"""Summarize audit results into aggregate statistics."""
from dataclasses import dataclass, field
from typing import Dict, List
from cronaudit.multi import AuditResult


@dataclass
class AuditSummary:
    total_servers: int = 0
    successful_servers: int = 0
    failed_servers: int = 0
    total_entries: int = 0
    entries_per_server: Dict[str, int] = field(default_factory=dict)
    top_commands: List[tuple] = field(default_factory=list)
    special_schedule_count: int = 0
    standard_schedule_count: int = 0


def summarize(results: List[AuditResult]) -> AuditSummary:
    """Produce an AuditSummary from a list of AuditResult objects."""
    summary = AuditSummary()
    summary.total_servers = len(results)

    command_counts: Dict[str, int] = {}

    for result in results:
        if result.error:
            summary.failed_servers += 1
        else:
            summary.successful_servers += 1

        entry_count = len(result.entries)
        summary.total_entries += entry_count
        summary.entries_per_server[result.server] = entry_count

        for entry in result.entries:
            if entry.schedule.startswith("@"):
                summary.special_schedule_count += 1
            else:
                summary.standard_schedule_count += 1

            cmd = entry.command.split()[0] if entry.command else ""
            if cmd:
                command_counts[cmd] = command_counts.get(cmd, 0) + 1

    summary.top_commands = sorted(
        command_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]

    return summary


def format_summary(summary: AuditSummary) -> str:
    """Render an AuditSummary as a human-readable string."""
    lines = [
        "=== Cron Audit Summary ===",
        f"Servers   : {summary.total_servers} total, "
        f"{summary.successful_servers} ok, {summary.failed_servers} failed",
        f"Entries   : {summary.total_entries} total "
        f"({summary.standard_schedule_count} standard, "
        f"{summary.special_schedule_count} special)",
    ]

    if summary.entries_per_server:
        lines.append("Per-server:")
        for server, count in sorted(summary.entries_per_server.items()):
            lines.append(f"  {server}: {count} entries")

    if summary.top_commands:
        lines.append("Top commands:")
        for cmd, count in summary.top_commands:
            lines.append(f"  {cmd}: {count}")

    return "\n".join(lines)
