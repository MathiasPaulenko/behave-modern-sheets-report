"""Tests for the CSV writer module."""

from __future__ import annotations

import csv
from io import StringIO

from behave_modern_sheets_report.csv_writer import COLUMN_MAP, CSVWriter
from behave_modern_sheets_report.models import RunSummary
from behave_modern_sheets_report.utils import STATUS_FAILED, STATUS_PASSED, STATUS_SKIPPED
from tests._helpers import make_scenario_result as _make_scenario


def _parse(stream: StringIO, delimiter: str = ",") -> list[dict[str, str]]:
    """Parse CSV content from a StringIO stream into a list of row dicts."""
    stream.seek(0)
    reader = csv.DictReader(stream, delimiter=delimiter)
    return list(reader)


class TestDefaultColumns:
    """Output with default columns."""

    def test_default_columns_header(self) -> None:
        """Header matches DEFAULT_COLUMNS exactly."""
        run = RunSummary(scenarios=[_make_scenario()])
        stream = StringIO()
        CSVWriter.write(run, stream)
        stream.seek(0)
        reader = csv.reader(stream)
        header = next(reader)
        assert header == ["feature", "scenario", "status", "duration", "tags", "error"]

    def test_default_columns_row(self) -> None:
        """A single row has the expected values for default columns."""
        scenario = _make_scenario(tags=["smoke", "auth"])
        run = RunSummary(scenarios=[scenario])
        stream = StringIO()
        CSVWriter.write(run, stream)
        rows = _parse(stream)
        assert len(rows) == 1
        row = rows[0]
        assert row["feature"] == "Login"
        assert row["scenario"] == "Successful login"
        assert row["status"] == "passed"
        assert row["duration"] == "1.234s"
        assert row["tags"] == "smoke;auth"
        assert row["error"] == ""


class TestSelectedColumns:
    """Output with a subset of columns."""

    def test_subset_columns(self) -> None:
        """Only the selected columns appear in header and rows."""
        run = RunSummary(scenarios=[_make_scenario()])
        stream = StringIO()
        CSVWriter.write(run, stream, columns=["feature", "status"])
        rows = _parse(stream)
        assert len(rows) == 1
        row = rows[0]
        assert set(row.keys()) == {"feature", "status"}
        assert row["feature"] == "Login"
        assert row["status"] == "passed"


class TestColumnOrder:
    """Output with columns in a non-default order."""

    def test_custom_order(self) -> None:
        """Columns appear in the specified order."""
        run = RunSummary(scenarios=[_make_scenario()])
        stream = StringIO()
        CSVWriter.write(run, stream, columns=["status", "feature"])
        stream.seek(0)
        reader = csv.reader(stream)
        header = next(reader)
        assert header == ["status", "feature"]
        rows = _parse(stream)
        assert rows[0]["status"] == "passed"
        assert rows[0]["feature"] == "Login"


class TestOnlyFailed:
    """Filtering by failed status."""

    def test_only_failed_true(self) -> None:
        """Only failed scenarios are written when only_failed=True."""
        scenarios = [
            _make_scenario(scenario_name="Pass", status=STATUS_PASSED),
            _make_scenario(scenario_name="Fail", status=STATUS_FAILED, error_message="boom"),
            _make_scenario(scenario_name="Skip", status=STATUS_SKIPPED),
        ]
        run = RunSummary(scenarios=scenarios)
        stream = StringIO()
        CSVWriter.write(run, stream, only_failed=True)
        rows = _parse(stream)
        assert len(rows) == 1
        assert rows[0]["scenario"] == "Fail"
        assert rows[0]["status"] == "failed"

    def test_only_failed_false_mixed(self) -> None:
        """All scenarios are written when only_failed=False with mixed statuses."""
        scenarios = [
            _make_scenario(scenario_name="Pass", status=STATUS_PASSED),
            _make_scenario(scenario_name="Fail", status=STATUS_FAILED, error_message="boom"),
            _make_scenario(scenario_name="Skip", status=STATUS_SKIPPED),
        ]
        run = RunSummary(scenarios=scenarios)
        stream = StringIO()
        CSVWriter.write(run, stream, only_failed=False)
        rows = _parse(stream)
        assert len(rows) == 3
        statuses = {r["status"] for r in rows}
        assert statuses == {"passed", "failed", "skipped"}


class TestDelimiters:
    """Different delimiter characters."""

    def test_comma_default(self) -> None:
        """Comma is the default delimiter."""
        run = RunSummary(scenarios=[_make_scenario()])
        stream = StringIO()
        CSVWriter.write(run, stream)
        stream.seek(0)
        first_line = stream.readline()
        assert "," in first_line
        assert ";" not in first_line

    def test_semicolon(self) -> None:
        """Semicolon delimiter produces semicolon-separated fields."""
        run = RunSummary(scenarios=[_make_scenario()])
        stream = StringIO()
        CSVWriter.write(run, stream, delimiter=";")
        rows = _parse(stream, delimiter=";")
        assert len(rows) == 1
        assert rows[0]["feature"] == "Login"

    def test_tab(self) -> None:
        """Tab delimiter produces tab-separated fields."""
        run = RunSummary(scenarios=[_make_scenario()])
        stream = StringIO()
        CSVWriter.write(run, stream, delimiter="\t")
        rows = _parse(stream, delimiter="\t")
        assert len(rows) == 1
        assert rows[0]["feature"] == "Login"


class TestTags:
    """Tag serialization."""

    def test_multiple_tags(self) -> None:
        """Multiple tags are joined with semicolons."""
        scenario = _make_scenario(tags=["smoke", "auth", "critical"])
        run = RunSummary(scenarios=[scenario])
        stream = StringIO()
        CSVWriter.write(run, stream)
        rows = _parse(stream)
        assert rows[0]["tags"] == "smoke;auth;critical"

    def test_empty_tags(self) -> None:
        """Empty tags list produces an empty string."""
        scenario = _make_scenario(tags=[])
        run = RunSummary(scenarios=[scenario])
        stream = StringIO()
        CSVWriter.write(run, stream)
        rows = _parse(stream)
        assert rows[0]["tags"] == ""


class TestDuration:
    """Duration formatting."""

    def test_seconds(self) -> None:
        """Duration >= 1s is formatted as 'X.XXXs'."""
        scenario = _make_scenario(duration=1.234)
        run = RunSummary(scenarios=[scenario])
        stream = StringIO()
        CSVWriter.write(run, stream)
        rows = _parse(stream)
        assert rows[0]["duration"] == "1.234s"

    def test_milliseconds(self) -> None:
        """Duration < 1s is formatted as 'Xms'."""
        scenario = _make_scenario(duration=0.012)
        run = RunSummary(scenarios=[scenario])
        stream = StringIO()
        CSVWriter.write(run, stream)
        rows = _parse(stream)
        assert rows[0]["duration"] == "12ms"

    def test_zero(self) -> None:
        """Duration < 0.001s is formatted as '0s'."""
        scenario = _make_scenario(duration=0.0)
        run = RunSummary(scenarios=[scenario])
        stream = StringIO()
        CSVWriter.write(run, stream)
        rows = _parse(stream)
        assert rows[0]["duration"] == "0s"


class TestError:
    """Error column formatting."""

    def test_error_with_type(self) -> None:
        """Error column concatenates message and type when type is present."""
        scenario = _make_scenario(
            status=STATUS_FAILED,
            error_message="Something went wrong",
            error_type="AssertionError",
        )
        run = RunSummary(scenarios=[scenario])
        stream = StringIO()
        CSVWriter.write(run, stream)
        rows = _parse(stream)
        assert rows[0]["error"] == "Something went wrong [AssertionError]"

    def test_error_without_type(self) -> None:
        """Error column is just the message when type is empty."""
        scenario = _make_scenario(
            status=STATUS_FAILED,
            error_message="Something went wrong",
        )
        run = RunSummary(scenarios=[scenario])
        stream = StringIO()
        CSVWriter.write(run, stream)
        rows = _parse(stream)
        assert rows[0]["error"] == "Something went wrong"

    def test_error_empty_passing(self) -> None:
        """Error column is empty for a passing scenario."""
        scenario = _make_scenario(status=STATUS_PASSED)
        run = RunSummary(scenarios=[scenario])
        stream = StringIO()
        CSVWriter.write(run, stream)
        rows = _parse(stream)
        assert rows[0]["error"] == ""


class TestEmptyStream:
    """Empty run with no scenarios."""

    def test_header_only(self) -> None:
        """Header is written with zero data rows when no scenarios exist."""
        run = RunSummary(scenarios=[])
        stream = StringIO()
        CSVWriter.write(run, stream)
        stream.seek(0)
        reader = csv.reader(stream)
        header = next(reader)
        assert header == ["feature", "scenario", "status", "duration", "tags", "error"]
        remaining = list(reader)
        assert remaining == []


class TestRoundtrip:
    """CSV output is parseable by csv.reader (roundtrip)."""

    def test_roundtrip(self) -> None:
        """Write then read back produces consistent data."""
        scenarios = [
            _make_scenario(
                scenario_name="S1",
                status=STATUS_PASSED,
                tags=["a", "b"],
                duration=1.5,
            ),
            _make_scenario(
                scenario_name="S2",
                status=STATUS_FAILED,
                error_message="oops",
                error_type="ValueError",
                duration=0.005,
            ),
        ]
        run = RunSummary(scenarios=scenarios)
        stream = StringIO()
        CSVWriter.write(run, stream)
        rows = _parse(stream)
        assert len(rows) == 2
        assert rows[0]["scenario"] == "S1"
        assert rows[0]["tags"] == "a;b"
        assert rows[0]["duration"] == "1.500s"
        assert rows[1]["scenario"] == "S2"
        assert rows[1]["error"] == "oops [ValueError]"
        assert rows[1]["duration"] == "5ms"


class TestIsOutline:
    """is_outline serialization."""

    def test_true(self) -> None:
        """is_outline=True is serialized as 'true'."""
        scenario = _make_scenario(is_outline=True)
        run = RunSummary(scenarios=[scenario])
        stream = StringIO()
        CSVWriter.write(run, stream, columns=["feature", "is_outline"])
        rows = _parse(stream)
        assert rows[0]["is_outline"] == "true"

    def test_false(self) -> None:
        """is_outline=False is serialized as 'false'."""
        scenario = _make_scenario(is_outline=False)
        run = RunSummary(scenarios=[scenario])
        stream = StringIO()
        CSVWriter.write(run, stream, columns=["feature", "is_outline"])
        rows = _parse(stream)
        assert rows[0]["is_outline"] == "false"


class TestColumnMap:
    """COLUMN_MAP integrity."""

    def test_all_fields_mapped(self) -> None:
        """Every COLUMN_MAP value corresponds to a ScenarioResult field."""
        scenario = _make_scenario()
        for col_name, field_name in COLUMN_MAP.items():
            assert hasattr(scenario, field_name), (
                f"Missing field {field_name} for column {col_name}"
            )
