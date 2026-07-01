#!/usr/bin/env python3
"""Regression tests for the MsQuic rebind/path-validation packet builder."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_msquic_rebind_pathvalidation_packet import (
    FORBIDDEN_PUBLIC_TEXT,
    build_packet,
    emit_markdown,
    write_outputs,
)


def write_env(path: Path, values: dict[str, str]) -> None:
    path.write_text("\n".join(f"{key}={value}" for key, value in values.items()) + "\n", encoding="utf-8")


def test_packet_classifies_missing_runner_env_without_overclaiming() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        runner = root / "runner.sh"
        runner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        packet = build_packet(
            root / "missing-msquic",
            runner,
            root / "missing-result.env",
        )
        assert packet["implementation"] == "MsQuic"
        assert packet["runtime_trial"]["can_claim_runtime_pass"] == "no"
        assert packet["runtime_trial"]["reason"] == "runner_result_env_missing"
        assert "validation=ok" in packet["claim_boundary"]["safe_claim"]


def test_packet_reads_ok_runner_result_as_runtime_pass() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        runner = root / "runner.sh"
        result = root / "result.env"
        runner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        write_env(
            result,
            {
                "run_id": "msquic-test-run",
                "artifact_dir": "/tmp/quic-connect-migration/harness/results/msquic-test-run",
                "validation": "ok",
                "blocked_or_failed_reason": "none",
                "msquictest_list_exit": "0",
                "msquictest_v4_exit": "0",
                "msquictest_v6_exit": "0",
                "listed_rebind_pathvalidation_count": "8",
                "v4_ok_count": "4",
                "v6_ok_count": "4",
                "total_ok_count": "8",
                "passed_summary_count": "2",
                "failed_marker_count": "0",
            },
        )
        packet = build_packet(root / "missing-msquic", runner, result)
        assert packet["runtime_trial"]["can_claim_runtime_pass"] == "yes"
        assert packet["runtime_trial"]["reason"] == "runner_validation_ok"
        assert packet["runner"]["result_env_values"].get("artifact_dir", "").startswith("harness/results/")
        markdown = emit_markdown(packet)
        assert "v4 ok count | `4`" in markdown
        assert "v6 ok count | `4`" in markdown
        assert "MsQuic browser handover" in markdown


def test_markdown_is_public_safe_and_names_runtime_boundary() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        runner = root / "runner.sh"
        runner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        packet = build_packet(root / "missing-msquic", runner, root / "missing-result.env")
        markdown = emit_markdown(packet)
        for forbidden in FORBIDDEN_PUBLIC_TEXT:
            assert forbidden not in markdown
        assert "Safe claim" in markdown
        assert "Unsafe claim" in markdown
        assert "QUIC_PARAM_CONN_LOCAL_ADDRESS" in markdown
        assert "AddPath/Probe/Switch" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        runner = root / "runner.sh"
        out = root / "packet.md"
        jout = root / "packet.json"
        runner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        packet = build_packet(root / "missing-msquic", runner, root / "missing-result.env")
        write_outputs(out, jout, packet)
        assert out.read_text(encoding="utf-8").startswith("# MsQuic Rebind Path Validation Packet")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["implementation"] == "MsQuic"
        assert ("/" + "Users/") not in jout.read_text(encoding="utf-8")


def main() -> int:
    test_packet_classifies_missing_runner_env_without_overclaiming()
    test_packet_reads_ok_runner_result_as_runtime_pass()
    test_markdown_is_public_safe_and_names_runtime_boundary()
    test_outputs_are_valid_json_and_markdown()
    print("build_msquic_rebind_pathvalidation_packet=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
