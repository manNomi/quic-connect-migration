#!/usr/bin/env python3
"""Regression tests for the non-iPhone professor decision packet."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_noniphone_professor_decision_packet import build_packet, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
    "i18" + "nexus",
]


def test_packet_extracts_professor_decisions() -> None:
    packet = build_packet(
        Path("data/noniphone-claim-readiness-dashboard-20260701.json"),
        Path("data/non-iphone-next-research-decision-20260630.json"),
        Path("data/non-iphone-gate-rerun-20260701.json"),
    )
    assert packet["public_safe"] is True
    assert packet["executive_summary"]["allowed_claim_count"] == 5
    assert packet["executive_summary"]["blocked_claim_count"] == 3
    assert packet["executive_summary"]["controlled_public_strong_cm_success_count"] == 0
    assert packet["blocked_summary"]["chrome_public_cm_success"]["blocked"] is True
    assert packet["blocked_summary"]["aws_s2n_live_success"]["blocked"] is True
    assert packet["blocked_summary"]["safari_handover_success"]["blocked"] is True
    decisions = {row["id"]: row for row in packet["meeting_decisions"]}
    assert decisions["scope_gap_paper"]["recommendation"] == "recommended"
    assert decisions["open_aws_s2n_path"]["recommendation"] == "conditional_high_value"
    assert len(packet["professor_questions"]) == 4
    assert len(packet["do_not_say"]) == 5


def test_markdown_is_public_safe_and_korean_decision_ready() -> None:
    packet = build_packet(
        Path("data/noniphone-claim-readiness-dashboard-20260701.json"),
        Path("data/non-iphone-next-research-decision-20260630.json"),
        Path("data/non-iphone-gate-rerun-20260701.json"),
    )
    markdown = emit_markdown(packet)
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "한 문장 결론" in markdown
    assert "교수님께 받을 Decision" in markdown
    assert "말하면 안 되는 문장" in markdown
    assert "Chrome public-origin single-session Connection Migration 성공을 주장하지 않는다" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    packet = build_packet(
        Path("data/noniphone-claim-readiness-dashboard-20260701.json"),
        Path("data/non-iphone-next-research-decision-20260630.json"),
        Path("data/non-iphone-gate-rerun-20260701.json"),
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "packet.md"
        jout = Path(tmpdir) / "packet.json"
        write_outputs(out, jout, packet)
        assert out.read_text(encoding="utf-8").startswith("# non-iPhone Professor Decision Packet")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["executive_summary"]["blocked_claim_count"] == 3


def main() -> int:
    test_packet_extracts_professor_decisions()
    test_markdown_is_public_safe_and_korean_decision_ready()
    test_outputs_are_valid_json_and_markdown()
    print("build_noniphone_professor_decision_packet=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
