# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-08-10

### Added

- Entry points registered in `behave.formatters` group (`csv-modern`, `xlsx-modern`, `ods-modern`) for automatic discovery by `behave-runner` and compatible tools.
- Gherkin v6 coverage: feature-level tags (`feature_tags` column), background step count (`background_steps` column), data table detection (`has_data_table` column), and docstring detection (`has_docstring` column).
- Tags column in Summary sheet for XLSX and ODS formats.

### Fixed

- Zero-step scenarios (e.g. skipped via tags) now correctly report `skipped` status instead of `passed` in `_derive_scenario_status`.
- `Collector.finalize()` now auto-finalizes pending scenarios and features before computing totals, preventing silent data loss when used without explicit `end_scenario()`/`end_feature()` calls.
- `end_step()` resets `_current_step` and `_step_start` when no scenario is active, preventing stale state from leaking into subsequent scenarios.
- `start_feature()` finalizes any in-progress scenario and feature and resets background state, preventing stale counts from a prior feature.
- `start_scenario()` handles `TypeError`/`ValueError` when converting `location.line` to int, falling back to `0`.
- `parse_columns()` removes duplicate column names to prevent duplicate CSV headers.
- `History.load()` catches `OSError` broadly (including `IsADirectoryError`) instead of only `FileNotFoundError`.
- Invalid `max_history` values (non-integer, negative, zero) now fall back to the default (100) instead of crashing.
- XLSX and ODS imports in `__init__.py` are now optional, so the package works without `openpyxl`/`odfpy` installed.
- `VALID_COLUMNS` is now exported in `utils.__all__` as a public constant.
- `pytest-asyncio` deprecation warning on Python 3.14 filtered to prevent test failures under `filterwarnings = ["error"]`.
- `pyproject.toml` license updated to SPDX expression format (`"MIT"`) and deprecated license classifier removed.

### Changed

- Test count increased from 386 to 413 with additional regression tests for all bug fixes.

## [1.0.0] - 2025-07-15

### Added

- Project scaffolding: `pyproject.toml` with setuptools build backend, extras `[behave]`, `[xlsx]`, `[ods]`, `[dev]`.
- Tooling configuration: ruff (`E,F,W,I,UP,B,C4,SIM`, line-length 100), mypy (`--strict`), pytest with coverage threshold 100.
- CI workflow with lint, typecheck, test matrix (ubuntu/windows/macos × Python 3.11/3.12/3.13/3.14), and packaging jobs.
- Release workflow via Trusted Publishing (OIDC) to PyPI.
- Pre-commit hooks: ruff, mypy, standard hygiene hooks.
- MIT license.
- Three output formats: CSV (stdlib), XLSX (openpyxl), ODS (odfpy).
- Multi-sheet workbooks: Summary, Details, Failures, and Trends sheets.
- Conditional formatting with color-coded pass/fail/skipped cells.
- Automatic trend history with atomic JSON persistence.
- Configurable columns, delimiter, failure-only filtering, and history limits.
- Full Behave status normalization including `xfailed`, `xpassed`, `error`, `hook_error`, `cleanup_error`, and `pending`.
- Undefined column in Trends sheet for complete scenario accounting.
- 100% test coverage with 386 tests including chaos and edge case suites.
