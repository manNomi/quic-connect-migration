#!/usr/bin/env python3
"""Regression tests for the non-iPhone reviewer risk audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_noniphone_reviewer_risk_audit import build_audit, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
    "i18" + "nexus",
]


def test_audit_names_critical_reviewer_risks() -> None:
    audit = build_audit(
        Path("data/noniphone-claim-readiness-dashboard-20260701.json"),
        Path("data/noniphone-professor-decision-packet-20260701.json"),
    )
    assert audit["public_safe"] is True
    assert audit["summary"]["risk_count"] == 9
    assert audit["summary"]["critical_count"] == 2
    assert audit["summary"]["high_count"] == 4
    assert "guarantee_overclaim" in audit["summary"]["critical_risks"]
    assert "public_positive_absence" in audit["summary"]["critical_risks"]
    risks = {row["id"]: row for row in audit["risks"]}
    assert risks["local_rebinding_external_validity"]["severity"] == "high"
    assert risks["aws_s2n_scope_confusion"]["severity"] == "high"
    assert "maturity/gap analysis" in audit["summary"]["audit_decision"]


def test_markdown_is_public_safe_and_reviewer_ready() -> None:
    markdown = emit_markdown(
        build_audit(
            Path("data/noniphone-claim-readiness-dashboard-20260701.json"),
            Path("data/noniphone-professor-decision-packet-20260701.json"),
        )
    )
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Reviewer-Safe Paper Posture" in markdown
    assert "HTTP/3 Connection Migration guarantees seamless work continuity" in markdown
    assert "We evaluate where QUIC/HTTP/3 migration primitives" in markdown
    assert "positive browser/AWS claims require opening external gates" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    audit = build_audit(
        Path("data/noniphone-claim-readiness-dashboard-20260701.json"),
        Path("data/noniphone-professor-decision-packet-20260701.json"),
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "risk.md"
        jout = Path(tmpdir) / "risk.json"
        write_outputs(out, jout, audit)
        assert out.read_text(encoding="utf-8").startswith("# non-iPhone Reviewer Risk")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["risk_count"] == 9


def main() -> int:
    test_audit_names_critical_reviewer_risks()
    test_markdown_is_public_safe_and_reviewer_ready()
    test_outputs_are_valid_json_and_markdown()
    print("build_noniphone_reviewer_risk_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
