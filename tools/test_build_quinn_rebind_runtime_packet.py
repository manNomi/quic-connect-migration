#!/usr/bin/env python3
"""Regression tests for the Quinn rebind runtime packet builder."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_quinn_rebind_runtime_packet import build_packet, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def test_packet_classifies_missing_runner_env_without_overclaiming() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        runner = root / "runner.sh"
        runner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        packet = build_packet(
            Path("/tmp/definitely-missing-quinn-clone"),
            runner,
            root / "missing-result.env",
        )
        assert packet["public_safe"] is True
        assert packet["implementation"] == "Quinn"
        assert packet["runtime_trial"]["status"] == "ready_not_run"
        assert packet["runtime_trial"]["can_claim_runtime_pass"] == "no"
        assert packet["runtime_trial"]["can_claim_browser_or_deployment"] == "no"
        assert packet["claim_boundary"]["unsafe_claim"]


def test_packet_reads_ok_runner_result_as_runtime_pass() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        runner = root / "runner.sh"
        result = root / "result.env"
        runner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        result.write_text(
            "validation=ok\n"
            "blocked_or_failed_reason=none\n"
            "cargo_quinn_rebind_exit=0\n"
            "cargo_quinn_proto_migration_exit=0\n"
            "rebind_recv_ok_count=1\n"
            "connected_log_count=1\n"
            "got_conn_log_count=1\n"
            "rebound_log_count=1\n"
            "proto_migration_ok_count=1\n"
            "proto_migration_initiated_count=1\n"
            "path_challenge_count=3\n"
            "path_response_count=3\n"
            "new_path_validated_count=1\n",
            encoding="utf-8",
        )
        packet = build_packet(
            Path("/tmp/definitely-missing-quinn-clone"),
            runner,
            result,
        )
        assert packet["runtime_trial"]["status"] == "ready_or_passed"
        assert packet["runtime_trial"]["reason"] == "runner_validation_ok"
        assert packet["runtime_trial"]["can_claim_runtime_pass"] == "yes"
        assert "local endpoint-rebind runtime PASS" in packet["claim_boundary"]["safe_claim"]


def test_markdown_is_public_safe_and_names_runtime_boundary() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        runner = root / "runner.sh"
        runner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        markdown = emit_markdown(
            build_packet(
                Path("/tmp/definitely-missing-quinn-clone"),
                runner,
                root / "missing-result.env",
            )
        )
        for forbidden in FORBIDDEN_PUBLIC_TEXT:
            assert forbidden not in markdown
        assert "Safe claim" in markdown
        assert "Unsafe claim" in markdown
        assert "Endpoint::rebind" in markdown
        assert "AddPath/Probe/Switch" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        runner = root / "runner.sh"
        out = root / "packet.md"
        jout = root / "packet.json"
        runner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        packet = build_packet(
            Path("/tmp/definitely-missing-quinn-clone"),
            runner,
            root / "missing-result.env",
        )
        write_outputs(out, jout, packet)
        assert out.read_text(encoding="utf-8").startswith("# Quinn Rebind Runtime Packet")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["implementation"] == "Quinn"


def main() -> int:
    test_packet_classifies_missing_runner_env_without_overclaiming()
    test_packet_reads_ok_runner_result_as_runtime_pass()
    test_markdown_is_public_safe_and_names_runtime_boundary()
    test_outputs_are_valid_json_and_markdown()
    print("build_quinn_rebind_runtime_packet=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
