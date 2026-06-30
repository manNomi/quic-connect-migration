#!/usr/bin/env python3
"""Regression tests for the non-iPhone paper section scaffold."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_noniphone_paper_section_scaffold import build_scaffold, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
    "i18" + "nexus",
]


def test_scaffold_maps_evidence_to_paper_sections() -> None:
    scaffold = build_scaffold(
        Path("data/sanitized-evidence-bundle-20260630.json"),
        Path("data/noniphone-paper-wording-guard-20260701.json"),
    )
    assert scaffold["public_safe"] is True
    assert scaffold["summary"]["section_count"] == 9
    assert scaffold["summary"]["missing_evidence_ids"] == {}
    assert scaffold["summary"]["missing_wording_sections"] == {}
    assert "Abstract" in scaffold["summary"]["paper_sections"]
    assert "Results" in scaffold["summary"]["paper_sections"]
    rows = {row["id"]: row for row in scaffold["sections"]}
    assert "noniphone-paper-wording-guard" in rows["abstract_positioning"]["evidence_ids"]
    assert "controlled-public-chrome-bridge-synthesis" in rows["method_public_cm_acceptance"]["evidence_ids"]
    assert "controlled-public-chrome-artifact-classifier-contract" in rows["method_public_cm_acceptance"]["evidence_ids"]
    assert rows["limitations_future_work"]["section"] == "Limitations"


def test_markdown_is_public_safe_and_drafting_ready() -> None:
    markdown = emit_markdown(
        build_scaffold(
            Path("data/sanitized-evidence-bundle-20260630.json"),
            Path("data/noniphone-paper-wording-guard-20260701.json"),
        )
    )
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Drafting Order" in markdown
    assert "conservative maturity/gap paper" in markdown
    assert "implementation, deployment, browser workload, and streaming/QoE results" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    scaffold = build_scaffold(
        Path("data/sanitized-evidence-bundle-20260630.json"),
        Path("data/noniphone-paper-wording-guard-20260701.json"),
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "scaffold.md"
        jout = Path(tmpdir) / "scaffold.json"
        write_outputs(out, jout, scaffold)
        assert out.read_text(encoding="utf-8").startswith("# non-iPhone Paper Section Scaffold")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["section_count"] == 9


def main() -> int:
    test_scaffold_maps_evidence_to_paper_sections()
    test_markdown_is_public_safe_and_drafting_ready()
    test_outputs_are_valid_json_and_markdown()
    print("build_noniphone_paper_section_scaffold=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
