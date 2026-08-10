"""CSV writing logic using only the Python standard library.

This module provides ``CSVWriter``, a static utility that serialises a
``RunSummary`` into CSV format via ``csv.DictWriter``.  No Behave or
openpyxl dependencies are required — only ``csv`` from the stdlib.
"""

from __future__ import annotations

import csv
from typing import TextIO

from .models import RunSummary, ScenarioResult
from .utils import DEFAULT_COLUMNS, STATUS_FAILED, format_duration

COLUMN_MAP: dict[str, str] = {
    "feature": "feature_name",
    "scenario": "scenario_name",
    "status": "status",
    "duration": "duration",
    "tags": "tags",
    "error": "error_message",
    "error_type": "error_type",
    "traceback": "traceback",
    "steps": "step_count",
    "passed_steps": "passed_steps",
    "failed_steps": "failed_steps",
    "skipped_steps": "skipped_steps",
    "file": "file",
    "line": "line",
    "rule": "rule",
    "is_outline": "is_outline",
    "feature_tags": "feature_tags",
    "background_steps": "background_steps",
    "has_data_table": "has_data_table",
    "has_docstring": "has_docstring",
}

__all__ = ["COLUMN_MAP", "CSVWriter", "scenario_cell_value"]


def scenario_cell_value(scenario: ScenarioResult, col: str) -> str:
    """Extract a single cell value from ``scenario`` for column ``col``.

    Args:
        scenario: The scenario result to serialize.
        col: The column name to extract.

    Returns:
        The string value for the cell.
    """
    field = COLUMN_MAP[col]
    if col == "tags":
        return ";".join(scenario.tags)
    if col == "feature_tags":
        return ";".join(scenario.feature_tags)
    if col == "duration":
        return format_duration(scenario.duration)
    if col == "error":
        if scenario.error_type:
            return f"{scenario.error_message} [{scenario.error_type}]"
        return scenario.error_message
    if col == "is_outline":
        return "true" if scenario.is_outline else "false"
    if col == "has_data_table":
        return "true" if scenario.has_data_table else "false"
    if col == "has_docstring":
        return "true" if scenario.has_docstring else "false"
    return str(getattr(scenario, field))


class CSVWriter:
    """Write scenario results as CSV using ``csv.DictWriter``."""

    @staticmethod
    def write(
        run_summary: RunSummary,
        stream: TextIO,
        columns: list[str] | None = None,
        delimiter: str = ",",
        only_failed: bool = False,
    ) -> None:
        """Serialize ``run_summary`` scenarios to ``stream`` as CSV.

        Args:
            run_summary: The complete run summary containing scenarios to write.
            stream: A writable text stream (e.g. ``StringIO`` or a file object).
            columns: Ordered list of column names to include.  When ``None``,
                ``DEFAULT_COLUMNS`` is used.
            delimiter: Field separator character (default ``,``).
            only_failed: When ``True``, only scenarios with status
                ``STATUS_FAILED`` are written.

        Returns:
            ``None``.  The CSV content is written directly to ``stream``.
        """
        cols = columns if columns is not None else DEFAULT_COLUMNS
        writer = csv.DictWriter(stream, fieldnames=cols, delimiter=delimiter)
        writer.writeheader()

        for scenario in run_summary.scenarios:
            if only_failed and scenario.status != STATUS_FAILED:
                continue
            writer.writerow(CSVWriter._row(scenario, cols))

    @staticmethod
    def _row(scenario: ScenarioResult, columns: list[str]) -> dict[str, str]:
        """Build a single CSV row dict from ``scenario`` for the given columns.

        Args:
            scenario: The scenario result to serialize.
            columns: The column names to include in the row.

        Returns:
            A dictionary mapping column names to their string values.
        """
        return {col: scenario_cell_value(scenario, col) for col in columns}
