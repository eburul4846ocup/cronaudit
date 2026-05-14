"""Format GroupingResult into human-readable text or JSON."""
from __future__ import annotations
import json
from typing import List
from cronaudit.grouper import GroupingResult, EntryGroup


def _group_to_dict(group: EntryGroup) -> dict:
    return {
        "key": group.key,
        "count": group.count,
        "servers": group.servers,
        "entries": [
            {
                "server": server,
                "schedule": e.special or e.schedule,
                "command": e.command,
                "user": e.user,
                "comment": e.comment,
            }
            for server, e in group.entries
        ],
    }


def group_to_text(result: GroupingResult, show_entries: bool = True) -> str:
    """Render a GroupingResult as plain text."""
    lines: List[str] = [
        f"=== Cron Grouping by '{result.by}' ===",
        f"Groups: {result.group_count}  |  Total entries: {result.total_entries}",
        "",
    ]
    for key in sorted(result.groups):
        group = result.groups[key]
        lines.append(f"[{key}]  ({group.count} entries, servers: {', '.join(group.servers)})")
        if show_entries:
            for server, entry in group.entries:
                sched = entry.special or entry.schedule or ""
                lines.append(f"  {server:20s}  {sched:25s}  {entry.command or ''}")
        lines.append("")
    return "\n".join(lines)


def group_to_json(result: GroupingResult) -> str:
    """Render a GroupingResult as a JSON string."""
    payload = {
        "by": result.by,
        "group_count": result.group_count,
        "total_entries": result.total_entries,
        "groups": [_group_to_dict(result.groups[k]) for k in sorted(result.groups)],
    }
    return json.dumps(payload, indent=2)
