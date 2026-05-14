"""Track and compare entry counts across snapshots to identify trends."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TrendPoint:
    label: str
    server_count: int
    entry_count: int
    failed_servers: int


@dataclass
class TrendReport:
    points: List[TrendPoint] = field(default_factory=list)

    @property
    def latest(self) -> Optional[TrendPoint]:
        return self.points[-1] if self.points else None

    @property
    def earliest(self) -> Optional[TrendPoint]:
        return self.points[0] if self.points else None

    def entry_delta(self) -> Optional[int]:
        """Return change in entry count from earliest to latest point."""
        if len(self.points) < 2:
            return None
        return self.latest.entry_count - self.earliest.entry_count

    def server_delta(self) -> Optional[int]:
        """Return change in server count from earliest to latest point."""
        if len(self.points) < 2:
            return None
        return self.latest.server_count - self.earliest.server_count


def build_trend_point(label: str, data: Dict) -> TrendPoint:
    """Build a TrendPoint from a snapshot metadata dict."""
    return TrendPoint(
        label=label,
        server_count=data.get("server_count", 0),
        entry_count=data.get("entry_count", 0),
        failed_servers=data.get("failed_servers", 0),
    )


def build_trend(snapshots: List[Dict]) -> TrendReport:
    """Build a TrendReport from a list of snapshot metadata dicts.

    Each dict must have keys: 'label', 'server_count', 'entry_count', 'failed_servers'.
    """
    points = [
        build_trend_point(s["label"], s)
        for s in snapshots
        if "label" in s
    ]
    return TrendReport(points=points)


def format_trend(report: TrendReport) -> str:
    """Render a TrendReport as a human-readable string."""
    if not report.points:
        return "No trend data available."

    lines = ["Trend Report", "============"]
    for p in report.points:
        lines.append(
            f"  [{p.label}] servers={p.server_count}  entries={p.entry_count}  "
            f"failed={p.failed_servers}"
        )

    e_delta = report.entry_delta()
    s_delta = report.server_delta()
    if e_delta is not None:
        sign = "+" if e_delta >= 0 else ""
        lines.append(f"\nEntry delta  : {sign}{e_delta}")
    if s_delta is not None:
        sign = "+" if s_delta >= 0 else ""
        lines.append(f"Server delta : {sign}{s_delta}")

    return "\n".join(lines)
