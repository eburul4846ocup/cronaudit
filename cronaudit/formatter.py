"""Output formatters for cronaudit reports (text, JSON, CSV)."""

import csv
import json
import io
from typing import List

from cronaudit.multi import AuditResult


def to_text(result: AuditResult) -> str:
    """Format an AuditResult as a human-readable text report."""
    lines = []
    lines.append("=" * 60)
    lines.append("CRON AUDIT REPORT")
    lines.append("=" * 60)
    lines.append(f"Servers audited : {result.total()}")
    lines.append(f"Successful      : {result.successful()}")
    lines.append(f"Failed          : {result.failed()}")
    lines.append(f"Total entries   : {result.total_entries()}")
    lines.append("")

    for sc in result.server_crontabs:
        status = "OK" if sc.is_ok() else "ERROR"
        lines.append(f"[{status}] {sc.server}")
        if sc.error:
            lines.append(f"  Error: {sc.error}")
        else:
            for entry in sc.entries:
                lines.append(f"  {entry.schedule:<25} {entry.command}")
        lines.append("")

    return "\n".join(lines)


def to_json(result: AuditResult) -> str:
    """Format an AuditResult as a JSON string."""
    data = {
        "summary": {
            "total_servers": result.total(),
            "successful": result.successful(),
            "failed": result.failed(),
            "total_entries": result.total_entries(),
        },
        "servers": [],
    }

    for sc in result.server_crontabs:
        server_data = {
            "server": sc.server,
            "ok": sc.is_ok(),
            "error": sc.error,
            "entries": [
                {
                    "schedule": e.schedule,
                    "command": e.command,
                    "comment": e.comment,
                    "raw": e.raw,
                }
                for e in sc.entries
            ],
        }
        data["servers"].append(server_data)

    return json.dumps(data, indent=2)


def to_csv(result: AuditResult) -> str:
    """Format an AuditResult as CSV rows (server, schedule, command, comment)."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["server", "schedule", "command", "comment", "error"])

    for sc in result.server_crontabs:
        if not sc.is_ok():
            writer.writerow([sc.server, "", "", "", sc.error])
        else:
            for entry in sc.entries:
                writer.writerow(
                    [sc.server, entry.schedule, entry.command, entry.comment or "", ""]
                )

    return output.getvalue()
