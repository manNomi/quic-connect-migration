#!/usr/bin/env python3
"""Regression tests for controlled-public baseline unlock checks."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from check_controlled_public_baseline_unlock import build_unlock_report


REQUIREMENTS = Path("data/final-browser-handover-required-trials.csv")
TRIAL_ID = "controlled-public-chrome-h3-baseline-001"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_minimal_bundle(
    root: Path,
    *,
    status: str = "PASS",
    classification: str = "controlled_public_application_h3_confirmed",
) -> None:
    write_json(root / "results" / "server.json", {"ok": True, "requests": [{"remote_addr": "127.0.0.1:1"}]})
    write_json(root / "results" / "public-origin-readiness.json", {"ok": True, "has_h3_alt_svc": True})
    write_json(root / "results" / "chrome-public-h3-summary.json", {"status": "PASS", "any_h3_observed": True})
    write_json(
        root / "results" / "controlled-public-h3-baseline-summary.json",
        {
            "status": status,
            "classification": classification,
            "server_qlog_has_application_h3": True,
            "server_qlog_has_path_validation": False,
            "server_requests": {
                "reached_expected_count": True,
                "remote_addr_count": 1,
                "request_labels": ["public-slow"],
                "request_workloads": ["browser-slow"],
            },
        },
    )
    write_json(root / "chrome" / "bootstrap-netlog.json", {"events": []})
    write_json(root / "chrome" / "second-netlog.json", {"events": []})
    (root / "qlog").mkdir(parents=True, exist_ok=True)
    (root / "qlog" / "trace.sqlog").write_text("{}\n", encoding="utf-8")


def test_pass_baseline_unlocks_active_trials() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp) / TRIAL_ID
        write_minimal_bundle(root)
        report = build_unlock_report(TRIAL_ID, root, REQUIREMENTS)
        assert report["baseline_summary_pass"] is True
        assert report["counts_toward_final_protocol"] is True
        assert report["artifact_bundle_complete"] is True
        assert report["unlocks_active_trials"] is True
        assert report["blockers"] == []


def test_negative_baseline_does_not_unlock() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp) / TRIAL_ID
        write_minimal_bundle(
            root,
            status="PASS_NEGATIVE_CONTROL",
            classification="controlled_public_application_h3_not_confirmed",
        )
        report = build_unlock_report(TRIAL_ID, root, REQUIREMENTS)
        assert report["baseline_summary_pass"] is False
        assert report["counts_toward_final_protocol"] is False
        assert report["artifact_bundle_complete"] is True
        assert report["unlocks_active_trials"] is False
        assert any("not an unlocking PASS classification" in blocker for blocker in report["blockers"])


def test_incomplete_bundle_does_not_unlock() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp) / TRIAL_ID
        write_minimal_bundle(root)
        (root / "chrome" / "second-netlog.json").unlink()
        report = build_unlock_report(TRIAL_ID, root, REQUIREMENTS)
        assert report["baseline_summary_pass"] is True
        assert report["counts_toward_final_protocol"] is True
        assert report["artifact_bundle_complete"] is False
        assert report["unlocks_active_trials"] is False
        assert any("missing artifact" in blocker for blocker in report["blockers"])


def test_missing_baseline_report_is_public_safe_and_blocked() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp) / TRIAL_ID
        report = build_unlock_report(TRIAL_ID, root, REQUIREMENTS)
        assert report["public_safe"] is True
        assert report["baseline_summary_pass"] is False
        assert report["counts_toward_final_protocol"] is False
        assert report["artifact_bundle_complete"] is False
        assert report["unlocks_active_trials"] is False
        assert report["claim_strength"] == "summary_missing"
        assert any("missing artifact" in blocker for blocker in report["blockers"])


def main() -> int:
    test_pass_baseline_unlocks_active_trials()
    test_negative_baseline_does_not_unlock()
    test_incomplete_bundle_does_not_unlock()
    test_missing_baseline_report_is_public_safe_and_blocked()
    print("check_controlled_public_baseline_unlock=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
