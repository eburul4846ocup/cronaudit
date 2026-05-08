"""Load and validate alert rules from a YAML/dict configuration."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from cronaudit.alerting import AlertRule

VALID_CONDITIONS = {"failure_rate", "min_entries", "max_entries", "server_down"}


def _parse_rule(raw: Dict[str, Any], index: int) -> Tuple[AlertRule, List[str]]:
    """Parse a single raw dict into an AlertRule; return (rule, errors)."""
    errors: List[str] = []
    name = raw.get("name", f"rule_{index}")
    condition = raw.get("condition", "")
    threshold = raw.get("threshold", 0.0)
    enabled = raw.get("enabled", True)

    if not condition:
        errors.append(f"Rule '{name}': missing 'condition'")
    elif condition not in VALID_CONDITIONS:
        errors.append(
            f"Rule '{name}': unknown condition '{condition}'; "
            f"valid: {sorted(VALID_CONDITIONS)}"
        )

    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        errors.append(f"Rule '{name}': threshold must be numeric")
        threshold = 0.0

    if condition == "failure_rate" and not (0.0 <= threshold <= 1.0):
        errors.append(
            f"Rule '{name}': failure_rate threshold must be between 0 and 1"
        )

    rule = AlertRule(
        name=str(name),
        condition=str(condition),
        threshold=threshold,
        enabled=bool(enabled),
    )
    return rule, errors


def load_alert_rules(
    config: Dict[str, Any],
) -> Tuple[List[AlertRule], List[str]]:
    """Load alert rules from a config dict.

    Returns (rules, validation_errors).  Rules with errors are still
    included so callers can decide how to handle partial configs.
    """
    raw_rules = config.get("alert_rules", [])
    if not isinstance(raw_rules, list):
        return [], ["'alert_rules' must be a list"]

    all_rules: List[AlertRule] = []
    all_errors: List[str] = []

    for i, raw in enumerate(raw_rules):
        if not isinstance(raw, dict):
            all_errors.append(f"Rule at index {i} must be a mapping")
            continue
        rule, errors = _parse_rule(raw, i)
        all_rules.append(rule)
        all_errors.extend(errors)

    return all_rules, all_errors
