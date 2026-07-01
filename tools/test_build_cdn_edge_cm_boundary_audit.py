#!/usr/bin/env python3
"""Regression tests for the CDN edge CM boundary audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_cdn_edge_cm_boundary_audit import build_audit, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def test_audit_separates_viewer_edge_from_origin_end_to_end() -> None:
    audit = build_audit()
    summary = audit["summary"]
    assert audit["public_safe"] is True
    assert "AWS CloudFront" in audit["implementations"]
    assert summary["cloudfront_viewer_edge_http3_cm"] == "supported_by_official_docs"
    assert summary["cloudfront_origin_end_to_end_quic_cm"] == "not_established_by_official_docs"
    assert summary["cloudflare_origin_http3"] == "not_supported_in_inspected_official_doc"
    assert summary["live_edge_trial_completed"] == "no"
    assert "viewer-to-edge" in summary["interpretation"]


def test_evidence_table_has_cloudfront_and_cloudflare_boundaries() -> None:
    audit = build_audit()
    ids = {item["id"] for item in audit["evidence"]}
    assert "cloudfront-viewer-supported-http-versions" in ids
    assert "cloudfront-api-httpversion-viewer-scope" in ids
    assert "cloudfront-origin-fetch-boundary" in ids
    assert "cloudfront-no-origin-change-enable" in ids
    assert "cloudflare-user-edge-scope" in ids
    assert "cloudflare-dashboard-api-toggle" in ids
    for item in audit["evidence"]:
        assert item["url"].startswith("https://")
        assert item["observation"]
        assert item["implication"]


def test_markdown_is_public_safe_and_names_boundaries() -> None:
    markdown = emit_markdown(build_audit())
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Safe claim" in markdown
    assert "Unsafe claim" in markdown
    assert "end-to-end origin QUIC Connection Migration" in markdown
    assert "viewer-edge" in markdown


def test_outputs_are_valid_markdown_and_json() -> None:
    audit = build_audit()
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "audit.md"
        jout = Path(tmpdir) / "audit.json"
        write_outputs(out, jout, audit)
        assert out.read_text(encoding="utf-8").startswith("# CDN Edge Connection Migration Boundary Audit")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["evidence_items"] >= 6
        assert parsed["reporting_boundary"]["unsafe_claim"]


def main() -> int:
    test_audit_separates_viewer_edge_from_origin_end_to_end()
    test_evidence_table_has_cloudfront_and_cloudflare_boundaries()
    test_markdown_is_public_safe_and_names_boundaries()
    test_outputs_are_valid_markdown_and_json()
    print("build_cdn_edge_cm_boundary_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
