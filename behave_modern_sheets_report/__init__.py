"""behave-modern-sheets-report — spreadsheet report formatters for Behave.

Provides three formatters that generate execution reports from Behave BDD
test runs:

- **CSV** — flat tabular output, no external dependencies.
- **XLSX** — multi-sheet Excel workbook with conditional formatting (requires ``openpyxl``).
- **ODS** — OpenDocument spreadsheet with styled cells (requires ``odfpy``).

XLSX and ODS include Summary, Details, Failures, and optional Trends sheets
populated from an automatic run history persisted to a JSON file. CSV outputs
a single table of scenario results.
"""

from __future__ import annotations

from .base_formatter import BaseSheetsFormatter
from .collector import Collector
from .csv_formatter import CSVFormatter
from .csv_writer import CSVWriter
from .history import History
from .models import FeatureSummary, HistoryEntry, RunSummary, ScenarioResult
from .ods_formatter import ODSFormatter
from .ods_writer import ODSWriter
from .xlsx_formatter import XLSXFormatter
from .xlsx_writer import XLSXWriter

__version__ = "0.1.0"

__all__ = [
    "BaseSheetsFormatter",
    "CSVFormatter",
    "CSVWriter",
    "Collector",
    "FeatureSummary",
    "History",
    "HistoryEntry",
    "ODSFormatter",
    "ODSWriter",
    "RunSummary",
    "ScenarioResult",
    "XLSXFormatter",
    "XLSXWriter",
    "__version__",
]
