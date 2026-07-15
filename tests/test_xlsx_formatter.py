"""Tests for the XLSX formatter module."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from openpyxl import load_workbook

from behave_modern_sheets_report.xlsx_formatter import XLSXFormatter
from tests._helpers import (
    StreamOpener as _StreamOpener,
)
from tests._helpers import (
    make_config as _make_config,
)
from tests._helpers import (
    make_feature_obj as _make_feature,
)
from tests._helpers import (
    make_scenario_obj as _make_scenario,
)
from tests._helpers import (
    make_step_obj as _make_step,
)
from tests._helpers import (
    run_full_cycle as _run_full_cycle,
)


class TestFullCycleWithHistory:
    """Full lifecycle produces .xlsx with Trends sheet populated."""

    def test_full_cycle_with_trends(self, tmp_path: Path) -> None:
        """Full cycle generates .xlsx with Summary, Details, and Trends."""
        output = tmp_path / "report.xlsx"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({"report_history_path": str(history)})
        fmt = XLSXFormatter(opener, config)

        feature = _make_feature("Login")
        scenario = _make_scenario("S1", status="passed")
        step = _make_step("passed")
        _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        assert output.exists()
        wb = load_workbook(output)
        assert "Summary" in wb.sheetnames
        assert "Details" in wb.sheetnames
        assert "Trends" in wb.sheetnames
        ws_trends = wb["Trends"]
        assert ws_trends.max_row == 2
        wb.close()

    def test_trends_accumulates_across_runs(self, tmp_path: Path) -> None:
        """Two runs produce two trend entries."""
        output = tmp_path / "report.xlsx"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({"report_history_path": str(history)})

        for i in range(2):
            fmt = XLSXFormatter(opener, config)
            feature = _make_feature(f"F{i}")
            scenario = _make_scenario(f"S{i}", status="passed")
            step = _make_step("passed")
            _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        wb = load_workbook(output)
        ws_trends = wb["Trends"]
        assert ws_trends.max_row == 3
        wb.close()


class TestClearHistory:
    """report_clear_history clears history before appending."""

    def test_clear_history_single_entry(self, tmp_path: Path) -> None:
        """clear_history=true results in Trends with only 1 entry."""
        output = tmp_path / "report.xlsx"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config(
            {
                "report_history_path": str(history),
                "report_clear_history": "true",
            }
        )

        for i in range(3):
            fmt = XLSXFormatter(opener, config)
            feature = _make_feature(f"F{i}")
            scenario = _make_scenario(f"S{i}", status="passed")
            step = _make_step("passed")
            _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        wb = load_workbook(output)
        ws_trends = wb["Trends"]
        assert ws_trends.max_row == 2
        wb.close()


class TestCustomHistoryPath:
    """report_history_path stores history in a custom location."""

    def test_custom_history_path(self, tmp_path: Path) -> None:
        """History is written to the custom path."""
        output = tmp_path / "report.xlsx"
        custom_history = tmp_path / "custom.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({"report_history_path": str(custom_history)})
        fmt = XLSXFormatter(opener, config)

        feature = _make_feature("Login")
        scenario = _make_scenario("S1", status="passed")
        step = _make_step("passed")
        _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        assert custom_history.exists()
        assert custom_history.read_text(encoding="utf-8").strip() != ""


class TestMaxHistory:
    """report_max_history limits the number of trend entries."""

    def test_max_history_truncates(self, tmp_path: Path) -> None:
        """max_history=2 keeps only 2 entries after 3 runs."""
        output = tmp_path / "report.xlsx"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config(
            {
                "report_history_path": str(history),
                "report_max_history": "2",
            }
        )

        for i in range(3):
            fmt = XLSXFormatter(opener, config)
            feature = _make_feature(f"F{i}")
            scenario = _make_scenario(f"S{i}", status="passed")
            step = _make_step("passed")
            _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        wb = load_workbook(output)
        ws_trends = wb["Trends"]
        assert ws_trends.max_row == 3
        wb.close()


class TestOnlyFailed:
    """report_only_failed filters Details but not Summary."""

    def test_only_failed_filters_details(self, tmp_path: Path) -> None:
        """only_failed=true shows only failed in Details, full Summary."""
        output = tmp_path / "report.xlsx"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config(
            {
                "report_history_path": str(history),
                "report_only_failed": "true",
            }
        )
        fmt = XLSXFormatter(opener, config)

        feature = _make_feature("Login")
        scenarios = [
            _make_scenario("Pass", status="passed"),
            _make_scenario("Fail", status="failed", error=ValueError("boom")),
        ]
        steps_pass = _make_step("passed")
        steps_fail = _make_step("failed")
        _run_full_cycle(
            fmt,
            feature,
            [
                (scenarios[0], [(steps_pass, steps_pass)]),
                (scenarios[1], [(steps_fail, steps_fail)]),
            ],
        )

        wb = load_workbook(output)
        ws_details = wb["Details"]
        assert ws_details.max_row == 2
        assert ws_details.cell(row=2, column=2).value == "Fail"

        ws_summary = wb["Summary"]
        assert ws_summary.max_row == 2
        wb.close()


class TestCloseNoScenarios:
    """close() without scenarios does not crash."""

    def test_no_scenarios(self, tmp_path: Path) -> None:
        """Close with no scenarios produces a valid xlsx with empty Summary."""
        output = tmp_path / "report.xlsx"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({"report_history_path": str(history)})
        fmt = XLSXFormatter(opener, config)

        fmt.close()

        assert output.exists()
        wb = load_workbook(output)
        assert "Summary" in wb.sheetnames
        ws = wb["Summary"]
        assert ws.max_row == 1
        wb.close()


class TestNoBehaveFallback:
    """Formatter works without Behave installed."""

    def test_instantiable_without_behave(self, tmp_path: Path) -> None:
        """The formatter can be instantiated when Behave is not installed."""
        output = tmp_path / "report.xlsx"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({"report_history_path": str(history)})
        fmt = XLSXFormatter(opener, config)

        feature = _make_feature("Login")
        scenario = _make_scenario("S1", status="passed")
        step = _make_step("passed")
        _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        assert output.exists()


class TestConfigOptions:
    """Config options are read from userdata."""

    def test_default_columns(self, tmp_path: Path) -> None:
        """Default columns are used when no report_columns is set."""
        output = tmp_path / "report.xlsx"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({"report_history_path": str(history)})
        fmt = XLSXFormatter(opener, config)
        assert fmt._columns == ["feature", "scenario", "status", "duration", "tags", "error"]

    def test_custom_columns(self, tmp_path: Path) -> None:
        """Custom columns are respected."""
        output = tmp_path / "report.xlsx"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config(
            {
                "report_history_path": str(history),
                "report_columns": "feature,scenario,status",
            }
        )
        fmt = XLSXFormatter(opener, config)
        assert fmt._columns == ["feature", "scenario", "status"]

    def test_default_max_history(self, tmp_path: Path) -> None:
        """Default max_history is 100."""
        opener = _StreamOpener(name=str(tmp_path / "report.xlsx"))
        config = _make_config({})
        fmt = XLSXFormatter(opener, config)
        assert fmt._max_history == 100

    def test_custom_max_history(self, tmp_path: Path) -> None:
        """Custom max_history is parsed."""
        opener = _StreamOpener(name=str(tmp_path / "report.xlsx"))
        config = _make_config({"report_max_history": "50"})
        fmt = XLSXFormatter(opener, config)
        assert fmt._max_history == 50

    def test_clear_history_default_false(self, tmp_path: Path) -> None:
        """clear_history defaults to False."""
        opener = _StreamOpener(name=str(tmp_path / "report.xlsx"))
        config = _make_config({})
        fmt = XLSXFormatter(opener, config)
        assert fmt._clear_history is False

    def test_history_path_default_none(self, tmp_path: Path) -> None:
        """history_path defaults to None."""
        opener = _StreamOpener(name=str(tmp_path / "report.xlsx"))
        config = _make_config({})
        fmt = XLSXFormatter(opener, config)
        assert fmt._history_path is None


class TestOutputPathResolution:
    """Output path resolution from stream_opener."""

    def test_path_from_stream_opener_name(self, tmp_path: Path) -> None:
        """Path is resolved from stream_opener.name."""
        output = tmp_path / "custom_report.xlsx"
        opener = _StreamOpener(name=str(output))
        config = _make_config({})
        fmt = XLSXFormatter(opener, config)
        assert fmt._resolve_output_path() == str(output)

    def test_default_path_when_no_name(self, tmp_path: Path) -> None:
        """Default path is 'report.xlsx' when stream_opener has no name."""
        opener = SimpleNamespace()
        config = _make_config({})
        fmt = XLSXFormatter(opener, config)
        assert fmt._resolve_output_path() == "report.xlsx"

    def test_default_path_when_no_stream_opener(self, tmp_path: Path) -> None:
        """Default path is 'report.xlsx' when stream_opener is None."""
        config = _make_config({})
        fmt = XLSXFormatter(None, config)
        assert fmt._resolve_output_path() == "report.xlsx"


class TestNoOpHooks:
    """No-op hooks do not crash."""

    def test_uri_noop(self, tmp_path: Path) -> None:
        """uri() does not raise."""
        opener = _StreamOpener(name=str(tmp_path / "report.xlsx"))
        config = _make_config({})
        fmt = XLSXFormatter(opener, config)
        fmt.uri("features/test.feature")

    def test_background_noop(self, tmp_path: Path) -> None:
        """background() does not raise."""
        opener = _StreamOpener(name=str(tmp_path / "report.xlsx"))
        config = _make_config({})
        fmt = XLSXFormatter(opener, config)
        fmt.background(SimpleNamespace())

    def test_rule_noop(self, tmp_path: Path) -> None:
        """rule() does not raise."""
        opener = _StreamOpener(name=str(tmp_path / "report.xlsx"))
        config = _make_config({})
        fmt = XLSXFormatter(opener, config)
        fmt.rule(SimpleNamespace(name="My rule"))


class TestConfigNone:
    """Config=None uses defaults."""

    def test_config_none(self, tmp_path: Path) -> None:
        """Formatter works with config=None."""
        opener = _StreamOpener(name=str(tmp_path / "report.xlsx"))
        fmt = XLSXFormatter(opener, None)
        assert fmt._columns == ["feature", "scenario", "status", "duration", "tags", "error"]
        assert fmt._only_failed is False
        assert fmt._clear_history is False
        assert fmt._history_path is None
        assert fmt._max_history == 100


class TestConfigWithoutUserdata:
    """Config with userdata=None uses defaults."""

    def test_config_userdata_none(self, tmp_path: Path) -> None:
        """Formatter works with config.userdata=None."""
        opener = _StreamOpener(name=str(tmp_path / "report.xlsx"))
        config = SimpleNamespace(userdata=None)
        fmt = XLSXFormatter(opener, config)
        assert fmt._columns == ["feature", "scenario", "status", "duration", "tags", "error"]


class TestEofWithoutFeature:
    """eof() with no feature started does not crash."""

    def test_eof_without_feature(self, tmp_path: Path) -> None:
        """eof() with no feature does not crash."""
        opener = _StreamOpener(name=str(tmp_path / "report.xlsx"))
        config = _make_config({})
        fmt = XLSXFormatter(opener, config)
        fmt.eof()


class TestDoubleCloseNoDuplicateHistory:
    """Double close() must not append duplicate history entries."""

    def test_double_close_no_duplicate_history(self, tmp_path: Path) -> None:
        """close() called twice appends only one history entry."""
        import json

        output = tmp_path / "report.xlsx"
        history_path = tmp_path / "h.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({"report_history_path": str(history_path)})
        fmt = XLSXFormatter(opener, config)
        feature = _make_feature("Login")
        scenario = _make_scenario("S1", status="passed")
        step = _make_step("passed")
        _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])
        fmt.close()
        fmt.close()

        data = json.loads(history_path.read_text(encoding="utf-8"))
        assert len(data) == 1
