#!/usr/bin/env python3
"""Regression tests for non-quic-go implementation findings."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_non_quicgo_implementation_findings import build_findings, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def test_findings_exclude_quic_go_and_preserve_boundaries() -> None:
    findings = build_findings(Path("data/implementation-survey.csv"))
    assert findings["public_safe"] is True
    assert findings["summary"]["survey_rows_excluding_quic_go"] == 17
    names = {row["name"] for row in findings["implementations"]}
    assert "quic-go" not in names
    assert "Cloudflare quiche" in names
    assert "HAProxy QUIC" in names
    assert findings["summary"]["active_migration_api_yes"] >= 7
    assert findings["summary"]["passive_migration_yes"] >= 13
    assert findings["summary"]["tests_yes"] >= 13
    classes = findings["summary"]["claim_class_counts"]
    assert classes["strong_cross_implementation_positive"] >= 6
    assert classes["server_or_app_runtime_positive"] >= 4
    assert classes["negative_control"] == 1
    quinn = next(row for row in findings["implementations"] if row["name"] == "Quinn")
    assert quinn["claim_class"] == "server_or_app_runtime_positive"
    assert "unsafe_claim" in findings["reporting_boundary"]


def test_markdown_is_public_safe_and_professor_ready() -> None:
    markdown = emit_markdown(build_findings(Path("data/implementation-survey.csv")))
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Professor-facing Answer" in markdown
    assert "quic-go remains the deepest controllable" in markdown
    assert "ordinary HTTP/3 availability does not imply active Connection Migration support" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    findings = build_findings(Path("data/implementation-survey.csv"))
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "findings.md"
        jout = Path(tmpdir) / "findings.json"
        write_outputs(out, jout, findings)
        assert out.read_text(encoding="utf-8").startswith("# Non-quic-go Implementation Findings")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["survey_rows_excluding_quic_go"] == 17


def main() -> int:
    test_findings_exclude_quic_go_and_preserve_boundaries()
    test_markdown_is_public_safe_and_professor_ready()
    test_outputs_are_valid_json_and_markdown()
    print("build_non_quicgo_implementation_findings=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
