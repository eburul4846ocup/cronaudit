"""Multi-server collection and aggregated reporting utilities."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from cronaudit.collector import ServerCrontab, collect_remote
from cronaudit.report import generate_report


@dataclass
class AuditConfig:
    """Configuration for a multi-server audit run."""

    hostnames: List[str]
    ssh_user: Optional[str] = None
    max_workers: int = 5
    timeout: int = 15


@dataclass
class AuditResult:
    """Aggregated results from auditing multiple servers."""

    results: Dict[str, ServerCrontab] = field(default_factory=dict)

    @property
    def successful(self) -> List[ServerCrontab]:
        return [r for r in self.results.values() if r.is_ok]

    @property
    def failed(self) -> List[ServerCrontab]:
        return [r for r in self.results.values() if not r.is_ok]

    @property
    def total_entries(self) -> int:
        return sum(len(r.entries) for r in self.successful)


def audit_servers(
    config: AuditConfig,
    collector: Optional[Callable[[str, Optional[str], int], ServerCrontab]] = None,
) -> AuditResult:
    """Run crontab collection across all configured servers in parallel."""
    if collector is None:
        collector = collect_remote

    audit = AuditResult()

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        future_to_host = {
            executor.submit(collector, host, config.ssh_user, config.timeout): host
            for host in config.hostnames
        }
        for future in as_completed(future_to_host):
            host = future_to_host[future]
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                result = ServerCrontab(hostname=host, error=str(exc))
            audit.results[host] = result

    return audit


def generate_multi_report(audit: AuditResult) -> str:
    """Produce a combined human-readable report for all servers."""
    lines: List[str] = []
    lines.append("=" * 60)
    lines.append("CRONAUDIT MULTI-SERVER REPORT")
    lines.append(f"Servers audited : {len(audit.results)}")
    lines.append(f"Successful      : {len(audit.successful)}")
    lines.append(f"Failed          : {len(audit.failed)}")
    lines.append(f"Total entries   : {audit.total_entries}")
    lines.append("=" * 60)

    for server in sorted(audit.successful, key=lambda s: s.hostname):
        lines.append(f"\n[ {server.hostname} ] ({len(server.entries)} entries)")
        lines.append("-" * 40)
        if server.entries:
            lines.append(generate_report(server.entries))
        else:
            lines.append("  (no crontab entries)")

    if audit.failed:
        lines.append("\n[ ERRORS ]")
        lines.append("-" * 40)
        for server in sorted(audit.failed, key=lambda s: s.hostname):
            lines.append(f"  {server.hostname}: {server.error}")

    return "\n".join(lines)
