"""History — persistent run history for the sheets report formatter.

Stores lightweight :class:`HistoryEntry` records in a JSON file so that
successive runs can be compared. Uses atomic writes (write to ``.tmp``,
then ``os.replace``) to prevent data corruption.
"""

from __future__ import annotations

import contextlib
import json
import os
from dataclasses import asdict
from pathlib import Path

from .models import HistoryEntry, RunSummary


class History:
    """Persistent run history backed by a JSON file.

    Args:
        path: Path to the history file. Defaults to
            ``.behave-sheets-history.json`` in the current working directory.
        max_entries: Maximum number of entries to retain. Must be >= 1.

    Raises:
        ValueError: If ``max_entries`` is less than 1.
    """

    def __init__(self, path: Path | None = None, max_entries: int = 100) -> None:
        if max_entries < 1:
            raise ValueError(f"max_entries must be >= 1, got {max_entries}")
        self._path = path if path is not None else Path(".behave-sheets-history.json")
        self._max_entries = max_entries

    def append(self, run_summary: RunSummary) -> list[HistoryEntry]:
        """Append a run summary to the history and return all entries.

        Args:
            run_summary: The completed :class:`RunSummary` to record.

        Returns:
            The full list of :class:`HistoryEntry` records after appending
            and truncation.

        Raises:
            PermissionError: If the history file cannot be written.
        """
        entry = self._run_summary_to_entry(run_summary)
        entries = self.load()
        entries.append(entry)
        if len(entries) > self._max_entries:
            entries = entries[-self._max_entries :]
        self._write_atomic(entries)
        return entries

    def load(self) -> list[HistoryEntry]:
        """Load history entries from the JSON file.

        Returns:
            A list of :class:`HistoryEntry` records. Returns ``[]`` if the
            file does not exist, is empty, cannot be read, or contains
            invalid JSON.
        """
        try:
            raw = self._path.read_text(encoding="utf-8")
        except (FileNotFoundError, PermissionError):
            return []
        if not raw.strip():
            return []
        return self._deserialize(raw)

    def clear(self) -> None:
        """Remove the history file if it exists.

        Does not raise if the file is already absent.
        """
        with contextlib.suppress(FileNotFoundError):
            self._path.unlink()

    def _run_summary_to_entry(self, run_summary: RunSummary) -> HistoryEntry:
        """Convert a :class:`RunSummary` to a :class:`HistoryEntry`.

        Args:
            run_summary: The run summary to convert.

        Returns:
            A :class:`HistoryEntry` with the run's aggregate metrics.
        """
        return HistoryEntry(
            run_id=run_summary.run_id,
            timestamp=run_summary.end_time,
            total_features=run_summary.total_features,
            total_scenarios=run_summary.total_scenarios,
            passed=run_summary.passed,
            failed=run_summary.failed,
            skipped=run_summary.skipped,
            undefined=run_summary.undefined,
            pass_rate=run_summary.pass_rate,
            duration=run_summary.duration,
        )

    def _write_atomic(self, data: list[HistoryEntry]) -> None:
        """Write entries to the history file atomically.

        Writes to a ``.tmp`` file first, then uses ``os.replace`` to swap
        it into place.

        Args:
            data: The list of entries to persist.

        Raises:
            PermissionError: If the file cannot be written.
            OSError: If the atomic replace fails.
        """
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            tmp_path.write_text(self._serialize(data), encoding="utf-8")
        except PermissionError as exc:
            raise PermissionError(f"Cannot write history file {self._path}: {exc}") from exc
        try:
            os.replace(tmp_path, self._path)
        except OSError:
            with contextlib.suppress(FileNotFoundError):
                tmp_path.unlink()
            raise

    def _serialize(self, entries: list[HistoryEntry]) -> str:
        """Serialize entries to a JSON string.

        Args:
            entries: List of :class:`HistoryEntry` objects.

        Returns:
            A JSON string with ``indent=2``.
        """
        return json.dumps([asdict(e) for e in entries], indent=2)

    def _deserialize(self, raw: str) -> list[HistoryEntry]:
        """Deserialize a JSON string to a list of entries.

        Args:
            raw: A JSON string containing an array of entry dicts.

        Returns:
            A list of :class:`HistoryEntry` records. Returns ``[]`` if the
            JSON is invalid or does not contain a list.
        """
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        entries: list[HistoryEntry] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                entries.append(
                    HistoryEntry(
                        run_id=str(item.get("run_id", "")),
                        timestamp=str(item.get("timestamp", "")),
                        total_features=int(item.get("total_features", 0)),
                        total_scenarios=int(item.get("total_scenarios", 0)),
                        passed=int(item.get("passed", 0)),
                        failed=int(item.get("failed", 0)),
                        skipped=int(item.get("skipped", 0)),
                        undefined=int(item.get("undefined", 0)),
                        pass_rate=float(item.get("pass_rate", 0.0)),
                        duration=float(item.get("duration", 0.0)),
                    )
                )
            except (TypeError, ValueError):
                continue
        return entries


__all__ = ["History"]
