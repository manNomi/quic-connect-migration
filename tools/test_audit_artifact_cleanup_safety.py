#!/usr/bin/env python3
"""Regression tests for artifact cleanup safety auditing."""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

from audit_artifact_cleanup_safety import DEFAULT_ARTIFACT_REFERENCE_CSVS, build_audit, classify_candidate
from draft_final_handover_result_row import CSV_FIELDS


def write_file(path: Path, content: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_experiments(path: Path, referenced_artifact: Path) -> None:
    row = {
        "trial_id": "referenced-trial-001",
        "date": "2026-06-24",
        "status": "PASS",
        "implementation": "test",
        "deployment_tier": "local",
        "protocol": "HTTP/3 over QUIC",
        "migration_trigger": "none",
        "path_validation_observed": "false",
        "tuple_change_observed": "false",
        "application_task": "test",
        "application_success": "true",
        "manual_intervention_required": "false",
        "failure_layer": "none",
        "artifact_dir": referenced_artifact.as_posix(),
        "notes": "test row",
    }
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerow(row)


def write_repetition_summary(path: Path, referenced_artifact: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["run_id", "artifact_dir"])
        writer.writeheader()
        writer.writerow({"run_id": "repetition-r1", "artifact_dir": referenced_artifact.as_posix()})


def test_classify_candidate_prefers_csv_reference() -> None:
    referenced, trials, planned, controlled, recommendation, _ = classify_candidate(
        "artifacts/controlled-public-chrome-h3-baseline-001",
        [],
        {"controlled-public-chrome-h3-baseline-001"},
    )
    assert referenced is False
    assert trials == []
    assert planned is True
    assert controlled is True
    assert recommendation == "keep-planned-final-trial"


def test_build_audit_marks_referenced_and_unreferenced() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artifacts = root / "artifacts"
        referenced = artifacts / "referenced-artifact"
        unreferenced = artifacts / "unreferenced-artifact"
        write_file(referenced / "result.txt")
        write_file(unreferenced / "result.txt")
        experiments = root / "experiments.csv"
        write_experiments(experiments, referenced)

        audit = build_audit(
            [artifacts.as_posix()],
            experiments,
            target_free_gib=0.01,
            repetitions=3,
            prefer_p1="safari",
        )
        by_name = {Path(item["path"]).name: item for item in audit["items"]}
        assert by_name["referenced-artifact"]["recommendation"] == "keep-referenced"
        assert by_name["referenced-artifact"]["referenced_trial_ids"] == ["referenced-trial-001"]
        assert by_name["unreferenced-artifact"]["recommendation"] == "review-unreferenced"
        assert audit["candidate_count"] == 2


def test_build_audit_keeps_extra_reference_csv_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artifacts = root / "artifacts"
        referenced = artifacts / "repetition-artifact"
        write_file(referenced / "result.txt")
        experiments = root / "experiments.csv"
        write_experiments(experiments, artifacts / "other-artifact")
        repetition_summary = root / "repetition.csv"
        write_repetition_summary(repetition_summary, referenced)

        audit = build_audit(
            [artifacts.as_posix()],
            experiments,
            target_free_gib=0.01,
            repetitions=3,
            prefer_p1="safari",
            extra_reference_csvs=[repetition_summary],
        )
        by_name = {Path(item["path"]).name: item for item in audit["items"]}
        assert by_name["repetition-artifact"]["recommendation"] == "keep-referenced"
        assert by_name["repetition-artifact"]["referenced_trial_ids"] == ["repetition-r1"]


def test_default_reference_csvs_include_timing_sensitivity_summary() -> None:
    assert "data/chrome-h3-rebinding-timing-sensitivity-20260624.csv" in DEFAULT_ARTIFACT_REFERENCE_CSVS


def test_default_reference_csvs_include_old_path_drop_summary() -> None:
    assert "data/chrome-h3-rebinding-old-path-drop-20260624.csv" in DEFAULT_ARTIFACT_REFERENCE_CSVS


def test_default_reference_csvs_include_old_path_drop_stress_summary() -> None:
    assert "data/chrome-h3-rebinding-old-path-drop-stress-20260624.csv" in DEFAULT_ARTIFACT_REFERENCE_CSVS


def test_default_reference_csvs_include_return_path_drop_controls_summary() -> None:
    assert "data/chrome-h3-rebinding-return-path-drop-controls-20260624.csv" in DEFAULT_ARTIFACT_REFERENCE_CSVS


def test_default_reference_csvs_include_transient_return_path_sweep_summary() -> None:
    assert "data/chrome-h3-rebinding-transient-return-path-sweep-20260624.csv" in DEFAULT_ARTIFACT_REFERENCE_CSVS


def main() -> int:
    test_classify_candidate_prefers_csv_reference()
    test_build_audit_marks_referenced_and_unreferenced()
    test_build_audit_keeps_extra_reference_csv_artifacts()
    test_default_reference_csvs_include_timing_sensitivity_summary()
    test_default_reference_csvs_include_old_path_drop_summary()
    test_default_reference_csvs_include_old_path_drop_stress_summary()
    test_default_reference_csvs_include_return_path_drop_controls_summary()
    test_default_reference_csvs_include_transient_return_path_sweep_summary()
    print("audit_artifact_cleanup_safety=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
