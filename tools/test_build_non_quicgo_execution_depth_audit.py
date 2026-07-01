#!/usr/bin/env python3
"""Regression tests for the non-quic-go execution-depth audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_non_quicgo_execution_depth_audit import build_audit, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def test_audit_preserves_quic_go_boundary_and_depth_counts() -> None:
    audit = build_audit(
        Path("data/implementation-survey.csv"),
        Path("harness/results/s2n-nlb-live-readiness-20260701-current/results/result.env"),
    )
    assert audit["public_safe"] is True
    assert audit["summary"]["survey_rows_excluding_quic_go"] == 17
    names = {row["name"] for row in audit["implementations"]}
    assert "quic-go" not in names
    assert "Cloudflare quiche" in names
    assert "HAProxy QUIC" in names
    assert audit["summary"]["depth_counts"]["local_test_suite_rerun"] >= 7
    assert audit["summary"]["depth_counts"]["local_runtime_or_app_demo"] >= 3
    assert audit["summary"]["depth_counts"]["negative_control_runtime"] == 1
    ngtcp2 = next(row for row in audit["implementations"] if row["name"] == "ngtcp2")
    assert ngtcp2["depth_class"] == "local_runtime_or_app_demo"
    assert "quic-go is the deepest controllable positive control" in audit["summary"]["interpretation"]
    assert "unsafe_claim" in audit["reporting_boundary"]


def test_aws_gate_is_public_safe_and_optional() -> None:
    audit = build_audit(Path("data/implementation-survey.csv"), Path("missing/result.env"))
    assert audit["aws_readiness"]["input_exists"] is False
    assert audit["aws_readiness"]["aws_identity_ok"] == "unknown"
    markdown = emit_markdown(audit)
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Professor-facing Answer" in markdown
    assert "why quic-go has the deepest controlled run" in markdown


def test_outputs_are_valid_markdown_json_and_csv() -> None:
    audit = build_audit(Path("data/implementation-survey.csv"), Path("missing/result.env"))
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "audit.md"
        jout = Path(tmpdir) / "audit.json"
        cout = Path(tmpdir) / "audit.csv"
        write_outputs(out, jout, cout, audit)
        assert out.read_text(encoding="utf-8").startswith("# Non-quic-go Execution Depth Audit")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["survey_rows_excluding_quic_go"] == 17
        csv_text = cout.read_text(encoding="utf-8")
        assert "why_not_quic_go_depth" in csv_text
        assert "HAProxy QUIC" in csv_text


def main() -> int:
    test_audit_preserves_quic_go_boundary_and_depth_counts()
    test_aws_gate_is_public_safe_and_optional()
    test_outputs_are_valid_markdown_json_and_csv()
    print("build_non_quicgo_execution_depth_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
