"""Behave formatter that produces an XLSX report with trend history.

Register in ``behave.ini``::

    [behave.formatters]
    xlsx-modern = behave_modern_sheets_report.xlsx_formatter:XLSXFormatter

Then run::

    behave -f xlsx-modern -o report.xlsx

The formatter delegates event collection to :class:`Collector`, persists
run history via :class:`History`, and serialization to :class:`XLSXWriter`.
"""

from __future__ import annotations

from pathlib import Path

from .base_formatter import BaseSheetsFormatter
from .models import HistoryEntry, RunSummary
from .xlsx_writer import XLSXWriter

__all__ = ["XLSXFormatter"]


class XLSXFormatter(BaseSheetsFormatter):
    """Behave formatter that writes an XLSX execution report with trends."""

    name = "xlsx-modern"
    description = "Excel report for Behave"
    _default_filename = "report.xlsx"

    def _write_report(
        self,
        run_summary: RunSummary,
        trends: list[HistoryEntry],
    ) -> None:
        """Write the XLSX report via :class:`XLSXWriter`.

        Args:
            run_summary: The complete run summary.
            trends: Historical run entries for the Trends sheet.
        """
        output_path = Path(self._resolve_output_path())
        XLSXWriter.write(
            run_summary,
            output_path,
            columns=self._columns,
            only_failed=self._only_failed,
            trends=trends,
        )
