"""Tests for the ODS formatter module."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from odf.opendocument import load
from odf.table import Table, TableCell, TableRow
from odf.text import P

from behave_modern_sheets_report.ods_formatter import ODSFormatter
from tests._helpers import (
    StreamOpener as _StreamOpener,
    make_config as _make_config,
    make_feature_obj as _make_feature,
    make_scenario_obj as _make_scenario,
    make_step_obj as _make_step,
    run_full_cycle as _run_full_cycle,
)


def _get_tables(doc: object) -> dict[str, object]:
    """Extract tables from an ODS document keyed by name."""
    tables: dict[str, object] = {}
    for table in doc.spreadsheet.getElementsByType(Table):
        tables[table.getAttribute("name")] = table
    return tables


def _get_cell_texts(table: object) -> list[list[str]]:
    """Extract cell text values from a table as a 2D list."""
    rows: list[list[str]] = []
    for row in table.getElementsByType(TableRow):
        cells: list[str] = []
        for cell in row.getElementsByType(TableCell):
            ps = cell.getElementsByType(P)
            text = "".join(str(p.firstChild.data) for p in ps if p.firstChild)
            cells.append(text)
        rows.append(cells)
    return rows


class TestFullCycleWithHistory:
    """Full lifecycle produces .ods with Trends sheet populated."""

    def test_full_cycle_with_trends(self, tmp_path: Path) -> None:
        """Full cycle generates .ods with Summary, Details, and Trends."""
        output = tmp_path / "report.ods"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({"report_history_path": str(history)})
        fmt = ODSFormatter(opener, config)

        feature = _make_feature("Login")
        scenario = _make_scenario("S1", status="passed")
        step = _make_step("passed")
        _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        assert output.exists()
        doc = load(str(output))
        tables = _get_tables(doc)
        assert "Summary" in tables
        assert "Details" in tables
        assert "Trends" in tables
        rows = _get_cell_texts(tables["Trends"])
        assert len(rows) == 2

    def test_trends_accumulates_across_runs(self, tmp_path: Path) -> None:
        """Two runs produce two trend entries."""
        output = tmp_path / "report.ods"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({"report_history_path": str(history)})

        for i in range(2):
            fmt = ODSFormatter(opener, config)
            feature = _make_feature(f"F{i}")
            scenario = _make_scenario(f"S{i}", status="passed")
            step = _make_step("passed")
            _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        doc = load(str(output))
        rows = _get_cell_texts(_get_tables(doc)["Trends"])
        assert len(rows) == 3


class TestClearHistory:
    """report_clear_history clears history before appending."""

    def test_clear_history_single_entry(self, tmp_path: Path) -> None:
        """clear_history=true results in Trends with only 1 entry."""
        output = tmp_path / "report.ods"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({
            "report_history_path": str(history),
            "report_clear_history": "true",
        })

        for i in range(3):
            fmt = ODSFormatter(opener, config)
            feature = _make_feature(f"F{i}")
            scenario = _make_scenario(f"S{i}", status="passed")
            step = _make_step("passed")
            _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        doc = load(str(output))
        rows = _get_cell_texts(_get_tables(doc)["Trends"])
        assert len(rows) == 2


class TestCustomHistoryPath:
    """report_history_path stores history in a custom location."""

    def test_custom_history_path(self, tmp_path: Path) -> None:
        """History is written to the custom path."""
        output = tmp_path / "report.ods"
        custom_history = tmp_path / "custom.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({"report_history_path": str(custom_history)})
        fmt = ODSFormatter(opener, config)

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
        output = tmp_path / "report.ods"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({
            "report_history_path": str(history),
            "report_max_history": "2",
        })

        for i in range(3):
            fmt = ODSFormatter(opener, config)
            feature = _make_feature(f"F{i}")
            scenario = _make_scenario(f"S{i}", status="passed")
            step = _make_step("passed")
            _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        doc = load(str(output))
        rows = _get_cell_texts(_get_tables(doc)["Trends"])
        assert len(rows) == 3


class TestOnlyFailed:
    """report_only_failed filters Details but not Summary."""

    def test_only_failed_filters_details(self, tmp_path: Path) -> None:
        """only_failed=true shows only failed in Details, full Summary."""
        output = tmp_path / "report.ods"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({
            "report_history_path": str(history),
            "report_only_failed": "true",
        })
        fmt = ODSFormatter(opener, config)

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

        doc = load(str(output))
        details_rows = _get_cell_texts(_get_tables(doc)["Details"])
        assert len(details_rows) == 2
        assert details_rows[1][1] == "Fail"

        summary_rows = _get_cell_texts(_get_tables(doc)["Summary"])
        assert len(summary_rows) == 2


class TestCloseNoScenarios:
    """close() without scenarios does not crash."""

    def test_no_scenarios(self, tmp_path: Path) -> None:
        """Close with no scenarios produces a valid ods with empty Summary."""
        output = tmp_path / "report.ods"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({"report_history_path": str(history)})
        fmt = ODSFormatter(opener, config)

        fmt.close()

        assert output.exists()
        doc = load(str(output))
        tables = _get_tables(doc)
        assert "Summary" in tables
        rows = _get_cell_texts(tables["Summary"])
        assert len(rows) == 1


class TestNoBehaveFallback:
    """Formatter works without Behave installed."""

    def test_instantiable_without_behave(self, tmp_path: Path) -> None:
        """The formatter can be instantiated when Behave is not installed."""
        output = tmp_path / "report.ods"
        history = tmp_path / "history.json"
        opener = _StreamOpener(name=str(output))
        config = _make_config({"report_history_path": str(history)})
        fmt = ODSFormatter(opener, config)

        feature = _make_feature("Login")
        scenario = _make_scenario("S1", status="passed")
        step = _make_step("passed")
        _run_full_cycle(fmt, feature, [(scenario, [(step, step)])])

        assert output.exists()


class TestConfigOptions:
    """Config options are read from userdata."""

    def test_default_columns(self, tmp_path: Path) -> None:
        """Default columns are used when no report_columns is set."""
        opener = _StreamOpener(name=str(tmp_path / "report.ods"))
        config = _make_config({})
        fmt = ODSFormatter(opener, config)
        assert fmt._columns == ["feature", "scenario", "status", "duration", "tags", "error"]

    def test_custom_columns(self, tmp_path: Path) -> None:
        """Custom columns are respected."""
        opener = _StreamOpener(name=str(tmp_path / "report.ods"))
        config = _make_config({"report_columns": "feature,scenario,status"})
        fmt = ODSFormatter(opener, config)
        assert fmt._columns == ["feature", "scenario", "status"]

    def test_default_max_history(self, tmp_path: Path) -> None:
        """Default max_history is 100."""
        opener = _StreamOpener(name=str(tmp_path / "report.ods"))
        config = _make_config({})
        fmt = ODSFormatter(opener, config)
        assert fmt._max_history == 100

    def test_custom_max_history(self, tmp_path: Path) -> None:
        """Custom max_history is parsed."""
        opener = _StreamOpener(name=str(tmp_path / "report.ods"))
        config = _make_config({"report_max_history": "50"})
        fmt = ODSFormatter(opener, config)
        assert fmt._max_history == 50

    def test_clear_history_default_false(self, tmp_path: Path) -> None:
        """clear_history defaults to False."""
        opener = _StreamOpener(name=str(tmp_path / "report.ods"))
        config = _make_config({})
        fmt = ODSFormatter(opener, config)
        assert fmt._clear_history is False

    def test_history_path_default_none(self, tmp_path: Path) -> None:
        """history_path defaults to None."""
        opener = _StreamOpener(name=str(tmp_path / "report.ods"))
        config = _make_config({})
        fmt = ODSFormatter(opener, config)
        assert fmt._history_path is None


class TestOutputPathResolution:
    """Output path resolution from stream_opener."""

    def test_path_from_stream_opener_name(self, tmp_path: Path) -> None:
        """Path is resolved from stream_opener.name."""
        output = tmp_path / "custom_report.ods"
        opener = _StreamOpener(name=str(output))
        config = _make_config({})
        fmt = ODSFormatter(opener, config)
        assert fmt._resolve_output_path() == str(output)

    def test_default_path_when_no_name(self, tmp_path: Path) -> None:
        """Default path is 'report.ods' when stream_opener has no name."""
        opener = SimpleNamespace()
        config = _make_config({})
        fmt = ODSFormatter(opener, config)
        assert fmt._resolve_output_path() == "report.ods"

    def test_default_path_when_no_stream_opener(self, tmp_path: Path) -> None:
        """Default path is 'report.ods' when stream_opener is None."""
        config = _make_config({})
        fmt = ODSFormatter(None, config)
        assert fmt._resolve_output_path() == "report.ods"


class TestNoOpHooks:
    """No-op hooks do not crash."""

    def test_uri_noop(self, tmp_path: Path) -> None:
        """uri() does not raise."""
        opener = _StreamOpener(name=str(tmp_path / "report.ods"))
        config = _make_config({})
        fmt = ODSFormatter(opener, config)
        fmt.uri("features/test.feature")

    def test_background_noop(self, tmp_path: Path) -> None:
        """background() does not raise."""
        opener = _StreamOpener(name=str(tmp_path / "report.ods"))
        config = _make_config({})
        fmt = ODSFormatter(opener, config)
        fmt.background(SimpleNamespace())

    def test_rule_noop(self, tmp_path: Path) -> None:
        """rule() does not raise."""
        opener = _StreamOpener(name=str(tmp_path / "report.ods"))
        config = _make_config({})
        fmt = ODSFormatter(opener, config)
        fmt.rule(SimpleNamespace(name="My rule"))


class TestConfigNone:
    """Config=None uses defaults."""

    def test_config_none(self, tmp_path: Path) -> None:
        """Formatter works with config=None."""
        opener = _StreamOpener(name=str(tmp_path / "report.ods"))
        fmt = ODSFormatter(opener, None)
        assert fmt._columns == ["feature", "scenario", "status", "duration", "tags", "error"]
        assert fmt._only_failed is False
        assert fmt._clear_history is False
        assert fmt._history_path is None
        assert fmt._max_history == 100


class TestConfigWithoutUserdata:
    """Config with userdata=None uses defaults."""

    def test_config_userdata_none(self, tmp_path: Path) -> None:
        """Formatter works with config.userdata=None."""
        opener = _StreamOpener(name=str(tmp_path / "report.ods"))
        config = SimpleNamespace(userdata=None)
        fmt = ODSFormatter(opener, config)
        assert fmt._columns == ["feature", "scenario", "status", "duration", "tags", "error"]


class TestEofWithoutFeature:
    """eof() with no feature started does not crash."""

    def test_eof_without_feature(self, tmp_path: Path) -> None:
        """eof() with no feature does not crash."""
        opener = _StreamOpener(name=str(tmp_path / "report.ods"))
        config = _make_config({})
        fmt = ODSFormatter(opener, config)
        fmt.eof()
