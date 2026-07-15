"""Tests for the history module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from behave_modern_sheets_report.history import History
from behave_modern_sheets_report.models import RunSummary
from tests._helpers import make_run_summary


class TestAppendLoadRoundtrip:
    """Tests for append + load roundtrip."""

    def test_roundtrip_preserves_data(self, tmp_path: Path) -> None:
        """Data is preserved across append and load."""
        hist = History(path=tmp_path / "history.json")
        rs = make_run_summary()
        entries = hist.append(rs)

        assert len(entries) == 1
        assert entries[0].run_id == "run-001"
        assert entries[0].total_features == 2
        assert entries[0].total_scenarios == 6
        assert entries[0].passed == 5
        assert entries[0].failed == 1
        assert entries[0].pass_rate == 83.33
        assert entries[0].duration == 10.5

        loaded = hist.load()
        assert len(loaded) == 1
        assert loaded[0].run_id == "run-001"
        assert loaded[0].total_features == 2
        assert loaded[0].passed == 5


class TestAppendMultiple:
    """Tests for multiple appends."""

    def test_multiple_entries_order(self, tmp_path: Path) -> None:
        """Most recent entry is at the end."""
        hist = History(path=tmp_path / "history.json")
        hist.append(make_run_summary(run_id="run-1"))
        hist.append(make_run_summary(run_id="run-2"))
        hist.append(make_run_summary(run_id="run-3"))

        loaded = hist.load()
        assert len(loaded) == 3
        assert loaded[0].run_id == "run-1"
        assert loaded[1].run_id == "run-2"
        assert loaded[2].run_id == "run-3"


class TestMaxEntries:
    """Tests for max_entries truncation."""

    def test_truncates_oldest(self, tmp_path: Path) -> None:
        """Entries beyond max_entries are truncated from the front."""
        hist = History(path=tmp_path / "history.json", max_entries=3)
        for i in range(5):
            hist.append(make_run_summary(run_id=f"run-{i}"))

        loaded = hist.load()
        assert len(loaded) == 3
        assert loaded[0].run_id == "run-2"
        assert loaded[1].run_id == "run-3"
        assert loaded[2].run_id == "run-4"

    def test_max_entries_one(self, tmp_path: Path) -> None:
        """max_entries=1 keeps only the last entry."""
        hist = History(path=tmp_path / "history.json", max_entries=1)
        hist.append(make_run_summary(run_id="run-1"))
        hist.append(make_run_summary(run_id="run-2"))

        loaded = hist.load()
        assert len(loaded) == 1
        assert loaded[0].run_id == "run-2"

    def test_max_entries_zero_raises(self, tmp_path: Path) -> None:
        """max_entries=0 raises ValueError."""
        with pytest.raises(ValueError, match="max_entries must be >= 1"):
            History(path=tmp_path / "history.json", max_entries=0)

    def test_max_entries_negative_raises(self, tmp_path: Path) -> None:
        """max_entries=-1 raises ValueError."""
        with pytest.raises(ValueError, match="max_entries must be >= 1"):
            History(path=tmp_path / "history.json", max_entries=-1)


class TestClear:
    """Tests for clear method."""

    def test_clear_removes_file(self, tmp_path: Path) -> None:
        """clear() removes the history file."""
        hist = History(path=tmp_path / "history.json")
        hist.append(make_run_summary())
        assert (tmp_path / "history.json").exists()

        hist.clear()
        assert not (tmp_path / "history.json").exists()

    def test_clear_without_file(self, tmp_path: Path) -> None:
        """clear() does not crash if file doesn't exist."""
        hist = History(path=tmp_path / "history.json")
        hist.clear()
        assert not (tmp_path / "history.json").exists()


class TestLoadEdgeCases:
    """Tests for load edge cases."""

    def test_load_nonexistent_returns_empty(self, tmp_path: Path) -> None:
        """load() returns [] if file doesn't exist."""
        hist = History(path=tmp_path / "nope.json")
        assert hist.load() == []

    def test_load_corrupt_json_returns_empty(self, tmp_path: Path) -> None:
        """load() returns [] if file contains invalid JSON."""
        path = tmp_path / "history.json"
        path.write_text("{invalid json", encoding="utf-8")
        hist = History(path=path)
        assert hist.load() == []

    def test_load_empty_file_returns_empty(self, tmp_path: Path) -> None:
        """load() returns [] if file is empty."""
        path = tmp_path / "history.json"
        path.write_text("", encoding="utf-8")
        hist = History(path=path)
        assert hist.load() == []

    def test_load_whitespace_only_returns_empty(self, tmp_path: Path) -> None:
        """load() returns [] if file contains only whitespace."""
        path = tmp_path / "history.json"
        path.write_text("   \n  \n", encoding="utf-8")
        hist = History(path=path)
        assert hist.load() == []

    def test_load_non_list_json_returns_empty(self, tmp_path: Path) -> None:
        """load() returns [] if JSON root is not a list."""
        path = tmp_path / "history.json"
        path.write_text('{"key": "value"}', encoding="utf-8")
        hist = History(path=path)
        assert hist.load() == []

    def test_load_permission_error_returns_empty(self, tmp_path: Path) -> None:
        """load() returns [] if the file cannot be read (PermissionError)."""
        path = tmp_path / "history.json"
        path.write_text("[]", encoding="utf-8")

        original_read = Path.read_text

        def raise_permission(self: Path, *args: object, **kwargs: object) -> str:
            raise PermissionError("denied")

        import unittest.mock

        with unittest.mock.patch.object(Path, "read_text", raise_permission):
            hist = History(path=path)
            assert hist.load() == []

        Path.read_text = original_read  # type: ignore[method-assign]

    def test_load_entry_with_non_dict_item_skipped(self, tmp_path: Path) -> None:
        """load() skips non-dict items in the JSON array."""
        path = tmp_path / "history.json"
        path.write_text('[42, "string"]', encoding="utf-8")
        hist = History(path=path)
        assert hist.load() == []


class TestAppendEmptyRun:
    """Tests for append with empty RunSummary."""

    def test_append_empty_run(self, tmp_path: Path) -> None:
        """append() with empty RunSummary stores zeros."""
        hist = History(path=tmp_path / "history.json")
        rs = RunSummary()
        entries = hist.append(rs)

        assert len(entries) == 1
        assert entries[0].total_features == 0
        assert entries[0].total_scenarios == 0
        assert entries[0].passed == 0
        assert entries[0].pass_rate == 0.0


class TestCustomPath:
    """Tests for custom path."""

    def test_custom_path(self, tmp_path: Path) -> None:
        """History works with a custom path."""
        custom = tmp_path / "subdir" / "custom.json"
        hist = History(path=custom)
        hist.append(make_run_summary(run_id="custom-run"))

        assert custom.exists()
        loaded = hist.load()
        assert len(loaded) == 1
        assert loaded[0].run_id == "custom-run"


class TestAtomicWrite:
    """Tests for atomic write behavior."""

    def test_no_tmp_residual(self, tmp_path: Path) -> None:
        """No .tmp file remains after append."""
        hist = History(path=tmp_path / "history.json")
        hist.append(make_run_summary())

        assert (tmp_path / "history.json").exists()
        assert not (tmp_path / "history.json.tmp").exists()


class TestAppendReturnsList:
    """Tests that append returns the complete list."""

    def test_append_returns_list_with_new_entry(self, tmp_path: Path) -> None:
        """append() returns list including the newly added entry."""
        hist = History(path=tmp_path / "history.json")
        hist.append(make_run_summary(run_id="run-1"))
        entries = hist.append(make_run_summary(run_id="run-2"))

        assert len(entries) == 2
        assert entries[0].run_id == "run-1"
        assert entries[1].run_id == "run-2"


class TestRunSummaryToEntry:
    """Tests for _run_summary_to_entry."""

    def test_all_fields_preserved(self, tmp_path: Path) -> None:
        """All fields from RunSummary are preserved in HistoryEntry."""
        hist = History(path=tmp_path / "history.json")
        rs = make_run_summary(
            run_id="test-run",
            passed=10,
            failed=2,
            skipped=1,
            undefined=1,
            total_features=3,
            total_scenarios=14,
            pass_rate=71.43,
            duration=42.5,
        )
        entry = hist._run_summary_to_entry(rs)

        assert entry.run_id == "test-run"
        assert entry.total_features == 3
        assert entry.total_scenarios == 14
        assert entry.passed == 10
        assert entry.failed == 2
        assert entry.skipped == 1
        assert entry.undefined == 1
        assert entry.pass_rate == 71.43
        assert entry.duration == 42.5
        assert entry.timestamp != ""


class TestDefaultPath:
    """Tests for default path."""

    def test_default_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default path is .behave-sheets-history.json in CWD."""
        monkeypatch.chdir(tmp_path)
        hist = History()
        hist.append(make_run_summary(run_id="default"))

        assert (tmp_path / ".behave-sheets-history.json").exists()
        loaded = hist.load()
        assert len(loaded) == 1
        assert loaded[0].run_id == "default"


class TestDeserializeWithMissingFields:
    """Tests for _deserialize with missing fields."""

    def test_deserialize_with_missing_fields(self, tmp_path: Path) -> None:
        """_deserialize uses defaults for missing fields."""
        path = tmp_path / "history.json"
        path.write_text(
            json.dumps([{"run_id": "partial", "passed": 3}]),
            encoding="utf-8",
        )
        hist = History(path=path)
        loaded = hist.load()

        assert len(loaded) == 1
        assert loaded[0].run_id == "partial"
        assert loaded[0].passed == 3
        assert loaded[0].failed == 0
        assert loaded[0].total_features == 0
        assert loaded[0].pass_rate == 0.0


class TestPermissionError:
    """Tests for permission error handling."""

    def test_permission_error_on_write(self, tmp_path: Path) -> None:
        """PermissionError on write is re-raised with clear message."""
        path = tmp_path / "history.json"
        hist = History(path=path)

        original_write = Path.write_text

        def raise_permission(self: Path, *args: object, **kwargs: object) -> int:
            raise PermissionError("denied")

        import unittest.mock

        with (
            unittest.mock.patch.object(Path, "write_text", raise_permission),
            pytest.raises(PermissionError, match="Cannot write history file"),
        ):
            hist.append(make_run_summary())

        Path.write_text = original_write  # type: ignore[method-assign]


class TestOSErrorOnReplace:
    """Tests for OSError handling during atomic replace."""

    def test_oserror_on_replace_cleans_tmp(self, tmp_path: Path) -> None:
        """OSError during os.replace cleans up tmp file and re-raises."""
        path = tmp_path / "history.json"
        hist = History(path=path)

        import unittest.mock

        with (
            unittest.mock.patch("os.replace", side_effect=OSError("replace failed")),
            pytest.raises(OSError, match="replace failed"),
        ):
            hist.append(make_run_summary())

        assert not (tmp_path / "history.json.tmp").exists()


class TestDeserializeNonNumericStrings:
    """Tests for _deserialize with non-numeric string values in numeric fields."""

    def test_non_numeric_passed_skips_entry(self, tmp_path: Path) -> None:
        """Entry with non-numeric 'passed' is skipped instead of crashing."""
        path = tmp_path / "history.json"
        path.write_text(
            json.dumps(
                [
                    {"run_id": "bad", "passed": "not_a_number"},
                    {"run_id": "good", "passed": 3},
                ]
            ),
            encoding="utf-8",
        )
        hist = History(path=path)
        loaded = hist.load()
        assert len(loaded) == 1
        assert loaded[0].run_id == "good"

    def test_non_numeric_pass_rate_skips_entry(self, tmp_path: Path) -> None:
        """Entry with non-numeric 'pass_rate' is skipped."""
        path = tmp_path / "history.json"
        path.write_text(
            json.dumps(
                [{"run_id": "bad", "pass_rate": "oops"}]
            ),
            encoding="utf-8",
        )
        hist = History(path=path)
        assert hist.load() == []

    def test_non_numeric_duration_skips_entry(self, tmp_path: Path) -> None:
        """Entry with non-numeric 'duration' is skipped."""
        path = tmp_path / "history.json"
        path.write_text(
            json.dumps(
                [{"run_id": "bad", "duration": "slow"}]
            ),
            encoding="utf-8",
        )
        hist = History(path=path)
        assert hist.load() == []
