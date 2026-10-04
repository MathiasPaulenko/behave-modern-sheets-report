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
        # Wait until the monotonic clock actually ticks once — on some
        # Windows runners the timer resolution can swallow a short sleep.
        start = time.monotonic()
        while time.monotonic() == start:
            time.sleep(0.001)
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


class TestFeatureTags:
    """Tests for feature-level tag capture."""

    def test_feature_tags_captured(self) -> None:
        """Feature tags are stored in FeatureSummary and propagated to scenarios."""
        c = Collector()
        c.start_feature(make_feature("Login", tags=["smoke", "regression"]))
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.features[0].tags == ["smoke", "regression"]
        assert rs.scenarios[0].feature_tags == ["smoke", "regression"]

    def test_feature_tags_empty_by_default(self) -> None:
        """Feature without tags has empty tags list."""
        c = Collector()
        c.start_feature(make_feature("Login"))
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.features[0].tags == []
        assert rs.scenarios[0].feature_tags == []


class TestBackgroundSteps:
    """Tests for background step counting via scenario.background_steps.

    Behave 1.3 emits a single ``background`` notification per feature/rule
    before any scenario and no end-of-background event. Each scenario
    exposes its own copies of the background steps in
    ``scenario.background_steps``, which the collector matches by identity.
    """

    def test_background_steps_counted(self) -> None:
        """Background steps count as steps and as background_steps."""
        bg1 = make_step("passed")
        bg2 = make_step("passed")
        own = make_step("passed")
        scenario = make_scenario("S1", background_steps=[bg1, bg2])
        c = Collector()
        c.start_feature(make_feature("Login"))
        c.start_scenario(scenario)
        for step in (bg1, bg2, own):
            c.start_step(step)
        for step in (bg1, bg2, own):
            c.end_step(step)
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].background_steps == 2
        assert rs.scenarios[0].step_count == 3
        assert rs.scenarios[0].passed_steps == 3
        assert rs.scenarios[0].status == STATUS_PASSED

    def test_failed_background_step_fails_scenario(self) -> None:
        """A failed background step marks the scenario as failed."""
        bg = make_step("failed", error=ValueError("bg boom"))
        own = make_step("skipped")
        scenario = make_scenario("S1", background_steps=[bg])
        c = Collector()
        c.start_feature(make_feature("Login"))
        c.start_scenario(scenario)
        c.start_step(bg)
        c.start_step(own)
        c.end_step(bg)  # Behave emits no result for steps skipped after a failure
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].status == STATUS_FAILED
        assert rs.scenarios[0].background_steps == 1
        assert rs.scenarios[0].failed_steps == 1
        assert rs.scenarios[0].skipped_steps == 1
        assert rs.scenarios[0].step_count == 2
        assert "bg boom" in rs.scenarios[0].error_message

    def test_skipped_scenario_background_not_executed(self) -> None:
        """A fully skipped scenario counts steps as skipped, background as 0."""
        bg = make_step("skipped")
        own = make_step("skipped")
        scenario = make_scenario("S1", background_steps=[bg])
        c = Collector()
        c.start_feature(make_feature("Login"))
        c.start_scenario(scenario)
        c.start_step(bg)
        c.start_step(own)
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].status == STATUS_SKIPPED
        assert rs.scenarios[0].background_steps == 0
        assert rs.scenarios[0].step_count == 2
        assert rs.scenarios[0].skipped_steps == 2

    def test_no_background_steps(self) -> None:
        """Scenario without background has background_steps=0."""
        c = Collector()
        c.start_feature(make_feature("Login"))
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].background_steps == 0


class TestRealBehaveProtocol:
    """Regression tests for the real Behave 1.3 event ordering.

    Behave notifies ``step`` for *all* steps of a scenario upfront, then
    fires ``result`` once per executed step. Steps that never run (skipped
    after a failure or in a skipped scenario) produce no ``result`` event.
    """

    def test_all_step_results_counted(self) -> None:
        """Every result is recorded even though steps were announced upfront."""
        steps = [make_step("passed") for _ in range(3)]
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S1"))
        for step in steps:
            c.start_step(step)
        for step in steps:
            c.end_step(step)
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].step_count == 3
        assert rs.scenarios[0].passed_steps == 3
        assert rs.scenarios[0].status == STATUS_PASSED

    def test_late_failure_detected(self) -> None:
        """A failure in a non-first step marks the scenario as failed."""
        s1 = make_step("passed")
        s2 = make_step("passed")
        s3 = make_step("failed", error=ValueError("late boom"))
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S1"))
        for step in (s1, s2, s3):
            c.start_step(step)
        for step in (s1, s2, s3):
            c.end_step(step)
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].status == STATUS_FAILED
        assert rs.scenarios[0].step_count == 3
        assert rs.scenarios[0].passed_steps == 2
        assert rs.scenarios[0].failed_steps == 1
        assert "late boom" in rs.scenarios[0].error_message

    def test_unexecuted_steps_flushed_as_skipped(self) -> None:
        """Steps announced but never resulted are counted as skipped."""
        s1 = make_step("passed")
        s2 = make_step("failed", error=ValueError("boom"))
        s3 = make_step("skipped")
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S1"))
        for step in (s1, s2, s3):
            c.start_step(step)
        c.end_step(s1)
        c.end_step(s2)
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].step_count == 3
        assert rs.scenarios[0].skipped_steps == 1
        assert rs.scenarios[0].status == STATUS_FAILED

    def test_start_scenario_finalizes_previous(self) -> None:
        """start_scenario without end_scenario finalizes the open scenario."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.start_scenario(make_scenario("S2"))
        c.start_step(make_step("failed", error=ValueError("x")))
        c.end_step(make_step("failed", error=ValueError("x")))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert [s.scenario_name for s in rs.scenarios] == ["S1", "S2"]
        assert rs.scenarios[0].status == STATUS_PASSED
        assert rs.scenarios[1].status == STATUS_FAILED
        assert rs.total_scenarios == 2

    def test_results_matched_by_identity(self) -> None:
        """Results are consumed for the exact step object Behave passes."""
        s1 = make_step("passed")
        s2 = make_step("skipped")
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S1"))
        c.start_step(s1)
        c.start_step(s2)
        c.end_step(s2)  # result arrives for the second step (first still pending)
        c.end_step(s1)
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].step_count == 2
        assert rs.scenarios[0].passed_steps == 1
        assert rs.scenarios[0].skipped_steps == 1


class TestDataTable:
    """Tests for data table detection."""

    def test_step_with_table_sets_flag(self) -> None:
        """A step with a table attribute sets has_data_table=True."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed", table=SimpleNamespace(rows=[])))
        c.end_step(make_step("passed", table=SimpleNamespace(rows=[])))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].has_data_table is True

    def test_step_without_table_leaves_flag_false(self) -> None:
        """Steps without tables leave has_data_table=False."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].has_data_table is False


class TestDocString:
    """Tests for docstring detection."""

    def test_step_with_docstring_sets_flag(self) -> None:
        """A step with a text attribute sets has_docstring=True."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed", text="some docstring content"))
        c.end_step(make_step("passed", text="some docstring content"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].has_docstring is True

    def test_step_without_docstring_leaves_flag_false(self) -> None:
        """Steps without docstrings leave has_docstring=False."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].has_docstring is False


class TestStartFeatureFinalizesScenario:
    """Regression: start_feature must finalize in-progress scenario."""

    def test_start_feature_finalizes_pending_scenario(self) -> None:
        """Starting a new feature finalizes the previous in-progress scenario."""
        c = Collector()
        c.start_feature(make_feature("F1"))
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        # Don't call end_scenario — start_feature should do it
        c.start_feature(make_feature("F2"))
        rs = c.finalize()

        assert rs.scenarios[0].scenario_name == "S1"
        assert rs.scenarios[0].status == STATUS_PASSED
        assert rs.total_features == 2

    def test_start_feature_resets_pending_state(self) -> None:
        """Steps announced outside a scenario do not leak into the next feature."""
        c = Collector()
        c.start_feature(make_feature("F1"))
        c.start_background()  # deprecated no-op hook
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_feature()
        # Pending state should not leak into the next feature
        c.start_feature(make_feature("F2"))
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].background_steps == 0


class TestStartScenarioInvalidLine:
    """Regression: start_scenario handles non-numeric line values."""

    def test_non_numeric_line_defaults_to_zero(self) -> None:
        """A non-numeric line value defaults to 0 instead of crashing."""
        c = Collector()
        c.start_feature(make_feature())
        scenario = make_scenario("S1", line=10)
        # Override location with a non-numeric line
        scenario.location = SimpleNamespace(filename="features/test.feature", line="not_a_number")
        c.start_scenario(scenario)
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].line == 0

    def test_none_line_defaults_to_zero(self) -> None:
        """A None line value defaults to 0 instead of crashing."""
        c = Collector()
        c.start_feature(make_feature())
        scenario = make_scenario("S1", line=10)
        scenario.location = SimpleNamespace(filename="features/test.feature", line=None)
        c.start_scenario(scenario)
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].line == 0


class TestEndStepWithoutScenario:
    """Regression: end_step resets state when scenario is None."""

    def test_end_step_without_scenario_resets_state(self) -> None:
        """end_step with no scenario consumes the pending step and does nothing."""
        c = Collector()
        c.start_feature(make_feature())
        # Start a step without a scenario
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        # The pending step was consumed, so a second end_step is a no-op
        c.end_step(make_step("passed"))
        # Now start a scenario and step normally
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].step_count == 1
        assert rs.scenarios[0].passed_steps == 1


class TestFinalizeAutoFinalizes:
    """Regression: finalize() finalizes pending scenario/feature for correct totals."""

    def test_finalize_without_end_scenario(self) -> None:
        """finalize() auto-finalizes a pending scenario so its status is counted."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        # Deliberately skip end_scenario() and end_feature()
        rs = c.finalize()

        assert rs.total_scenarios == 1
        assert rs.passed == 1
        assert rs.failed == 0
        assert rs.scenarios[0].status == STATUS_PASSED

    def test_finalize_without_end_feature(self) -> None:
        """finalize() auto-finalizes a pending feature so its duration is set."""
        c = Collector()
        c.start_feature(make_feature("F1"))
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("passed"))
        c.end_step(make_step("passed"))
        c.end_scenario()
        # Deliberately skip end_feature()
        rs = c.finalize()

        assert rs.total_features == 1
        assert rs.features[0].total_scenarios == 1
        assert rs.features[0].passed == 1

    def test_finalize_without_any_end_calls(self) -> None:
        """finalize() with no end calls still produces consistent totals."""
        c = Collector()
        c.start_feature(make_feature("F1"))
        c.start_scenario(make_scenario("S1"))
        c.start_step(make_step("failed"))
        c.end_step(make_step("failed"))
        # Skip all end calls
        rs = c.finalize()

        assert rs.total_scenarios == 1
        assert rs.failed == 1
        assert rs.passed == 0
        assert rs.scenarios[0].status == STATUS_FAILED


class TestDeriveScenarioStatusZeroSteps:
    """Regression: scenario with zero steps is SKIPPED, not PASSED."""

    def test_zero_step_scenario_is_skipped(self) -> None:
        """A scenario with no steps (e.g. skipped via tags) gets STATUS_SKIPPED."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S1"))
        # No steps — simulate tag-skipped scenario
        c.end_scenario()
        c.end_feature()
        rs = c.finalize()

        assert rs.scenarios[0].status == STATUS_SKIPPED
        assert rs.skipped == 1
        assert rs.passed == 0

    def test_zero_step_scenario_in_finalize(self) -> None:
        """Zero-step scenario finalized via finalize() is also SKIPPED."""
        c = Collector()
        c.start_feature(make_feature())
        c.start_scenario(make_scenario("S1"))
        # No steps, no end_scenario — finalize auto-finalizes
        rs = c.finalize()

        assert rs.scenarios[0].status == STATUS_SKIPPED
        assert rs.skipped == 1
