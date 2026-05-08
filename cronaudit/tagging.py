"""Tag cron entries and results for categorization and filtering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from cronaudit.parser import CronEntry
from cronaudit.collector import ServerCrontab


@dataclass
class TagRule:
    """A rule that assigns a tag when a command matches a pattern."""
    tag: str
    pattern: str  # substring match against command
    description: str = ""


@dataclass
class TaggedEntry:
    """A cron entry decorated with a set of tags."""
    entry: CronEntry
    tags: Set[str] = field(default_factory=set)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags


@dataclass
class TaggedCrontab:
    """A server crontab whose entries have been tagged."""
    server: str
    tagged_entries: List[TaggedEntry] = field(default_factory=list)
    error: str = ""

    @property
    def is_ok(self) -> bool:
        return not self.error

    def entries_with_tag(self, tag: str) -> List[TaggedEntry]:
        return [te for te in self.tagged_entries if te.has_tag(tag)]


def apply_rules(entry: CronEntry, rules: List[TagRule]) -> Set[str]:
    """Return the set of tags that apply to a single entry."""
    tags: Set[str] = set()
    for rule in rules:
        if rule.pattern.lower() in entry.command.lower():
            tags.add(rule.tag)
    return tags


def tag_crontab(crontab: ServerCrontab, rules: List[TagRule]) -> TaggedCrontab:
    """Apply tagging rules to all entries in a ServerCrontab."""
    tagged_entries = [
        TaggedEntry(entry=e, tags=apply_rules(e, rules))
        for e in crontab.entries
    ]
    return TaggedCrontab(
        server=crontab.server,
        tagged_entries=tagged_entries,
        error=crontab.error,
    )


def tag_all(crontabs: List[ServerCrontab], rules: List[TagRule]) -> List[TaggedCrontab]:
    """Apply tagging rules to a list of ServerCrontab objects."""
    return [tag_crontab(ct, rules) for ct in crontabs]


def collect_tags(tagged_crontabs: List[TaggedCrontab]) -> Dict[str, int]:
    """Return a mapping of tag -> entry count across all tagged crontabs."""
    counts: Dict[str, int] = {}
    for tc in tagged_crontabs:
        for te in tc.tagged_entries:
            for tag in te.tags:
                counts[tag] = counts.get(tag, 0) + 1
    return counts
