# behave-modern-sheets-report

[![CI](https://github.com/MathiasPaulenko/behave-modern-sheets-report/actions/workflows/ci.yml/badge.svg)](https://github.com/MathiasPaulenko/behave-modern-sheets-report/actions/workflows/ci.yml)
[![Release](https://github.com/MathiasPaulenko/behave-modern-sheets-report/actions/workflows/release.yml/badge.svg)](https://github.com/MathiasPaulenko/behave-modern-sheets-report/actions/workflows/release.yml)
[![PyPI version](https://img.shields.io/pypi/v/behave-modern-sheets-report.svg)](https://pypi.org/project/behave-modern-sheets-report/)
[![Python versions](https://img.shields.io/pypi/pyversions/behave-modern-sheets-report.svg)](https://pypi.org/project/behave-modern-sheets-report/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/MathiasPaulenko/behave-modern-sheets-report)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)
[![Type checker: mypy](https://img.shields.io/badge/type%20checker-mypy-blue.svg)](https://mypy-lang.org/)
[![Stable](https://img.shields.io/badge/status-stable-brightgreen.svg)](https://github.com/MathiasPaulenko/behave-modern-sheets-report)
[![SemVer](https://img.shields.io/badge/semver-2.0.0-blue.svg)](https://semver.org/spec/v2.0.0.html)

> Modern spreadsheet report formatters for **Behave** BDD — generate CSV, XLSX, and ODS execution reports with multi-sheet layouts, conditional formatting, and automatic trend history.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Format Comparison](#format-comparison)
- [Report Structure](#report-structure)
- [CLI Usage](#cli-usage)
- [Configuration Options](#configuration-options)
- [Available Columns](#available-columns)
- [Automatic History & Trends](#automatic-history--trends)
- [Programmatic Usage](#programmatic-usage)
- [Architecture](#architecture)
- [Ecosystem](#ecosystem)
- [Contributing](#contributing)
- [Security](#security)
- [Changelog](#changelog)
- [License](#license)

## Features

| | Feature | Description |
| --- | --- | --- |
| 📊 | **Three output formats** | CSV (stdlib, zero dependencies), XLSX (via `openpyxl`), and ODS (via `odfpy`) |
| 📑 | **Multi-sheet workbooks** | Summary, Details, Failures, and Trends sheets in XLSX and ODS |
| 🎨 | **Conditional formatting** | Color-coded pass/fail cells for at-a-glance status reading |
| 📈 | **Automatic trend history** | Every run is persisted to a JSON file and visualized in a Trends sheet |
| ⚙️ | **Configurable columns** | Choose which columns appear in the Details sheet via `userdata` |
| 🔒 | **Atomic history writes** | Corruption-proof file I/O using temp file + `os.replace` |
| ✅ | **100% test coverage** | Fully tested across Python 3.11, 3.12, 3.13, and 3.14 on Linux, Windows, and macOS |
| 🪶 | **Zero required dependencies** | CSV works with Python stdlib alone; XLSX and ODS are opt-in extras |

## Requirements

- Python 3.11 or higher
- [Behave](https://github.com/behave/behave) >= 1.2.6 (for running BDD tests)
- `openpyxl >= 3.1` (optional, for XLSX output)
- `odfpy >= 1.4` (optional, for ODS output)

## Installation

```bash
pip install behave-modern-sheets-report
```

### Extras

| Extra | Packages | When to use |
| --- | --- | --- |
| `[behave]` | `behave>=1.2.6` | You need Behave installed alongside the formatter |
| `[xlsx]` | `openpyxl>=3.1` | You want XLSX output |
| `[ods]` | `odfpy>=1.4` | You want ODS output |
| `[dev]` | `pytest`, `ruff`, `mypy`, `build`, `twine` | Local development |

Install with multiple extras:

```bash
pip install "behave-modern-sheets-report[xlsx,ods]"
```

For full development setup:

```bash
git clone https://github.com/MathiasPaulenko/behave-modern-sheets-report.git
cd behave-modern-sheets-report
pip install -e ".[dev,xlsx,ods]"
pre-commit install
```

## Quick Start

1. The formatters are registered as `behave.formatters` entry points, so they are discoverable by `behave-runner` and other tools automatically. If you use plain `behave`, register them in your `behave.ini`:

   ```ini
   [behave.formatters]
   csv-modern = behave_modern_sheets_report.csv_formatter:CSVFormatter
   xlsx-modern = behave_modern_sheets_report.xlsx_formatter:XLSXFormatter
   ods-modern = behave_modern_sheets_report.ods_formatter:ODSFormatter
   ```

2. Run Behave with any (or all) of the formatters:

   ```bash
   behave -f xlsx-modern -o report.xlsx
   ```

3. Open `report.xlsx` in Excel, LibreOffice, or Google Sheets.

## Format Comparison

| Feature | CSV | XLSX | ODS |
|---|---|---|---|
| Dependency | stdlib | `openpyxl` | `odfpy` |
| Multi-sheet | Single file | Yes | Yes |
| Conditional formatting | — | Cell fills | Cell styles |
| Auto-filters | — | Yes | — |
| Freeze panes | — | Yes | — |
| Bold headers | — | Yes | Yes |
| Trends sheet | — | Yes | Yes |
| Install extra | — | `[xlsx]` | `[ods]` |

## Report Structure

XLSX and ODS reports contain up to four sheets:

| Sheet | Content | When present |
| --- | --- | --- |
| **Summary** | One row per feature with totals, pass rate, and duration | Always |
| **Details** | One row per scenario with configurable columns | Always |
| **Failures** | Failed scenarios only — error message, type, traceback, file, line | Always (empty if no failures) |
| **Trends** | Historical run entries with pass rate evolution over time | When history exists |

CSV reports produce a single flat file with one row per scenario (equivalent to the Details sheet).

### Conditional formatting colors

| Status | Cell fill |
| --- | --- |
| Passed | Green (`#C6EFCE`) |
| Failed | Red (`#FFC7CE`) |
| Skipped | Yellow (`#FFEB9C`) |

## CLI Usage

The formatters are registered as `behave.formatters` entry points in `pyproject.toml`, making them discoverable by `behave-runner` and compatible tools. When using plain `behave`, register them in `behave.ini`:

```ini
[behave.formatters]
csv-modern = behave_modern_sheets_report.csv_formatter:CSVFormatter
xlsx-modern = behave_modern_sheets_report.xlsx_formatter:XLSXFormatter
ods-modern = behave_modern_sheets_report.ods_formatter:ODSFormatter
```

Generate reports:

```bash
behave -f csv-modern -o report.csv
behave -f xlsx-modern -o report.xlsx
behave -f ods-modern -o report.ods
```

Multiple formatters can be used simultaneously to produce all formats in a single run:

```bash
behave -f csv-modern -o report.csv -f xlsx-modern -o report.xlsx -f ods-modern -o report.ods
```

You can also set `userdata` options directly in `behave.ini`:

```ini
[behave.userdata]
report_columns = feature,scenario,status,duration,error
report_only_failed = false
report_max_history = 50
```

## Configuration Options

All options are passed via Behave's `userdata` (command-line `-D` or `behave.ini`):

| Option | Type | Default | Description |
|---|---|---|---|
| `report_columns` | CSV string | `feature,scenario,status,duration,tags,error` | Columns shown in Details sheet |
| `report_only_failed` | bool | `false` | Show only failed scenarios in Details |
| `report_delimiter` | string | `comma` | CSV delimiter (`comma`, `semicolon`, `tab`) |
| `report_clear_history` | bool | `false` | Clear history before appending current run |
| `report_history_path` | string | `.behave-sheets-history.json` | Path to history JSON file |
| `report_max_history` | int | `100` | Maximum history entries to retain |

### Examples

Generate an XLSX report with only failed scenarios and a custom column set:

```bash
behave -f xlsx-modern -o report.xlsx \
  -D report_only_failed=true \
  -D report_columns=feature,scenario,status,error \
  -D report_max_history=50
```

Use a semicolon delimiter for CSV (useful in European locales):

```bash
behave -f csv-modern -o report.csv -D report_delimiter=semicolon
```

Clear history before a fresh run (e.g. after changing the test suite):

```bash
behave -f xlsx-modern -o report.xlsx -D report_clear_history=true
```

Store history in a custom location (e.g. outside the working directory):

```bash
behave -f xlsx-modern -o report.xlsx -D report_history_path=/tmp/behave-history.json
```

## Available Columns

The `report_columns` option accepts any combination of the following column names (comma-separated):

| Column | Description |
| --- | --- |
| `feature` | Feature name |
| `scenario` | Scenario name |
| `status` | Scenario status (`passed`, `failed`, `skipped`, `undefined`) |
| `duration` | Execution time (human-readable, e.g. `1.234s`, `12ms`) |
| `tags` | Scenario tags (semicolon-separated) |
| `error` | Error message with type if available (e.g. `AssertionError [...]`) |
| `error_type` | Exception type name |
| `traceback` | Full traceback string |
| `steps` | Total step count |
| `passed_steps` | Number of passed steps |
| `failed_steps` | Number of failed steps |
| `skipped_steps` | Number of skipped steps |
| `file` | Feature file path |
| `line` | Line number in the feature file |
| `rule` | Gherkin rule name (empty if none) |
| `is_outline` | `true` if scenario outline example row, `false` otherwise |
| `feature_tags` | Feature-level tags (semicolon-separated) |
| `background_steps` | Number of background steps executed before the scenario |
| `has_data_table` | `true` if any step includes a Gherkin data table |
| `has_docstring` | `true` if any step includes a Gherkin docstring |

**Default columns**: `feature,scenario,status,duration,tags,error`

## Automatic History & Trends

Every run is automatically appended to a JSON history file (`.behave-sheets-history.json` by default). The history feeds the **Trends** sheet in XLSX and ODS reports, showing pass rate evolution across runs.

- **`report_history_path`** — custom location for the history file.
- **`report_clear_history`** — clears all previous entries before appending the current run (useful for fresh starts).
- **`report_max_history`** — limits the number of retained entries (oldest are dropped).

History is managed atomically (write to `.tmp`, then `os.replace`) to prevent corruption.

### History file format

The history file is a JSON array of entry objects:

```json
[
  {
    "run_id": "run_a1b2c3d4e5f6",
    "timestamp": "2025-01-15T10:30:00.123456+00:00",
    "total_features": 3,
    "total_scenarios": 15,
    "passed": 14,
    "failed": 1,
    "skipped": 0,
    "undefined": 0,
    "pass_rate": 93.3,
    "duration": 2.45
  }
]
```

## Programmatic Usage

You can use the collector, writers, and history directly without Behave:

```python
from behave_modern_sheets_report import Collector, CSVWriter, XLSXWriter, History
from pathlib import Path

# Collect results from Behave events
collector = Collector()
collector.start_feature(feature_obj)
collector.start_scenario(scenario_obj)
collector.start_step(step_obj)
collector.end_step(step_obj)
collector.end_scenario()
collector.end_feature()
run_summary = collector.finalize()

# Write CSV (no extra dependencies needed)
with open("report.csv", "w", newline="") as f:
    CSVWriter.write(run_summary, f)

# Write XLSX (requires openpyxl)
history = History(max_entries=50)
trends = history.append(run_summary)
XLSXWriter.write(run_summary, Path("report.xlsx"), trends=trends)
```

This is useful for integrating the report generation into custom test runners or CI pipelines.

## Architecture

```text
Behave Runner
    │
    ├── CSVFormatter ──► Collector ──► RunSummary ──► CSVWriter ──► report.csv
    ├── XLSXFormatter ──► Collector ──► RunSummary ──► XLSXWriter ──► report.xlsx
    └── ODSFormatter ───► Collector ──► RunSummary ──► ODSWriter ───► report.ods
                                        │
                                        └──► History ──► .behave-sheets-history.json
                                                │
                                                └──► Trends sheet
```

**Collector** processes Behave events (feature, scenario, step, result) and builds a `RunSummary`. **Writers** serialize the summary into the target format. **History** persists run metrics between executions for trend analysis.

### Key design decisions

- **Pure data models** — `models.py` has zero external dependencies. Dataclasses can be serialized to any format without importing Behave, openpyxl, or odfpy.
- **Single Behave integration point** — `Collector` is the only module that touches Behave objects. Everything else operates on pure dataclasses, making the writers and history fully testable without Behave.
- **Opt-in dependencies** — CSV works with stdlib alone. `openpyxl` and `odfpy` are only imported when their respective writer is called.
- **Atomic file I/O** — History writes to a `.tmp` file first, then uses `os.replace` for an atomic swap. This prevents corruption if the process is killed mid-write.

## Ecosystem

Part of the **behave-modern-*** formatter family:

| Package | Formats | Status |
| --- | --- | --- |
| `behave-modern-json-report` | JSON | ✅ |
| `behave-modern-html-report` | HTML | ✅ |
| `behave-modern-md-report` | Markdown | ✅ |
| `behave-modern-console-report` | Console (rich terminal) | ✅ |
| `behave-modern-sheets-report` | CSV, XLSX, ODS | **this package** |

## Contributing

Contributions are welcome! Please read the [Contributing Guide](CONTRIBUTING.md) and our [Code of Conduct](CODE_OF_CONDUCT.md) before submitting pull requests.

### Development commands

```bash
make lint        # ruff check + format check
make typecheck   # mypy --strict
make test        # pytest with verbose output
make format      # ruff auto-fix + format
make build       # build sdist + wheel
```

## Security

If you discover a security vulnerability, please refer to our [Security Policy](SECURITY.md) for responsible disclosure instructions.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history and notable changes.

## License

MIT — see [LICENSE](LICENSE) for full text.

---

<p align="center">Made with care by <a href="https://github.com/MathiasPaulenko">Mathias Paulenko</a></p>
