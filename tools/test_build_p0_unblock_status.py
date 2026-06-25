#!/usr/bin/env python3
"""Regression tests for the P0 unblock status builder."""

from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from build_p0_unblock_status import build_status, emit_markdown, write_csv, write_output


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


def test_local_readiness_overlay_refines_next_trial_blockers() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        scorecard = root / "scorecard.csv"
        write_fixture(
            matrix,
            """
            order,trial_id,requirement_id,phase,browser,heartbeat,ready,state,required_gates,missing_gates
            1,controlled-public-chrome-h3-baseline-001,chrome-controlled-public-application-h3-baseline,baseline,Chrome,n/a,False,blocked,controlled_public_config_present;public_origin_host_configured;public_origin_url_configured;tls_config_present,controlled_public_config_present;public_origin_host_configured;public_origin_url_configured;tls_config_present
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
        local_readiness = {
            "ready": False,
            "config_path": "harness/config/controlled-public-origin.env",
            "config_exists": True,
            "next_trial": {"trial_id": "controlled-public-chrome-h3-baseline-001"},
            "required_gates": [
                "controlled_public_config_present",
                "public_origin_host_configured",
                "public_origin_url_configured",
                "tls_config_present",
            ],
            "missing_required_gates": ["public_origin_host_configured", "tls_config_present"],
            "disk": {"free_gib": 9.2},
        }
        status = build_status(matrix, scorecard, local_readiness=local_readiness)
        rows = {row["unblock_item"]: row for row in status["rows"]}
        markdown = emit_markdown(status)

        assert status["local_readiness"]["overlay_applied"] is True
        assert rows["controlled_public_config_present"]["status"] == "ready-for-next-trial"
        assert rows["controlled_public_config_present"]["blocks_next_trial"] == "no"
        assert rows["public_origin_url_configured"]["status"] == "ready-for-next-trial"
        assert rows["public_origin_url_configured"]["blocks_next_trial"] == "no"
        assert rows["public_origin_host_configured"]["status"] == "needed-now"
        assert rows["tls_config_present"]["status"] == "needed-now"
        assert "local next-trial overlay | `applied`" in markdown
        assert "`public_origin_host_configured`, `tls_config_present`" in markdown


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


def test_dash_outputs_print_stdout_without_dash_file() -> None:
    original_cwd = Path.cwd()
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        scorecard = root / "scorecard.csv"
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
        try:
            os.chdir(root)
            markdown_buffer = io.StringIO()
            with contextlib.redirect_stdout(markdown_buffer):
                write_output(emit_markdown(status), "-")
            assert markdown_buffer.getvalue().startswith("# P0 Unblock Status")

            csv_buffer = io.StringIO()
            with contextlib.redirect_stdout(csv_buffer):
                write_csv(status, "-")
            assert csv_buffer.getvalue().startswith("order,unblock_item,status")
            assert not Path("-").exists()
        finally:
            os.chdir(original_cwd)


def main() -> int:
    test_next_trial_gates_are_needed_now()
    test_local_readiness_overlay_refines_next_trial_blockers()
    test_status_is_public_safe_and_writable()
    test_dash_outputs_print_stdout_without_dash_file()
    print("build_p0_unblock_status=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
