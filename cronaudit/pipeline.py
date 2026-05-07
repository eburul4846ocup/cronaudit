"""Audit pipeline — orchestrates collection, filtering, notification and hooks."""

from dataclasses import dataclass, field
from typing import List, Optional

from cronaudit.multi import AuditResult
from cronaudit.filter import FilterCriteria, filter_results
from cronaudit.notifier import NotificationConfig, NotificationResult, send_notification
from cronaudit.hooks import HookRegistry, EVENT_PRE_AUDIT, EVENT_POST_AUDIT, EVENT_ON_ERROR


@dataclass
class PipelineConfig:
    """Top-level configuration for a pipeline run."""
    notification: Optional[NotificationConfig] = None
    criteria: Optional[FilterCriteria] = None
    hooks: HookRegistry = field(default_factory=HookRegistry)


@dataclass
class PipelineResult:
    """Aggregated output of a pipeline run."""
    results: List[AuditResult]
    notification: Optional[NotificationResult] = None

    @property
    def total_servers(self) -> int:
        return len(self.results)

    @property
    def failed_servers(self) -> int:
        return sum(1 for r in self.results if r.error is not None)

    @property
    def total_entries(self) -> int:
        return sum(len(r.entries) for r in self.results)


def run_pipeline(
    raw_results: List[AuditResult],
    config: PipelineConfig,
) -> PipelineResult:
    """Execute the full audit pipeline.

    Steps:
    1. Dispatch pre_audit hook.
    2. Apply optional filter criteria.
    3. Dispatch post_audit hook.
    4. Send notification if configured.
    5. Return PipelineResult.

    If any result carries an error the on_error hook is dispatched for it.
    """
    config.hooks.dispatch(EVENT_PRE_AUDIT, results=raw_results)

    for r in raw_results:
        if r.error:
            config.hooks.dispatch(EVENT_ON_ERROR, server=r.server, error=r.error)

    if config.criteria is not None:
        processed = filter_results(raw_results, config.criteria)
    else:
        processed = list(raw_results)

    config.hooks.dispatch(EVENT_POST_AUDIT, results=processed)

    notif_result: Optional[NotificationResult] = None
    if config.notification is not None:
        notif_result = send_notification(processed, config.notification)

    return PipelineResult(results=processed, notification=notif_result)
