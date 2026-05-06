"""Tests for the cronaudit.collector module."""

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cronaudit.collector import (
    ServerCrontab,
    collect_from_file,
    collect_local,
    collect_remote,
)


SAMPLE_CRONTAB = textwrap.dedent("""\
    # Daily backup
    0 2 * * * /usr/local/bin/backup.sh
    @reboot /usr/local/bin/startup.sh
""")


class TestServerCrontab:
    def test_is_ok_when_no_error(self):
        sc = ServerCrontab(hostname="host1")
        assert sc.is_ok is True

    def test_is_ok_false_when_error(self):
        sc = ServerCrontab(hostname="host1", error="connection refused")
        assert sc.is_ok is False

    def test_entries_default_empty(self):
        sc = ServerCrontab(hostname="host1")
        assert sc.entries == []


class TestCollectLocal:
    @patch("cronaudit.collector.subprocess.run")
    def test_collect_local_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=SAMPLE_CRONTAB, stderr="")
        result = collect_local()
        assert result.is_ok
        assert result.hostname == "localhost"
        assert len(result.entries) == 2

    @patch("cronaudit.collector.subprocess.run")
    def test_collect_local_no_crontab(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="no crontab for user")
        result = collect_local()
        assert result.is_ok
        assert result.entries == []

    @patch("cronaudit.collector.subprocess.run")
    def test_collect_local_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="permission denied")
        result = collect_local()
        assert not result.is_ok
        assert "permission denied" in result.error

    @patch("cronaudit.collector.subprocess.run", side_effect=FileNotFoundError)
    def test_collect_local_crontab_not_found(self, _):
        result = collect_local()
        assert not result.is_ok
        assert "not found" in result.error


class TestCollectRemote:
    @patch("cronaudit.collector.subprocess.run")
    def test_collect_remote_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=SAMPLE_CRONTAB, stderr="")
        result = collect_remote("web01", ssh_user="admin")
        assert result.is_ok
        assert result.hostname == "web01"
        assert len(result.entries) == 2
        called_cmd = mock_run.call_args[0][0]
        assert "admin@web01" in called_cmd

    @patch("cronaudit.collector.subprocess.run")
    def test_collect_remote_timeout(self, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=15)
        result = collect_remote("slowhost")
        assert not result.is_ok
        assert "timed out" in result.error


class TestCollectFromFile:
    def test_collect_from_file_success(self, tmp_path: Path):
        cron_file = tmp_path / "crontab.txt"
        cron_file.write_text(SAMPLE_CRONTAB)
        result = collect_from_file("archivehost", str(cron_file))
        assert result.is_ok
        assert result.hostname == "archivehost"
        assert len(result.entries) == 2

    def test_collect_from_file_missing(self, tmp_path: Path):
        result = collect_from_file("host", str(tmp_path / "nonexistent.txt"))
        assert not result.is_ok
        assert result.error is not None
