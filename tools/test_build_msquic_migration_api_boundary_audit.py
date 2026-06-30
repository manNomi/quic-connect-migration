#!/usr/bin/env python3
"""Regression tests for the MsQuic migration API boundary audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_msquic_migration_api_boundary_audit import build_audit, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def test_audit_separates_migration_support_from_quic_go_api_shape() -> None:
    audit = build_audit(Path("missing-msquic-clone"))
    assert audit["public_safe"] is True
    assert audit["implementation"] == "MsQuic"
    assert audit["summary"]["migration_enabled_default"] == "TRUE"
    assert audit["summary"]["load_balancing_default"] == "QUIC_LOAD_BALANCING_DISABLED"
    assert audit["summary"]["nat_rebinding_tests_present"] == "yes"
    assert audit["summary"]["quic_go_style_addpath_probe_switch_public_api"] == "not_established_by_public_header_scan"
    assert "quic-go" in audit["summary"]["interpretation"]
    assert "Unsafe claim" not in emit_markdown(audit).split("## Summary", 1)[1].split("## Conclusion", 1)[0]


def test_evidence_table_contains_public_links_and_required_topics() -> None:
    audit = build_audit(Path("missing-msquic-clone"))
    ids = {item["id"] for item in audit["evidence"]}
    assert "migration-setting-public-api" in ids
    assert "settings-doc-migration-lb-boundary" in ids
    assert "local-address-connection-param" in ids
    assert "local-address-set-state-check" in ids
    assert "peer-address-changed-event-api" in ids
    assert "nat-port-rebind-test" in ids
    assert "nat-address-rebind-test" in ids
    for item in audit["evidence"]:
        assert item["url"].startswith("https://github.com/microsoft/msquic/blob/")
        assert item["observation"]
        assert item["implication"]


def test_markdown_is_public_safe_and_names_boundaries() -> None:
    markdown = emit_markdown(build_audit(Path("missing-msquic-clone")))
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Safe claim" in markdown
    assert "Unsafe claim" in markdown
    assert "deployment friction" in markdown
    assert "same direct application-triggered active migration API shape as quic-go" in markdown


def test_outputs_are_valid_markdown_and_json() -> None:
    audit = build_audit(Path("missing-msquic-clone"))
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "audit.md"
        jout = Path(tmpdir) / "audit.json"
        write_outputs(out, jout, audit)
        assert out.read_text(encoding="utf-8").startswith("# MsQuic Migration API Boundary Audit")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["evidence_items"] >= 10
        assert parsed["reporting_boundary"]["unsafe_claim"]


def main() -> int:
    test_audit_separates_migration_support_from_quic_go_api_shape()
    test_evidence_table_contains_public_links_and_required_topics()
    test_markdown_is_public_safe_and_names_boundaries()
    test_outputs_are_valid_markdown_and_json()
    print("build_msquic_migration_api_boundary_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
