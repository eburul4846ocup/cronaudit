"""Filter and search utilities for cron entries across audit results."""

from dataclasses import dataclass, field
from typing import List, Optional, Callable
from cronaudit.parser import CronEntry
from cronaudit.multi import AuditResult


@dataclass
class FilterCriteria:
    """Criteria used to filter cron entries."""
    server: Optional[str] = None
    command_contains: Optional[str] = None
    user: Optional[str] = None
    schedule: Optional[str] = None
    has_comment: Optional[bool] = None


def _matches(entry: CronEntry, server: str, criteria: FilterCriteria) -> bool:
    """Return True if the entry matches all specified criteria."""
    if criteria.server and criteria.server.lower() not in server.lower():
        return False
    if criteria.command_contains:
        if criteria.command_contains.lower() not in entry.command.lower():
            return False
    if criteria.user and entry.user:
        if criteria.user.lower() not in entry.user.lower():
            return False
    if criteria.schedule:
        raw = entry.raw_schedule or ""
        if criteria.schedule.lower() not in raw.lower():
            return False
    if criteria.has_comment is not None:
        has = bool(entry.comment)
        if has != criteria.has_comment:
            return False
    return True


def filter_results(
    results: List[AuditResult],
    criteria: FilterCriteria,
) -> List[AuditResult]:
    """Return new AuditResult list with entries filtered by criteria."""
    from cronaudit.multi import AuditResult as AR
    filtered = []
    for result in results:
        if result.error:
            filtered.append(result)
            continue
        matching = [
            e for e in result.entries
            if _matches(e, result.server, criteria)
        ]
        filtered.append(
            AR(server=result.server, entries=matching, error=result.error)
        )
    return filtered


def search_command(results: List[AuditResult], keyword: str) -> List[AuditResult]:
    """Convenience wrapper: filter by command keyword."""
    return filter_results(results, FilterCriteria(command_contains=keyword))


def filter_by_server(results: List[AuditResult], server_name: str) -> List[AuditResult]:
    """Convenience wrapper: filter to a specific server."""
    return filter_results(results, FilterCriteria(server=server_name))
