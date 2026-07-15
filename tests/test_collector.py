"""Tests for the collector module."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from behave_modern_sheets_report.collector import Collector
from behave_modern_sheets_report.utils import (
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_SKIPPED,
    STATUS_UNDEFINED,
)
from tests._helpers import (
    make_feature_obj as make_feature,
)
from tests._helpers import (
    make_scenario_obj as make_scenario,
)
from tests._helpers import (
    make_step_obj as make_step,
)


class TestCompleteRunPassing:
    """Tests for a complete passing run."""

    def test_complete_passing_run(self) -> None:
        """Feature → scenario → step → result → end produces a passing RunSummary."""
        c = Collector()
        c.start_feature(make_feature("Login"))
        c.start_scenario(make_scenario("Successful login"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.total_features == 1
        assert rs.total_scenarios == 1
        assert rs.passed == 1
        assert rs.failed == 0
        assert rs.pass_rate == 100.0
        assert rs.scenarios[0].status == STATUS_PASSED
        assert rs.scenarios[0].step_count == 1
        assert rs.scenarios[0].passed_steps == 1
        assert rs.features[0].feature_name == "Login"
        assert rs.features[0].passed == 1

    def test_duration_calculated(self) -> None:
        """Feature, scenario and run durations are positive."""
        import time

        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario())
        c.start_step(make_step("passed"))
        time.sleep(0.01)
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.duration > 0
        assert rs.features[0].duration > 0
        assert rs.scenarios[0].duration > 0


class TestFailedStep:
    """Tests for failed step propagation."""

    def test_failed_step_propagates_to_scenario(self) -> None:
        """A failed step marks the scenario as failed."""
        exc = ValueError("Something went wrong")
        c = Collector()
        c.start_feature(make_feature("Checkout"))
        c.start_scenario(make_scenario("Payment fails"))
        c.start_step(make_step("failed", error=exc))
        c.end_step(make_step("failed", error=exc))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].status == STATUS_FAILED
        assert rs.scenarios[0].failed_steps == 1
        assert "Something went wrong" in rs.scenarios[0].error_message
        assert rs.scenarios[0].error_type == "ValueError"
        assert rs.scenarios[0].traceback != ""
        assert rs.failed == 1
        assert rs.features[0].failed == 1

    def test_first_failed_step_error_preserved(self) -> None:
        """When multiple steps fail, the first error is preserved."""
        exc1 = ValueError("first error")
        exc2 = RuntimeError("second error")
        c = Collector()
        c.start_feature(make_feature("Checkout"))
        c.start_scenario(make_scenario("Multiple failures"))
        c.start_step(make_step("failed", error=exc1))
        c.end_step(make_step("failed", error=exc1))
        c.start_step(make_step("failed", error=exc2))
        c.end_step(make_step("failed", error=exc2))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].failed_steps == 2
        assert "first error" in rs.scenarios[0].error_message
        assert rs.scenarios[0].error_type == "ValueError"

    def test_error_message_without_exception(self) -> None:
        """A step with error_message but no exception object captures the message."""
        step = SimpleNamespace(
            name="step", status="failed", error=None, error_message="Custom error"
        )
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario())
        c.start_step(step)
        c.end_step(step)
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].error_message == "Custom error"
        assert rs.scenarios[0].error_type == ""
        assert rs.scenarios[0].traceback == ""

    def test_error_non_exception_object(self) -> None:
        """A step with a non-exception error object captures its string form."""
        step = SimpleNamespace(name="step", status="failed", error="string error", error_message="")
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario())
        c.start_step(step)
        c.end_step(step)
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].error_message == "string error"
        assert rs.scenarios[0].error_type == ""

    def test_long_traceback_truncated(self) -> None:
        """Traceback longer than 500 characters is truncated."""
        exc = ValueError("x" * 600)
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario())
        c.start_step(make_step("failed", error=exc))
        c.end_step(make_step("failed", error=exc))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert len(rs.scenarios[0].traceback) <= 500
        assert rs.scenarios[0].traceback.endswith("...")


class TestSkippedSteps:
    """Tests for skipped steps."""

    def test_all_skipped_scenario_is_skipped(self) -> None:
        """If all steps are skipped, scenario status is skipped."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("Skipped scenario"))
        c.start_step(make_step("skipped"))
        c.end_step(make_step("skipped"))
        c.start_step(make_step("skipped"))
        c.end_step(make_step("skipped"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].status == STATUS_SKIPPED
        assert rs.scenarios[0].skipped_steps == 2
        assert rs.skipped == 1
        assert rs.features[0].skipped == 1

    def test_mixed_passed_skipped_is_passed(self) -> None:
        """If some steps pass and some skip, scenario is passed."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario())
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.start_step(make_step("skipped"))
        c.end_step(make_step("skipped"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].status == STATUS_PASSED
        assert rs.scenarios[0].passed_steps == 1
        assert rs.scenarios[0].skipped_steps == 1

    def test_mixed_passed_undefined_is_undefined(self) -> None:
        """If some steps pass and some are undefined, scenario is undefined."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario())
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.start_step(make_step("undefined"))
        c.end_step(make_step("undefined"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].status == STATUS_UNDEFINED
        assert rs.scenarios[0].passed_steps == 1
        assert rs.scenarios[0].step_count == 2
        assert rs.undefined == 1


class TestMultipleFeaturesScenarios:
    """Tests for multiple features and scenarios."""

    def test_multiple_features_and_scenarios(self) -> None:
        """Multiple features with multiple scenarios produce correct totals."""
        c = Collector()

        c.start_feature(make_feature("Login"))
        c.start_scenario(make_scenario("Login OK"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.start_scenario(make_scenario("Login fail"))
        c.start_step(make_step("failed", error=ValueError("bad")))
        c.end_step(make_step("failed", error=ValueError("bad")))
        c.end_scenario()
        c.end_feature()

        c.start_feature(make_feature("Search"))
        c.start_scenario(make_scenario("Search works"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()

        rs = c.finalize()

        assert rs.total_features == 2
        assert rs.total_scenarios == 3
        assert rs.passed == 2
        assert rs.failed == 1
        assert rs.pass_rate == pytest.approx(100.0 * 2 / 3)
        assert rs.features[0].feature_name == "Login"
        assert rs.features[0].passed == 1
        assert rs.features[0].failed == 1
        assert rs.features[1].feature_name == "Search"
        assert rs.features[1].passed == 1


class TestScenarioOutline:
    """Tests for scenario outlines."""

    def test_outline_flag_preserved(self) -> None:
        """is_outline=True is preserved in the ScenarioResult."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("Outline example", is_outline=True))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].is_outline is True


class TestTags:
    """Tests for tag preservation."""

    def test_tags_preserved_in_scenario(self) -> None:
        """Scenario tags are preserved in the ScenarioResult."""
        c = Collector()
        c.start_feature(make_feature("Login", tags=["feature_tag"]))
        c.start_scenario(make_scenario("Login OK", tags=["smoke", "auth"]))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].tags == ["smoke", "auth"]


class TestPassRate:
    """Tests for pass rate calculation."""

    def test_zero_percent(self) -> None:
        """All scenarios failed → pass_rate 0.0."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("F1"))
        c.start_step(make_step("failed", error=ValueError("e")))
        c.end_step(make_step("failed", error=ValueError("e")))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.pass_rate == 0.0

    def test_fifty_percent(self) -> None:
        """Half passed, half failed → pass_rate 50.0."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("P"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.start_scenario(make_scenario("F"))
        c.start_step(make_step("failed", error=ValueError("e")))
        c.end_step(make_step("failed", error=ValueError("e")))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.pass_rate == 50.0

    def test_hundred_percent(self) -> None:
        """All passed → pass_rate 100.0."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("P1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.start_scenario(make_scenario("P2"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.pass_rate == 100.0


class TestEmptyRun:
    """Tests for edge cases with no data."""

    def test_finalize_empty_run(self) -> None:
        """finalize() with no features produces a valid empty RunSummary."""
        c = Collector()
        rs = c.finalize()

        assert rs.total_features == 0
        assert rs.total_scenarios == 0
        assert rs.passed == 0
        assert rs.failed == 0
        assert rs.pass_rate == 0.0
        assert rs.features == []
        assert rs.scenarios == []


class TestNoOps:
    """Tests for no-op behavior when end is called without start."""

    def test_end_feature_without_start(self) -> None:
        """end_feature() without start_feature() is a no-op."""
        c = Collector()
        c.end_feature()
        rs = c.finalize()
        assert rs.total_features == 0

    def test_end_scenario_without_start(self) -> None:
        """end_scenario() without start_scenario() is a no-op."""
        c = Collector()
        c.end_scenario()
        rs = c.finalize()
        assert rs.total_scenarios == 0

    def test_end_step_without_start(self) -> None:
        """end_step() without start_step() is a no-op."""
        c = Collector()
        c.end_step(make_step("passed"))
        rs = c.finalize()
        assert rs.total_scenarios == 0

    def test_end_step_without_scenario(self) -> None:
        """end_step() with start_step but no scenario is a no-op."""
        c = Collector()
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        rs = c.finalize()
        assert rs.total_scenarios == 0


class TestRulePreserved:
    """Tests for rule name preservation."""

    def test_rule_name_preserved(self) -> None:
        """Rule name is captured in the ScenarioResult."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S", rule_name="Auth rule"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].rule == "Auth rule"


class TestUndefinedStatus:
    """Tests for undefined step status."""

    def test_undefined_step_status(self) -> None:
        """A step with undefined status results in scenario status undefined."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario())
        c.start_step(make_step("undefined"))
        c.end_step(make_step("undefined"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].step_count == 1
        assert rs.scenarios[0].passed_steps == 0
        assert rs.scenarios[0].failed_steps == 0
        assert rs.scenarios[0].skipped_steps == 0
        assert rs.scenarios[0].status == STATUS_UNDEFINED
        assert rs.features[0].undefined == 1


class TestScenarioWithoutFeature:
    """Tests for scenario lifecycle without an active feature."""

    def test_start_scenario_without_feature(self) -> None:
        """start_scenario without start_feature creates scenario with empty feature_name."""
        c = Collector()
        c.start_scenario(make_scenario("Orphan"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        rs = c.finalize()

        assert rs.total_features == 0
        assert rs.total_scenarios == 1
        assert rs.scenarios[0].feature_name == ""
        assert rs.scenarios[0].status == STATUS_PASSED

    def test_end_step_with_scenario_but_no_step_start(self) -> None:
        """end_step with scenario but no start_step is a no-op."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario())
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].step_count == 0


class TestScenarioWithoutLocation:
    """Tests for scenario without location attribute."""

    def test_scenario_without_location(self) -> None:
        """Scenario with location=None uses empty file and line 0."""
        scenario = SimpleNamespace(
            name="No location",
            tags=[],
            location=None,
            rule=None,
            is_outline=False,
        )
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(scenario)
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].file == ""
        assert rs.scenarios[0].line == 0


class TestFailedStepNoError:
    """Tests for failed step with no error information."""

    def test_failed_step_no_error_info(self) -> None:
        """A failed step with no error/exception/error_message returns empty strings."""
        step = SimpleNamespace(name="step", status="failed", error=None, error_message="")
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario())
        c.start_step(step)
        c.end_step(step)
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].error_message == ""
        assert rs.scenarios[0].error_type == ""
        assert rs.scenarios[0].traceback == ""


class TestFeaturePassRate:
    """Tests for per-feature pass rate."""

    def test_feature_pass_rate(self) -> None:
        """Feature pass_rate is calculated from its scenarios."""
        c = Collector()
        c.start_feature(make_feature("F"))
        c.start_scenario(make_scenario("P1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.start_scenario(make_scenario("P2"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.start_scenario(make_scenario("F1"))
        c.start_step(make_step("failed", error=ValueError("e")))
        c.end_step(make_step("failed", error=ValueError("e")))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.features[0].total_scenarios == 3
        assert rs.features[0].passed == 2
        assert rs.features[0].failed == 1
        assert rs.features[0].pass_rate == pytest.approx(100.0 * 2 / 3)

    def test_feature_with_zero_scenarios(self) -> None:
        """A feature with no scenarios has pass_rate 0.0."""
        c = Collector()
        c.start_feature(make_feature("Empty"))
        c.end_feature()
        rs = c.finalize()

        assert rs.features[0].total_scenarios == 0
        assert rs.features[0].pass_rate == 0.0

    def test_start_feature_auto_finalizes_previous(self) -> None:
        """start_feature finalizes the previous feature if still in progress."""
        c = Collector()
        c.start_feature(make_feature("F1"))
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.start_feature(make_feature("F2"))
        rs = c.finalize()

        assert len(rs.features) == 2
        assert rs.features[0].feature_name == "F1"
        assert rs.features[0].total_scenarios == 1
        assert rs.features[0].passed == 1
        assert rs.features[0].pass_rate == 100.0
        assert rs.features[1].feature_name == "F2"

    def test_step_status_enum_is_converted(self) -> None:
        """Step status as enum (like Behave's Status) is converted via .name."""
        from enum import Enum

        class Status(Enum):
            passed = 11
            failed = 20

        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed"))
        step_with_enum = SimpleNamespace(status=Status.passed)
        c.end_step(step_with_enum)
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].status == STATUS_PASSED
        assert rs.scenarios[0].passed_steps == 1
