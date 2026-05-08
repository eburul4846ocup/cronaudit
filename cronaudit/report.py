"""Report generation module for cronaudit."""

from typing import List, Optional
from cronaudit.parser import CronEntry


def format_entry(entry: CronEntry, show_server: bool = True) -> str:
    """Format a single CronEntry into a readable string."""
    parts = []

    if show_server and entry.server:
        parts.append(f"[{entry.server}]")

    if entry.user:
        parts.append(f"user={entry.user}")

    if not entry.is_valid:
        parts.append(f"INVALID({entry.error})")
        parts.append(f"raw={entry.raw.strip()!r}")
        return " | ".join(parts)

    if entry.is_special:
        schedule_str = f"{entry.schedule} ({entry.special_description})"
    else:
        schedule_str = entry.schedule

    parts.append(f"schedule={schedule_str!r}")
    parts.append(f"cmd={entry.command!r}")

    if entry.comment:
        parts.append(f"# {entry.comment}")

    return " | ".join(parts)


def summarize_entries(entries: List[CronEntry]) -> str:
    """Return a short summary string for a list of CronEntry objects."""
    total = len(entries)
    valid = sum(1 for e in entries if e.is_valid)
    invalid = total - valid
    servers = len(set(e.server or "(local)" for e in entries))
    return (
        f"{total} entries ({valid} valid, {invalid} invalid) "
        f"across {servers} server(s)"
    )


def generate_report(
    entries: List[CronEntry],
    title: str = "Crontab Audit Report",
    show_invalid: bool = True,
) -> str:
    """Generate a full text report from a list of CronEntry objects."""
    lines = []
    lines.append("=" * 60)
    lines.append(title)
    lines.append("=" * 60)

    servers = sorted(set(e.server or "(local)" for e in entries))

    valid_entries = [e for e in entries if e.is_valid]
    invalid_entries = [e for e in entries if not e.is_valid]

    lines.append(f"Total entries : {len(entries)}")
    lines.append(f"Valid         : {len(valid_entries)}")
    lines.append(f"Invalid       : {len(invalid_entries)}")
    lines.append(f"Servers       : {len(servers)}")
    lines.append("")

    for server in servers:
        lines.append(f"--- {server} ---")
        server_entries = [e for e in entries if (e.server or "(local)") == server]
        for entry in server_entries:
            if not entry.is_valid and not show_invalid:
                continue
            lines.append("  " + format_entry(entry, show_server=False))
        lines.append("")

    if invalid_entries and show_invalid:
        lines.append("=" * 60)
        lines.append("INVALID ENTRIES")
        lines.append("=" * 60)
        for entry in invalid_entries:
            lines.append("  " + format_entry(entry))
        lines.append("")

    return "\n".join(lines)
