"""Tests for the models module."""

from __future__ import annotations

from behave_modern_sheets_report.models import (
    FeatureSummary,
    HistoryEntry,
    RunSummary,
    ScenarioResult,
)


class TestScenarioResult:
    """Tests for ScenarioResult dataclass."""

    def test_defaults(self) -> None:
        """Constructor with no arguments uses sensible defaults."""
        sr = ScenarioResult()
        assert sr.feature_name == ""
        assert sr.scenario_name == ""
        assert sr.status == ""
        assert sr.duration == 0.0
        assert sr.tags == []
        assert sr.error_message == ""
        assert sr.error_type == ""
        assert sr.traceback == ""
        assert sr.step_count == 0
        assert sr.passed_steps == 0
        assert sr.failed_steps == 0
        assert sr.skipped_steps == 0
        assert sr.file == ""
        assert sr.line == 0
        assert sr.rule == ""
        assert sr.is_outline is False

    def test_all_fields(self) -> None:
        """Constructor with all fields specified."""
        sr = ScenarioResult(
            feature_name="Login",
            scenario_name="Successful login",
            status="passed",
            duration=1.23,
            tags=["smoke", "auth"],
            error_message="",
            error_type="",
            traceback="",
            step_count=5,
            passed_steps=5,
            failed_steps=0,
            skipped_steps=0,
            file="features/login.feature",
            line=10,
            rule="Auth rule",
            is_outline=True,
        )
        assert sr.feature_name == "Login"
        assert sr.scenario_name == "Successful login"
        assert sr.status == "passed"
        assert sr.duration == 1.23
        assert sr.tags == ["smoke", "auth"]
        assert sr.step_count == 5
        assert sr.passed_steps == 5
        assert sr.file == "features/login.feature"
        assert sr.line == 10
        assert sr.rule == "Auth rule"
        assert sr.is_outline is True

    def test_dot_notation_access(self) -> None:
        """Fields are accessible via dot notation."""
        sr = ScenarioResult(feature_name="Search", status="failed")
        assert sr.feature_name == "Search"
        assert sr.status == "failed"

    def test_equality_same_values(self) -> None:
        """Two instances with same values are equal."""
        sr1 = ScenarioResult(feature_name="F", scenario_name="S", status="passed")
        sr2 = ScenarioResult(feature_name="F", scenario_name="S", status="passed")
        assert sr1 == sr2

    def test_inequality_different_values(self) -> None:
        """Two instances with different values are not equal."""
        sr1 = ScenarioResult(feature_name="F", status="passed")
        sr2 = ScenarioResult(feature_name="F", status="failed")
        assert sr1 != sr2

    def test_tags_default_is_new_list_each_time(self) -> None:
        """Each instance gets its own list for tags."""
        sr1 = ScenarioResult()
        sr2 = ScenarioResult()
        sr1.tags.append("tag1")
        assert sr2.tags == []


class TestFeatureSummary:
    """Tests for FeatureSummary dataclass."""

    def test_defaults(self) -> None:
        """Constructor with no arguments uses sensible defaults."""
        fs = FeatureSummary()
        assert fs.feature_name == ""
        assert fs.total_scenarios == 0
        assert fs.passed == 0
        assert fs.failed == 0
        assert fs.skipped == 0
        assert fs.undefined == 0
        assert fs.pass_rate == 0.0
        assert fs.duration == 0.0

    def test_all_fields(self) -> None:
        """Constructor with all fields specified."""
        fs = FeatureSummary(
            feature_name="Login",
            total_scenarios=10,
            passed=8,
            failed=1,
            skipped=1,
            undefined=0,
            pass_rate=80.0,
            duration=5.5,
        )
        assert fs.feature_name == "Login"
        assert fs.total_scenarios == 10
        assert fs.passed == 8
        assert fs.failed == 1
        assert fs.skipped == 1
        assert fs.undefined == 0
        assert fs.pass_rate == 80.0
        assert fs.duration == 5.5

    def test_equality_same_values(self) -> None:
        """Two instances with same values are equal."""
        fs1 = FeatureSummary(feature_name="F", passed=5)
        fs2 = FeatureSummary(feature_name="F", passed=5)
        assert fs1 == fs2


class TestRunSummary:
    """Tests for RunSummary dataclass."""

    def test_defaults(self) -> None:
        """Constructor with no arguments uses sensible defaults."""
        rs = RunSummary()
        assert rs.run_id == ""
        assert rs.start_time == ""
        assert rs.end_time == ""
        assert rs.duration == 0.0
        assert rs.total_features == 0
        assert rs.total_scenarios == 0
        assert rs.passed == 0
        assert rs.failed == 0
        assert rs.skipped == 0
        assert rs.undefined == 0
        assert rs.pass_rate == 0.0
        assert rs.features == []
        assert rs.scenarios == []

    def test_all_fields(self) -> None:
        """Constructor with all fields specified."""
        fs = FeatureSummary(feature_name="Login", passed=5)
        sr = ScenarioResult(feature_name="Login", status="passed")
        rs = RunSummary(
            run_id="run-001",
            start_time="2025-01-01T00:00:00Z",
            end_time="2025-01-01T00:05:00Z",
            duration=300.0,
            total_features=1,
            total_scenarios=5,
            passed=4,
            failed=1,
            skipped=0,
            undefined=0,
            pass_rate=80.0,
            features=[fs],
            scenarios=[sr],
        )
        assert rs.run_id == "run-001"
        assert rs.start_time == "2025-01-01T00:00:00Z"
        assert rs.end_time == "2025-01-01T00:05:00Z"
        assert rs.duration == 300.0
        assert rs.total_features == 1
        assert rs.total_scenarios == 5
        assert rs.passed == 4
        assert rs.failed == 1
        assert rs.pass_rate == 80.0
        assert len(rs.features) == 1
        assert rs.features[0].feature_name == "Login"
        assert len(rs.scenarios) == 1
        assert rs.scenarios[0].status == "passed"

    def test_empty_lists(self) -> None:
        """RunSummary with empty lists."""
        rs = RunSummary(run_id="run-empty")
        assert rs.features == []
        assert rs.scenarios == []
        assert len(rs.features) == 0
        assert len(rs.scenarios) == 0

    def test_populated_lists(self) -> None:
        """RunSummary with features and scenarios populated."""
        features = [
            FeatureSummary(feature_name="F1", passed=3),
            FeatureSummary(feature_name="F2", failed=2),
        ]
        scenarios = [
            ScenarioResult(feature_name="F1", scenario_name="S1", status="passed"),
            ScenarioResult(feature_name="F1", scenario_name="S2", status="passed"),
            ScenarioResult(feature_name="F2", scenario_name="S3", status="failed"),
        ]
        rs = RunSummary(features=features, scenarios=scenarios)
        assert len(rs.features) == 2
        assert len(rs.scenarios) == 3
        assert rs.features[0].feature_name == "F1"
        assert rs.features[1].feature_name == "F2"
        assert rs.scenarios[0].scenario_name == "S1"
        assert rs.scenarios[2].status == "failed"

    def test_lists_default_are_new_each_time(self) -> None:
        """Each instance gets its own list for features and scenarios."""
        rs1 = RunSummary()
        rs2 = RunSummary()
        rs1.features.append(FeatureSummary())
        rs1.scenarios.append(ScenarioResult())
        assert rs2.features == []
        assert rs2.scenarios == []

    def test_equality_same_values(self) -> None:
        """Two instances with same values are equal."""
        rs1 = RunSummary(run_id="r1", passed=5)
        rs2 = RunSummary(run_id="r1", passed=5)
        assert rs1 == rs2


class TestHistoryEntry:
    """Tests for HistoryEntry dataclass."""

    def test_defaults(self) -> None:
        """Constructor with no arguments uses sensible defaults."""
        he = HistoryEntry()
        assert he.run_id == ""
        assert he.timestamp == ""
        assert he.total_features == 0
        assert he.total_scenarios == 0
        assert he.passed == 0
        assert he.failed == 0
        assert he.skipped == 0
        assert he.undefined == 0
        assert he.pass_rate == 0.0
        assert he.duration == 0.0

    def test_all_fields(self) -> None:
        """Constructor with all fields specified."""
        he = HistoryEntry(
            run_id="run-001",
            timestamp="2025-01-01T00:00:00Z",
            total_features=3,
            total_scenarios=15,
            passed=12,
            failed=2,
            skipped=1,
            undefined=0,
            pass_rate=80.0,
            duration=120.0,
        )
        assert he.run_id == "run-001"
        assert he.timestamp == "2025-01-01T00:00:00Z"
        assert he.total_features == 3
        assert he.total_scenarios == 15
        assert he.passed == 12
        assert he.failed == 2
        assert he.skipped == 1
        assert he.undefined == 0
        assert he.pass_rate == 80.0
        assert he.duration == 120.0

    def test_equality_same_values(self) -> None:
        """Two instances with same values are equal."""
        he1 = HistoryEntry(run_id="r1", passed=5)
        he2 = HistoryEntry(run_id="r1", passed=5)
        assert he1 == he2

    def test_inequality_different_values(self) -> None:
        """Two instances with different values are not equal."""
        he1 = HistoryEntry(run_id="r1", passed=5)
        he2 = HistoryEntry(run_id="r1", passed=3)
        assert he1 != he2
