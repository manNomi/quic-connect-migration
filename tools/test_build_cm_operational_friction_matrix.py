#!/usr/bin/env python3
"""Regression tests for the CM operational friction matrix builder."""

from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from build_cm_operational_friction_matrix import build_matrix, emit_markdown


def write_fixture(path: Path, text: str) -> None:
    path.write_text(dedent(text).lstrip(), encoding="utf-8")


def test_matrix_links_experiments_and_literature() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        rubric = root / "rubric.csv"
        experiments = root / "experiments.csv"
        literature = root / "literature.csv"
        write_fixture(
            rubric,
            """
            friction_id,layer,friction,why_it_discourages_or_blocks_cm,experiment_terms_any,literature_terms_any,repo_claim_scope,next_proof_needed,confidence
            cid-load-balancing,load-balancer,CID routing needed,5-tuple routing can break migration,aws-nlb;wrong-server-id,QUIC-LB;AWS NLB,Scoped LB claim,Repeat browser test,A
            """,
        )
        write_fixture(
            experiments,
            """
            trial_id,status,implementation,deployment_tier,migration_trigger,failure_layer,notes
            aws-nlb-quic-data-plane-001,PASS,quic-go,AWS NLB,AddPath,none,positive
            aws-nlb-quic-wrong-server-id-001,PASS_NEGATIVE_CONTROL,quic-go,AWS NLB,wrong cid,nlb-cid-server-id-mismatch,negative
            """,
        )
        write_fixture(
            literature,
            """
            grade,type,title,venue_or_status,relevance,next_action
            A,draft,QUIC-LB: Generating Routable QUIC Connection IDs,IETF,CID routing,Use
            A,cloud,AWS NLB QUIC protocol support,AWS,Server ID,Use
            """,
        )
        args = argparse.Namespace(
            rubric=rubric.as_posix(),
            experiments=experiments.as_posix(),
            literature=literature.as_posix(),
        )
        matrix = build_matrix(args)
        markdown = emit_markdown(matrix)
        row = matrix["rows"][0]
        assert row["experiment_match_count"] == 2
        assert row["literature_match_count"] == 2
        assert row["paper_use"] == "source-backed explanation with repo evidence"
        assert "AKIA" not in markdown
        assert "PRIVATE_KEY" not in markdown


def main() -> int:
    test_matrix_links_experiments_and_literature()
    print("build_cm_operational_friction_matrix=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
