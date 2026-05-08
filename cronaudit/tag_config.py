"""Load tagging rules from a YAML or JSON config file."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from cronaudit.tagging import TagRule

_REQUIRED_KEYS = {"tag", "pattern"}


def _parse_rule(raw: object, index: int) -> TagRule:
    if not isinstance(raw, dict):
        raise ValueError(f"Rule at index {index} must be a mapping, got {type(raw).__name__}")
    missing = _REQUIRED_KEYS - raw.keys()
    if missing:
        raise ValueError(f"Rule at index {index} missing keys: {missing}")
    tag = str(raw["tag"]).strip()
    pattern = str(raw["pattern"]).strip()
    if not tag:
        raise ValueError(f"Rule at index {index}: 'tag' must not be empty")
    if not pattern:
        raise ValueError(f"Rule at index {index}: 'pattern' must not be empty")
    return TagRule(tag=tag, pattern=pattern, description=str(raw.get("description", "")))


def load_tag_rules(path: str | Path) -> List[TagRule]:
    """Load tag rules from a JSON file.

    Expected format::

        [
          {"tag": "backup", "pattern": "backup", "description": "Backup jobs"},
          {"tag": "deploy", "pattern": "deploy"}
        ]
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Tag config file not found: {p}")
    with p.open() as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("Tag config must be a JSON array of rule objects")
    return [_parse_rule(item, i) for i, item in enumerate(data)]
