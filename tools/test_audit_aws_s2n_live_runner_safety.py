#!/usr/bin/env python3
"""Regression tests for the AWS s2n live runner safety audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from audit_aws_s2n_live_runner_safety import build_audit, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def test_audit_detects_gates_resources_and_cleanup() -> None:
    audit = build_audit(
        Path("harness/scripts/run-aws-s2n-nlb-live-data-plane.sh"),
        Path("harness/results/s2n-nlb-live-readiness-20260701-gate/results/result.env"),
    )
    assert audit["public_safe"] is True
    assert audit["summary"]["fail_closed_ok"] is True
    assert audit["summary"]["resource_inventory_ok"] is True
    assert audit["summary"]["cleanup_coverage_ok"] is True
    assert audit["summary"]["risk_boundary_ok"] is True
    assert audit["summary"]["estimated_live_resources"]["ec2_instances"] == 2
    assert audit["summary"]["current_gate"]["blocked_reason"] in {
        "aws_identity_invalid_client_token",
        "unknown",
    }


def test_markdown_is_public_safe_and_boundaried() -> None:
    markdown = emit_markdown(
        build_audit(
            Path("harness/scripts/run-aws-s2n-nlb-live-data-plane.sh"),
            Path("harness/results/s2n-nlb-live-readiness-20260701-gate/results/result.env"),
        )
    )
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "not live AWS evidence" in markdown
    assert "forwarding echo first" in markdown
    assert "AddPath/Probe/Switch" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    audit = build_audit(
        Path("harness/scripts/run-aws-s2n-nlb-live-data-plane.sh"),
        Path("harness/results/s2n-nlb-live-readiness-20260701-gate/results/result.env"),
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "audit.md"
        jout = Path(tmpdir) / "audit.json"
        write_outputs(out, jout, audit)
        assert out.read_text(encoding="utf-8").startswith("# AWS s2n Live Runner Safety Audit")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["cleanup_coverage_ok"] is True


def main() -> int:
    test_audit_detects_gates_resources_and_cleanup()
    test_markdown_is_public_safe_and_boundaried()
    test_outputs_are_valid_json_and_markdown()
    print("audit_aws_s2n_live_runner_safety=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
