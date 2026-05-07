"""Archive and retrieve historical export bundles (zip archives)."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class ArchiveEntry:
    name: str
    path: str
    created_at: str
    size_bytes: int


def create_archive(
    source_files: List[str],
    archive_dir: str = ".",
    label: Optional[str] = None,
) -> str:
    """Zip *source_files* into a timestamped archive and return its path."""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    stem = f"cronaudit_{label}_{ts}" if label else f"cronaudit_{ts}"
    archive_path = Path(archive_dir) / (stem + ".zip")
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fp in source_files:
            p = Path(fp)
            if p.exists():
                zf.write(p, arcname=p.name)

    return str(archive_path)


def list_archives(archive_dir: str = ".") -> List[ArchiveEntry]:
    """Return metadata for every cronaudit zip archive in *archive_dir*."""
    entries: List[ArchiveEntry] = []
    for p in sorted(Path(archive_dir).glob("cronaudit_*.zip")):
        stat = p.stat()
        created = datetime.utcfromtimestamp(stat.st_mtime).strftime("%Y-%m-%dT%H:%M:%SZ")
        entries.append(
            ArchiveEntry(
                name=p.name,
                path=str(p),
                created_at=created,
                size_bytes=stat.st_size,
            )
        )
    return entries


def extract_archive(archive_path: str, dest_dir: str = ".") -> List[str]:
    """Extract *archive_path* into *dest_dir* and return extracted file paths."""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    extracted: List[str] = []
    with zipfile.ZipFile(archive_path, "r") as zf:
        for member in zf.namelist():
            zf.extract(member, path=dest)
            extracted.append(str(dest / member))
    return extracted
