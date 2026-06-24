#!/usr/bin/env python3
"""Regression tests for final handover result row drafting."""

from __future__ import annotations

import csv
from pathlib import Path

from audit_final_browser_handover_trials import load_rows, row_matches
from draft_final_handover_result_row import CSV_FIELDS, build_row, emit_csv


REQUIREMENTS = load_rows(Path("data/final-browser-handover-required-trials.csv"))


def requirement(requirement_id: str) -> dict[str, str]:
    for item in REQUIREMENTS:
        if item["requirement_id"] == requirement_id:
            return item
    raise AssertionError(f"missing requirement: {requirement_id}")


def base_network_summary(classification: str = "possible_connection_migration") -> dict:
    return {
        "status": "PASS",
        "classification": classification,
        "browser_kind": "chrome",
        "browser_completed_cleanly": True,
        "server_qlog_has_path_validation": classification == "possible_connection_migration",
        "server_requests": {
            "reached_expected_count": True,
            "remote_addr_count": 2,
            "request_workloads": ["browser-downlink", "downlink-stream"],
            "request_labels": ["public-downlink-noheartbeat", "public-downlink-noheartbeat-stream"],
        },
        "client_path_change": {"classification": "client_active_path_changed"},
    }


def assert_csv_roundtrip(row: dict[str, str]) -> None:
    parsed = list(csv.DictReader(emit_csv(row).splitlines()))
    assert len(parsed) == 1
    assert list(parsed[0].keys()) == CSV_FIELDS
    assert parsed[0] == row


def test_chrome_active_positive_matches_final_requirement() -> None:
    row = build_row(
        "controlled-public-chrome-downlink-noheartbeat-network-change-001",
        Path("repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001"),
        base_network_summary(),
        "2026-06-24",
    )
    assert row["status"] == "PASS"
    assert row["failure_layer"] == "none"
    assert row_matches(requirement("chrome-downlink-noheartbeat-active-cm"), row)
    assert_csv_roundtrip(row)


def test_chrome_reconnect_is_negative_control_not_counted_as_cm() -> None:
    summary = base_network_summary("reconnect_or_multiple_sessions")
    summary["status"] = "PASS_NEGATIVE_CONTROL"
    summary["server_qlog_has_path_validation"] = True
    row = build_row(
        "controlled-public-chrome-downlink-noheartbeat-network-change-002",
        Path("repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-002"),
        summary,
        "2026-06-24",
    )
    assert row["status"] == "PASS_NEGATIVE_CONTROL"
    assert not row_matches(requirement("chrome-downlink-noheartbeat-active-cm"), row)


def test_chrome_heartbeat_nochange_matches_baseline_requirement() -> None:
    summary = {
        "status": "PASS",
        "classification": "controlled_public_server_qlog_h3_confirmed_browser_netlog_inconclusive",
        "browser_kind": "chrome",
        "server_qlog_has_path_validation": False,
        "server_requests": {
            "reached_expected_count": True,
            "remote_addr_count": 2,
            "request_workloads": ["browser-downlink", "downlink-stream", "heartbeat"],
            "request_labels": ["public-downlink-heartbeat", "public-downlink-heartbeat-stream", "heartbeat"],
        },
    }
    row = build_row(
        "controlled-public-chrome-downlink-heartbeat-nochange-001",
        Path("repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001"),
        summary,
        "2026-06-24",
    )
    assert row["status"] == "PASS"
    assert "no_path_change_baseline" in row["notes"]
    assert row_matches(requirement("chrome-downlink-heartbeat-nochange-baseline"), row)


def test_safari_server_qlog_only_matches_p1_feasibility() -> None:
    summary = base_network_summary("possible_connection_migration_server_qlog_only")
    summary["status"] = "PASS_FEASIBILITY"
    summary["browser_kind"] = "safari"
    summary["server_qlog_has_path_validation"] = True
    row = build_row(
        "controlled-public-safari-downlink-network-change-001",
        Path("repro/quic-go-min-repro/artifacts/controlled-public-safari-downlink-network-change-001"),
        summary,
        "2026-06-24",
    )
    assert row["status"] == "PASS_FEASIBILITY"
    assert row["failure_layer"] == "server-qlog-only"
    assert row_matches(requirement("p1-safari-or-android-feasibility"), row)


def test_baseline_matches_application_h3_requirement() -> None:
    summary = {
        "status": "PASS",
        "classification": "controlled_public_application_h3_confirmed",
        "server_qlog_has_path_validation": False,
        "server_requests": {
            "reached_expected_count": True,
            "remote_addr_count": 1,
            "request_workloads": ["browser-slow", "slow-js"],
            "request_labels": ["public-slow", "public-slow-js"],
        },
    }
    row = build_row(
        "controlled-public-chrome-h3-baseline-001",
        Path("repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001"),
        summary,
        "2026-06-24",
    )
    assert row["status"] == "PASS"
    assert row_matches(requirement("chrome-controlled-public-application-h3-baseline"), row)


def main() -> int:
    test_chrome_active_positive_matches_final_requirement()
    test_chrome_reconnect_is_negative_control_not_counted_as_cm()
    test_chrome_heartbeat_nochange_matches_baseline_requirement()
    test_safari_server_qlog_only_matches_p1_feasibility()
    test_baseline_matches_application_h3_requirement()
    print("draft_final_handover_result_row=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
