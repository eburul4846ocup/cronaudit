"""Tests for cronaudit.retention."""
import time
from pathlib import Path

import pytest

from cronaudit.retention import RetentionPolicy, RetentionResult, apply_retention


def _touch(path: Path, age_days: float = 0) -> Path:
    path.write_text("data")
    if age_days:
        mtime = time.time() - age_days * 86400
        import os
        os.utime(path, (mtime, mtime))
    return path


def test_empty_directory_returns_empty_result(tmp_path):
    result = apply_retention(tmp_path, RetentionPolicy())
    assert result.removed_count == 0
    assert result.kept_count == 0
    assert bool(result) is True


def test_missing_directory_returns_empty_result(tmp_path):
    missing = tmp_path / "nonexistent"
    result = apply_retention(missing, RetentionPolicy())
    assert result.removed_count == 0


def test_old_files_are_removed(tmp_path):
    _touch(tmp_path / "old.snap", age_days=40)
    _touch(tmp_path / "new.snap", age_days=1)
    policy = RetentionPolicy(max_age_days=30, max_count=100)
    result = apply_retention(tmp_path, policy)
    assert result.removed_count == 1
    assert result.removed[0].name == "old.snap"
    assert result.kept_count == 1


def test_excess_files_pruned_by_count(tmp_path):
    for i in range(5):
        _touch(tmp_path / f"snap_{i:02d}.snap", age_days=i + 1)
    policy = RetentionPolicy(max_age_days=365, max_count=3)
    result = apply_retention(tmp_path, policy)
    assert result.removed_count == 2
    assert result.kept_count == 3


def test_dry_run_does_not_delete(tmp_path):
    _touch(tmp_path / "old.snap", age_days=60)
    policy = RetentionPolicy(max_age_days=30, dry_run=True)
    result = apply_retention(tmp_path, policy)
    assert result.removed_count == 1
    assert (tmp_path / "old.snap").exists()


def test_no_files_removed_when_within_limits(tmp_path):
    for i in range(3):
        _touch(tmp_path / f"snap_{i}.snap", age_days=1)
    policy = RetentionPolicy(max_age_days=30, max_count=10)
    result = apply_retention(tmp_path, policy)
    assert result.removed_count == 0
    assert result.kept_count == 3


def test_result_bool_false_on_errors():
    result = RetentionResult()
    result.errors.append((Path("/fake"), "permission denied"))
    assert bool(result) is False


def test_both_age_and_count_applied(tmp_path):
    _touch(tmp_path / "very_old.snap", age_days=90)
    for i in range(6):
        _touch(tmp_path / f"recent_{i}.snap", age_days=2)
    policy = RetentionPolicy(max_age_days=30, max_count=4)
    result = apply_retention(tmp_path, policy)
    names = [p.name for p in result.removed]
    assert "very_old.snap" in names
    assert result.kept_count == 4
