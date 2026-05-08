"""Tests for cronaudit.tag_config."""
import json
import pytest
from pathlib import Path

from cronaudit.tag_config import load_tag_rules


def _write(tmp_path: Path, data) -> Path:
    p = tmp_path / "tags.json"
    p.write_text(json.dumps(data))
    return p


def test_load_valid_rules(tmp_path):
    data = [
        {"tag": "backup", "pattern": "backup", "description": "Backup jobs"},
        {"tag": "deploy", "pattern": "deploy"},
    ]
    rules = load_tag_rules(_write(tmp_path, data))
    assert len(rules) == 2
    assert rules[0].tag == "backup"
    assert rules[0].pattern == "backup"
    assert rules[0].description == "Backup jobs"
    assert rules[1].description == ""


def test_load_missing_tag_key(tmp_path):
    data = [{"pattern": "backup"}]
    with pytest.raises(ValueError, match="missing keys"):
        load_tag_rules(_write(tmp_path, data))


def test_load_missing_pattern_key(tmp_path):
    data = [{"tag": "backup"}]
    with pytest.raises(ValueError, match="missing keys"):
        load_tag_rules(_write(tmp_path, data))


def test_load_empty_tag_raises(tmp_path):
    data = [{"tag": "", "pattern": "backup"}]
    with pytest.raises(ValueError, match="'tag' must not be empty"):
        load_tag_rules(_write(tmp_path, data))


def test_load_empty_pattern_raises(tmp_path):
    data = [{"tag": "backup", "pattern": ""}]
    with pytest.raises(ValueError, match="'pattern' must not be empty"):
        load_tag_rules(_write(tmp_path, data))


def test_load_not_a_list_raises(tmp_path):
    p = _write(tmp_path, {"tag": "backup", "pattern": "backup"})
    with pytest.raises(ValueError, match="JSON array"):
        load_tag_rules(p)


def test_load_rule_not_a_dict_raises(tmp_path):
    data = ["not-a-dict"]
    with pytest.raises(ValueError, match="must be a mapping"):
        load_tag_rules(_write(tmp_path, data))


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_tag_rules(tmp_path / "nonexistent.json")


def test_load_empty_list(tmp_path):
    rules = load_tag_rules(_write(tmp_path, []))
    assert rules == []
