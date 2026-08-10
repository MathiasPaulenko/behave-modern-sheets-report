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

__version__ = "1.1.1"

__all__ = [
    "BaseSheetsFormatter",
    "CSVFormatter",
    "CSVWriter",
    "Collector",
    "FeatureSummary",
    "History",
    "HistoryEntry",
    "RunSummary",
    "ScenarioResult",
    "__version__",
]

try:
    from .xlsx_formatter import XLSXFormatter
    from .xlsx_writer import XLSXWriter

    __all__ += ["XLSXFormatter", "XLSXWriter"]
except ImportError:  # pragma: no cover
    pass

try:
    from .ods_formatter import ODSFormatter
    from .ods_writer import ODSWriter

    __all__ += ["ODSFormatter", "ODSWriter"]
except ImportError:  # pragma: no cover
    pass
