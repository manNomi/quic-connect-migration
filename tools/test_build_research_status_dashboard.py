#!/usr/bin/env python3
"""Regression tests for the research status dashboard builder."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from build_research_status_dashboard import build_dashboard, emit_markdown, first_action_from_missing_gates
from research_clock import utc_date_iso


def write_fixture(path: Path, text: str) -> None:
    path.write_text(dedent(text).lstrip(), encoding="utf-8")


def test_first_action_prioritizes_config_before_later_gates() -> None:
    action = first_action_from_missing_gates(
        {
            "baseline_summary_ready": 7,
            "controlled_public_config_present": 10,
            "desktop_secondary_path_ready": 7,
        }
    )
    assert "init-controlled-public-config.sh" in action
    assert "controlled-public origin env file" in action


def test_dashboard_summarizes_public_safe_inputs() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        experiments = root / "experiment-results.csv"
        matrix = root / "matrix.csv"
        scorecard = root / "scorecard.csv"
        friction = root / "friction.csv"
        claim_support = root / "claim-support.csv"
        replication_audit = root / "replication-audit.csv"
        manifest = root / "manifest.json"
        write_fixture(
            experiments,
            """
            trial_id,status
            t1,PASS
            t2,PASS_NEGATIVE_CONTROL
            """,
        )
        write_fixture(
            matrix,
            """
            order,trial_id,requirement_id,phase,browser,heartbeat,ready,state,required_gates,missing_gates
            1,controlled-public-chrome-h3-baseline-001,chrome-controlled-public-application-h3-baseline,baseline,Chrome,n/a,False,blocked,controlled_public_config_present;disk_ready,controlled_public_config_present
            """,
        )
        write_fixture(
            scorecard,
            """
            requirement_id,paper_use
            chrome-controlled-public-application-h3-baseline,pending; required before active CM claim
            """,
        )
        write_fixture(
            friction,
            """
            friction_id,paper_use
            active-path-proof,source-backed explanation with repo evidence
            """,
        )
        write_fixture(
            claim_support,
            """
            claim_id,support_level
            c1,supported_scoped
            c2,not_supported_yet
            """,
        )
        write_fixture(
            replication_audit,
            """
            condition_id,evidence_role
            r1,stable_candidate
            r2,transition_zone
            """,
        )
        manifest.write_text(
            json.dumps(
                {
                    "verification": {"checks": "52", "passed": "52", "ok": "yes"},
                    "ci": {"available": "yes", "status": "completed", "conclusion": "success", "run_id": "1"},
                    "research_audit": {"final_browser_handover_trials": "0/6"},
                }
            ),
            encoding="utf-8",
        )
        args = argparse.Namespace(
            experiments=experiments.as_posix(),
            matrix=matrix.as_posix(),
            scorecard=scorecard.as_posix(),
            manifest=manifest.as_posix(),
            friction=friction.as_posix(),
            claim_support=claim_support.as_posix(),
            replication_audit=replication_audit.as_posix(),
            replication_run_plan=(root / "replication-run-plan.csv").as_posix(),
            p0_unblock=(root / "p0-unblock-status.csv").as_posix(),
            p0_baseline_execution_packet=(root / "p0-baseline-execution-packet.csv").as_posix(),
            p0_baseline_preflight=(root / "p0-baseline-preflight-check.csv").as_posix(),
            p0_baseline_preflight_controls=(root / "p0-baseline-preflight-control-report.csv").as_posix(),
            final_capture_storage_budget=(root / "final-capture-storage-budget.csv").as_posix(),
            aws_identity_readiness=(root / "aws-identity-readiness.json").as_posix(),
            artifact_cleanup_apply_report=(root / "artifact-cleanup-apply-report.md").as_posix(),
        )
        dashboard = build_dashboard(args)
        markdown = emit_markdown(dashboard)
        assert dashboard["experiment_trials"] == 2
        assert dashboard["planned_execution_state_counts"] == {"blocked": 1}
        assert dashboard["operational_friction_paper_use_counts"] == {"source-backed explanation with repo evidence": 1}
        assert dashboard["claim_support_counts"] == {"not_supported_yet": 1, "supported_scoped": 1}
        assert dashboard["replication_role_counts"] == {"stable_candidate": 1, "transition_zone": 1}
        assert dashboard["final_browser_handover"] == "0/6"
        assert "p0_baseline_preflight_controls" in dashboard["key_paths"]
        assert "final_capture_storage_budget" in dashboard["key_paths"]
        assert "aws_identity_readiness" in dashboard["key_paths"]
        assert "artifact_cleanup_apply_report" in dashboard["key_paths"]
        assert "PRIVATE_KEY" not in markdown
        assert "AKIA" not in markdown


def test_generated_date_uses_utc_day() -> None:
    assert utc_date_iso() == datetime.now(timezone.utc).date().isoformat()


def main() -> int:
    test_first_action_prioritizes_config_before_later_gates()
    test_dashboard_summarizes_public_safe_inputs()
    test_generated_date_uses_utc_day()
    print("build_research_status_dashboard=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
