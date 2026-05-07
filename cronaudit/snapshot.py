"""Persist and load ServerCrontab snapshots for later diffing."""

import json
from pathlib import Path
from typing import List, Optional
from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab


def _entry_to_dict(entry: CronEntry) -> dict:
    return {
        "schedule": entry.schedule,
        "command": entry.command,
        "user": entry.user,
        "comment": entry.comment,
        "raw": entry.raw,
    }


def _entry_from_dict(data: dict) -> CronEntry:
    return CronEntry(
        schedule=data.get("schedule", ""),
        command=data.get("command", ""),
        user=data.get("user"),
        comment=data.get("comment"),
        raw=data.get("raw", ""),
    )


def save_snapshot(snapshot: ServerCrontab, path: Path) -> None:
    """Serialize a ServerCrontab to a JSON file.

    Args:
        snapshot: The ServerCrontab instance to persist.
        path:     Destination file path.
    """
    payload = {
        "server": snapshot.server,
        "error": snapshot.error,
        "entries": [_entry_to_dict(e) for e in snapshot.entries],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_snapshot(path: Path) -> ServerCrontab:
    """Deserialize a ServerCrontab from a JSON file.

    Args:
        path: Source file path previously written by save_snapshot.

    Returns:
        Reconstructed ServerCrontab.

    Raises:
        FileNotFoundError: If path does not exist.
        ValueError: If the file cannot be parsed.
    """
    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid snapshot file {path}: {exc}") from exc

    sc = ServerCrontab(server=data.get("server", ""))
    sc.error = data.get("error")
    sc.entries = [_entry_from_dict(e) for e in data.get("entries", [])]
    return sc


def list_snapshots(directory: Path) -> List[Path]:
    """Return sorted list of .json snapshot files in directory."""
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.json"))
