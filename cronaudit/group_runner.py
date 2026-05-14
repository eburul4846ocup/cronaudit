"""High-level runner that groups entries and produces a formatted summary."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from cronaudit.collector import ServerCrontab
from cronaudit.grouper import GroupingResult, group_by


@dataclass
class GroupRunConfig:
    by: str = "schedule"
    command_words: int = 1
    min_group_size: int = 1


@dataclass
class GroupRunResult:
    config: GroupRunConfig
    result: Optional[GroupingResult] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.result is not None

    def summary_line(self) -> str:
        if not self.ok:
            return f"Grouping failed: {self.error}"
        assert self.result is not None
        return (
            f"Grouped by '{self.result.by}': "
            f"{self.result.group_count} groups, "
            f"{self.result.total_entries} entries"
        )


def run_grouping(
    crontabs: List[ServerCrontab],
    config: Optional[GroupRunConfig] = None,
) -> GroupRunResult:
    """Run grouping over a list of ServerCrontab objects."""
    cfg = config or GroupRunConfig()
    try:
        raw = group_by(crontabs, by=cfg.by, command_words=cfg.command_words)
        # Filter out groups smaller than min_group_size
        if cfg.min_group_size > 1:
            raw.groups = {
                k: v for k, v in raw.groups.items() if v.count >= cfg.min_group_size
            }
        return GroupRunResult(config=cfg, result=raw)
    except Exception as exc:  # noqa: BLE001
        return GroupRunResult(config=cfg, error=str(exc))
