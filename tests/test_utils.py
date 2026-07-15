"""Tests for the utils module."""

from __future__ import annotations

import re
import time

from behave_modern_sheets_report.utils import (
    DEFAULT_COLUMNS,
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_SKIPPED,
    STATUS_UNDEFINED,
    STATUS_UNTESTED,
    format_duration,
    generate_id,
    monotonic_seconds,
    normalize_status,
    now_iso,
    parse_bool,
    parse_columns,
    parse_delimiter,
    safe_str,
    safe_tags,
)


class TestSafeStr:
    """Tests for safe_str."""

    def test_none_returns_empty(self) -> None:
        assert safe_str(None) == ""

    def test_int_returns_string(self) -> None:
        assert safe_str(42) == "42"

    def test_normal_string(self) -> None:
        assert safe_str("hello") == "hello"

    def test_string_with_whitespace_stripped(self) -> None:
        assert safe_str("  hello world  ") == "hello world"

    def test_long_string_truncated(self) -> None:
        long_str = "a" * 600
        result = safe_str(long_str)
        assert len(result) == 503
        assert result.endswith("...")
        assert result[:500] == "a" * 500

    def test_empty_string(self) -> None:
        assert safe_str("") == ""

    def test_exactly_500_not_truncated(self) -> None:
        exact = "a" * 500
        result = safe_str(exact)
        assert result == exact
        assert "..." not in result


class TestSafeTags:
    """Tests for safe_tags."""

    def test_none_returns_empty_list(self) -> None:
        assert safe_tags(None) == []

    def test_simple_string(self) -> None:
        assert safe_tags("smoke") == ["smoke"]

    def test_string_with_commas(self) -> None:
        assert safe_tags("smoke, auth, regression") == ["smoke", "auth", "regression"]

    def test_list(self) -> None:
        assert safe_tags(["a", "b", "c"]) == ["a", "b", "c"]

    def test_empty_list(self) -> None:
        assert safe_tags([]) == []

    def test_unexpected_type_returns_empty(self) -> None:
        assert safe_tags(42) == []

    def test_string_with_empty_parts_filtered(self) -> None:
        assert safe_tags("a, , b,") == ["a", "b"]

    def test_list_with_empty_strings_filtered(self) -> None:
        assert safe_tags(["a", "", "b", "  "]) == ["a", "b"]


class TestFormatDuration:
    """Tests for format_duration."""

    def test_zero_returns_zero(self) -> None:
        assert format_duration(0) == "0s"

    def test_negative_returns_na(self) -> None:
        assert format_duration(-1.0) == "N/A"

    def test_nan_returns_na(self) -> None:
        assert format_duration(float("nan")) == "N/A"

    def test_inf_returns_na(self) -> None:
        assert format_duration(float("inf")) == "N/A"

    def test_neg_inf_returns_na(self) -> None:
        assert format_duration(float("-inf")) == "N/A"

    def test_below_millisecond_returns_zero(self) -> None:
        assert format_duration(0.0001) == "0s"

    def test_milliseconds(self) -> None:
        assert format_duration(0.012) == "12ms"

    def test_seconds(self) -> None:
        assert format_duration(1.234) == "1.234s"

    def test_large_seconds(self) -> None:
        assert format_duration(60.5) == "60.500s"

    def test_exactly_one_millisecond(self) -> None:
        assert format_duration(0.001) == "1ms"

    def test_exactly_one_second(self) -> None:
        assert format_duration(1.0) == "1.000s"


class TestNormalizeStatus:
    """Tests for normalize_status."""

    def test_passed(self) -> None:
        assert normalize_status("passed") == STATUS_PASSED

    def test_failed(self) -> None:
        assert normalize_status("failed") == STATUS_FAILED

    def test_skipped(self) -> None:
        assert normalize_status("skipped") == STATUS_SKIPPED

    def test_undefined(self) -> None:
        assert normalize_status("undefined") == STATUS_UNDEFINED

    def test_unknown_returns_untested(self) -> None:
        assert normalize_status("unknown") == STATUS_UNTESTED

    def test_empty_string_returns_untested(self) -> None:
        assert normalize_status("") == STATUS_UNTESTED

    def test_none_returns_untested(self) -> None:
        assert normalize_status(None) == STATUS_UNTESTED

    def test_case_insensitive(self) -> None:
        assert normalize_status("PASSED") == STATUS_PASSED
        assert normalize_status("Failed") == STATUS_FAILED

    def test_xfailed_maps_to_passed(self) -> None:
        assert normalize_status("xfailed") == STATUS_PASSED

    def test_xpassed_maps_to_passed(self) -> None:
        assert normalize_status("xpassed") == STATUS_PASSED

    def test_error_maps_to_failed(self) -> None:
        assert normalize_status("error") == STATUS_FAILED

    def test_hook_error_maps_to_failed(self) -> None:
        assert normalize_status("hook_error") == STATUS_FAILED

    def test_cleanup_error_maps_to_failed(self) -> None:
        assert normalize_status("cleanup_error") == STATUS_FAILED

    def test_pending_maps_to_undefined(self) -> None:
        assert normalize_status("pending") == STATUS_UNDEFINED


class TestParseColumns:
    """Tests for parse_columns."""

    def test_none_returns_default(self) -> None:
        assert parse_columns(None) == DEFAULT_COLUMNS

    def test_empty_string_returns_default(self) -> None:
        assert parse_columns("") == DEFAULT_COLUMNS

    def test_single_column(self) -> None:
        assert parse_columns("feature") == ["feature"]

    def test_multiple_columns(self) -> None:
        assert parse_columns("feature, scenario") == ["feature", "scenario"]

    def test_columns_with_extra_spaces(self) -> None:
        assert parse_columns(" feature , scenario , status ") == ["feature", "scenario", "status"]

    def test_double_comma_filters_empty(self) -> None:
        assert parse_columns("feature,,scenario") == ["feature", "scenario"]

    def test_whitespace_only_returns_default(self) -> None:
        assert parse_columns("   ") == DEFAULT_COLUMNS

    def test_returns_new_list_each_call(self) -> None:
        result = parse_columns(None)
        result.append("extra")
        result2 = parse_columns(None)
        assert "extra" not in result2

    def test_invalid_column_filtered_out(self) -> None:
        assert parse_columns("feature, bogus, scenario") == ["feature", "scenario"]

    def test_all_invalid_returns_default(self) -> None:
        assert parse_columns("bogus, fake, nope") == DEFAULT_COLUMNS

    def test_mixed_valid_invalid(self) -> None:
        result = parse_columns("feature, bogus, status, fake")
        assert result == ["feature", "status"]


class TestParseDelimiter:
    """Tests for parse_delimiter."""

    def test_none_returns_comma(self) -> None:
        assert parse_delimiter(None) == ","

    def test_comma(self) -> None:
        assert parse_delimiter("comma") == ","

    def test_semicolon(self) -> None:
        assert parse_delimiter("semicolon") == ";"

    def test_tab(self) -> None:
        assert parse_delimiter("tab") == "\t"

    def test_invalid_returns_comma(self) -> None:
        assert parse_delimiter("invalid") == ","

    def test_case_insensitive(self) -> None:
        assert parse_delimiter("Comma") == ","
        assert parse_delimiter("TAB") == "\t"


class TestParseBool:
    """Tests for parse_bool."""

    def test_none_returns_false(self) -> None:
        assert parse_bool(None) is False

    def test_true(self) -> None:
        assert parse_bool("true") is True

    def test_true_case_insensitive(self) -> None:
        assert parse_bool("True") is True

    def test_one(self) -> None:
        assert parse_bool("1") is True

    def test_yes(self) -> None:
        assert parse_bool("yes") is True

    def test_false(self) -> None:
        assert parse_bool("false") is False

    def test_zero(self) -> None:
        assert parse_bool("0") is False

    def test_no(self) -> None:
        assert parse_bool("no") is False

    def test_invalid_returns_false(self) -> None:
        assert parse_bool("invalid") is False


class TestGenerateId:
    """Tests for generate_id."""

    def test_format(self) -> None:
        result = generate_id("run")
        assert result.startswith("run_")
        assert len(result) == 4 + 12  # "run_" + 12 hex chars

    def test_default_prefix(self) -> None:
        result = generate_id()
        assert result.startswith("run_")

    def test_custom_prefix(self) -> None:
        result = generate_id("feat")
        assert result.startswith("feat_")

    def test_uniqueness_1000_calls(self) -> None:
        ids = {generate_id() for _ in range(1000)}
        assert len(ids) == 1000


class TestNowIso:
    """Tests for now_iso."""

    def test_returns_iso_format(self) -> None:
        result = now_iso()
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", result)

    def test_contains_timezone(self) -> None:
        result = now_iso()
        assert "+00:00" in result


class TestMonotonicSeconds:
    """Tests for monotonic_seconds."""

    def test_returns_positive_float(self) -> None:
        start = time.monotonic()
        time.sleep(0.01)
        elapsed = monotonic_seconds(start)
        assert isinstance(elapsed, float)
        assert elapsed > 0

    def test_returns_float_type(self) -> None:
        start = time.monotonic()
        result = monotonic_seconds(start)
        assert isinstance(result, float)
