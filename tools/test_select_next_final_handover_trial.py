#!/usr/bin/env python3
"""Regression tests for final handover next-trial selection."""

from __future__ import annotations

import argparse
import csv
import contextlib
import io
import os
import tempfile
from pathlib import Path

from draft_final_handover_result_row import CSV_FIELDS, build_row
from select_next_final_handover_trial import build_selection, write_output


REQUIREMENTS = "data/final-browser-handover-required-trials.csv"


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def args_for(
    experiments: Path,
    config: Path | None = None,
    use_local_config: bool = False,
    redact_sensitive: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        experiments=experiments.as_posix(),
        requirements=REQUIREMENTS,
        config=(config.as_posix() if config else "harness/config/controlled-public-origin.env"),
        use_local_config=use_local_config,
        repetitions=3,
        prefer_p1="safari",
        redact_sensitive=redact_sensitive,
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


def write_private_config(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "PUBLIC_ORIGIN_HOST=h3.private-lab.test",
                "PUBLIC_ORIGIN_PORT=443",
                "PUBLIC_ORIGIN_URL=https://h3.private-lab.test/browser-slow",
                "TLS_CERT_FILE=/private/lab/fullchain.pem",
                "TLS_KEY_FILE=/private/lab/privkey.pem",
                "LISTEN_ADDR=0.0.0.0:443",
                "TCP_ADDR=0.0.0.0:443",
                "ALT_SVC='h3=\":443\"; ma=60'",
                "NETWORK_CHANGE_CMD='printf path-change'",
                "ANDROID_NETWORK_CHANGE_CMD='printf android-path-change'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


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


def test_redacted_local_config_selection_does_not_leak_private_commands() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        experiments = tmp_path / "experiments.csv"
        config = tmp_path / "controlled-public-origin.env"
        write_rows(
            experiments,
            [
                baseline_row(),
                nochange_row("controlled-public-chrome-downlink-noheartbeat-nochange-001"),
                nochange_row("controlled-public-chrome-downlink-heartbeat-nochange-001"),
            ],
        )
        write_private_config(config)

        selection = build_selection(args_for(experiments, config, use_local_config=True, redact_sensitive=True))

    next_trial = selection["next_trial"]
    combined = f"{next_trial['server_command']}\n{next_trial['client_command']}"
    assert selection["public_safe_default"] is True
    assert selection["redact_sensitive"] is True
    assert next_trial["trial_id"] == "controlled-public-chrome-downlink-noheartbeat-network-change-001"
    assert "h3.private-lab.test" not in combined
    assert "/private/lab" not in combined
    assert "printf path-change" not in combined
    assert "<redacted-public-origin-host>" in combined
    assert "<redacted-network-change-cmd>" in combined


def test_dash_output_prints_stdout_without_dash_file() -> None:
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        try:
            os.chdir(tmp)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                write_output("hello\n", "-")
            assert buffer.getvalue() == "hello\n"
            assert not Path("-").exists()
        finally:
            os.chdir(original_cwd)


def main() -> int:
    test_empty_selects_baseline()
    test_after_baseline_selects_nochange_first()
    test_after_baselines_selects_first_active_noheartbeat()
    test_active_repetition_advances_by_trial_id()
    test_redacted_local_config_selection_does_not_leak_private_commands()
    test_dash_output_prints_stdout_without_dash_file()
    print("select_next_final_handover_trial=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
