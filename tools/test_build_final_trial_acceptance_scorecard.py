#!/usr/bin/env python3
"""Regression tests for the final trial acceptance scorecard."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from build_final_trial_acceptance_scorecard import build_scorecard, emit_markdown, write_csv


def write_fixture(path: Path, text: str) -> None:
    path.write_text(dedent(text).lstrip(), encoding="utf-8")


def test_incomplete_active_requirement_is_not_claimable() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        requirements = root / "requirements.csv"
        experiments = root / "experiments.csv"
        write_fixture(
            requirements,
            """
            requirement_id,phase,browser,description,min_count,accepted_statuses,trial_id_contains_all,deployment_contains_all,trigger_contains_all,task_contains_all,notes_contains_all,notes_contains_any,notes_excludes_any
            chrome-downlink-noheartbeat-active-cm,active-network-change,Chrome,active,1,PASS,controlled-public;network-change;chrome;downlink;noheartbeat,controlled public,active;path;change,downlink,,possible_connection_migration,reconnect_or_multiple_sessions;tuple_changed_without_path_validation
            """,
        )
        write_fixture(
            experiments,
            """
            trial_id,date,status,implementation,deployment_tier,protocol,migration_trigger,path_validation_observed,tuple_change_observed,application_task,application_success,manual_intervention_required,failure_layer,artifact_dir,notes
            local-control,2026-06-24,PASS,quic-go,local,QUIC,AddPath,true,true,echo,true,false,none,artifacts/local,possible_connection_migration
            """,
        )
        scorecard = build_scorecard(requirements, experiments, "missing.env", False, 1, "safari")
        row = scorecard["rows"][0]
        assert scorecard["final_protocol_complete"] is False
        assert row["matched_count"] == 0
        assert row["paper_use"] == "pending; do not claim browser CM success"
        assert "reconnect_or_multiple_sessions" in row["reject_if"]


def test_complete_baseline_requirement_is_baseline_evidence() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        requirements = root / "requirements.csv"
        experiments = root / "experiments.csv"
        csv_output = root / "scorecard.csv"
        write_fixture(
            requirements,
            """
            requirement_id,phase,browser,description,min_count,accepted_statuses,trial_id_contains_all,deployment_contains_all,trigger_contains_all,task_contains_all,notes_contains_all,notes_contains_any,notes_excludes_any
            chrome-controlled-public-application-h3-baseline,baseline,Chrome,baseline,1,PASS,controlled-public;baseline,controlled public,,browser,,controlled_public_application_h3_confirmed,
            """,
        )
        write_fixture(
            experiments,
            """
            trial_id,date,status,implementation,deployment_tier,protocol,migration_trigger,path_validation_observed,tuple_change_observed,application_task,application_success,manual_intervention_required,failure_layer,artifact_dir,notes
            controlled-public-chrome-h3-baseline-001,2026-06-24,PASS,Chrome + controlled public quic-go H3,controlled public browser baseline,HTTP/3 over QUIC,controlled public application H3 baseline; no active path-change,false,false,GET /browser-slow plus streaming GET /slow-js,true,false,none,artifacts/baseline,controlled_public_application_h3_confirmed; controlled_public_server_qlog_h3_confirmed
            """,
        )
        scorecard = build_scorecard(requirements, experiments, "missing.env", False, 1, "safari")
        markdown = emit_markdown(scorecard)
        write_csv(scorecard, csv_output)
        row = scorecard["rows"][0]
        assert scorecard["final_protocol_complete"] is True
        assert row["paper_use"] == "baseline/control evidence available"
        assert "server result" in row["required_artifact_roles"]
        assert "PRIVATE_KEY" not in markdown
        assert csv_output.exists()


def main() -> int:
    test_incomplete_active_requirement_is_not_claimable()
    test_complete_baseline_requirement_is_baseline_evidence()
    print("build_final_trial_acceptance_scorecard=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
