#!/usr/bin/env python3
"""Regression tests for the ngtcp2 runtime trial packet builder."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_ngtcp2_runtime_trial_packet import build_packet, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def make_test_log(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "Running test suite with seed 0xabc...",
                "/pkt/test_ngtcp2_pkt_encode_path_challenge_frame[ OK    ]",
                "/pkt/test_ngtcp2_pkt_encode_path_response_frame[ OK    ]",
                "/conn/test_ngtcp2_conn_client_connection_migration[ OK    ]",
                "/conn/test_ngtcp2_conn_recv_path_challenge[ OK    ]",
                "/conn/test_ngtcp2_conn_disable_active_migration[ OK    ]",
                "/conn/test_ngtcp2_conn_path_validation[ OK    ]",
                "6 of 6 (100%) tests successful, 0 (0%) test skipped.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_packet_classifies_missing_runner_env_without_overclaiming() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        log = root / "ngtcp2.log"
        runner = root / "runner.sh"
        make_test_log(log)
        runner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        packet = build_packet(
            Path("/tmp/definitely-missing-ngtcp2-clone"),
            log,
            runner,
            root / "missing-result.env",
        )
        assert packet["public_safe"] is True
        assert packet["implementation"] == "ngtcp2"
        assert packet["focused_test_state"]["passed_tests"] == 6
        assert packet["runtime_trial"]["can_claim_runtime_pass"] == "no"
        assert packet["runtime_trial"]["can_claim_browser_or_deployment"] == "no"
        assert packet["claim_boundary"]["unsafe_claim"]


def test_packet_reads_blocked_runner_result() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        log = root / "ngtcp2.log"
        runner = root / "runner.sh"
        result = root / "result.env"
        make_test_log(log)
        runner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        result.write_text(
            "validation=blocked\n"
            "blocked_or_failed_reason=missing_pkg_config_libev\n"
            "client_exit=not-run\n",
            encoding="utf-8",
        )
        packet = build_packet(
            Path("/tmp/definitely-missing-ngtcp2-clone"),
            log,
            runner,
            result,
        )
        assert packet["runtime_trial"]["status"] == "blocked"
        assert packet["runtime_trial"]["reason"] == "missing_pkg_config_libev"
        assert packet["runner"]["result_env_values"]["validation"] == "blocked"


def test_markdown_is_public_safe_and_names_runtime_boundary() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        log = root / "ngtcp2.log"
        runner = root / "runner.sh"
        make_test_log(log)
        runner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        markdown = emit_markdown(
            build_packet(
                Path("/tmp/definitely-missing-ngtcp2-clone"),
                log,
                runner,
                root / "missing-result.env",
            )
        )
        for forbidden in FORBIDDEN_PUBLIC_TEXT:
            assert forbidden not in markdown
        assert "Safe claim" in markdown
        assert "Unsafe claim" in markdown
        assert "libev" in markdown
        assert "runtime PASS" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        log = root / "ngtcp2.log"
        runner = root / "runner.sh"
        out = root / "packet.md"
        jout = root / "packet.json"
        make_test_log(log)
        runner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        packet = build_packet(
            Path("/tmp/definitely-missing-ngtcp2-clone"),
            log,
            runner,
            root / "missing-result.env",
        )
        write_outputs(out, jout, packet)
        assert out.read_text(encoding="utf-8").startswith("# ngtcp2 Runtime Trial Packet")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["implementation"] == "ngtcp2"


def main() -> int:
    test_packet_classifies_missing_runner_env_without_overclaiming()
    test_packet_reads_blocked_runner_result()
    test_markdown_is_public_safe_and_names_runtime_boundary()
    test_outputs_are_valid_json_and_markdown()
    print("build_ngtcp2_runtime_trial_packet=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
