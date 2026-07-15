"""Shared utility helpers for the sheets report formatter.

Zero external dependencies — only Python stdlib. These helpers cover status
normalization, safe string conversions, timing, identifier generation, and
parsing of user-supplied configuration values.
"""

from __future__ import annotations

import math
import time
import uuid
from datetime import UTC, datetime

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------

STATUS_PASSED = "passed"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
STATUS_UNDEFINED = "undefined"
STATUS_UNTESTED = "untested"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_COLUMNS: list[str] = ["feature", "scenario", "status", "duration", "tags", "error"]

VALID_COLUMNS: frozenset[str] = frozenset({
    "feature", "scenario", "status", "duration", "tags", "error",
    "error_type", "traceback", "steps", "passed_steps", "failed_steps",
    "skipped_steps", "file", "line", "rule", "is_outline",
})

_MAX_STR_LENGTH = 500


# ---------------------------------------------------------------------------
# Safe conversions
# ---------------------------------------------------------------------------


def safe_str(value: object | None) -> str:
    """Convert a value to a stripped, truncated string.

    Args:
        value: Any value or ``None``.

    Returns:
        A stripped string representation of ``value``. If the result exceeds
        500 characters it is truncated to 500 and suffixed with ``"..."``.
        ``None`` returns an empty string.

    Examples:
        >>> safe_str(None)
        ''
        >>> safe_str("  hello  ")
        'hello'
        >>> safe_str(42)
        '42'
    """
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) > _MAX_STR_LENGTH:
        return text[:_MAX_STR_LENGTH] + "..."
    return text


def safe_tags(value: object | None) -> list[str]:
    """Normalize tag-like input into a list of strings.

    Args:
        value: ``None``, a comma-separated string, a list of strings, or
            any other type.

    Returns:
        A list of tag strings. ``None`` returns ``[]``. A string is split by
        commas and each part is stripped. A list is copied with each item
        converted to a stripped string. Any other type returns ``[]``.

    Examples:
        >>> safe_tags(None)
        []
        >>> safe_tags("smoke, auth")
        ['smoke', 'auth']
        >>> safe_tags(["a", "b"])
        ['a', 'b']
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------


def monotonic_seconds(start: float) -> float:
    """Return elapsed seconds since ``start`` using a monotonic clock.

    Args:
        start: A ``time.monotonic()`` reference value.

    Returns:
        Elapsed seconds as a float.
    """
    return time.monotonic() - start


def now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string.

    Returns:
        An ISO 8601 formatted timestamp with timezone information.

    Examples:
        >>> now_iso()  # doctest: +SKIP
        '2025-01-01T12:00:00.123456+00:00'
    """
    return datetime.now(UTC).isoformat()


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as a human-readable string.

    Args:
        seconds: Duration in seconds. Must be non-negative.

    Returns:
        A string like ``"1.234s"``, ``"12ms"`` or ``"0s"``.
        Returns ``"N/A"`` for negative, NaN, or infinite values.

    Examples:
        >>> format_duration(0)
        '0s'
        >>> format_duration(0.012)
        '12ms'
        >>> format_duration(1.234)
        '1.234s'
    """
    if seconds < 0 or math.isnan(seconds) or math.isinf(seconds):
        return "N/A"
    if seconds < 0.001:
        return "0s"
    if seconds < 1.0:
        return f"{int(seconds * 1000)}ms"
    return f"{seconds:.3f}s"


# ---------------------------------------------------------------------------
# Status normalization
# ---------------------------------------------------------------------------


def normalize_status(behave_status: str | None) -> str:
    """Map a Behave status string to a canonical status constant.

    Behave's ``Status`` enum includes values beyond the basic four: ``xfailed``
    (expected failure that failed) and ``xpassed`` (expected failure that
    passed) are treated as ``passed``; ``error``, ``hook_error``, and
    ``cleanup_error`` are treated as ``failed``; ``pending`` is treated as
    ``undefined``.

    Args:
        behave_status: A status string from Behave (e.g. ``"passed"``).

    Returns:
        One of ``STATUS_PASSED``, ``STATUS_FAILED``, ``STATUS_SKIPPED``,
        ``STATUS_UNDEFINED``, or ``STATUS_UNTESTED`` for unrecognized values.

    Examples:
        >>> normalize_status("passed")
        'passed'
        >>> normalize_status("xfailed")
        'passed'
        >>> normalize_status("error")
        'failed'
        >>> normalize_status("pending")
        'undefined'
        >>> normalize_status("unknown")
        'untested'
    """
    if behave_status is None:
        return STATUS_UNTESTED
    status = behave_status.lower().strip()
    if status in (STATUS_PASSED, "xfailed", "xpassed"):
        return STATUS_PASSED
    if status in (STATUS_FAILED, "error", "hook_error", "cleanup_error"):
        return STATUS_FAILED
    if status == STATUS_SKIPPED:
        return STATUS_SKIPPED
    if status in (STATUS_UNDEFINED, "pending"):
        return STATUS_UNDEFINED
    return STATUS_UNTESTED


# ---------------------------------------------------------------------------
# Identifiers
# ---------------------------------------------------------------------------


def generate_id(prefix: str = "run") -> str:
    """Generate a unique identifier with a prefix.

    Args:
        prefix: A prefix prepended to the hex identifier.

    Returns:
        A string like ``"run_a1b2c3d4e5f6"``.

    Examples:
        >>> generate_id("feat")  # doctest: +SKIP
        'feat_a1b2c3d4e5f6'
    """
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Configuration parsing
# ---------------------------------------------------------------------------


def parse_columns(raw: str | None) -> list[str]:
    """Parse a comma-separated column list from user input.

    Unknown column names are silently filtered out. If all names are
    invalid or ``raw`` is ``None``/empty, ``DEFAULT_COLUMNS`` is returned.

    Args:
        raw: A comma-separated string of column names, or ``None``.

    Returns:
        A list of valid, stripped column names. Returns
        ``DEFAULT_COLUMNS`` if ``raw`` is ``None``, empty, or contains
        only invalid names.

    Examples:
        >>> parse_columns(None)
        ['feature', 'scenario', 'status', 'duration', 'tags', 'error']
        >>> parse_columns("feature, scenario")
        ['feature', 'scenario']
        >>> parse_columns("feature, bogus")
        ['feature']
    """
    if raw is None or not raw.strip():
        return list(DEFAULT_COLUMNS)
    parsed = [col.strip() for col in raw.split(",") if col.strip()]
    valid = [col for col in parsed if col in VALID_COLUMNS]
    if not valid:
        return list(DEFAULT_COLUMNS)
    return valid


def parse_delimiter(raw: str | None) -> str:
    """Parse a delimiter name into the actual delimiter character.

    Args:
        raw: One of ``"comma"``, ``"semicolon"``, ``"tab"`` (case-insensitive).

    Returns:
        The delimiter character: ``,``, ``;``, or ``\\t``. Defaults to ``,`
        for unrecognized or ``None`` values.

    Examples:
        >>> parse_delimiter("comma")
        ','
        >>> parse_delimiter("semicolon")
        ';'
        >>> parse_delimiter("tab")
        '\\t'
    """
    if raw is None:
        return ","
    value = raw.lower().strip()
    if value == "comma":
        return ","
    if value == "semicolon":
        return ";"
    if value == "tab":
        return "\t"
    return ","


def parse_bool(raw: str | None) -> bool:
    """Parse a boolean value from a string.

    Args:
        raw: One of ``"true"``, ``"1"``, ``"yes"``, ``"false"``, ``"0"``,
            ``"no"`` (case-insensitive).

    Returns:
        ``True`` for truthy values, ``False`` otherwise.

    Examples:
        >>> parse_bool("true")
        True
        >>> parse_bool("0")
        False
    """
    if raw is None:
        return False
    value = raw.lower().strip()
    return value in ("true", "1", "yes")


__all__ = [
    "DEFAULT_COLUMNS",
    "STATUS_FAILED",
    "STATUS_PASSED",
    "STATUS_SKIPPED",
    "STATUS_UNDEFINED",
    "STATUS_UNTESTED",
    "format_duration",
    "generate_id",
    "monotonic_seconds",
    "normalize_status",
    "now_iso",
    "parse_bool",
    "parse_columns",
    "parse_delimiter",
    "safe_str",
    "safe_tags",
]
