# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Critical:** scenario statuses and step counts were silently wrong. Behave announces every `step` upfront and fires `result` once per executed step, but the collector assumed alternating step/result pairs — only the first result per scenario was recorded, so failures beyond the first step were lost and scenarios were misreported as `passed`. The collector now queues announced steps and records every result.
- Steps skipped after a failure (Behave emits no `result` for them) are now counted as `skipped` at scenario end instead of disappearing from the totals.
- **Critical:** features using `Background:` reported every scenario as `skipped` with zero steps. The collector relied on an end-of-background event that Behave never emits, leaving its `_in_background` flag set forever. Background steps are now detected via `scenario.background_steps`, count toward `steps` and the status counters, and `background_steps` reports how many actually executed.
- `has_data_table`/`has_docstring` now inspect every executed step, not only the first.
- `BaseSheetsFormatter` now mirrors the `stream_opener`/`stream`/`config` attributes expected by `behave.formatter.base.Formatter` (so inherited helpers such as `stdout_mode` work), and `close()` closes the stream opener, fixing a file-handle leak in CSV output.
- `safe_tags()` drops `None` items instead of producing a literal `"None"` tag, and accepts tuples/sets (e.g. Behave's `effective_tags`).
- The example project's `environment.py` moved into `features/` — Behave only loads it from there.
- The test suite now exercises the real Behave event ordering; new unit and integration regression tests cover failures in non-first steps and feature backgrounds.
- Integration tests no longer fail to collect when `openpyxl`/`odfpy` are missing (optional imports guarded with `pytest.importorskip`).
- Corrected documentation claims about automatic formatter discovery — Behave registers formatters only via the `[behave.formatters]` config section.
- `SECURITY.md` supported versions updated for the `1.1.x` series (it still claimed `0.1.x` / pre-alpha).

### Changed

- `steps` now includes background steps (matching Behave's own step totals); `background_steps` reports the subset that are background steps.
- `Collector.start_background()`/`end_background()` are deprecated no-ops kept for API compatibility.
- Build requirement bumped to `setuptools>=77`, required for the SPDX `license` string.

### Removed

- `behave.formatters` entry points from `pyproject.toml` — Behave does not consume Python entry points for formatter discovery.

## [1.1.1] - 2026-08-10

### Fixed

- Re-release of 1.1.0 as 1.1.1 because the `v1.1.0` tag already existed on the remote.
- CI: added `CHANGELOG.md` to the release workflow trigger paths.

## [1.1.0] - 2026-08-10

### Added

- Entry points declared in the `behave.formatters` group (`csv-modern`, `xlsx-modern`, `ods-modern`). **Note:** Behave does not consume these entry points; they were removed in a later release. Register formatters via `[behave.formatters]` in your config.
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

## [1.0.1] - 2026-08-06

### Fixed

- Added missing author email in `pyproject.toml`.

## [1.0.0] - 2026-07-15

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
