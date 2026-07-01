#!/usr/bin/env python3
"""Regression tests for the XQUIC full-suite Linux replay audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_xquic_full_suite_linux_audit import build_audit, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def write_fixture(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_audit_keeps_xquic_partial_until_linux_pass_exists() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        nat = write_fixture(
            root / "results.env",
            "\n".join(
                [
                    "client0_exit=0",
                    "path0_rebinding_evidence_count=2",
                    "path0_pass_count=2",
                    "client1_exit=0",
                    "path1_rebinding_evidence_count=1",
                    "path1_pass_count=2",
                ]
            )
            + "\n",
        )
        macos = write_fixture(
            root / "xquic-build-tests.log",
            "AppleClang 17.0.0\nxqc_qpack_test.c:462:33: error: variable length array folded to constant array as an extension [-Werror,-Wgnu-folding-constant]\n",
        )
        runner = write_fixture(
            root / "run-xquic-full-suite-linux.sh",
            "\n".join(
                [
                    "linux_required",
                    "xquic_commit_mismatch",
                    'cmake --build "$BORINGSSL_DIR/build" --target ssl crypto',
                    'cmake --build "$BUILD_DIR" --target run_tests test_client test_server',
                    '"$BUILD_DIR/tests/run_tests"',
                    'sh "$XQUIC_DIR/scripts/case_test.sh"',
                    "This artifact is public-safe.",
                ]
            ),
        )
        audit = build_audit(root / "missing-xquic", nat, macos, runner)
        assert audit["public_safe"] is True
        assert audit["implementation"] == "XQUIC"
        assert audit["existing_nat_rebinding_demo"]["status"] == "PASS"
        assert audit["macos_full_suite_attempt"]["status"] == "blocked_by_appleclang_werror"
        assert audit["summary"]["linux_runner_ready"] == "yes"
        assert "do not claim full-suite PASS" in audit["summary"]["paper_use"]
        assert "full test-suite PASS" in audit["reporting_boundary"]["unsafe_claim"]


def test_evidence_links_cover_source_runtime_and_test_boundaries() -> None:
    audit = build_audit(
        Path("missing-xquic"),
        Path("missing-results.env"),
        Path("missing-build.log"),
        Path("harness/scripts/run-xquic-full-suite-linux.sh"),
    )
    ids = {item["id"] for item in audit["evidence"]}
    assert "official-requirements" in ids
    assert "werror-cmake-flags" in ids
    assert "run-tests-target" in ids
    assert "peer-address-callback-api" in ids
    assert "ready-to-create-path-api" in ids
    assert "nat-rebinding-validation" in ids
    assert "test-client-rebind-socket" in ids
    assert "test-server-peer-change-callback" in ids
    for item in audit["evidence"]:
        assert item["url"].startswith("https://github.com/alibaba/xquic/blob/")
        assert item["observation"]
        assert item["implication"]


def test_markdown_is_public_safe_and_names_boundaries() -> None:
    markdown = emit_markdown(
        build_audit(
            Path("missing-xquic"),
            Path("missing-results.env"),
            Path("missing-build.log"),
            Path("harness/scripts/run-xquic-full-suite-linux.sh"),
        )
    )
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Safe claim" in markdown
    assert "Unsafe claim" in markdown
    assert "focused_or_partial_positive" in markdown
    assert "Linux full-suite artifact passes" in markdown


def test_outputs_are_valid_markdown_and_json() -> None:
    audit = build_audit(
        Path("missing-xquic"),
        Path("missing-results.env"),
        Path("missing-build.log"),
        Path("harness/scripts/run-xquic-full-suite-linux.sh"),
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "audit.md"
        jout = Path(tmpdir) / "audit.json"
        write_outputs(out, jout, audit)
        assert out.read_text(encoding="utf-8").startswith("# XQUIC Full-suite Linux Audit")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["source_evidence_items"] >= 12
        assert parsed["reporting_boundary"]["next_non_iphone_gate"]


def main() -> int:
    test_audit_keeps_xquic_partial_until_linux_pass_exists()
    test_evidence_links_cover_source_runtime_and_test_boundaries()
    test_markdown_is_public_safe_and_names_boundaries()
    test_outputs_are_valid_markdown_and_json()
    print("build_xquic_full_suite_linux_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
