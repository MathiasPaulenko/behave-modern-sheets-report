"""Behave formatter that produces a CSV report.

Register in ``behave.ini``::

    [behave.formatters]
    csv-modern = behave_modern_sheets_report.csv_formatter:CSVFormatter

Then run::

    behave -f csv-modern -o report.csv

The formatter is a thin adapter: it delegates event collection to
:class:`Collector` and serialization to :class:`CSVWriter`.
"""

from __future__ import annotations

import sys
from typing import TextIO

from .base_formatter import BaseSheetsFormatter
from .csv_writer import CSVWriter
from .models import HistoryEntry, RunSummary

__all__ = ["CSVFormatter"]


class CSVFormatter(BaseSheetsFormatter):
    """Behave formatter that writes a CSV execution report.

    Inherits the Behave lifecycle hooks from :class:`BaseSheetsFormatter`
    and delegates CSV serialization to :class:`CSVWriter`.
    """

    name = "csv-modern"
    description = "CSV report for Behave"
    _default_filename = "report.csv"
    _use_history = False

    def _write_report(
        self,
        run_summary: RunSummary,
        trends: list[HistoryEntry],
    ) -> None:
        """Write the CSV report via :class:`CSVWriter`.

        Args:
            run_summary: The complete run summary.
            trends: Historical run entries (unused for CSV).
        """
        stream = self._resolve_stream()
        try:
            CSVWriter.write(
                run_summary,
                stream,
                columns=self._columns,
                delimiter=self._delimiter,
                only_failed=self._only_failed,
            )
        finally:
            if hasattr(stream, "flush"):
                stream.flush()

    def _resolve_stream(self) -> TextIO:
        """Resolve the output stream for the CSV report.

        Uses ``stream_opener.open()`` when available, otherwise falls back
        to ``sys.stdout``.  If ``open()`` returns ``None``, falls back to
        ``sys.stdout`` as well.

        Returns:
            A writable text stream.
        """
        if self._stream_opener is not None:
            opener = getattr(self._stream_opener, "open", None)
            if callable(opener):
                stream: TextIO = opener()
                if stream is not None:
                    return stream
        return sys.stdout
