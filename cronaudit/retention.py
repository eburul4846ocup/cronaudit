"""Retention policy for snapshots and archives."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple


@dataclass
class RetentionPolicy:
    """Defines how long snapshots/archives should be kept."""
    max_age_days: int = 30
    max_count: int = 50
    dry_run: bool = False


@dataclass
class RetentionResult:
    removed: List[Path] = field(default_factory=list)
    kept: List[Path] = field(default_factory=list)
    errors: List[Tuple[Path, str]] = field(default_factory=list)

    @property
    def removed_count(self) -> int:
        return len(self.removed)

    @property
    def kept_count(self) -> int:
        return len(self.kept)

    def __bool__(self) -> bool:
        return len(self.errors) == 0


def _file_age_days(path: Path) -> float:
    mtime = path.stat().st_mtime
    age = datetime.now() - datetime.fromtimestamp(mtime)
    return age.total_seconds() / 86400


def apply_retention(directory: Path, policy: RetentionPolicy) -> RetentionResult:
    """Apply retention policy to files in *directory*.

    Files are removed if they exceed *max_age_days* OR if the total count
    exceeds *max_count* (oldest files pruned first).
    """
    result = RetentionResult()

    if not directory.exists():
        return result

    files = sorted(
        [p for p in directory.iterdir() if p.is_file()],
        key=lambda p: p.stat().st_mtime,
    )

    cutoff = datetime.now() - timedelta(days=policy.max_age_days)

    to_remove: List[Path] = []
    for f in files:
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < cutoff:
            to_remove.append(f)

    remaining = [f for f in files if f not in to_remove]
    if len(remaining) > policy.max_count:
        excess = len(remaining) - policy.max_count
        to_remove.extend(remaining[:excess])

    for path in to_remove:
        try:
            if not policy.dry_run:
                path.unlink()
            result.removed.append(path)
        except OSError as exc:
            result.errors.append((path, str(exc)))

    result.kept = [f for f in files if f not in to_remove]
    return result
