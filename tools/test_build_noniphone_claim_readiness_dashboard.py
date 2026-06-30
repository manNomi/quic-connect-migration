#!/usr/bin/env python3
"""Regression tests for the non-iPhone claim readiness dashboard."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_noniphone_claim_readiness_dashboard import build_dashboard, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
    "i18" + "nexus",
]


def test_dashboard_separates_supported_and_blocked_claims() -> None:
    dashboard = build_dashboard()
    assert dashboard["public_safe"] is True
    assert dashboard["summary"]["claim_count"] == 8
    assert dashboard["summary"]["claim_allowed_count"] == 5
    assert dashboard["summary"]["claim_blocked_count"] == 3
    assert dashboard["summary"]["missing_evidence_by_claim"] == {}
    assert dashboard["context"]["aws_identity_classification"] == "invalid_client_token"
    assert dashboard["context"]["public_origin_h3_alt_svc"] is False
    assert dashboard["context"]["noniphone_desktop_path_ready"] is False
    assert dashboard["context"]["controlled_public_strong_cm_success_count"] == 0

    claims = {row["id"]: row for row in dashboard["claims"]}
    assert claims["implementation_maturity"]["claim_allowed"] is True
    assert claims["controlled_public_chrome_cm"]["claim_allowed"] is False
    assert claims["controlled_public_chrome_cm"]["status"] == "not_supported_yet"
    assert "controlled-public-chrome-bridge-synthesis" in claims["controlled_public_chrome_cm"]["evidence_found"]
    assert claims["aws_s2n_live_claim"]["status"] == "blocked"
    assert claims["safari_cross_browser_claim"]["status"] == "blocked_feasibility"
    assert claims["streaming_qoe_claim"]["claim_allowed"] is True
    assert "QoE" in claims["streaming_qoe_claim"]["label"]


def test_markdown_is_public_safe_and_names_no_overclaim_boundaries() -> None:
    markdown = emit_markdown(build_dashboard())
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "not strong enough for controlled-public Chrome single-session CM success" in markdown
    assert "Do not claim Chrome public-origin single-session Connection Migration success" in markdown
    assert "Do not claim live AWS NLB+s2n forwarding or active migration success" in markdown
    assert "maturity/gap report" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    dashboard = build_dashboard()
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "dashboard.md"
        jout = Path(tmpdir) / "dashboard.json"
        write_outputs(out, jout, dashboard)
        assert out.read_text(encoding="utf-8").startswith("# non-iPhone Claim Readiness Dashboard")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["claim_count"] == dashboard["summary"]["claim_count"]


def main() -> int:
    test_dashboard_separates_supported_and_blocked_claims()
    test_markdown_is_public_safe_and_names_no_overclaim_boundaries()
    test_outputs_are_valid_json_and_markdown()
    print("build_noniphone_claim_readiness_dashboard=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
