"""Minimal environment for the example Behave project."""

from __future__ import annotations


def before_all(context: object) -> None:
    """Print a message before all tests start."""
    print("Starting example Behave test run...")


def after_all(context: object) -> None:
    """Print a message after all tests finish."""
    print("Example Behave test run complete.")
