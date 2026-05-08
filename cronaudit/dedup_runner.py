"""High-level runner that integrates deduplication into the audit pipeline."""
from dataclasses import dataclass, field
from typing import List, Optional
from cronaudit.collector import ServerCrontab
from cronaudit.deduplicator import (
    DeduplicationResult,
    find_duplicates,
    format_duplicates,
)


@dataclass
class DedupRunConfig:
    """Configuration for a deduplication run."""
    cross_server: bool = True
    include_user: bool = True
    output_path: Optional[str] = None


@dataclass
class DedupRunResult:
    """Outcome of running deduplication over a set of server crontabs."""
    config: DedupRunConfig
    dedup: DeduplicationResult
    written_to: Optional[str] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def summary_line(self) -> str:
        d = self.dedup
        return (
            f"Servers: {len(set(s for g in d.groups for s, _ in g.entries))} | "
            f"Total entries: {d.total_entries} | "
            f"Duplicates: {d.duplicate_count}"
        )


def run_deduplication(
    crontabs: List[ServerCrontab],
    config: Optional[DedupRunConfig] = None,
) -> DedupRunResult:
    """Run deduplication and optionally write a report to disk."""
    if config is None:
        config = DedupRunConfig()

    try:
        result = find_duplicates(
            crontabs,
            cross_server=config.cross_server,
            include_user=config.include_user,
        )
    except Exception as exc:  # pragma: no cover
        return DedupRunResult(config=config, dedup=DeduplicationResult(), error=str(exc))

    written_to: Optional[str] = None
    if config.output_path:
        try:
            report_text = format_duplicates(result)
            with open(config.output_path, "w", encoding="utf-8") as fh:
                fh.write(report_text)
            written_to = config.output_path
        except OSError as exc:
            return DedupRunResult(config=config, dedup=result, error=str(exc))

    return DedupRunResult(config=config, dedup=result, written_to=written_to)
