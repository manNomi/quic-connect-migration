#!/usr/bin/env python3
"""Regression tests for the quicly full-e2e Linux runner audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_quicly_full_e2e_linux_audit import build_audit, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def write_env(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "ready=yes",
                "prove_exit=1",
                "path_subtest_seen=yes",
                "path_subtest_ok=yes",
                "cid_seq_check_ok=yes",
                "slow_start_failed=yes",
                "validation=ok_path_migration",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def runner_fixture(path: Path) -> Path:
    text = "\n".join(
        [
            "linux_required",
            "quicly_commit_mismatch",
            "missing_perl_net_empty_port",
            "git submodule update --init --recursive",
            'cmake -S "$QUICLY_DIR" -B "$QUICLY_BUILD_DIR"',
            'cmake --build "$QUICLY_BUILD_DIR" --target test.t cli udpfw',
            '"$QUICLY_BUILD_DIR/test.t"',
            "prove -v t/e2e.t",
            "ok_full_e2e",
            "This artifact is public-safe.",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return path


def test_audit_keeps_quicly_focused_until_full_linux_pass_exists() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        focused = write_env(root / "result.env")
        runner = runner_fixture(root / "runner.sh")
        audit = build_audit(root / "missing-quicly", focused, runner)
        assert audit["public_safe"] is True
        assert audit["implementation"] == "quicly"
        assert audit["summary"]["focused_e2e_status"] == "PASS_FOCUSED_E2E"
        assert audit["summary"]["focused_path_subtest_ok"] == "yes"
        assert audit["summary"]["focused_cid_seq_check_ok"] == "yes"
        assert audit["summary"]["focused_full_prove_exit"] == "1"
        assert audit["summary"]["linux_runner_ready"] == "yes"
        assert "do not claim full e2e PASS" in audit["summary"]["paper_use"]
        assert "quicly full t/e2e.t PASS" in audit["reporting_boundary"]["unsafe_claim"]


def test_evidence_links_cover_primitives_e2e_and_boundary() -> None:
    audit = build_audit(
        Path("missing-quicly"),
        Path("harness/results/quicly-e2e-path-migration-local-20260630/results/result.env"),
        Path("harness/scripts/run-quicly-full-e2e-linux.sh"),
    )
    ids = {item["id"] for item in audit["evidence"]}
    assert "official-build-instructions" in ids
    assert "official-test-instructions" in ids
    assert "frame-primitive" in ids
    assert "path-validation-state" in ids
    assert "promote-path" in ids
    assert "path-response-validation" in ids
    assert "path-migration-e2e" in ids
    assert "slow-start-boundary" in ids
    for item in audit["evidence"]:
        assert item["url"].startswith("https://github.com/h2o/quicly/blob/")
        assert item["observation"]
        assert item["implication"]


def test_markdown_is_public_safe_and_names_boundaries() -> None:
    markdown = emit_markdown(
        build_audit(
            Path("missing-quicly"),
            Path("harness/results/quicly-e2e-path-migration-local-20260630/results/result.env"),
            Path("harness/scripts/run-quicly-full-e2e-linux.sh"),
        )
    )
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Safe claim" in markdown
    assert "Unsafe claim" in markdown
    assert "focused_e2e_positive_with_full_e2e_gate" in markdown
    assert "validation=ok_full_e2e" in markdown
    assert "full quicly e2e success" in markdown


def test_outputs_are_valid_markdown_and_json() -> None:
    audit = build_audit(
        Path("missing-quicly"),
        Path("harness/results/quicly-e2e-path-migration-local-20260630/results/result.env"),
        Path("harness/scripts/run-quicly-full-e2e-linux.sh"),
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "audit.md"
        jout = Path(tmpdir) / "audit.json"
        write_outputs(out, jout, audit)
        assert out.read_text(encoding="utf-8").startswith("# quicly Full e2e Linux Runner Audit")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["source_evidence_items"] >= 10
        assert parsed["reporting_boundary"]["next_non_iphone_gate"]


def main() -> int:
    test_audit_keeps_quicly_focused_until_full_linux_pass_exists()
    test_evidence_links_cover_primitives_e2e_and_boundary()
    test_markdown_is_public_safe_and_names_boundaries()
    test_outputs_are_valid_markdown_and_json()
    print("build_quicly_full_e2e_linux_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
