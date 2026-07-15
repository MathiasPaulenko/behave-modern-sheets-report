# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
