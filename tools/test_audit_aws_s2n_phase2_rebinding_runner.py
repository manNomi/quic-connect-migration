#!/usr/bin/env python3
"""Regression tests for the AWS s2n phase-2 rebinding runner audit."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_aws_s2n_phase2_rebinding_runner import build_audit, emit_markdown


def test_audit_detects_phase2_runner_tokens() -> None:
    audit = build_audit(
        Path("harness/scripts/run-aws-s2n-nlb-live-data-plane.sh"),
        Path("experiments/s2n-quic-nlb-cid-provider/src/bin/nlb_live_client.rs"),
        Path("repro/quic-go-min-repro/cmd/udprebindproxy/main.go"),
        Path("harness/results/aws-s2n-nlb-rebinding-proxy-preflight-20260701/results/result.env"),
    )
    summary = audit["summary"]
    assert summary["runner_mode_ready"] is True
    assert summary["chunked_client_ready"] is True
    assert summary["remote_proxy_bind_ready"] is True
    assert summary["pre_resource_preflight_recorded"] is True
    assert summary["preflight_path_change_mode"] == "rebinding_proxy"
    assert summary["preflight_rebinding_proxy_source_ready"] == "yes"


def test_markdown_preserves_claim_boundary() -> None:
    audit = build_audit(
        Path("harness/scripts/run-aws-s2n-nlb-live-data-plane.sh"),
        Path("experiments/s2n-quic-nlb-cid-provider/src/bin/nlb_live_client.rs"),
        Path("repro/quic-go-min-repro/cmd/udprebindproxy/main.go"),
        Path("harness/results/aws-s2n-nlb-rebinding-proxy-preflight-20260701/results/result.env"),
    )
    markdown = emit_markdown(audit)
    assert "Unsafe claim" in markdown
    assert "application-triggered active migration" in markdown
    assert "preflight is blocked before AWS resource creation" in markdown


if __name__ == "__main__":
    test_audit_detects_phase2_runner_tokens()
    test_markdown_preserves_claim_boundary()
    print("audit_aws_s2n_phase2_rebinding_runner=ok")
