#!/usr/bin/env python3
"""Regression tests for the AWS s2n phase-2 path-change design."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_aws_s2n_phase2_path_change_design import build_design, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def test_design_selects_proxy_phase2_when_public_api_absent() -> None:
    design = build_design(
        Path("data/s2n-active-migration-api-audit-20260630.json"),
        Path("data/aws-s2n-live-runner-safety-audit-20260701.json"),
        Path("data/non-iphone-gate-rerun-20260701.json"),
    )
    assert design["public_safe"] is True
    assert design["summary"]["public_active_trigger_api_found"] is False
    assert design["summary"]["live_runner_safety_ok"] is True
    assert design["summary"]["preferred_phase2_design"] == "phase2_nat_rebinding_proxy"
    ids = {option["id"] for option in design["options"]}
    assert "phase1_forwarding_echo_prerequisite" in ids
    assert "phase2_nat_rebinding_proxy" in ids
    assert "phase2_public_api_wait_or_patch" in ids


def test_markdown_is_public_safe_and_clear_about_claims() -> None:
    markdown = emit_markdown(
        build_design(
            Path("data/s2n-active-migration-api-audit-20260630.json"),
            Path("data/aws-s2n-live-runner-safety-audit-20260701.json"),
            Path("data/non-iphone-gate-rerun-20260701.json"),
        )
    )
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "NAT-rebinding proxy" in markdown
    assert "not as a result row" in markdown
    assert "current upstream s2n public API" in markdown
    assert "AddPath/Probe/Switch" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    design = build_design(
        Path("data/s2n-active-migration-api-audit-20260630.json"),
        Path("data/aws-s2n-live-runner-safety-audit-20260701.json"),
        Path("data/non-iphone-gate-rerun-20260701.json"),
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "design.md"
        jout = Path(tmpdir) / "design.json"
        write_outputs(out, jout, design)
        assert out.read_text(encoding="utf-8").startswith("# AWS s2n Phase-2 Path-Change Design")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["preferred_phase2_design"] == "phase2_nat_rebinding_proxy"


def main() -> int:
    test_design_selects_proxy_phase2_when_public_api_absent()
    test_markdown_is_public_safe_and_clear_about_claims()
    test_outputs_are_valid_json_and_markdown()
    print("build_aws_s2n_phase2_path_change_design=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
