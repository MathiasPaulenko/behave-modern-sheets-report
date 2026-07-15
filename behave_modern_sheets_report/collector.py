"""Collector — translates Behave runtime events into a RunSummary.

The collector is the **only** module that depends on Behave objects. It
receives high-level objects (``Feature``, ``Scenario``, ``Step``) from the
formatter and builds :class:`RunSummary` instances without leaking Behave
types into the model. Behave objects are typed as ``Any`` so the module
can be used without Behave installed (e.g. in unit tests with
``SimpleNamespace`` mocks).
"""

from __future__ import annotations

import time
from typing import Any

from .models import FeatureSummary, RunSummary, ScenarioResult
from .utils import (
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_SKIPPED,
    STATUS_UNDEFINED,
    generate_id,
    monotonic_seconds,
    normalize_status,
    now_iso,
    safe_str,
    safe_tags,
)


class Collector:
    """Accumulates Behave events into a :class:`RunSummary`.

    The collector is stateful. Create one per formatter run, feed it events
    in order (``start_feature`` → ``start_scenario`` → ``start_step`` →
    ``end_step`` → ``end_scenario`` → ``end_feature``), then call
    :meth:`finalize` to obtain the complete :class:`RunSummary`.

    Attributes:
        run_id: Unique identifier generated at construction time.
    """

    def __init__(self) -> None:
        """Initialize the collector with empty state."""
        self.run_id = generate_id("run")
        self._start_time = now_iso()
        self._start_monotonic = time.monotonic()

        self._features: list[FeatureSummary] = []
        self._scenarios: list[ScenarioResult] = []

        self._current_feature: FeatureSummary | None = None
        self._current_scenario: ScenarioResult | None = None
        self._current_step: Any | None = None

        self._feature_start: float | None = None
        self._scenario_start: float | None = None
        self._step_start: float | None = None

    # ------------------------------------------------------------------
    # Feature lifecycle
    # ------------------------------------------------------------------

    def start_feature(self, behave_feature: Any) -> None:
        """Begin tracking a feature.

        Finalizes the previous feature if one is in progress.

        Args:
            behave_feature: A Behave ``Feature`` object (or mock).
        """
        if self._current_feature is not None:
            self.end_feature()
        name = safe_str(getattr(behave_feature, "name", "")) or safe_str(
            getattr(behave_feature, "filename", "")
        )
        feature = FeatureSummary(feature_name=name)
        self._features.append(feature)
        self._current_feature = feature
        self._feature_start = time.monotonic()

    def end_feature(self) -> None:
        """Finalize the current feature and compute its duration.

        No-op if no feature was started.
        """
        feature = self._current_feature
        if feature is None:
            return
        assert self._feature_start is not None
        feature.duration = monotonic_seconds(self._feature_start)
        self._current_feature = None
        self._feature_start = None

    # ------------------------------------------------------------------
    # Scenario lifecycle
    # ------------------------------------------------------------------

    def start_scenario(self, behave_scenario: Any) -> None:
        """Begin tracking a scenario within the current feature.

        Args:
            behave_scenario: A Behave ``Scenario`` object (or mock).
        """
        feature = self._current_feature
        feature_name = feature.feature_name if feature else ""

        name = safe_str(getattr(behave_scenario, "name", ""))
        tags = safe_tags(getattr(behave_scenario, "tags", None))

        location = getattr(behave_scenario, "location", None)
        file_name = ""
        line = 0
        if location is not None:
            file_name = safe_str(getattr(location, "filename", ""))
            line = int(getattr(location, "line", 0) or 0)

        rule_obj = getattr(behave_scenario, "rule", None)
        rule_name = ""
        if rule_obj is not None:
            rule_name = safe_str(getattr(rule_obj, "name", ""))

        is_outline = bool(getattr(behave_scenario, "is_outline", False))

        scenario = ScenarioResult(
            feature_name=feature_name,
            scenario_name=name,
            tags=tags,
            file=file_name,
            line=line,
            rule=rule_name,
            is_outline=is_outline,
        )
        self._scenarios.append(scenario)
        self._current_scenario = scenario
        self._scenario_start = time.monotonic()

    def end_scenario(self) -> None:
        """Finalize the current scenario and derive its status from steps.

        No-op if no scenario was started.
        """
        scenario = self._current_scenario
        if scenario is None:
            return
        assert self._scenario_start is not None
        scenario.duration = monotonic_seconds(self._scenario_start)
        scenario.status = self._derive_scenario_status(scenario)
        if self._current_feature is not None:
            self._current_feature.total_scenarios += 1
            if scenario.status == STATUS_PASSED:
                self._current_feature.passed += 1
            elif scenario.status == STATUS_FAILED:
                self._current_feature.failed += 1
            elif scenario.status == STATUS_SKIPPED:
                self._current_feature.skipped += 1
            else:
                self._current_feature.undefined += 1
        self._current_scenario = None
        self._scenario_start = None

    # ------------------------------------------------------------------
    # Step lifecycle
    # ------------------------------------------------------------------

    def start_step(self, behave_step: Any) -> None:
        """Register the start of a step within the current scenario.

        Args:
            behave_step: A Behave ``Step`` object (or mock).
        """
        self._current_step = behave_step
        self._step_start = time.monotonic()

    def end_step(self, behave_step: Any) -> None:
        """Finalize the current step and accumulate counters.

        Args:
            behave_step: A Behave ``Step`` object (or mock).
        """
        scenario = self._current_scenario
        if scenario is None or self._current_step is None:
            return
        raw_status = getattr(behave_step, "status", "")
        if hasattr(raw_status, "name"):
            raw_status = raw_status.name
        status = self._map_status(safe_str(raw_status))
        scenario.step_count += 1
        if status == STATUS_PASSED:
            scenario.passed_steps += 1
        elif status == STATUS_FAILED:
            scenario.failed_steps += 1
            if not scenario.error_message:
                error_message, error_type, traceback_str = self._extract_error(behave_step)
                scenario.error_message = error_message
                scenario.error_type = error_type
                scenario.traceback = traceback_str
        elif status == STATUS_SKIPPED:
            scenario.skipped_steps += 1
        self._current_step = None
        self._step_start = None

    # ------------------------------------------------------------------
    # Finalization
    # ------------------------------------------------------------------

    def finalize(self) -> RunSummary:
        """Build and return the complete :class:`RunSummary`.

        Returns:
            A :class:`RunSummary` with aggregated totals, pass rate, and
            all feature/scenario details.
        """
        end_time = now_iso()
        duration = monotonic_seconds(self._start_monotonic)

        total_scenarios = len(self._scenarios)
        passed = sum(1 for s in self._scenarios if s.status == STATUS_PASSED)
        failed = sum(1 for s in self._scenarios if s.status == STATUS_FAILED)
        skipped = sum(1 for s in self._scenarios if s.status == STATUS_SKIPPED)
        undefined = sum(1 for s in self._scenarios if s.status == STATUS_UNDEFINED)
        pass_rate = (passed / total_scenarios * 100) if total_scenarios > 0 else 0.0

        for feature in self._features:
            feature_total = feature.total_scenarios
            feature.pass_rate = feature.passed / feature_total * 100 if feature_total > 0 else 0.0

        return RunSummary(
            run_id=self.run_id,
            start_time=self._start_time,
            end_time=end_time,
            duration=duration,
            total_features=len(self._features),
            total_scenarios=total_scenarios,
            passed=passed,
            failed=failed,
            skipped=skipped,
            undefined=undefined,
            pass_rate=pass_rate,
            features=list(self._features),
            scenarios=list(self._scenarios),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_status(behave_status: str) -> str:
        """Map a Behave status string to a canonical status.

        Args:
            behave_status: Raw status string from Behave.

        Returns:
            A canonical status constant from :mod:`utils`.
        """
        return normalize_status(behave_status)

    @staticmethod
    def _derive_scenario_status(scenario: ScenarioResult) -> str:
        """Derive the scenario status from accumulated step counters.

        Args:
            scenario: The finalized :class:`ScenarioResult`.

        Returns:
            ``STATUS_FAILED`` if any step failed, ``STATUS_SKIPPED`` if all
            steps were skipped, ``STATUS_UNDEFINED`` if any step is undefined,
            ``STATUS_PASSED`` otherwise.
        """
        if scenario.failed_steps > 0:
            return STATUS_FAILED
        if scenario.step_count > 0 and scenario.skipped_steps == scenario.step_count:
            return STATUS_SKIPPED
        accounted = scenario.passed_steps + scenario.failed_steps + scenario.skipped_steps
        if scenario.step_count > 0 and accounted < scenario.step_count:
            return STATUS_UNDEFINED
        return STATUS_PASSED

    @staticmethod
    def _extract_error(behave_step: Any) -> tuple[str, str, str]:
        """Extract error information from a failed step.

        The traceback is truncated to a maximum of 500 characters to avoid
        leaking excessive internal details in reports.

        Args:
            behave_step: A Behave ``Step`` object (or mock).

        Returns:
            A tuple of ``(error_message, error_type, traceback)``. Returns
            empty strings if no error is present.
        """
        exc = getattr(behave_step, "error", None)
        if exc is None:
            exc = getattr(behave_step, "exception", None)
        if exc is None:
            error_message = safe_str(getattr(behave_step, "error_message", ""))
            if error_message:
                return error_message, "", ""
            return "", "", ""
        if isinstance(exc, BaseException):
            import traceback as tb_mod

            tb_str = "".join(tb_mod.format_exception(type(exc), exc, exc.__traceback__))
            if len(tb_str) > 500:
                tb_str = tb_str[:497] + "..."
            return safe_str(exc), type(exc).__name__, tb_str
        return safe_str(exc), "", ""
