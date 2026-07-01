#!/usr/bin/env python3
"""Regression tests for the mvfst focused Linux runner audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_mvfst_focused_linux_runner_audit import build_audit, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def write_fixture(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def runner_fixture(path: Path) -> Path:
    text = "\n".join(
        [
            "linux_required",
            "mvfst_commit_mismatch",
            'RUNNER_MODE="${RUNNER_MODE:-buck}"',
            "QuicClientTransportLiteMigrationTest",
            'buck2 test "$target"',
            "getdeps.py --allow-system-packages",
            "This artifact is public-safe.",
            "A paper-ready focused PASS requires all three BUCK targets",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return path


def readiness_fixture() -> dict:
    return {
        "source_commit": "d9d65a3ab3e6ffba785d6605afe6f05b8db015ec",
        "remote_head": "d9d65a3ab3e6ffba785d6605afe6f05b8db015ec",
        "readiness": {
            "validation": "blocked",
            "blocked_reasons": ["buck2_missing", "disk_below_threshold"],
        },
        "total_test_cases_observed": 106,
        "total_high_value_test_cases_observed": 78,
        "focused_targets": [
            {
                "kind": "path-manager",
                "file": "quic/state/test/QuicPathManagerTest.cpp",
                "buck_target": "quic/state/test:quic_path_manager_test",
                "test_case_count": 55,
                "high_value_test_count": 27,
            },
            {
                "kind": "client-active-migration",
                "file": "quic/client/test/QuicClientTransportLiteMigrationTest.cpp",
                "buck_target": "quic/client/test:QuicClientTransportLiteMigrationTest",
                "test_case_count": 14,
                "high_value_test_count": 14,
            },
            {
                "kind": "server-passive-migration",
                "file": "quic/server/test/QuicServerTransportMigrationTest.cpp",
                "buck_target": "quic/server/test:QuicServerTransportMigrationTest",
                "test_case_count": 37,
                "high_value_test_count": 37,
            },
        ],
    }


def test_audit_packages_runner_without_promoting_mvfst_to_pass() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        readiness = write_fixture(root / "readiness.json", readiness_fixture())
        runner = runner_fixture(root / "runner.sh")
        audit = build_audit(root / "missing-mvfst", readiness, runner)
        assert audit["public_safe"] is True
        assert audit["implementation"] == "mvfst"
        assert audit["summary"]["focused_target_count"] == 3
        assert audit["summary"]["test_cases_observed"] == 106
        assert audit["summary"]["high_value_test_cases_observed"] == 78
        assert audit["summary"]["linux_runner_ready"] == "yes"
        assert "do not claim local mvfst execution" in audit["summary"]["paper_use"]
        assert "Local mvfst build/test PASS" in audit["reporting_boundary"]["unsafe_claim"]


def test_evidence_links_cover_source_buck_and_test_boundaries() -> None:
    audit = build_audit(
        Path("missing-mvfst"),
        Path("data/mvfst-migration-test-readiness-20260630.json"),
        Path("harness/scripts/run-mvfst-focused-migration-tests-linux.sh"),
    )
    ids = {item["id"] for item in audit["evidence"]}
    assert "path-manager-purpose" in ids
    assert "client-start-path-probe" in ids
    assert "client-migrate-connection" in ids
    assert "server-passive-migration" in ids
    assert "buck-path-manager-target" in ids
    assert "buck-client-migration-target" in ids
    assert "buck-server-migration-target" in ids
    assert "server-nat-rebinding-test-cases" in ids
    for item in audit["evidence"]:
        assert item["url"].startswith("https://github.com/facebook/mvfst/blob/")
        assert item["observation"]
        assert item["implication"]


def test_markdown_is_public_safe_and_names_boundaries() -> None:
    markdown = emit_markdown(
        build_audit(
            Path("missing-mvfst"),
            Path("data/mvfst-migration-test-readiness-20260630.json"),
            Path("harness/scripts/run-mvfst-focused-migration-tests-linux.sh"),
        )
    )
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Safe claim" in markdown
    assert "Unsafe claim" in markdown
    assert "source_test_map_only" in markdown
    assert "all three focused BUCK targets exiting 0" in markdown


def test_outputs_are_valid_markdown_and_json() -> None:
    audit = build_audit(
        Path("missing-mvfst"),
        Path("data/mvfst-migration-test-readiness-20260630.json"),
        Path("harness/scripts/run-mvfst-focused-migration-tests-linux.sh"),
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "audit.md"
        jout = Path(tmpdir) / "audit.json"
        write_outputs(out, jout, audit)
        assert out.read_text(encoding="utf-8").startswith("# mvfst Focused Linux Runner Audit")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["source_evidence_items"] >= 8
        assert parsed["reporting_boundary"]["next_non_iphone_gate"]


def main() -> int:
    test_audit_packages_runner_without_promoting_mvfst_to_pass()
    test_evidence_links_cover_source_buck_and_test_boundaries()
    test_markdown_is_public_safe_and_names_boundaries()
    test_outputs_are_valid_markdown_and_json()
    print("build_mvfst_focused_linux_runner_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
