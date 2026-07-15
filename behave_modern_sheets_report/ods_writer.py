"""ODS writing logic using odfpy.

This module provides ``ODSWriter``, a static utility that serialises a
``RunSummary`` into a multi-sheet OpenDocument spreadsheet.  Requires the
``odfpy`` package (installed via the ``[ods]`` extra).

Auto-filters are not supported by odfpy's API and are therefore omitted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from odf.opendocument import OpenDocumentSpreadsheet  # type: ignore[import-untyped]
from odf.style import Style, TableCellProperties, TextProperties  # type: ignore[import-untyped]
from odf.table import Table, TableCell, TableRow  # type: ignore[import-untyped]
from odf.text import P  # type: ignore[import-untyped]

from .csv_writer import scenario_cell_value
from .models import FeatureSummary, HistoryEntry, RunSummary, ScenarioResult
from .utils import (
    DEFAULT_COLUMNS,
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_SKIPPED,
    format_duration,
)

_SUMMARY_HEADERS = [
    "Feature",
    "Total",
    "Passed",
    "Failed",
    "Skipped",
    "Undefined",
    "Pass Rate",
    "Duration",
]

_FAILURES_HEADERS = [
    "Feature",
    "Scenario",
    "Error",
    "Error Type",
    "Traceback",
    "File",
    "Line",
]

_TRENDS_HEADERS = [
    "Timestamp",
    "Pass Rate",
    "Total Features",
    "Total Scenarios",
    "Passed",
    "Failed",
    "Skipped",
    "Undefined",
    "Duration",
]

__all__ = ["ODSWriter"]


class ODSWriter:
    """Write scenario results as a multi-sheet ODS document."""

    @staticmethod
    def write(
        run_summary: RunSummary,
        path: Path,
        columns: list[str] | None = None,
        only_failed: bool = False,
        trends: list[HistoryEntry] | None = None,
    ) -> None:
        """Serialize ``run_summary`` into an ODS file at ``path``.

        Args:
            run_summary: The complete run summary containing features and
                scenarios to write.
            path: Destination file path for the ``.ods`` file.
            columns: Ordered list of column names for the Details sheet.
                When ``None``, ``DEFAULT_COLUMNS`` is used.
            only_failed: When ``True``, the Details sheet only includes
                failed scenarios.  Summary and Trends remain complete.
            trends: Historical run entries for the Trends sheet.  When
                ``None`` or empty, the Trends sheet is omitted.
        """
        cols = columns if columns is not None else DEFAULT_COLUMNS
        doc = OpenDocumentSpreadsheet()

        bold_style = ODSWriter._create_bold_style(doc)
        passed_style = ODSWriter._create_status_style(doc, "C6EFCE", bold=True)
        failed_style = ODSWriter._create_status_style(doc, "FFC7CE", bold=True)
        skipped_style = ODSWriter._create_status_style(doc, "FFEB9C", bold=True)
        status_styles: dict[str, str] = {
            STATUS_PASSED: passed_style,
            STATUS_FAILED: failed_style,
            STATUS_SKIPPED: skipped_style,
        }

        ODSWriter._write_summary(doc, run_summary.features, bold_style)
        ODSWriter._write_details(
            doc, run_summary.scenarios, cols, only_failed, bold_style, status_styles
        )
        ODSWriter._write_failures(doc, run_summary.scenarios, bold_style)
        if trends is not None and len(trends) > 0:
            ODSWriter._write_trends(doc, trends, bold_style)

        path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(path))

    @staticmethod
    def _write_summary(
        doc: OpenDocumentSpreadsheet,
        features: list[FeatureSummary],
        bold_style: str,
    ) -> None:
        """Write the Summary sheet with one row per feature.

        Args:
            doc: The ODF spreadsheet document.
            features: List of feature summaries to write.
            bold_style: Name of the bold style for headers.
        """
        table = Table(name="Summary")
        ODSWriter._add_header_row(table, _SUMMARY_HEADERS, bold_style)

        for feature in features:
            row = TableRow()
            values = [
                feature.feature_name,
                str(feature.total_scenarios),
                str(feature.passed),
                str(feature.failed),
                str(feature.skipped),
                str(feature.undefined),
                f"{feature.pass_rate:.1f}%",
                format_duration(feature.duration),
            ]
            for value in values:
                row.addElement(ODSWriter._text_cell(value))
            table.addElement(row)

        doc.spreadsheet.addElement(table)

    @staticmethod
    def _write_details(
        doc: OpenDocumentSpreadsheet,
        scenarios: list[ScenarioResult],
        columns: list[str],
        only_failed: bool,
        bold_style: str,
        status_styles: dict[str, str],
    ) -> None:
        """Write the Details sheet with one row per scenario.

        Args:
            doc: The ODF spreadsheet document.
            scenarios: List of scenario results to write.
            columns: Column names to include.
            only_failed: When ``True``, only failed scenarios are included.
            bold_style: Name of the bold style for headers.
            status_styles: Mapping of status to style name for conditional fill.
        """
        table = Table(name="Details")
        ODSWriter._add_header_row(table, columns, bold_style)

        for scenario in scenarios:
            if only_failed and scenario.status != STATUS_FAILED:
                continue
            row = TableRow()
            for col in columns:
                value = ODSWriter._scenario_value(scenario, col)
                style_name = status_styles.get(scenario.status) if col == "status" else None
                row.addElement(ODSWriter._text_cell(value, style_name))
            table.addElement(row)

        doc.spreadsheet.addElement(table)

    @staticmethod
    def _write_failures(
        doc: OpenDocumentSpreadsheet,
        scenarios: list[ScenarioResult],
        bold_style: str,
    ) -> None:
        """Write the Failures sheet with only failed scenarios.

        Args:
            doc: The ODF spreadsheet document.
            scenarios: List of scenario results to filter.
            bold_style: Name of the bold style for headers.
        """
        table = Table(name="Failures")
        ODSWriter._add_header_row(table, _FAILURES_HEADERS, bold_style)

        for scenario in scenarios:
            if scenario.status != STATUS_FAILED:
                continue
            row = TableRow()
            values = [
                scenario.feature_name,
                scenario.scenario_name,
                scenario.error_message,
                scenario.error_type,
                scenario.traceback,
                scenario.file,
                str(scenario.line),
            ]
            for value in values:
                row.addElement(ODSWriter._text_cell(value))
            table.addElement(row)

        doc.spreadsheet.addElement(table)

    @staticmethod
    def _write_trends(
        doc: OpenDocumentSpreadsheet,
        trends: list[HistoryEntry],
        bold_style: str,
    ) -> None:
        """Write the Trends sheet with one row per history entry.

        Args:
            doc: The ODF spreadsheet document.
            trends: List of historical run entries.
            bold_style: Name of the bold style for headers.
        """
        table = Table(name="Trends")
        ODSWriter._add_header_row(table, _TRENDS_HEADERS, bold_style)

        for entry in trends:
            row = TableRow()
            values = [
                entry.timestamp,
                f"{entry.pass_rate:.1f}%",
                str(entry.total_features),
                str(entry.total_scenarios),
                str(entry.passed),
                str(entry.failed),
                str(entry.skipped),
                str(entry.undefined),
                format_duration(entry.duration),
            ]
            for value in values:
                row.addElement(ODSWriter._text_cell(value))
            table.addElement(row)

        doc.spreadsheet.addElement(table)

    @staticmethod
    def _add_header_row(table: Table, headers: list[str], bold_style: str) -> None:
        """Add a header row with bold styling to a table.

        Args:
            table: The ODF table to add the row to.
            headers: List of header labels.
            bold_style: Name of the bold style to apply.
        """
        row = TableRow()
        for header in headers:
            row.addElement(ODSWriter._text_cell(header, bold_style))
        table.addElement(row)

    @staticmethod
    def _text_cell(value: str, style_name: str | None = None) -> TableCell:
        """Create a text cell with an optional style.

        Args:
            value: The cell text content.
            style_name: Optional style name to apply.

        Returns:
            An ODF ``TableCell`` element.
        """
        attrs: dict[str, Any] = {}
        if style_name is not None:
            attrs["stylename"] = style_name
        cell = TableCell(**attrs)
        cell.addElement(P(text=value))
        return cell

    @staticmethod
    def _scenario_value(scenario: ScenarioResult, col: str) -> str:
        """Extract a single cell value from ``scenario`` for column ``col``.

        Args:
            scenario: The scenario result to serialize.
            col: The column name to extract.

        Returns:
            The string value for the cell.
        """
        return scenario_cell_value(scenario, col)

    @staticmethod
    def _create_bold_style(doc: OpenDocumentSpreadsheet) -> str:
        """Create and register a bold text style in the document.

        Args:
            doc: The ODF spreadsheet document.

        Returns:
            The name of the registered style.
        """
        style = Style(name="BoldHeader")
        style.addElement(TextProperties(fontweight="bold"))
        doc.styles.addElement(style)
        return "BoldHeader"

    @staticmethod
    def _create_status_style(
        doc: OpenDocumentSpreadsheet,
        bg_color: str,
        bold: bool = False,
    ) -> str:
        """Create and register a cell style with background color.

        Args:
            doc: The ODF spreadsheet document.
            bg_color: Hex color code for the background (without leading ``#``).
            bold: Whether the text should be bold.

        Returns:
            The name of the registered style.
        """
        name = f"Status_{bg_color}"
        style = Style(name=name)
        props = TableCellProperties(backgroundcolor=f"#{bg_color}")
        style.addElement(props)
        if bold:
            style.addElement(TextProperties(fontweight="bold"))
        doc.styles.addElement(style)
        return name
