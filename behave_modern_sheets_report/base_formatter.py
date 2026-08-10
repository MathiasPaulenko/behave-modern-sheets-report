"""Base formatter with the common Behave lifecycle for spreadsheet reports.

:class:`XLSXFormatter`, :class:`ODSFormatter`, and :class:`CSVFormatter`
share identical event collection and Behave lifecycle hooks.  This module
provides :class:`BaseSheetsFormatter` so subclasses only need to declare
their writer class, default filename, and whether they use trend history.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from behave.formatter.base import Formatter as _BaseFormatter  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    _BaseFormatter = object  # type: ignore[assignment, misc, unused-ignore]

from .collector import Collector
from .history import History
from .models import HistoryEntry, RunSummary
from .utils import parse_bool, parse_columns, parse_delimiter

__all__ = ["BaseSheetsFormatter"]


class BaseSheetsFormatter(_BaseFormatter):  # type: ignore[misc]
    """Common base for XLSX, ODS, and CSV Behave formatters.

    Subclasses must set ``_default_filename``, ``_use_history``, and implement
    :meth:`_write_report`.

    Attributes:
        name: Formatter name registered with Behave.
        description: Human-readable description for ``--format-help``.
        _default_filename: Fallback filename when stream_opener has no name.
        _use_history: Whether to persist run history for trend data.
    """

    name = "sheets-modern"
    description = "Spreadsheet report for Behave"
    _default_filename: str = "report"
    _use_history: bool = True

    def __init__(self, stream_opener: Any = None, config: Any = None) -> None:
        """Initialize the formatter with user options and a collector.

        Args:
            stream_opener: Behave stream opener for the report output.
            config: Behave configuration object with ``userdata`` dict.
        """
        self._stream_opener = stream_opener
        self._collector = Collector()

        userdata: dict[str, str] = {}
        if config is not None:
            raw_userdata = getattr(config, "userdata", None)
            if isinstance(raw_userdata, dict):
                userdata = raw_userdata

        self._columns = parse_columns(userdata.get("report_columns"))
        self._only_failed = parse_bool(userdata.get("report_only_failed"))
        self._delimiter = parse_delimiter(userdata.get("report_delimiter"))
        self._clear_history = parse_bool(userdata.get("report_clear_history"))
        self._history_path: str | None = userdata.get("report_history_path")
        max_history_raw = userdata.get("report_max_history")
        try:
            max_history = int(max_history_raw) if max_history_raw else 100
        except (TypeError, ValueError):
            max_history = 100
        if max_history < 1:
            max_history = 100
        self._max_history = max_history
        self._closed = False

    def uri(self, uri: str) -> None:
        """Behave hook: a feature file URI is available.

        Args:
            uri: The URI of the feature file.
        """

    def feature(self, feature: Any) -> None:
        """Behave hook: a feature has started.

        Args:
            feature: A Behave ``Feature`` object (or mock).
        """
        self._collector.start_feature(feature)

    def background(self, background: Any) -> None:
        """Behave hook: background steps are about to run.

        Tells the collector that subsequent steps belong to the background
        so they can be counted separately.

        Args:
            background: A Behave ``Background`` object (or mock).
        """
        self._collector.start_background(background)

    def rule(self, rule: Any) -> None:
        """Behave hook: a rule has started (Gherkin v6).

        Args:
            rule: A Behave ``Rule`` object (or mock).
        """

    def scenario(self, scenario: Any) -> None:
        """Behave hook: a scenario has started.

        Finalizes the previous scenario if one is in progress, then starts
        tracking the new scenario.

        Args:
            scenario: A Behave ``Scenario`` object (or mock).
        """
        if self._collector._current_scenario is not None:
            self._collector.end_scenario()
        self._collector.start_scenario(scenario)

    def step(self, step: Any) -> None:
        """Behave hook: a step has been queued.

        Args:
            step: A Behave ``Step`` object (or mock).
        """
        self._collector.start_step(step)

    def result(self, step: Any) -> None:
        """Behave hook: a step result is available.

        Args:
            step: A Behave ``Step`` object with final status (or mock).
        """
        self._collector.end_step(step)

    def eof(self) -> None:
        """Behave hook: end of feature file.

        Finalizes any in-progress scenario and feature for the current file.
        """
        if self._collector._current_scenario is not None:
            self._collector.end_scenario()
        if self._collector._current_feature is not None:
            self._collector.end_feature()

    def close(self) -> None:
        """Behave hook: finalize the run and write the report.

        Calls ``eof()`` to finalize remaining scenario/feature, optionally
        appends the run to :class:`History` for trend data, resolves the
        output, and delegates to :meth:`_write_report`.

        Subsequent calls are no-ops to prevent duplicate history entries.
        """
        if self._closed:
            return
        self._closed = True
        self.eof()
        run_summary = self._collector.finalize()

        trends: list[HistoryEntry] = []
        if self._use_history:
            history_path = Path(self._history_path) if self._history_path else None
            history = History(path=history_path, max_entries=self._max_history)
            if self._clear_history:
                history.clear()
            trends = history.append(run_summary)

        self._write_report(run_summary, trends)

    def _resolve_output_path(self) -> str:
        """Resolve the output file path for the report.

        Uses ``stream_opener.name`` when available, otherwise falls back
        to ``_default_filename``.

        Returns:
            The file path as a string.
        """
        if self._stream_opener is not None:
            name = getattr(self._stream_opener, "name", None)
            if name:
                return str(name)
        return self._default_filename

    def _write_report(
        self,
        run_summary: RunSummary,
        trends: list[HistoryEntry],
    ) -> None:
        """Write the report.

        Subclasses must implement this method to delegate to their
        respective writer (XLSXWriter, ODSWriter, CSVWriter, etc.).

        Args:
            run_summary: The complete run summary.
            trends: Historical run entries for the Trends sheet.
        """
        raise NotImplementedError
