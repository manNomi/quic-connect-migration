#!/usr/bin/env python3
"""Regression tests for the paper evidence gap register builder."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from build_paper_evidence_gap_register import build_register, emit_markdown, write_csv


def write_fixture(path: Path, text: str) -> None:
    path.write_text(dedent(text).lstrip(), encoding="utf-8")


def test_pending_publishable_claim_links_all_incomplete_requirements() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        rubric = root / "rubric.csv"
        requirements = root / "requirements.csv"
        experiments = root / "experiments.csv"
        write_fixture(
            rubric,
            """
            claim,evidence_item,minimum_required,source_or_basis,current_repo_status,notes
            Claim is publishable as browser CM evidence,combined evidence chain,all evidence,current research rubric,pending,needs final rows
            """,
        )
        write_fixture(
            requirements,
            """
            requirement_id,phase,browser,description,min_count,accepted_statuses,trial_id_contains_all,deployment_contains_all,trigger_contains_all,task_contains_all,notes_contains_all,notes_contains_any,notes_excludes_any
            chrome-controlled-public-application-h3-baseline,baseline,Chrome,baseline,1,PASS,controlled-public;baseline,controlled public,,browser,,controlled_public_application_h3_confirmed,
            chrome-downlink-noheartbeat-active-cm,active-network-change,Chrome,active,1,PASS,controlled-public;network-change;chrome,controlled public,active;path;change,downlink,,possible_connection_migration,reconnect_or_multiple_sessions
            """,
        )
        write_fixture(
            experiments,
            """
            trial_id,implementation,deployment_tier,protocol,migration_trigger,application_task,status,failure_layer,notes
            quic-go-local-positive,quic-go,local,QUIC,AddPath,echo,PASS,,possible_connection_migration
            """,
        )
        register = build_register(rubric, requirements, experiments)
        row = register["rows"][0]
        assert register["final_protocol_complete"] is False
        assert row["paper_use_now"] == "do not claim yet"
        assert "chrome-controlled-public-application-h3-baseline" in row["blocking_requirement_ids"]
        assert "chrome-downlink-noheartbeat-active-cm" in row["blocking_requirement_ids"]


def test_supported_claim_is_public_safe_and_csv_writable() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        rubric = root / "rubric.csv"
        requirements = root / "requirements.csv"
        experiments = root / "experiments.csv"
        csv_output = root / "gap.csv"
        write_fixture(
            rubric,
            """
            claim,evidence_item,minimum_required,source_or_basis,current_repo_status,notes
            Deployment path supports CM,routing continuity,CID-aware route,AWS NLB,observed,scoped AWS result
            """,
        )
        write_fixture(
            requirements,
            """
            requirement_id,phase,browser,description,min_count,accepted_statuses,trial_id_contains_all,deployment_contains_all,trigger_contains_all,task_contains_all,notes_contains_all,notes_contains_any,notes_excludes_any
            chrome-controlled-public-application-h3-baseline,baseline,Chrome,baseline,0,PASS,controlled-public;baseline,controlled public,,browser,,controlled_public_application_h3_confirmed,
            """,
        )
        write_fixture(
            experiments,
            """
            trial_id,implementation,deployment_tier,protocol,migration_trigger,application_task,status,failure_layer,notes
            nlb-cid-positive,s2n-quic,AWS NLB,QUIC,tuple change,echo,PASS,,cid-aware-route
            """,
        )
        register = build_register(rubric, requirements, experiments)
        markdown = emit_markdown(register)
        write_csv(register, csv_output)
        assert register["rows"][0]["paper_use_now"] == "scoped claim supported"
        assert "PRIVATE_KEY" not in markdown
        assert "AWS_SECRET" not in markdown
        assert csv_output.exists()


def main() -> int:
    test_pending_publishable_claim_links_all_incomplete_requirements()
    test_supported_claim_is_public_safe_and_csv_writable()
    print("build_paper_evidence_gap_register=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
