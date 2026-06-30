#!/usr/bin/env python3
"""Regression tests for the sanitized evidence bundle builder."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_sanitized_evidence_bundle import build_bundle, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def test_bundle_has_claim_boundaries() -> None:
    bundle = build_bundle()
    assert bundle["public_safe"] is True
    assert bundle["item_count"] >= 18
    assert not bundle["missing_evidence_docs"]
    assert not bundle["missing_runners_or_tools"]
    ids = {item["id"] for item in bundle["items"]}
    assert "quicly-focused-e2e-path-migration" in ids
    assert "quicly-full-e2e-linux-audit" in ids
    assert "haproxy-http3-negative-control" in ids
    assert "s2n-nlb-live-readiness" in ids
    assert "aws-s2n-nlb-live-runner" in ids
    assert "aws-s2n-live-runner-safety-audit" in ids
    assert "aws-s2n-phase2-path-change-design" in ids
    assert "s2n-active-migration-api-audit" in ids
    assert "mvfst-migration-test-readiness" in ids
    assert "mvfst-focused-linux-runner-audit" in ids
    assert "nginx-quic-bpf-linux-runner" in ids
    assert "safari-webdriver-session-readiness" in ids
    assert "user-provided-public-origin-readiness" in ids
    assert "non-iphone-gate-rerun-20260701" in ids
    assert "controlled-public-chrome-bridge-synthesis" in ids
    assert "controlled-public-chrome-artifact-classifier-contract" in ids
    assert "controlled-public-chrome-contract-application-audit" in ids
    assert "chrome-desktop-noniphone-media-local-refresh" in ids
    assert "chrome-desktop-noniphone-musiclike-local-refresh" in ids
    assert "chrome-desktop-noniphone-buffered-media-local-refresh" in ids
    assert "noniphone-workload-qoe-synthesis" in ids
    assert "controlled-public-origin-workload-deploy-packet" in ids
    assert "noniphone-desktop-path-change-readiness" in ids
    assert "noniphone-public-workload-trial-packet" in ids
    assert "noniphone-claim-readiness-dashboard" in ids
    assert "noniphone-professor-decision-packet" in ids
    assert "noniphone-reviewer-risk-audit" in ids
    assert "noniphone-paper-wording-guard" in ids
    assert "noniphone-paper-section-scaffold" in ids
    assert "non-quicgo-implementation-findings" in ids
    assert "msquic-migration-api-boundary-audit" in ids
    assert "xquic-full-suite-linux-audit" in ids
    assert "aws-s2n-phase2-rebinding-runner-audit" in ids
    assert "aws-s2n-phase2-artifact-classifier-contract" in ids
    assert "chrome-desktop-noniphone-range-local-refresh" in ids
    assert "chrome-desktop-noniphone-upload-local-refresh" in ids
    for item in bundle["items"]:
        assert item["supports"]
        assert item["do_not_claim"]
        assert item["next_gap"]


def test_markdown_is_public_safe_and_names_boundary_terms() -> None:
    markdown = emit_markdown(build_bundle())
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "do not claim" in markdown
    assert "readiness_blocked" in markdown
    assert "negative_control" in markdown
    assert "full e2e PASS" not in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    bundle = build_bundle()
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "bundle.md"
        jout = Path(tmpdir) / "bundle.json"
        write_outputs(out, jout, bundle)
        assert out.read_text(encoding="utf-8").startswith("# Sanitized Evidence Bundle")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["item_count"] == bundle["item_count"]


def main() -> int:
    test_bundle_has_claim_boundaries()
    test_markdown_is_public_safe_and_names_boundary_terms()
    test_outputs_are_valid_json_and_markdown()
    print("build_sanitized_evidence_bundle=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
