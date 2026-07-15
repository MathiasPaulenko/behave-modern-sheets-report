"""Tests for the CSV formatter module."""

from __future__ import annotations

import csv
import sys
from io import StringIO
from types import SimpleNamespace
from typing import Any

from behave_modern_sheets_report.csv_formatter import CSVFormatter
from tests._helpers import (
    NoFlushStream as _NoFlushStream,
    StreamOpener as _StreamOpener,
    make_feature_obj as _make_feature,
    make_scenario_obj as _make_scenario,
    make_step_obj as _make_step,
    run_full_cycle as _run_full_cycle,
)


class TestFullCycle:
    """Complete lifecycle: feature → scenario → step → result → eof → close."""

    def test_full_cycle_output(self) -> None:
        """A full cycle produces valid CSV with expected data."""
        stream = StringIO()
        opener = _StreamOpener(stream)
        config = SimpleNamespace(userdata={})
        fmt = CSVFormatter(opener, config)

        feature = _make_feature("Login")
        scenario = _make_scenario("Successful login", tags=["smoke"])
        step = _make_step("passed")
        _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        stream.seek(0)
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["feature"] == "Login"
        assert rows[0]["scenario"] == "Successful login"
        assert rows[0]["status"] == "passed"
        assert rows[0]["tags"] == "smoke"


class TestConfigOptions:
    """Options read from config.userdata."""

    def test_custom_columns(self) -> None:
        """report_columns controls which columns appear in output."""
        stream = StringIO()
        opener = _StreamOpener(stream)
        config = SimpleNamespace(userdata={"report_columns": "feature,status"})
        fmt = CSVFormatter(opener, config)

        feature = _make_feature("Login")
        scenario = _make_scenario("S1")
        step = _make_step("passed")
        _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        stream.seek(0)
        reader = csv.reader(stream)
        header = next(reader)
        assert header == ["feature", "status"]

    def test_only_failed_true(self) -> None:
        """report_only_failed=true filters out non-failed scenarios."""
        stream = StringIO()
        opener = _StreamOpener(stream)
        config = SimpleNamespace(userdata={"report_only_failed": "true"})
        fmt = CSVFormatter(opener, config)

        feature = _make_feature("Auth")
        passing = _make_scenario("Pass")
        failing = _make_scenario("Fail")
        pass_step = _make_step("passed")
        fail_step = _make_step("failed", error=AssertionError("boom"))
        _run_full_cycle(
            fmt,
            feature,
            [
                (passing, [(pass_step, pass_step)]),
                (failing, [(fail_step, fail_step)]),
            ],
        )

        stream.seek(0)
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["scenario"] == "Fail"
        assert rows[0]["status"] == "failed"

    def test_delimiter_semicolon(self) -> None:
        """report_delimiter=semicolon produces semicolon-separated output."""
        stream = StringIO()
        opener = _StreamOpener(stream)
        config = SimpleNamespace(userdata={"report_delimiter": "semicolon"})
        fmt = CSVFormatter(opener, config)

        feature = _make_feature("Login")
        scenario = _make_scenario("S1")
        step = _make_step("passed")
        _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        stream.seek(0)
        reader = csv.DictReader(stream, delimiter=";")
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["feature"] == "Login"


class TestDoubleEof:
    """Double eof() does not duplicate output."""

    def test_double_eof_no_duplication(self) -> None:
        """Calling eof() twice does not produce duplicate scenarios."""
        stream = StringIO()
        opener = _StreamOpener(stream)
        config = SimpleNamespace(userdata={})
        fmt = CSVFormatter(opener, config)

        feature = _make_feature("Login")
        scenario = _make_scenario("S1")
        step = _make_step("passed")

        fmt.uri("features/login.feature")
        fmt.feature(feature)
        fmt.scenario(scenario)
        fmt.step(step)
        fmt.result(step)
        fmt.eof()
        fmt.eof()
        fmt.close()

        stream.seek(0)
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert len(rows) == 1


class TestCloseWithoutEof:
    """close() without prior eof() finalizes automatically."""

    def test_close_without_eof(self) -> None:
        """close() calls eof() internally and produces correct output."""
        stream = StringIO()
        opener = _StreamOpener(stream)
        config = SimpleNamespace(userdata={})
        fmt = CSVFormatter(opener, config)

        feature = _make_feature("Login")
        scenario = _make_scenario("S1")
        step = _make_step("passed")

        fmt.uri("features/login.feature")
        fmt.feature(feature)
        fmt.scenario(scenario)
        fmt.step(step)
        fmt.result(step)
        fmt.close()

        stream.seek(0)
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["scenario"] == "S1"
        assert rows[0]["status"] == "passed"


class TestCloseNoScenarios:
    """close() with no scenarios does not crash."""

    def test_no_scenarios(self) -> None:
        """close() with zero scenarios writes header only."""
        stream = StringIO()
        opener = _StreamOpener(stream)
        config = SimpleNamespace(userdata={})
        fmt = CSVFormatter(opener, config)

        fmt.close()

        stream.seek(0)
        reader = csv.reader(stream)
        header = next(reader)
        assert header == ["feature", "scenario", "status", "duration", "tags", "error"]
        remaining = list(reader)
        assert remaining == []


class TestNoBehaveFallback:
    """Formatter works without Behave installed (_BaseFormatter = object)."""

    def test_instantiable_without_behave(self) -> None:
        """The formatter can be instantiated when Behave is not installed."""
        stream = StringIO()
        opener = _StreamOpener(stream)
        config = SimpleNamespace(userdata={})
        fmt = CSVFormatter(opener, config)
        assert fmt.name == "csv-modern"
        assert fmt.description == "CSV report for Behave"


class TestStreamToStringIO:
    """Stream to StringIO produces exact content."""

    def test_stringio_content(self) -> None:
        """Output written to StringIO matches expected CSV content."""
        stream = StringIO()
        opener = _StreamOpener(stream)
        config = SimpleNamespace(userdata={})
        fmt = CSVFormatter(opener, config)

        feature = _make_feature("Login")
        scenario = _make_scenario("S1", tags=["a", "b"])
        step = _make_step("passed")
        _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        stream.seek(0)
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert len(rows) == 1
        row = rows[0]
        assert row["feature"] == "Login"
        assert row["scenario"] == "S1"
        assert row["status"] == "passed"
        assert row["tags"] == "a;b"
        assert row["error"] == ""


class TestStreamToStdout:
    """Stream to sys.stdout writes to stdout."""

    def test_stdout_output(self, capsys: Any) -> None:
        """When stream_opener is None, output goes to sys.stdout."""
        config = SimpleNamespace(userdata={})
        fmt = CSVFormatter(None, config)

        feature = _make_feature("Login")
        scenario = _make_scenario("S1")
        step = _make_step("passed")
        _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        captured = capsys.readouterr()
        assert "Login" in captured.out
        assert "S1" in captured.out
        assert "passed" in captured.out


class TestUriAndBackground:
    """uri() and background() are no-ops that don't crash."""

    def test_uri_noop(self) -> None:
        """uri() does not raise."""
        config = SimpleNamespace(userdata={})
        fmt = CSVFormatter(None, config)
        fmt.uri("features/test.feature")

    def test_background_noop(self) -> None:
        """background() does not raise."""
        config = SimpleNamespace(userdata={})
        fmt = CSVFormatter(None, config)
        fmt.background(SimpleNamespace())

    def test_rule_noop(self) -> None:
        """rule() does not raise."""
        config = SimpleNamespace(userdata={})
        fmt = CSVFormatter(None, config)
        fmt.rule(SimpleNamespace(name="My rule"))


class TestEdgeCases:
    """Edge cases for branch coverage."""

    def test_config_without_userdata(self) -> None:
        """Config with userdata=None uses default options."""
        config = SimpleNamespace(userdata=None)
        fmt = CSVFormatter(None, config)
        assert fmt._columns == ["feature", "scenario", "status", "duration", "tags", "error"]

    def test_config_none(self) -> None:
        """Config=None uses default options."""
        fmt = CSVFormatter(None, None)
        assert fmt._columns == ["feature", "scenario", "status", "duration", "tags", "error"]

    def test_stream_opener_without_open(self) -> None:
        """stream_opener without .open() falls back to stdout."""
        opener = SimpleNamespace()
        config = SimpleNamespace(userdata={})
        fmt = CSVFormatter(opener, config)
        stream = fmt._resolve_stream()
        assert stream is sys.stdout

    def test_eof_without_feature(self) -> None:
        """eof() with no feature started does not crash."""
        config = SimpleNamespace(userdata={})
        fmt = CSVFormatter(None, config)
        fmt.eof()

    def test_stream_without_flush(self) -> None:
        """close() with a stream that has no flush() does not crash."""
        stream = _NoFlushStream()
        opener = _StreamOpener(stream)
        config = SimpleNamespace(userdata={})
        fmt = CSVFormatter(opener, config)
        fmt.close()
        assert "feature" in stream.buffer
