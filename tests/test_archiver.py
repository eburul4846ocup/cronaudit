"""Tests for cronaudit.archiver."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from cronaudit.archiver import (
    ArchiveEntry,
    create_archive,
    extract_archive,
    list_archives,
)


def _write_files(tmp_path: Path, names: list) -> list:
    paths = []
    for name in names:
        p = tmp_path / name
        p.write_text(f"content of {name}")
        paths.append(str(p))
    return paths


# ---------------------------------------------------------------------------
# create_archive
# ---------------------------------------------------------------------------

def test_create_archive_returns_zip_path(tmp_path):
    files = _write_files(tmp_path / "src", ["report.txt"])
    arc = create_archive(files, archive_dir=str(tmp_path / "arc"))
    assert arc.endswith(".zip")
    assert Path(arc).exists()


def test_create_archive_contains_files(tmp_path):
    files = _write_files(tmp_path / "src", ["a.txt", "b.json"])
    arc = create_archive(files, archive_dir=str(tmp_path / "arc"))
    with zipfile.ZipFile(arc) as zf:
        names = zf.namelist()
    assert "a.txt" in names
    assert "b.json" in names


def test_create_archive_with_label(tmp_path):
    files = _write_files(tmp_path / "src", ["r.txt"])
    arc = create_archive(files, archive_dir=str(tmp_path), label="weekly")
    assert "weekly" in Path(arc).name


def test_create_archive_missing_file_ignored(tmp_path):
    arc = create_archive(
        ["/nonexistent/ghost.txt"],
        archive_dir=str(tmp_path),
    )
    with zipfile.ZipFile(arc) as zf:
        assert zf.namelist() == []


def test_create_archive_creates_dir(tmp_path):
    nested = tmp_path / "x" / "y"
    files = _write_files(tmp_path, ["f.csv"])
    create_archive(files, archive_dir=str(nested))
    assert nested.is_dir()


# ---------------------------------------------------------------------------
# list_archives
# ---------------------------------------------------------------------------

def test_list_archives_empty(tmp_path):
    assert list_archives(str(tmp_path)) == []


def test_list_archives_finds_archives(tmp_path):
    files = _write_files(tmp_path / "src", ["r.txt"])
    create_archive(files, archive_dir=str(tmp_path))
    entries = list_archives(str(tmp_path))
    assert len(entries) == 1
    assert isinstance(entries[0], ArchiveEntry)


def test_list_archives_entry_fields(tmp_path):
    files = _write_files(tmp_path / "src", ["r.txt"])
    create_archive(files, archive_dir=str(tmp_path))
    entry = list_archives(str(tmp_path))[0]
    assert entry.name.endswith(".zip")
    assert entry.size_bytes > 0
    assert "T" in entry.created_at


# ---------------------------------------------------------------------------
# extract_archive
# ---------------------------------------------------------------------------

def test_extract_archive_restores_files(tmp_path):
    src = _write_files(tmp_path / "src", ["data.txt"])
    arc = create_archive(src, archive_dir=str(tmp_path / "arc"))
    extracted = extract_archive(arc, dest_dir=str(tmp_path / "out"))
    assert any("data.txt" in e for e in extracted)
    assert Path(extracted[0]).exists()


def test_extract_archive_returns_paths(tmp_path):
    src = _write_files(tmp_path / "src", ["a.csv", "b.txt"])
    arc = create_archive(src, archive_dir=str(tmp_path / "arc"))
    extracted = extract_archive(arc, dest_dir=str(tmp_path / "out"))
    assert len(extracted) == 2
