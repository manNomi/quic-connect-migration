#!/usr/bin/env python3
"""Regression tests for the Chromium/Cronet policy boundary audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_chromium_cronet_policy_boundary_audit import build_audit, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def test_audit_separates_source_support_from_browser_handover() -> None:
    audit = build_audit()
    summary = audit["summary"]
    assert audit["public_safe"] is True
    assert audit["implementation"] == "Chromium Chrome Cronet"
    assert summary["client_socket_migration_hook_present"] == "yes"
    assert summary["network_change_policy_knobs_present"] == "yes"
    assert summary["netlog_migration_observability_present"] == "yes"
    assert summary["cronet_network_change_migration_default"] == "disabled_when_quic_enabled"
    assert summary["browser_runtime_handover_proven_by_this_audit"] == "no"
    assert "implementation-absence" in summary["interpretation"]


def test_evidence_table_has_required_chromium_and_android_policy_sources() -> None:
    audit = build_audit()
    ids = {item["id"] for item in audit["evidence"]}
    assert "quicparams-default-network-migration-policy" in ids
    assert "client-session-migrate-to-socket" in ids
    assert "client-session-disconnected-default-callbacks" in ids
    assert "netlog-migration-mode-trigger" in ids
    assert "netlog-migration-success-failure" in ids
    assert "netlog-network-change-events" in ids
    assert "cronet-explicitly-disables-network-change-migration" in ids
    assert "android-cronet-connection-migration-options" in ids
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
    assert "single-session HTTP/3 Connection Migration" in markdown
    assert "source hooks alone" in markdown
    assert "Cronet network-change migration default" in markdown


def test_outputs_are_valid_markdown_and_json() -> None:
    audit = build_audit()
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "audit.md"
        jout = Path(tmpdir) / "audit.json"
        write_outputs(out, jout, audit)
        assert out.read_text(encoding="utf-8").startswith("# Chromium/Cronet Policy Boundary Audit")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["evidence_items"] >= 12
        assert parsed["reporting_boundary"]["unsafe_claim"]


def main() -> int:
    test_audit_separates_source_support_from_browser_handover()
    test_evidence_table_has_required_chromium_and_android_policy_sources()
    test_markdown_is_public_safe_and_names_boundaries()
    test_outputs_are_valid_markdown_and_json()
    print("build_chromium_cronet_policy_boundary_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
