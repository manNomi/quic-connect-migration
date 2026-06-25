#!/usr/bin/env python3
"""Regression tests for the P0 baseline execution packet."""

from __future__ import annotations

import argparse
import contextlib
import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from build_p0_baseline_execution_packet import build_execution_packet, emit_markdown, write_csv, write_output


def write_fixture(path: Path, text: str) -> None:
    path.write_text(dedent(text).lstrip(), encoding="utf-8")


def write_placeholder_config(path: Path) -> None:
    write_fixture(
        path,
        """
        PUBLIC_ORIGIN_HOST=example.com
        PUBLIC_ORIGIN_PORT=443
        PUBLIC_ORIGIN_URL=https://example.com/
        TLS_CERT_FILE=example
        TLS_KEY_FILE=example
        LISTEN_ADDR=0.0.0.0:443
        TCP_ADDR=0.0.0.0:443
        ALT_SVC='h3=":443"; ma=60'
        CHROME_BIN=/bin/sh
        """,
    )


def make_args(root: Path) -> argparse.Namespace:
    matrix = root / "matrix.csv"
    scorecard = root / "scorecard.csv"
    experiments = root / "experiments.csv"
    requirements = root / "requirements.csv"
    config = root / "missing.env"
    write_fixture(
        matrix,
        """
        order,trial_id,requirement_id,phase,browser,heartbeat,ready,state,required_gates,missing_gates
        1,controlled-public-chrome-h3-baseline-001,chrome-controlled-public-application-h3-baseline,baseline,Chrome,n/a,False,blocked,controlled_public_config_present;public_origin_host_configured;public_origin_url_configured;tls_config_present;disk_ready,controlled_public_config_present;public_origin_host_configured;public_origin_url_configured;tls_config_present
        """,
    )
    write_fixture(
        scorecard,
        """
        requirement_id,complete
        chrome-controlled-public-application-h3-baseline,False
        """,
    )
    write_fixture(
        experiments,
        """
        trial_id,implementation,deployment_tier,protocol,migration_trigger,application_task,status,failure_layer,notes
        previous,quic-go,local,QUIC,none,echo,PASS,,ok
        """,
    )
    write_fixture(
        requirements,
        """
        requirement_id,phase,browser,description,min_count,accepted_statuses,trial_id_contains_all,deployment_contains_all,trigger_contains_all,task_contains_all,notes_contains_all,notes_contains_any,notes_excludes_any
        chrome-controlled-public-application-h3-baseline,baseline,Chrome,baseline,1,PASS,controlled-public;baseline,controlled public,,browser,,controlled_public_application_h3_confirmed,
        """,
    )
    return argparse.Namespace(
        matrix=matrix.as_posix(),
        scorecard=scorecard.as_posix(),
        experiments=experiments.as_posix(),
        requirements=requirements.as_posix(),
        config=config.as_posix(),
        repetitions=3,
        prefer_p1="safari",
        chrome_bin="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        safari_bin="/Applications/Safari.app/Contents/MacOS/Safari",
        safari_tp_bin="/Applications/Safari Technology Preview.app/Contents/MacOS/Safari Technology Preview",
        min_disk_gib=5.0,
        timeout=1.0,
    )


def test_execution_packet_orders_private_config_before_capture() -> None:
    with TemporaryDirectory() as tmp:
        execution = build_execution_packet(make_args(Path(tmp)))
        rows = execution["stage_rows"]
        assert execution["next_trial"]["trial_id"] == "controlled-public-chrome-h3-baseline-001"
        assert execution["next_trial_ready"] is False
        assert rows[0]["stage"] == "0-private-config"
        assert rows[0]["status"] == "blocked"
        assert rows[1]["stage"] == "1-preflight"
        assert rows[1]["command"] == "bash harness/scripts/final-p0-baseline-preflight.sh"
        assert rows[3]["stage"] == "3-browser-client"
        assert rows[3]["command"] == "bash harness/scripts/final-p0-baseline-run.sh"
        assert rows[4]["stage"] == "4-post-trial-registration"
        assert "final-handover-register-trial.sh" in rows[4]["command"]
        assert "APPLY=1" in rows[4]["command"]
        assert "controlled_public_config_present" in execution["needed_now_gates"]


def test_existing_placeholder_config_refines_stage_zero_needed_now_gates() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        args = make_args(root)
        write_placeholder_config(Path(args.config))
        execution = build_execution_packet(args)
        needed_now = set(execution["needed_now_gates"])

        assert execution["next_trial_ready"] is False
        assert "controlled_public_config_present" not in needed_now
        assert {
            "public_origin_host_configured",
            "public_origin_url_configured",
            "tls_config_present",
        }.issubset(needed_now)
        assert execution["stage_rows"][0]["status"] == "blocked"


def test_execution_packet_is_public_safe_and_writable() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        execution = build_execution_packet(make_args(root))
        output = root / "execution.csv"
        markdown = emit_markdown(execution)
        write_csv(execution, output)
        assert "P0 Baseline Execution Packet" in markdown
        assert "PRIVATE_KEY" not in markdown
        assert "AKIA" not in markdown
        assert output.exists()


def test_dash_outputs_print_stdout_without_dash_file() -> None:
    original_cwd = Path.cwd()
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        execution = build_execution_packet(make_args(root))
        try:
            os.chdir(root)
            markdown_buffer = io.StringIO()
            with contextlib.redirect_stdout(markdown_buffer):
                write_output(emit_markdown(execution), "-")
            assert markdown_buffer.getvalue().startswith("# P0 Baseline Execution Packet")

            csv_buffer = io.StringIO()
            with contextlib.redirect_stdout(csv_buffer):
                write_csv(execution, "-")
            assert csv_buffer.getvalue().startswith("stage,order,status")
            assert not Path("-").exists()
        finally:
            os.chdir(original_cwd)


def main() -> int:
    test_execution_packet_orders_private_config_before_capture()
    test_existing_placeholder_config_refines_stage_zero_needed_now_gates()
    test_execution_packet_is_public_safe_and_writable()
    test_dash_outputs_print_stdout_without_dash_file()
    print("build_p0_baseline_execution_packet=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
