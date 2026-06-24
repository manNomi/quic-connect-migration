#!/usr/bin/env python3
"""Regression tests for appending validated final handover result rows."""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

from append_final_handover_result_row import build_append_result
from draft_final_handover_result_row import CSV_FIELDS


REQUIREMENTS = Path("data/final-browser-handover-required-trials.csv")


def write_summary(root: Path, classification: str) -> None:
    status = "PASS" if classification == "possible_connection_migration" else "PASS_NEGATIVE_CONTROL"
    summary = {
        "status": status,
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
    summary_path = root / "results" / "controlled-public-h3-network-change-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def write_active_chrome_bundle(root: Path, classification: str = "possible_connection_migration") -> None:
    write_summary(root, classification)
    (root / "results" / "server.json").write_text('{"ok": true}\n', encoding="utf-8")
    (root / "qlog").mkdir(parents=True, exist_ok=True)
    (root / "qlog" / "trace.qlog").write_text('{"name":"path_challenge"}\n', encoding="utf-8")
    (root / "results" / "public-origin-readiness.json").write_text('{"ok": true}\n', encoding="utf-8")
    (root / "results" / "network-change.json").write_text('{"command_present": true, "exit": 0}\n', encoding="utf-8")
    (root / "results" / "client-path-change-summary.json").write_text(
        '{"classification":"client_active_path_changed","active_path_changed":true}\n',
        encoding="utf-8",
    )
    (root / "chrome").mkdir(parents=True, exist_ok=True)
    (root / "chrome" / "network-change-netlog.json").write_text('{"events":[]}\n', encoding="utf-8")


def write_empty_experiments(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS)
        writer.writeheader()


def row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as fp:
        return len(list(csv.DictReader(fp)))


def test_dry_run_does_not_append() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artifact = root / "artifact"
        experiments = root / "experiments.csv"
        write_summary(artifact, "possible_connection_migration")
        write_empty_experiments(experiments)
        result = build_append_result(
            "controlled-public-chrome-downlink-noheartbeat-network-change-001",
            artifact,
            experiments,
            REQUIREMENTS,
            "2026-06-24",
            None,
            True,
            False,
            False,
        )
        assert result.appended is False
        assert result.counts_toward_final_protocol is True
        assert row_count(experiments) == 0


def test_apply_appends_positive_once() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artifact = root / "artifact"
        experiments = root / "experiments.csv"
        write_summary(artifact, "possible_connection_migration")
        write_empty_experiments(experiments)
        result = build_append_result(
            "controlled-public-chrome-downlink-noheartbeat-network-change-001",
            artifact,
            experiments,
            REQUIREMENTS,
            "2026-06-24",
            None,
            True,
            False,
            True,
        )
        assert result.appended is True
        assert row_count(experiments) == 1


def test_duplicate_is_not_appended() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artifact = root / "artifact"
        experiments = root / "experiments.csv"
        write_summary(artifact, "possible_connection_migration")
        write_empty_experiments(experiments)
        trial_id = "controlled-public-chrome-downlink-noheartbeat-network-change-001"
        first = build_append_result(trial_id, artifact, experiments, REQUIREMENTS, "2026-06-24", None, True, False, True)
        second = build_append_result(trial_id, artifact, experiments, REQUIREMENTS, "2026-06-24", None, True, False, True)
        assert first.appended is True
        assert second.appended is False
        assert second.duplicate_trial_id is True
        assert row_count(experiments) == 1


def test_require_final_countable_blocks_negative_control_apply() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artifact = root / "artifact"
        experiments = root / "experiments.csv"
        write_summary(artifact, "reconnect_or_multiple_sessions")
        write_empty_experiments(experiments)
        result = build_append_result(
            "controlled-public-chrome-downlink-noheartbeat-network-change-001",
            artifact,
            experiments,
            REQUIREMENTS,
            "2026-06-24",
            None,
            True,
            False,
            True,
        )
        assert result.appended is False
        assert result.counts_toward_final_protocol is False
        assert row_count(experiments) == 0


def test_require_artifact_bundle_blocks_summary_only_apply() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artifact = root / "artifact"
        experiments = root / "experiments.csv"
        write_summary(artifact, "possible_connection_migration")
        write_empty_experiments(experiments)
        result = build_append_result(
            "controlled-public-chrome-downlink-noheartbeat-network-change-001",
            artifact,
            experiments,
            REQUIREMENTS,
            "2026-06-24",
            None,
            True,
            True,
            True,
        )
        assert result.appended is False
        assert result.artifact_bundle_complete is False
        assert result.artifact_bundle_blockers
        assert row_count(experiments) == 0


def test_require_artifact_bundle_allows_complete_bundle_apply() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artifact = root / "artifact"
        experiments = root / "experiments.csv"
        write_active_chrome_bundle(artifact)
        write_empty_experiments(experiments)
        result = build_append_result(
            "controlled-public-chrome-downlink-noheartbeat-network-change-001",
            artifact,
            experiments,
            REQUIREMENTS,
            "2026-06-24",
            None,
            True,
            True,
            True,
        )
        assert result.appended is True
        assert result.artifact_bundle_complete is True
        assert row_count(experiments) == 1


def main() -> int:
    test_dry_run_does_not_append()
    test_apply_appends_positive_once()
    test_duplicate_is_not_appended()
    test_require_final_countable_blocks_negative_control_apply()
    test_require_artifact_bundle_blocks_summary_only_apply()
    test_require_artifact_bundle_allows_complete_bundle_apply()
    print("append_final_handover_result_row=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
