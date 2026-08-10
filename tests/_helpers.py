"""Shared test helpers for the behave-modern-sheets-report test suite."""

from __future__ import annotations

from io import StringIO
from types import SimpleNamespace
from typing import Any

from behave_modern_sheets_report.models import (
    FeatureSummary,
    HistoryEntry,
    RunSummary,
    ScenarioResult,
)
from behave_modern_sheets_report.utils import STATUS_PASSED

# ---------------------------------------------------------------------------
# Mock Behave objects (SimpleNamespace)
# ---------------------------------------------------------------------------


def make_feature_obj(
    name: str = "Login",
    tags: list[str] | None = None,
) -> SimpleNamespace:
    """Build a mock Behave feature object."""
    return SimpleNamespace(
        name=name,
        filename=f"features/{name.lower()}.feature",
        tags=tags if tags is not None else [],
    )


def make_scenario_obj(
    name: str = "S1",
    tags: list[str] | None = None,
    is_outline: bool = False,
    line: int | None = 10,
    rule_name: str | None = None,
    status: str | None = None,
    error: object | None = None,
) -> SimpleNamespace:
    """Build a mock Behave scenario object."""
    location = (
        SimpleNamespace(filename="features/login.feature", line=line) if line is not None else None
    )
    rule = SimpleNamespace(name=rule_name) if rule_name else None
    ns = SimpleNamespace(
        name=name,
        tags=tags if tags is not None else [],
        location=location,
        rule=rule,
        is_outline=is_outline,
    )
    if status is not None:
        ns.status = status
    if error is not None:
        ns.error = error
    return ns


def make_step_obj(
    status: str = "passed",
    error: object | None = None,
    table: object | None = None,
    text: object | None = None,
) -> SimpleNamespace:
    """Build a mock Behave step object."""
    return SimpleNamespace(name="step", status=status, error=error, table=table, text=text)


# ---------------------------------------------------------------------------
# Model factories (dataclasses)
# ---------------------------------------------------------------------------


def make_feature_summary(
    name: str = "Login",
    total: int = 3,
    passed: int = 2,
    failed: int = 1,
    skipped: int = 0,
    undefined: int = 0,
    pass_rate: float = 66.7,
    duration: float = 1.234,
    tags: list[str] | None = None,
) -> FeatureSummary:
    """Build a FeatureSummary with sensible defaults."""
    return FeatureSummary(
        feature_name=name,
        tags=tags if tags is not None else [],
        total_scenarios=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        undefined=undefined,
        pass_rate=pass_rate,
        duration=duration,
    )


def make_scenario_result(
    *,
    feature_name: str = "Login",
    scenario_name: str = "Successful login",
    status: str = STATUS_PASSED,
    duration: float = 1.234,
    tags: list[str] | None = None,
    feature_tags: list[str] | None = None,
    error_message: str = "",
    error_type: str = "",
    traceback: str = "",
    step_count: int = 5,
    passed_steps: int = 5,
    failed_steps: int = 0,
    skipped_steps: int = 0,
    file: str = "features/login.feature",
    line: int = 10,
    rule: str = "",
    is_outline: bool = False,
    background_steps: int = 0,
    has_data_table: bool = False,
    has_docstring: bool = False,
) -> ScenarioResult:
    """Build a ScenarioResult with sensible defaults."""
    return ScenarioResult(
        feature_name=feature_name,
        scenario_name=scenario_name,
        status=status,
        duration=duration,
        tags=tags if tags is not None else [],
        feature_tags=feature_tags if feature_tags is not None else [],
        error_message=error_message,
        error_type=error_type,
        traceback=traceback,
        step_count=step_count,
        passed_steps=passed_steps,
        failed_steps=failed_steps,
        skipped_steps=skipped_steps,
        file=file,
        line=line,
        rule=rule,
        is_outline=is_outline,
        background_steps=background_steps,
        has_data_table=has_data_table,
        has_docstring=has_docstring,
    )


def make_history_entry(
    timestamp: str = "2025-01-01T12:00:00+00:00",
    pass_rate: float = 85.5,
    total_features: int = 2,
    total_scenarios: int = 10,
    passed: int = 8,
    failed: int = 1,
    skipped: int = 1,
    duration: float = 5.0,
) -> HistoryEntry:
    """Build a HistoryEntry with sensible defaults."""
    return HistoryEntry(
        timestamp=timestamp,
        pass_rate=pass_rate,
        total_features=total_features,
        total_scenarios=total_scenarios,
        passed=passed,
        failed=failed,
        skipped=skipped,
        duration=duration,
    )


def make_run_summary(
    features: list[FeatureSummary] | None = None,
    scenarios: list[ScenarioResult] | None = None,
    run_id: str = "run-001",
    passed: int | None = None,
    failed: int | None = None,
    skipped: int | None = None,
    undefined: int | None = None,
    total_features: int | None = None,
    total_scenarios: int | None = None,
    pass_rate: float | None = None,
    duration: float = 10.5,
) -> RunSummary:
    """Build a RunSummary with the given features and scenarios.

    When ``passed``/``failed``/etc. are ``None``, they are computed from
    the scenarios list if provided, otherwise sensible defaults are used.
    """
    if passed is None:
        passed = sum(1 for s in scenarios if s.status == "passed") if scenarios is not None else 5
    if failed is None:
        failed = sum(1 for s in scenarios if s.status == "failed") if scenarios is not None else 1
    if skipped is None:
        skipped = sum(1 for s in scenarios if s.status == "skipped") if scenarios is not None else 0
    if undefined is None:
        undefined = (
            sum(1 for s in scenarios if s.status == "undefined") if scenarios is not None else 0
        )
    if total_features is None:
        total_features = len(features) if features is not None else 2
    if total_scenarios is None:
        total_scenarios = len(scenarios) if scenarios is not None else 6
    if pass_rate is None:
        if scenarios is None:
            pass_rate = 83.33
        elif len(scenarios) == 0:
            pass_rate = 0.0
        else:
            pass_rate = 100.0 if all(s.status == "passed" for s in scenarios) else 0.0

    return RunSummary(
        run_id=run_id,
        start_time="2025-01-01T00:00:00+00:00",
        end_time="2025-01-01T00:00:10+00:00",
        duration=duration,
        total_features=total_features,
        total_scenarios=total_scenarios,
        passed=passed,
        failed=failed,
        skipped=skipped,
        undefined=undefined,
        pass_rate=pass_rate,
        features=features if features is not None else [],
        scenarios=scenarios if scenarios is not None else [],
    )


# ---------------------------------------------------------------------------
# Test utilities
# ---------------------------------------------------------------------------


class StreamOpener:
    """Mock stream opener for formatter tests.

    If ``stream`` is provided, ``open()`` returns it.
    If ``name`` is provided, it is used for path resolution.
    """

    def __init__(self, stream: Any = None, name: str | None = None) -> None:
        self._stream = stream if stream is not None else StringIO()
        self.name = name

    def open(self) -> Any:
        return self._stream


class NoFlushStream:
    """A minimal stream that supports write but not flush."""

    def __init__(self) -> None:
        self.buffer: str = ""

    def write(self, data: str) -> int:
        self.buffer += data
        return len(data)


def make_config(userdata: dict[str, str] | None = None) -> SimpleNamespace:
    """Build a mock config with userdata."""
    return SimpleNamespace(userdata=userdata if userdata is not None else {})


def run_full_cycle(
    formatter: Any,
    feature: SimpleNamespace,
    scenarios: list[tuple[SimpleNamespace, list[tuple[SimpleNamespace, SimpleNamespace]]]],
) -> None:
    """Run a complete Behave lifecycle through the formatter.

    Args:
        formatter: The formatter instance.
        feature: Mock feature object.
        scenarios: List of (scenario, [(step, result), ...]) tuples.
    """
    formatter.uri(f"features/{feature.name.lower()}.feature")
    formatter.feature(feature)
    for scenario, steps in scenarios:
        formatter.scenario(scenario)
        for step, result in steps:
            formatter.step(step)
            formatter.result(result)
    formatter.eof()
    formatter.close()
