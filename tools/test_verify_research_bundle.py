#!/usr/bin/env python3
"""Regression tests for the research bundle verifier."""

from __future__ import annotations

import sys

from verify_research_bundle import run_check


def test_run_check_forces_utc_timezone_for_children() -> None:
    result = run_check(
        "child_timezone",
        [sys.executable, "-c", "import os; print(os.environ.get('TZ', ''))"],
        {0},
        10,
    )
    assert result.ok is True
    assert result.stdout_tail == "UTC"


def main() -> int:
    test_run_check_forces_utc_timezone_for_children()
    print("verify_research_bundle=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
