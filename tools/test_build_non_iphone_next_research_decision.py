#!/usr/bin/env python3
"""Regression tests for the non-iPhone next research decision brief."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_non_iphone_next_research_decision import build_decision, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def test_decision_prioritizes_deployment_and_browser_bridge() -> None:
    decision = build_decision(Path("data/sanitized-evidence-bundle-20260630.json"))
    assert decision["public_safe"] is True
    assert decision["source_bundle_exists"] is True
    assert decision["track_count"] == 7
    assert decision["missing_evidence_ids"] == {}
    tracks = {row["id"]: row for row in decision["tracks"]}
    assert decision["tracks"][0]["id"] == "aws-s2n-nlb-live-forwarding"
    assert tracks["aws-s2n-nlb-live-forwarding"]["can_run_now"] is False
    assert "invalid_client_token" in tracks["aws-s2n-nlb-live-forwarding"]["blocker"]
    assert "non-iphone-gate-rerun-20260701" in tracks["aws-s2n-nlb-live-forwarding"]["supporting_evidence_found"]
    assert tracks["chrome-controlled-public-workloads"]["rank"] == 2
    assert tracks["chrome-controlled-public-workloads"]["current_state"] == "local_controls_pass_public_bridge_gap_origin_and_desktop_path_blocked"
    assert "user-provided-public-origin-readiness" in tracks["chrome-controlled-public-workloads"]["supporting_evidence_found"]
    assert "controlled-public-chrome-bridge-synthesis" in tracks["chrome-controlled-public-workloads"]["supporting_evidence_found"]
    assert "controlled-public-chrome-artifact-classifier-contract" in tracks["chrome-controlled-public-workloads"]["supporting_evidence_found"]
    assert "controlled-public-chrome-contract-application-audit" in tracks["chrome-controlled-public-workloads"]["supporting_evidence_found"]
    assert "chrome-desktop-noniphone-musiclike-local-refresh" in tracks["chrome-controlled-public-workloads"]["supporting_evidence_found"]
    assert "chrome-desktop-noniphone-buffered-media-local-refresh" in tracks["chrome-controlled-public-workloads"]["supporting_evidence_found"]
    assert "noniphone-workload-qoe-synthesis" in tracks["chrome-controlled-public-workloads"]["supporting_evidence_found"]
    assert "controlled-public-origin-workload-deploy-packet" in tracks["chrome-controlled-public-workloads"]["supporting_evidence_found"]
    assert "noniphone-desktop-path-change-readiness" in tracks["chrome-controlled-public-workloads"]["supporting_evidence_found"]
    assert "noniphone-public-workload-trial-packet" in tracks["chrome-controlled-public-workloads"]["supporting_evidence_found"]
    assert "chrome-desktop-noniphone-upload-local-refresh" in tracks["chrome-controlled-public-workloads"]["supporting_evidence_found"]
    assert tracks["firefox-desktop-runtime-trial"]["rank"] == 3
    assert tracks["firefox-desktop-runtime-trial"]["current_state"] == "trial_packet_ready_binary_and_path_blocked"
    assert "firefox-neqo-browser-boundary-audit" in tracks["firefox-desktop-runtime-trial"]["supporting_evidence_found"]
    assert "firefox-desktop-runtime-trial-packet" in tracks["firefox-desktop-runtime-trial"]["supporting_evidence_found"]
    assert tracks["safari-desktop-baseline"]["current_state"] == "binary_ready_session_blocked"


def test_markdown_is_public_safe_and_names_claim_boundaries() -> None:
    markdown = emit_markdown(build_decision(Path("data/sanitized-evidence-bundle-20260630.json")))
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "deployment/browser bridge" in markdown
    assert "PASS_FEASIBILITY" in markdown
    assert "Do not keep expanding generic implementation survey now" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    decision = build_decision(Path("data/sanitized-evidence-bundle-20260630.json"))
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "decision.md"
        jout = Path(tmpdir) / "decision.json"
        write_outputs(out, jout, decision)
        assert out.read_text(encoding="utf-8").startswith("# Non-iPhone Next Research Decision Brief")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["track_count"] == decision["track_count"]


def main() -> int:
    test_decision_prioritizes_deployment_and_browser_bridge()
    test_markdown_is_public_safe_and_names_claim_boundaries()
    test_outputs_are_valid_json_and_markdown()
    print("build_non_iphone_next_research_decision=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
