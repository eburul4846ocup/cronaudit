"""Collector module for gathering crontab entries from multiple servers."""

import subprocess
import shlex
from dataclasses import dataclass, field
from typing import List, Optional

from cronaudit.parser import CronEntry, parse_crontab


@dataclass
class ServerCrontab:
    """Holds parsed crontab entries for a single server."""

    hostname: str
    entries: List[CronEntry] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def is_ok(self) -> bool:
        return self.error is None


def collect_local(hostname: str = "localhost") -> ServerCrontab:
    """Collect crontab entries from the local machine via crontab -l."""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0 and "no crontab for" in result.stderr.lower():
            return ServerCrontab(hostname=hostname, entries=[])
        if result.returncode != 0:
            return ServerCrontab(hostname=hostname, error=result.stderr.strip())
        entries = parse_crontab(result.stdout)
        return ServerCrontab(hostname=hostname, entries=entries)
    except FileNotFoundError:
        return ServerCrontab(hostname=hostname, error="crontab command not found")
    except subprocess.TimeoutExpired:
        return ServerCrontab(hostname=hostname, error="command timed out")


def collect_remote(hostname: str, ssh_user: Optional[str] = None, timeout: int = 15) -> ServerCrontab:
    """Collect crontab entries from a remote server over SSH."""
    target = f"{ssh_user}@{hostname}" if ssh_user else hostname
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", target, "crontab -l"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0 and "no crontab for" in result.stderr.lower():
            return ServerCrontab(hostname=hostname, entries=[])
        if result.returncode != 0:
            return ServerCrontab(hostname=hostname, error=result.stderr.strip())
        entries = parse_crontab(result.stdout)
        return ServerCrontab(hostname=hostname, entries=entries)
    except FileNotFoundError:
        return ServerCrontab(hostname=hostname, error="ssh command not found")
    except subprocess.TimeoutExpired:
        return ServerCrontab(hostname=hostname, error=f"SSH connection to {hostname} timed out")


def collect_from_file(hostname: str, filepath: str) -> ServerCrontab:
    """Load crontab entries from a local file (useful for auditing exports)."""
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            content = fh.read()
        entries = parse_crontab(content)
        return ServerCrontab(hostname=hostname, entries=entries)
    except OSError as exc:
        return ServerCrontab(hostname=hostname, error=str(exc))
