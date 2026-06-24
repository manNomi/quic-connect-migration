#!/usr/bin/env python3
"""Regression tests for the P0 unblock status builder."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from build_p0_unblock_status import build_status, emit_markdown, write_csv


def write_fixture(path: Path, text: str) -> None:
    path.write_text(dedent(text).lstrip(), encoding="utf-8")


def test_next_trial_gates_are_needed_now() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        scorecard = root / "scorecard.csv"
        write_fixture(
            matrix,
            """
            order,trial_id,requirement_id,phase,browser,heartbeat,ready,state,required_gates,missing_gates
            1,controlled-public-chrome-h3-baseline-001,chrome-controlled-public-application-h3-baseline,baseline,Chrome,n/a,False,blocked,controlled_public_config_present;public_origin_url_configured;disk_ready,controlled_public_config_present;public_origin_url_configured
            2,controlled-public-chrome-downlink-network-change-001,chrome-downlink-noheartbeat-active-cm,active-network-change,Chrome,false,False,blocked,controlled_public_config_present;baseline_summary_ready;desktop_secondary_path_ready,controlled_public_config_present;baseline_summary_ready;desktop_secondary_path_ready
            """,
        )
        write_fixture(
            scorecard,
            """
            requirement_id,complete
            chrome-controlled-public-application-h3-baseline,False
            chrome-downlink-noheartbeat-active-cm,False
            """,
        )
        status = build_status(matrix, scorecard)
        rows = {row["unblock_item"]: row for row in status["rows"]}
        assert status["next_trial"]["trial_id"] == "controlled-public-chrome-h3-baseline-001"
        assert rows["controlled_public_config_present"]["status"] == "needed-now"
        assert rows["public_origin_url_configured"]["status"] == "needed-now"
        assert rows["baseline_summary_ready"]["status"] == "needed-after-baseline"
        assert rows["desktop_secondary_path_ready"]["blocks_next_trial"] == "no"


def test_status_is_public_safe_and_writable() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        scorecard = root / "scorecard.csv"
        output = root / "status.csv"
        write_fixture(
            matrix,
            """
            order,trial_id,requirement_id,phase,browser,heartbeat,ready,state,required_gates,missing_gates
            1,t1,r1,baseline,Chrome,n/a,False,blocked,tls_config_present,tls_config_present
            """,
        )
        write_fixture(
            scorecard,
            """
            requirement_id,complete
            r1,False
            """,
        )
        status = build_status(matrix, scorecard)
        markdown = emit_markdown(status)
        write_csv(status, output)
        assert "Never commit private keys" in markdown
        assert "PRIVATE_KEY" not in markdown
        assert "AKIA" not in markdown
        assert output.exists()


def main() -> int:
    test_next_trial_gates_are_needed_now()
    test_status_is_public_safe_and_writable()
    print("build_p0_unblock_status=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
