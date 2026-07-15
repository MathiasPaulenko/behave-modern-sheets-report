"""Behave formatter that produces an ODS report with trend history.

Register in ``behave.ini``::

    [behave.formatters]
    ods-modern = behave_modern_sheets_report.ods_formatter:ODSFormatter

Then run::

    behave -f ods-modern -o report.ods

The formatter delegates event collection to :class:`Collector`, persists
run history via :class:`History`, and serialization to :class:`ODSWriter`.
"""

from __future__ import annotations

from pathlib import Path

from .base_formatter import BaseSheetsFormatter
from .models import HistoryEntry, RunSummary
from .ods_writer import ODSWriter

__all__ = ["ODSFormatter"]


class ODSFormatter(BaseSheetsFormatter):
    """Behave formatter that writes an ODS execution report with trends."""

    name = "ods-modern"
    description = "OpenDocument Spreadsheet report for Behave"
    _default_filename = "report.ods"

    def _write_report(
        self,
        run_summary: RunSummary,
        trends: list[HistoryEntry],
    ) -> None:
        """Write the ODS report via :class:`ODSWriter`.

        Args:
            run_summary: The complete run summary.
            trends: Historical run entries for the Trends sheet.
        """
        output_path = Path(self._resolve_output_path())
        ODSWriter.write(
            run_summary,
            output_path,
            columns=self._columns,
            only_failed=self._only_failed,
            trends=trends,
        )
