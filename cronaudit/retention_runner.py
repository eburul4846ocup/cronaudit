"""High-level runner that applies retention to snapshot and archive directories."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cronaudit.retention import RetentionPolicy, RetentionResult, apply_retention


@dataclass
class RetentionRunConfig:
    snapshot_dir: Optional[Path] = None
    archive_dir: Optional[Path] = None
    max_age_days: int = 30
    max_count: int = 50
    dry_run: bool = False


@dataclass
class RetentionRunResult:
    snapshots: RetentionResult
    archives: RetentionResult

    @property
    def total_removed(self) -> int:
        return self.snapshots.removed_count + self.archives.removed_count

    @property
    def total_kept(self) -> int:
        return self.snapshots.kept_count + self.archives.kept_count

    def __bool__(self) -> bool:
        return bool(self.snapshots) and bool(self.archives)

    def summary(self) -> str:
        lines = [
            f"Retention run ({'dry-run' if not bool(self) else 'live'}):",
            f"  Snapshots — removed: {self.snapshots.removed_count}, "
            f"kept: {self.snapshots.kept_count}, "
            f"errors: {len(self.snapshots.errors)}",
            f"  Archives  — removed: {self.archives.removed_count}, "
            f"kept: {self.archives.kept_count}, "
            f"errors: {len(self.archives.errors)}",
            f"  Total removed: {self.total_removed}",
        ]
        return "\n".join(lines)


def run_retention(config: RetentionRunConfig) -> RetentionRunResult:
    """Apply retention policy to snapshot and archive directories."""
    policy = RetentionPolicy(
        max_age_days=config.max_age_days,
        max_count=config.max_count,
        dry_run=config.dry_run,
    )

    snap_result = (
        apply_retention(config.snapshot_dir, policy)
        if config.snapshot_dir
        else RetentionResult()
    )
    arch_result = (
        apply_retention(config.archive_dir, policy)
        if config.archive_dir
        else RetentionResult()
    )

    return RetentionRunResult(snapshots=snap_result, archives=arch_result)
