#!/usr/bin/env python3
"""Regression tests for final handover external input handoff packets."""

from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from build_final_handover_external_inputs import build_items, emit_markdown, write_output


def fake_worksheet(baseline_ready: bool = False) -> dict:
    return {
        "baseline_config_ready": baseline_ready,
        "active_network_change_config_ready": False,
        "android_network_change_config_ready": False,
        "baseline_missing": [] if baseline_ready else ["PUBLIC_ORIGIN_HOST", "TLS_CERT_FILE"],
        "active_missing": ["NETWORK_CHANGE_CMD"],
        "android_missing": ["ANDROID_NETWORK_CHANGE_CMD"],
    }


def fake_checklist(storage_ready: bool = False) -> dict:
    return {
        "next_trial": {"trial_id": "controlled-public-chrome-h3-baseline-001"},
        "next_trial_ready": False,
        "storage": {
            "current_free_human": "2.2 GiB",
            "target_free_gib": 5.0,
            "target_met_by_selected": storage_ready,
            "remaining_gap_human": "1.9 GiB",
        },
        "final_trials": {
            "complete": False,
            "complete_count": 0,
            "requirement_count": 6,
        },
    }


def fake_handover() -> dict:
    return {
        "secondary_path_ready": False,
        "android_ready": False,
        "aws_identity_ok": False,
        "disk_available_gib": 2.2,
    }


def by_id(items: list) -> dict:
    return {item.id: item for item in items}


def test_now_inputs_are_marked_needed() -> None:
    items = by_id(build_items(fake_worksheet(), fake_checklist(), fake_handover()))
    assert items["disk-free-space"].urgency == "now"
    assert items["disk-free-space"].status == "needed"
    assert items["controlled-public-baseline-config"].status == "needed"
    assert "PUBLIC_ORIGIN_HOST" in items["controlled-public-baseline-config"].evidence
    assert items["active-network-change-path"].status == "needed-after-baseline"


def test_ready_now_inputs_do_not_leak_private_values() -> None:
    items = build_items(fake_worksheet(baseline_ready=True), fake_checklist(storage_ready=True), fake_handover())
    handoff = {
        "check_date": "2026-06-24",
        "public_safe": True,
        "next_trial": {"trial_id": "controlled-public-chrome-h3-baseline-001"},
        "next_trial_ready": False,
        "can_codex_run_next_trial_now": False,
        "needed_now_count": 0,
        "items": [item.__dict__ for item in items],
    }
    markdown = emit_markdown(handoff)
    assert "`disk-free-space`" in markdown
    assert "PRIVATE_KEY" not in markdown
    assert "AWS_SECRET" not in markdown


def test_dash_output_prints_stdout_without_dash_file() -> None:
    original_cwd = Path.cwd()
    with TemporaryDirectory() as tmp:
        try:
            os.chdir(tmp)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                write_output("handoff\n", "-")
            assert buffer.getvalue() == "handoff\n"
            assert not Path("-").exists()
        finally:
            os.chdir(original_cwd)


def main() -> int:
    test_now_inputs_are_marked_needed()
    test_ready_now_inputs_do_not_leak_private_values()
    test_dash_output_prints_stdout_without_dash_file()
    print("build_final_handover_external_inputs=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
