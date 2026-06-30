#!/usr/bin/env python3
"""Regression tests for the non-iPhone paper wording guard."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_noniphone_paper_wording_guard import build_guard, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
    "i18" + "nexus",
]


def test_guard_covers_paper_sections_and_risks() -> None:
    guard = build_guard(
        Path("data/noniphone-reviewer-risk-audit-20260701.json"),
        Path("data/noniphone-claim-readiness-dashboard-20260701.json"),
    )
    assert guard["public_safe"] is True
    assert guard["summary"]["rule_count"] == 9
    assert guard["summary"]["missing_risk_ids"] == {}
    assert "abstract" in guard["summary"]["sections"]
    assert "limitations" in guard["summary"]["sections"]
    assert "guarantee_overclaim" in guard["summary"]["critical_risks"]
    assert guard["summary"]["allowed_claim_count"] == 5
    assert guard["summary"]["blocked_claim_count"] == 3
    rules = {(row["section"], row["avoid"]): row for row in guard["rules"]}
    abstract_rule = rules[("abstract", "HTTP/3 Connection Migration guarantees seamless task continuity under unstable mobile networks.")]
    assert "assesses" in abstract_rule["use_en"]
    assert "평가한다" in abstract_rule["use_ko"]


def test_markdown_is_public_safe_and_bilingual() -> None:
    markdown = emit_markdown(
        build_guard(
            Path("data/noniphone-reviewer-risk-audit-20260701.json"),
            Path("data/noniphone-claim-readiness-dashboard-20260701.json"),
        )
    )
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "use EN" in markdown
    assert "use KO" in markdown
    assert "Avoid guarantee, prove, validated, seamless, and works" in markdown
    assert "public Chrome, AWS+s2n, and Safari claims" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    guard = build_guard(
        Path("data/noniphone-reviewer-risk-audit-20260701.json"),
        Path("data/noniphone-claim-readiness-dashboard-20260701.json"),
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "guard.md"
        jout = Path(tmpdir) / "guard.json"
        write_outputs(out, jout, guard)
        assert out.read_text(encoding="utf-8").startswith("# non-iPhone Paper Wording Guard")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["rule_count"] == 9


def main() -> int:
    test_guard_covers_paper_sections_and_risks()
    test_markdown_is_public_safe_and_bilingual()
    test_outputs_are_valid_json_and_markdown()
    print("build_noniphone_paper_wording_guard=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
