#!/usr/bin/env python3
"""Regression tests for the research bundle verifier."""

from __future__ import annotations

import sys
from pathlib import Path

from verify_research_bundle import default_checks, run_check


def test_run_check_forces_utc_timezone_for_children() -> None:
    result = run_check(
        "child_timezone",
        [sys.executable, "-c", "import os; print(os.environ.get('TZ', ''))"],
        {0},
        10,
    )
    assert result.ok is True
    assert result.stdout_tail == "UTC"


def test_scratch_artifact_bundle_negative_check_uses_generated_output() -> None:
    generated_dir = Path("/tmp/verify-scratch")
    checks = default_checks(sys.executable, generated_dir)
    item = next(
        check
        for check in checks
        if check[0] == "final_handover_trial_artifact_bundle_require_complete_expected_incomplete"
    )
    command = item[1]
    assert "--output" in command
    assert str(generated_dir / "final-handover-trial-artifact-bundle-check.md") in command


def main() -> int:
    test_run_check_forces_utc_timezone_for_children()
    test_scratch_artifact_bundle_negative_check_uses_generated_output()
    print("verify_research_bundle=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
