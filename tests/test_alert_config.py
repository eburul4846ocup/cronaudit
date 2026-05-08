"""Tests for cronaudit.alert_config."""
from __future__ import annotations

from cronaudit.alert_config import load_alert_rules


def test_load_valid_rules():
    cfg = {
        "alert_rules": [
            {"name": "r1", "condition": "failure_rate", "threshold": 0.5},
            {"name": "r2", "condition": "server_down", "threshold": 1},
        ]
    }
    rules, errors = load_alert_rules(cfg)
    assert len(rules) == 2
    assert errors == []


def test_load_missing_condition():
    cfg = {"alert_rules": [{"name": "bad", "threshold": 0.1}]}
    rules, errors = load_alert_rules(cfg)
    assert len(rules) == 1          # rule still returned
    assert any("missing 'condition'" in e for e in errors)


def test_load_unknown_condition():
    cfg = {"alert_rules": [{"name": "x", "condition": "unknown"}]}
    _, errors = load_alert_rules(cfg)
    assert any("unknown condition" in e for e in errors)


def test_load_invalid_threshold_type():
    cfg = {"alert_rules": [{"name": "t", "condition": "min_entries", "threshold": "abc"}]}
    _, errors = load_alert_rules(cfg)
    assert any("numeric" in e for e in errors)


def test_failure_rate_threshold_out_of_range():
    cfg = {"alert_rules": [{"name": "r", "condition": "failure_rate", "threshold": 1.5}]}
    _, errors = load_alert_rules(cfg)
    assert any("between 0 and 1" in e for e in errors)


def test_disabled_rule_loaded():
    cfg = {
        "alert_rules": [
            {"name": "r", "condition": "server_down", "threshold": 1, "enabled": False}
        ]
    }
    rules, errors = load_alert_rules(cfg)
    assert rules[0].enabled is False
    assert errors == []


def test_alert_rules_not_a_list():
    _, errors = load_alert_rules({"alert_rules": "bad"})
    assert any("must be a list" in e for e in errors)


def test_non_dict_rule_skipped_with_error():
    cfg = {"alert_rules": ["not_a_dict"]}
    rules, errors = load_alert_rules(cfg)
    assert rules == []
    assert any("must be a mapping" in e for e in errors)


def test_empty_config_returns_no_rules():
    rules, errors = load_alert_rules({})
    assert rules == []
    assert errors == []


def test_default_name_assigned_when_missing():
    cfg = {"alert_rules": [{"condition": "server_down", "threshold": 1}]}
    rules, _ = load_alert_rules(cfg)
    assert rules[0].name == "rule_0"
