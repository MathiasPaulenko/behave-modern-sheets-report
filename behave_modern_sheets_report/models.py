"""Pure dataclasses for the sheets execution model.

Zero dependencies on Behave, openpyxl, odfpy or any other external library.
These dataclasses represent the canonical data that flows from the collector
through the writers and into CSV, XLSX or ODS reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ScenarioResult:
    """A single scenario result — one row in the CSV / Details sheet.

    Attributes:
        feature_name: Name of the parent feature.
        scenario_name: Name of the scenario.
        status: Canonical status string (``passed``, ``failed``, ``skipped``, ``undefined``).
        duration: Execution time in seconds.
        tags: Scenario tags as a list of strings.
        error_message: Error message if the scenario failed, empty otherwise.
        error_type: Exception type name if the scenario failed, empty otherwise.
        traceback: Full traceback string if the scenario failed, empty otherwise.
        step_count: Total number of steps in the scenario.
        passed_steps: Number of steps that passed.
        failed_steps: Number of steps that failed.
        skipped_steps: Number of steps that were skipped.
        file: Feature file path.
        line: Line number of the scenario in the feature file.
        rule: Gherkin rule name if the scenario belongs to a rule, empty otherwise.
        is_outline: Whether the scenario is a scenario outline example row.
    """

    feature_name: str = ""
    scenario_name: str = ""
    status: str = ""
    duration: float = 0.0
    tags: list[str] = field(default_factory=list)
    error_message: str = ""
    error_type: str = ""
    traceback: str = ""
    step_count: int = 0
    passed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    file: str = ""
    line: int = 0
    rule: str = ""
    is_outline: bool = False


@dataclass(slots=True)
class FeatureSummary:
    """Aggregated summary for a single feature.

    Attributes:
        feature_name: Name of the feature.
        total_scenarios: Total number of scenarios in the feature.
        passed: Number of scenarios that passed.
        failed: Number of scenarios that failed.
        skipped: Number of scenarios that were skipped.
        undefined: Number of scenarios with undefined steps.
        pass_rate: Percentage of passed scenarios (0.0–100.0).
        duration: Total execution time in seconds.
    """

    feature_name: str = ""
    total_scenarios: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    undefined: int = 0
    pass_rate: float = 0.0
    duration: float = 0.0


@dataclass(slots=True)
class RunSummary:
    """Root summary object for a complete Behave run.

    Attributes:
        run_id: Unique identifier for the run.
        start_time: ISO 8601 timestamp of run start.
        end_time: ISO 8601 timestamp of run end.
        duration: Total execution time in seconds.
        total_features: Total number of features executed.
        total_scenarios: Total number of scenarios executed.
        passed: Number of scenarios that passed.
        failed: Number of scenarios that failed.
        skipped: Number of scenarios that were skipped.
        undefined: Number of scenarios with undefined steps.
        pass_rate: Overall pass rate percentage (0.0–100.0).
        features: List of per-feature summaries.
        scenarios: List of per-scenario results.
    """

    run_id: str = ""
    start_time: str = ""
    end_time: str = ""
    duration: float = 0.0
    total_features: int = 0
    total_scenarios: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    undefined: int = 0
    pass_rate: float = 0.0
    features: list[FeatureSummary] = field(default_factory=list)
    scenarios: list[ScenarioResult] = field(default_factory=list)


@dataclass(slots=True)
class HistoryEntry:
    """Lightweight record for run history persistence.

    Attributes:
        run_id: Unique identifier for the run.
        timestamp: ISO 8601 timestamp of the run.
        total_features: Total number of features executed.
        total_scenarios: Total number of scenarios executed.
        passed: Number of scenarios that passed.
        failed: Number of scenarios that failed.
        skipped: Number of scenarios that were skipped.
        undefined: Number of scenarios with undefined steps.
        pass_rate: Overall pass rate percentage (0.0–100.0).
        duration: Total execution time in seconds.
    """

    run_id: str = ""
    timestamp: str = ""
    total_features: int = 0
    total_scenarios: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    undefined: int = 0
    pass_rate: float = 0.0
    duration: float = 0.0


__all__ = [
    "FeatureSummary",
    "HistoryEntry",
    "RunSummary",
    "ScenarioResult",
]
