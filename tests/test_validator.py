"""Tests for cronaudit.validator."""

import pytest
from cronaudit.validator import validate_expression, ValidationResult


def test_valid_standard_expression():
    result = validate_expression("0 12 * * *")
    assert result.valid is True
    assert result.errors == []


def test_valid_special_keyword():
    for kw in ("@daily", "@reboot", "@hourly", "@monthly", "@weekly"):
        result = validate_expression(kw)
        assert result.valid is True, f"{kw} should be valid"


def test_invalid_too_few_fields():
    result = validate_expression("0 12 *")
    assert result.valid is False
    assert any("3" in e for e in result.errors)


def test_invalid_too_many_fields():
    result = validate_expression("0 12 * * * extra")
    assert result.valid is False


def test_invalid_minute_out_of_range():
    result = validate_expression("60 12 * * *")
    assert result.valid is False
    assert any("minute" in e for e in result.errors)


def test_invalid_hour_out_of_range():
    result = validate_expression("0 25 * * *")
    assert result.valid is False
    assert any("hour" in e for e in result.errors)


def test_valid_step_expression():
    result = validate_expression("*/15 * * * *")
    assert result.valid is True


def test_valid_range_expression():
    result = validate_expression("0 9-17 * * 1-5")
    assert result.valid is True


def test_valid_list_expression():
    result = validate_expression("0 8,12,18 * * *")
    assert result.valid is True


def test_invalid_non_numeric_field():
    result = validate_expression("abc 12 * * *")
    assert result.valid is False


def test_validation_result_bool_true():
    r = ValidationResult(valid=True)
    assert bool(r) is True


def test_validation_result_bool_false():
    r = ValidationResult(valid=False, errors=["some error"])
    assert bool(r) is False
