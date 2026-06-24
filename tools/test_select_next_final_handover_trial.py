#!/usr/bin/env python3
"""Regression tests for final handover next-trial selection."""

from __future__ import annotations

import argparse
import csv
import tempfile
from pathlib import Path

from draft_final_handover_result_row import CSV_FIELDS, build_row
from select_next_final_handover_trial import build_selection


REQUIREMENTS = "data/final-browser-handover-required-trials.csv"


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def args_for(experiments: Path) -> argparse.Namespace:
    return argparse.Namespace(
        experiments=experiments.as_posix(),
        requirements=REQUIREMENTS,
        config="harness/config/controlled-public-origin.env",
        use_local_config=False,
        repetitions=3,
        prefer_p1="safari",
    )


def baseline_row() -> dict[str, str]:
    return build_row(
        "controlled-public-chrome-h3-baseline-001",
        Path("repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001"),
        {
            "status": "PASS",
            "classification": "controlled_public_application_h3_confirmed",
            "server_qlog_has_path_validation": False,
            "server_requests": {"reached_expected_count": True, "remote_addr_count": 1},
        },
        "2026-06-24",
    )


def nochange_row(trial_id: str) -> dict[str, str]:
    heartbeat = "heartbeat" in trial_id and "noheartbeat" not in trial_id
    return build_row(
        trial_id,
        Path(f"repro/quic-go-min-repro/artifacts/{trial_id}"),
        {
            "status": "PASS",
            "classification": "controlled_public_server_qlog_h3_confirmed_browser_netlog_inconclusive",
            "browser_kind": "chrome",
            "server_qlog_has_path_validation": False,
            "server_requests": {
                "reached_expected_count": True,
                "remote_addr_count": 1,
                "request_workloads": ["browser-downlink", "downlink-stream"] + (["heartbeat"] if heartbeat else []),
                "request_labels": ["public-downlink-heartbeat" if heartbeat else "public-downlink-noheartbeat"],
            },
        },
        "2026-06-24",
    )


def active_row(trial_id: str) -> dict[str, str]:
    heartbeat = "heartbeat" in trial_id and "noheartbeat" not in trial_id
    return build_row(
        trial_id,
        Path(f"repro/quic-go-min-repro/artifacts/{trial_id}"),
        {
            "status": "PASS",
            "classification": "possible_connection_migration",
            "browser_kind": "chrome",
            "browser_completed_cleanly": True,
            "server_qlog_has_path_validation": True,
            "server_requests": {
                "reached_expected_count": True,
                "remote_addr_count": 2,
                "request_workloads": ["browser-downlink", "downlink-stream"] + (["heartbeat"] if heartbeat else []),
                "request_labels": ["public-downlink-heartbeat" if heartbeat else "public-downlink-noheartbeat"],
            },
            "client_path_change": {"classification": "client_active_path_changed"},
        },
        "2026-06-24",
    )


def select_with_rows(rows: list[dict[str, str]]) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        experiments = Path(tmp) / "experiments.csv"
        write_rows(experiments, rows)
        return build_selection(args_for(experiments))


def test_empty_selects_baseline() -> None:
    selection = select_with_rows([])
    assert selection["next_trial"]["trial_id"] == "controlled-public-chrome-h3-baseline-001"
    assert selection["next_trial_index"] == 1


def test_after_baseline_selects_nochange_first() -> None:
    selection = select_with_rows([baseline_row()])
    assert selection["next_trial"]["trial_id"] == "controlled-public-chrome-downlink-noheartbeat-nochange-001"
    assert selection["next_trial_index"] == 2


def test_after_baselines_selects_first_active_noheartbeat() -> None:
    selection = select_with_rows(
        [
            baseline_row(),
            nochange_row("controlled-public-chrome-downlink-noheartbeat-nochange-001"),
            nochange_row("controlled-public-chrome-downlink-heartbeat-nochange-001"),
        ]
    )
    assert selection["next_trial"]["trial_id"] == "controlled-public-chrome-downlink-noheartbeat-network-change-001"
    assert selection["next_trial_index"] == 4


def test_active_repetition_advances_by_trial_id() -> None:
    selection = select_with_rows(
        [
            baseline_row(),
            nochange_row("controlled-public-chrome-downlink-noheartbeat-nochange-001"),
            nochange_row("controlled-public-chrome-downlink-heartbeat-nochange-001"),
            active_row("controlled-public-chrome-downlink-noheartbeat-network-change-001"),
            active_row("controlled-public-chrome-downlink-noheartbeat-network-change-002"),
        ]
    )
    assert selection["next_trial"]["trial_id"] == "controlled-public-chrome-downlink-noheartbeat-network-change-003"
    assert selection["next_trial_index"] == 6


def main() -> int:
    test_empty_selects_baseline()
    test_after_baseline_selects_nochange_first()
    test_after_baselines_selects_first_active_noheartbeat()
    test_active_repetition_advances_by_trial_id()
    print("select_next_final_handover_trial=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
