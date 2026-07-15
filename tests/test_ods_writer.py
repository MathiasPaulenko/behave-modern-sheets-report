"""Tests for the ODS writer module."""

from __future__ import annotations

from pathlib import Path

from odf.opendocument import load
from odf.table import Table, TableCell, TableRow
from odf.text import P

from behave_modern_sheets_report.ods_writer import ODSWriter
from tests._helpers import (
    make_feature_summary as _make_feature,
    make_history_entry as _make_history_entry,
    make_run_summary as _make_run_summary,
    make_scenario_result as _make_scenario,
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


class TestValidFile:
    """Generated file is a valid .ods readable by odfpy."""

    def test_file_is_valid(self, tmp_path: Path) -> None:
        """The output file can be loaded by odfpy.load."""
        run = _make_run_summary(
            features=[_make_feature()],
            scenarios=[_make_scenario()],
        )
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path)
        doc = load(str(path))
        tables = _get_tables(doc)
        assert "Summary" in tables


class TestSheetsPresent:
    """Correct sheets are present in the document."""

    def test_four_sheets_with_trends(self, tmp_path: Path) -> None:
        """All 4 sheets present when trends is provided."""
        run = _make_run_summary(
            features=[_make_feature()],
            scenarios=[_make_scenario()],
        )
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path, trends=[_make_history_entry()])
        doc = load(str(path))
        tables = _get_tables(doc)
        assert "Summary" in tables
        assert "Details" in tables
        assert "Failures" in tables
        assert "Trends" in tables

    def test_three_sheets_without_trends(self, tmp_path: Path) -> None:
        """Trends sheet omitted when trends is None."""
        run = _make_run_summary(
            features=[_make_feature()],
            scenarios=[_make_scenario()],
        )
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path, trends=None)
        doc = load(str(path))
        tables = _get_tables(doc)
        assert "Summary" in tables
        assert "Details" in tables
        assert "Failures" in tables
        assert "Trends" not in tables

    def test_three_sheets_with_empty_trends(self, tmp_path: Path) -> None:
        """Trends sheet omitted when trends is empty list."""
        run = _make_run_summary(
            features=[_make_feature()],
            scenarios=[_make_scenario()],
        )
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path, trends=[])
        doc = load(str(path))
        tables = _get_tables(doc)
        assert "Trends" not in tables


class TestSummarySheet:
    """Summary sheet content."""

    def test_summary_one_row_per_feature(self, tmp_path: Path) -> None:
        """Summary has one data row per feature plus a header."""
        features = [_make_feature("Login"), _make_feature("Auth")]
        run = _make_run_summary(features=features, scenarios=[_make_scenario()])
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path)
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Summary"])
        assert len(rows) == 3
        assert rows[0][0] == "Feature"
        assert rows[1][0] == "Login"
        assert rows[2][0] == "Auth"

    def test_summary_pass_rate_formatted(self, tmp_path: Path) -> None:
        """Pass rate is formatted as a percentage string."""
        features = [_make_feature(pass_rate=85.5)]
        run = _make_run_summary(features=features, scenarios=[_make_scenario()])
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path)
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Summary"])
        assert rows[1][6] == "85.5%"

    def test_summary_duration_formatted(self, tmp_path: Path) -> None:
        """Duration is formatted with format_duration."""
        features = [_make_feature(duration=1.234)]
        run = _make_run_summary(features=features, scenarios=[_make_scenario()])
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path)
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Summary"])
        assert rows[1][7] == "1.234s"


class TestDetailsSheet:
    """Details sheet content."""

    def test_details_one_row_per_scenario(self, tmp_path: Path) -> None:
        """Details has one data row per scenario plus a header."""
        scenarios = [
            _make_scenario(scenario_name="S1"),
            _make_scenario(scenario_name="S2"),
        ]
        run = _make_run_summary(features=[_make_feature()], scenarios=scenarios)
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path)
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Details"])
        assert len(rows) == 3
        assert rows[1][1] == "S1"
        assert rows[2][1] == "S2"

    def test_details_custom_columns(self, tmp_path: Path) -> None:
        """Custom columns are respected in Details header and rows."""
        run = _make_run_summary(
            features=[_make_feature()],
            scenarios=[_make_scenario()],
        )
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path, columns=["feature", "status"])
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Details"])
        assert rows[0] == ["feature", "status"]
        assert rows[1] == ["Login", "passed"]


class TestFailuresSheet:
    """Failures sheet content."""

    def test_failures_only_failed(self, tmp_path: Path) -> None:
        """Failures sheet contains only failed scenarios."""
        scenarios = [
            _make_scenario(scenario_name="Pass", status="passed"),
            _make_scenario(
                scenario_name="Fail",
                status="failed",
                error_message="boom",
                error_type="AssertionError",
                traceback="Traceback here",
            ),
        ]
        run = _make_run_summary(features=[_make_feature()], scenarios=scenarios)
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path)
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Failures"])
        assert len(rows) == 2
        assert rows[1][1] == "Fail"
        assert rows[1][2] == "boom"
        assert rows[1][3] == "AssertionError"
        assert rows[1][4] == "Traceback here"

    def test_failures_empty_when_no_failures(self, tmp_path: Path) -> None:
        """Failures sheet has only header when no scenarios failed."""
        run = _make_run_summary(
            features=[_make_feature()],
            scenarios=[_make_scenario(status="passed")],
        )
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path)
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Failures"])
        assert len(rows) == 1


class TestTrendsSheet:
    """Trends sheet content."""

    def test_trends_one_row_per_entry(self, tmp_path: Path) -> None:
        """Trends sheet has one data row per history entry."""
        trends = [
            _make_history_entry(timestamp="2025-01-01T12:00:00+00:00"),
            _make_history_entry(timestamp="2025-01-02T12:00:00+00:00"),
        ]
        run = _make_run_summary(
            features=[_make_feature()],
            scenarios=[_make_scenario()],
        )
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path, trends=trends)
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Trends"])
        assert len(rows) == 3
        assert rows[1][0] == "2025-01-01T12:00:00+00:00"
        assert rows[1][1] == "85.5%"
        assert rows[2][0] == "2025-01-02T12:00:00+00:00"


class TestOnlyFailed:
    """only_failed filtering."""

    def test_only_failed_filters_details(self, tmp_path: Path) -> None:
        """only_failed=True filters Details but not Summary."""
        features = [_make_feature(total=2, passed=1, failed=1, pass_rate=50.0)]
        scenarios = [
            _make_scenario(scenario_name="Pass", status="passed"),
            _make_scenario(scenario_name="Fail", status="failed"),
        ]
        run = _make_run_summary(features=features, scenarios=scenarios)
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path, only_failed=True)
        doc = load(str(path))

        details_rows = _get_cell_texts(_get_tables(doc)["Details"])
        assert len(details_rows) == 2
        assert details_rows[1][1] == "Fail"

        summary_rows = _get_cell_texts(_get_tables(doc)["Summary"])
        assert len(summary_rows) == 2
        assert summary_rows[1][0] == "Login"


class TestEmptyRun:
    """Empty run with no scenarios."""

    def test_empty_run(self, tmp_path: Path) -> None:
        """Empty run produces Summary with headers only, no crash."""
        run = _make_run_summary(features=[], scenarios=[])
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path)
        doc = load(str(path))
        tables = _get_tables(doc)
        assert "Summary" in tables
        rows = _get_cell_texts(tables["Summary"])
        assert len(rows) == 1
        assert rows[0][0] == "Feature"


class TestTagsAndDuration:
    """Tags and duration serialization in Details."""

    def test_tags_semicolon_separated(self, tmp_path: Path) -> None:
        """Tags are joined with semicolons in Details."""
        run = _make_run_summary(
            features=[_make_feature()],
            scenarios=[_make_scenario(tags=["smoke", "auth"])],
        )
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path)
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Details"])
        assert rows[1][4] == "smoke;auth"

    def test_duration_formatted(self, tmp_path: Path) -> None:
        """Duration is formatted with format_duration in Details."""
        run = _make_run_summary(
            features=[_make_feature()],
            scenarios=[_make_scenario(duration=0.012)],
        )
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path)
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Details"])
        assert rows[1][3] == "12ms"


class TestEdgeCases:
    """Edge cases for branch coverage."""

    def test_error_with_type_in_details(self, tmp_path: Path) -> None:
        """Error column concatenates message and type when type is present."""
        run = _make_run_summary(
            features=[_make_feature()],
            scenarios=[
                _make_scenario(
                    status="failed",
                    error_message="boom",
                    error_type="ValueError",
                ),
            ],
        )
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path)
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Details"])
        assert rows[1][5] == "boom [ValueError]"

    def test_is_outline_column(self, tmp_path: Path) -> None:
        """is_outline column is serialized as 'true'/'false'."""
        run = _make_run_summary(
            features=[_make_feature()],
            scenarios=[_make_scenario(is_outline=True)],
        )
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path, columns=["feature", "is_outline"])
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Details"])
        assert rows[1][1] == "true"

    def test_skipped_status_in_details(self, tmp_path: Path) -> None:
        """Skipped scenario appears in Details with correct status."""
        run = _make_run_summary(
            features=[_make_feature()],
            scenarios=[_make_scenario(status="skipped")],
        )
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path)
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Details"])
        assert rows[1][2] == "skipped"

    def test_only_failed_no_failed_scenarios(self, tmp_path: Path) -> None:
        """only_failed=True with no failed scenarios produces empty Details."""
        run = _make_run_summary(
            features=[_make_feature()],
            scenarios=[_make_scenario(status="passed")],
        )
        path = tmp_path / "report.ods"
        ODSWriter.write(run, path, only_failed=True)
        doc = load(str(path))
        rows = _get_cell_texts(_get_tables(doc)["Details"])
        assert len(rows) == 1


class TestStatusStyles:
    """Status style creation covers all branches."""

    def test_status_style_without_bold(self, tmp_path: Path) -> None:
        """_create_status_style with bold=False does not crash."""
        from odf.opendocument import OpenDocumentSpreadsheet

        doc = OpenDocumentSpreadsheet()
        name = ODSWriter._create_status_style(doc, "DDFFDD", bold=False)
        assert name == "Status_DDFFDD"
