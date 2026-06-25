#!/usr/bin/env python3
"""Regression tests for the P0 preflight synthetic control report."""

from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from build_p0_preflight_control_report import build_report, emit_markdown, write_csv, write_output


def test_control_report_passes_all_scenarios() -> None:
    report = build_report()
    rows = {row["scenario"]: row for row in report["rows"]}
    assert report["all_controls_passed"] is True
    assert rows["missing_config_blocks_capture"]["actual_go"] is False
    assert rows["synthetic_ready_allows_baseline_capture"]["actual_go"] is True
    assert rows["stale_needed_now_gate_blocks_capture"]["actual_go"] is False


def test_control_report_outputs_are_public_safe() -> None:
    report = build_report()
    markdown = emit_markdown(report)
    with TemporaryDirectory() as tmp:
        output = Path(tmp) / "controls.csv"
        write_csv(report, output)
        assert output.exists()
    assert "synthetic-h3.test" not in markdown
    assert "TLS_KEY_FILE" not in markdown
    assert "AKIA" not in markdown


def test_dash_outputs_print_stdout_without_dash_file() -> None:
    original_cwd = Path.cwd()
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        report = build_report()
        try:
            os.chdir(root)
            markdown_buffer = io.StringIO()
            with contextlib.redirect_stdout(markdown_buffer):
                write_output(emit_markdown(report), "-")
            assert markdown_buffer.getvalue().startswith("# P0 Baseline Preflight Control Report")

            csv_buffer = io.StringIO()
            with contextlib.redirect_stdout(csv_buffer):
                write_csv(report, "-")
            assert csv_buffer.getvalue().startswith("scenario,expected_go,actual_go")
            assert not Path("-").exists()
        finally:
            os.chdir(original_cwd)


def main() -> int:
    test_control_report_passes_all_scenarios()
    test_control_report_outputs_are_public_safe()
    test_dash_outputs_print_stdout_without_dash_file()
    print("build_p0_preflight_control_report=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
