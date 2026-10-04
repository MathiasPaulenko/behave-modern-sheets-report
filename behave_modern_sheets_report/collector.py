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

    The collector is stateful. Create one per formatter run and feed it
    events in the order Behave produces them — ``start_feature``,
    ``start_scenario``, then ``start_step`` for *every* step of the scenario
    (announced upfront), ``end_step`` once per executed step, and finally
    ``end_scenario``/``end_feature``. Steps that never produce a result are
    counted as skipped. Call :meth:`finalize` to obtain the complete
    :class:`RunSummary`.

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

        self._feature_start: float | None = None
        self._scenario_start: float | None = None
        self._pending_steps: list[Any] = []
        self._bg_step_ids: set[int] = set()

    # ------------------------------------------------------------------
    # Feature lifecycle
    # ------------------------------------------------------------------

    def start_feature(self, behave_feature: Any) -> None:
        """Begin tracking a feature.

        Finalizes the previous scenario and feature if either is in progress.

        Args:
            behave_feature: A Behave ``Feature`` object (or mock).
        """
        if self._current_scenario is not None:
            self.end_scenario()
        if self._current_feature is not None:
            self.end_feature()
        self._pending_steps.clear()
        self._bg_step_ids.clear()
        name = safe_str(getattr(behave_feature, "name", "")) or safe_str(
            getattr(behave_feature, "filename", "")
        )
        tags = safe_tags(getattr(behave_feature, "tags", None))
        feature = FeatureSummary(feature_name=name, tags=tags)
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

    def start_background(self, behave_background: Any | None = None) -> None:
        """No-op kept for API compatibility.

        Behave emits a single ``background`` notification per feature or rule,
        before any scenario starts, and provides no end-of-background event —
        so this flag cannot delimit background steps. They are detected
        instead via ``scenario.background_steps`` in :meth:`start_scenario`.
        """

    def end_background(self) -> None:
        """No-op kept for API compatibility. See :meth:`start_background`."""

    # ------------------------------------------------------------------
    # Scenario lifecycle
    # ------------------------------------------------------------------

    def start_scenario(self, behave_scenario: Any) -> None:
        """Begin tracking a scenario within the current feature.

        Args:
            behave_scenario: A Behave ``Scenario`` object (or mock).
        """
        if self._current_scenario is not None:
            self.end_scenario()
        feature = self._current_feature
        feature_name = feature.feature_name if feature else ""
        feature_tags = feature.tags if feature else []

        name = safe_str(getattr(behave_scenario, "name", ""))
        tags = safe_tags(getattr(behave_scenario, "tags", None))

        location = getattr(behave_scenario, "location", None)
        file_name = ""
        line = 0
        if location is not None:
            file_name = safe_str(getattr(location, "filename", ""))
            try:
                line = int(getattr(location, "line", 0) or 0)
            except (TypeError, ValueError):
                line = 0

        rule_obj = getattr(behave_scenario, "rule", None)
        rule_name = ""
        if rule_obj is not None:
            rule_name = safe_str(getattr(rule_obj, "name", ""))

        is_outline = bool(getattr(behave_scenario, "is_outline", False))

        # Background steps are per-scenario copies in Behave >= 1.2.6.dev6;
        # matching by identity lets us attribute their results to the scenario.
        bg_steps = getattr(behave_scenario, "background_steps", None) or []
        self._bg_step_ids = {id(step) for step in bg_steps}
        self._pending_steps = []

        scenario = ScenarioResult(
            feature_name=feature_name,
            scenario_name=name,
            tags=tags,
            feature_tags=list(feature_tags),
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

        No-op if no scenario was started. Steps that were announced but never
        produced a result (skipped after a failure, or in a skipped scenario)
        are counted from their final model status before computing the status.
        """
        scenario = self._current_scenario
        if scenario is None:
            self._pending_steps.clear()
            return
        for pending_step in self._pending_steps:
            self._record_step(scenario, pending_step, executed=False)
        self._pending_steps.clear()
        self._bg_step_ids.clear()
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
        """Register that a step was announced for the current scenario.

        Behave notifies ``step`` for *all* steps of a scenario upfront, then
        fires ``result`` once per executed step, so steps are queued here and
        matched with their results in :meth:`end_step`.

        Args:
            behave_step: A Behave ``Step`` object (or mock).
        """
        self._pending_steps.append(behave_step)

    def end_step(self, behave_step: Any) -> None:
        """Record the result of a step in the current scenario.

        No-op if no step was announced beforehand (defensive).

        Args:
            behave_step: A Behave ``Step`` object (or mock) carrying the
                final ``status``/``error`` information.
        """
        if not self._pending_steps:
            return
        self._discard_pending(behave_step)
        scenario = self._current_scenario
        if scenario is None:
            return
        self._record_step(scenario, behave_step, executed=True)

    def _discard_pending(self, behave_step: Any) -> None:
        """Remove a step from the pending queue, matching by identity."""
        for index, pending_step in enumerate(self._pending_steps):
            if pending_step is behave_step:
                del self._pending_steps[index]
                return
        self._pending_steps.pop(0)

    def _record_step(self, scenario: ScenarioResult, behave_step: Any, executed: bool) -> None:
        """Accumulate counters and flags for a single step.

        ``executed=False`` is used for steps that were announced but never
        produced a result; those are not counted as executed background steps.
        """
        raw_status = getattr(behave_step, "status", "")
        if hasattr(raw_status, "name"):
            raw_status = raw_status.name
        status = self._map_status(safe_str(raw_status))
        scenario.step_count += 1
        if executed and id(behave_step) in self._bg_step_ids:
            scenario.background_steps += 1
        if self._has_data_table(behave_step):
            scenario.has_data_table = True
        if self._has_docstring(behave_step):
            scenario.has_docstring = True
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

    # ------------------------------------------------------------------
    # Finalization
    # ------------------------------------------------------------------

    def finalize(self) -> RunSummary:
        """Build and return the complete :class:`RunSummary`.

        Finalizes any in-progress scenario and feature before computing
        totals so that the returned summary is always consistent, even if
        the caller did not explicitly call :meth:`end_scenario` or
        :meth:`end_feature`.

        Returns:
            A :class:`RunSummary` with aggregated totals, pass rate, and
            all feature/scenario details.
        """
        if self._current_scenario is not None:
            self.end_scenario()
        if self._current_feature is not None:
            self.end_feature()

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
        if scenario.step_count == 0:
            return STATUS_SKIPPED
        if scenario.skipped_steps == scenario.step_count:
            return STATUS_SKIPPED
        accounted = scenario.passed_steps + scenario.failed_steps + scenario.skipped_steps
        if accounted < scenario.step_count:
            return STATUS_UNDEFINED
        return STATUS_PASSED

    @staticmethod
    def _has_data_table(behave_step: Any) -> bool:
        """Check whether a step includes a Gherkin data table."""
        table = getattr(behave_step, "table", None)
        if table is not None:
            return True
        return getattr(behave_step, "data_table", None) is not None

    @staticmethod
    def _has_docstring(behave_step: Any) -> bool:
        """Check whether a step includes a Gherkin docstring."""
        text = getattr(behave_step, "text", None)
        if text is not None and safe_str(text):
            return True
        return getattr(behave_step, "doc_string", None) is not None

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
