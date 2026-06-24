#!/usr/bin/env python3
"""Regression tests for final handover artifact registration validation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from validate_final_handover_trial_artifact import build_validation


REQUIREMENTS = Path("data/final-browser-handover-required-trials.csv")


def write_summary(root: Path, summary: dict) -> Path:
    summary_path = root / "results" / "controlled-public-h3-network-change-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary_path


def base_summary(classification: str) -> dict:
    return {
        "status": "PASS" if classification == "possible_connection_migration" else "PASS_NEGATIVE_CONTROL",
        "classification": classification,
        "browser_kind": "chrome",
        "browser_completed_cleanly": True,
        "server_qlog_has_path_validation": classification
        in {"possible_connection_migration", "reconnect_or_multiple_sessions"},
        "server_requests": {
            "reached_expected_count": True,
            "remote_addr_count": 2,
            "request_workloads": ["browser-downlink", "downlink-stream"],
            "request_labels": ["public-downlink-noheartbeat", "public-downlink-noheartbeat-stream"],
        },
        "client_path_change": {"classification": "client_active_path_changed"},
    }


def validate_tmp(trial_id: str, summary: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / trial_id
        write_summary(root, summary)
        return build_validation(trial_id, root, REQUIREMENTS, "2026-06-24")


def test_positive_chrome_counts() -> None:
    result = validate_tmp(
        "controlled-public-chrome-downlink-noheartbeat-network-change-001",
        base_summary("possible_connection_migration"),
    )
    assert result["appendable_to_experiment_results"] is True
    assert result["counts_toward_final_protocol"] is True
    assert result["claim_strength"] == "counts_toward_final_protocol"
    assert result["matched_final_requirements"] == ["chrome-downlink-noheartbeat-active-cm"]


def test_reconnect_negative_control_does_not_count() -> None:
    result = validate_tmp(
        "controlled-public-chrome-downlink-noheartbeat-network-change-002",
        base_summary("reconnect_or_multiple_sessions"),
    )
    assert result["appendable_to_experiment_results"] is True
    assert result["counts_toward_final_protocol"] is False
    assert result["claim_strength"] == "negative_control_record_only"
    assert any("negative-control" in warning for warning in result["warnings"])
    assert any("reconnect_or_multiple_sessions" in warning for warning in result["warnings"])


def test_safari_feasibility_counts_as_p1_only() -> None:
    summary = base_summary("possible_connection_migration_server_qlog_only")
    summary["status"] = "PASS_FEASIBILITY"
    summary["browser_kind"] = "safari"
    summary["server_qlog_has_path_validation"] = True
    result = validate_tmp("controlled-public-safari-downlink-network-change-001", summary)
    assert result["appendable_to_experiment_results"] is True
    assert result["counts_toward_final_protocol"] is True
    assert result["claim_strength"] == "p1_feasibility_counts_toward_protocol"
    assert result["matched_final_requirements"] == ["p1-safari-or-android-feasibility"]
    assert any("feasibility" in warning for warning in result["warnings"])


def main() -> int:
    test_positive_chrome_counts()
    test_reconnect_negative_control_does_not_count()
    test_safari_feasibility_counts_as_p1_only()
    print("validate_final_handover_trial_artifact=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
