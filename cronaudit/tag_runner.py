"""High-level runner that loads tag rules and tags a list of ServerCrontabs."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from cronaudit.collector import ServerCrontab
from cronaudit.tag_config import load_tag_rules
from cronaudit.tagging import TagRule, TaggedCrontab, collect_tags, tag_all


@dataclass
class TagRunResult:
    """Outcome of a tagging run."""
    tagged_crontabs: List[TaggedCrontab] = field(default_factory=list)
    tag_counts: Dict[str, int] = field(default_factory=dict)
    rules_loaded: int = 0
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error

    @property
    def total_tagged(self) -> int:
        return sum(len(tc.tagged_entries) for tc in self.tagged_crontabs)


def run_tagging(
    crontabs: List[ServerCrontab],
    rules_path: Optional[str | Path] = None,
    rules: Optional[List[TagRule]] = None,
) -> TagRunResult:
    """Tag *crontabs* using rules from *rules_path* or a pre-built *rules* list.

    Exactly one of ``rules_path`` or ``rules`` must be provided.
    """
    if rules_path is not None and rules is not None:
        return TagRunResult(error="Provide either rules_path or rules, not both.")
    if rules_path is None and rules is None:
        return TagRunResult(error="Either rules_path or rules must be provided.")

    if rules_path is not None:
        try:
            resolved_rules = load_tag_rules(rules_path)
        except (FileNotFoundError, ValueError) as exc:
            return TagRunResult(error=str(exc))
    else:
        resolved_rules = list(rules)  # type: ignore[arg-type]

    tagged = tag_all(crontabs, resolved_rules)
    counts = collect_tags(tagged)

    return TagRunResult(
        tagged_crontabs=tagged,
        tag_counts=counts,
        rules_loaded=len(resolved_rules),
    )
