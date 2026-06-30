#!/usr/bin/env python3
"""Regression tests for the Firefox/Neqo browser boundary audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_firefox_neqo_browser_boundary_audit import build_audit, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def test_audit_separates_neqo_transport_from_firefox_runtime() -> None:
    audit = build_audit()
    summary = audit["summary"]
    assert audit["public_safe"] is True
    assert audit["implementation"] == "Neqo"
    assert audit["browser_runtime"] == "Firefox"
    assert summary["firefox_adjacency_supported"] == "yes"
    assert summary["transport_migration_api_present"] == "yes"
    assert summary["passive_rebinding_handling_present"] == "yes"
    assert summary["local_neqo_transport_migration_rerun"] == "53_passed_0_failed_recorded_20260630"
    assert summary["firefox_browser_runtime_handover_proven_by_this_audit"] == "no"
    assert summary["firefox_browser_runtime_rows_in_current_study"] == "absent"


def test_evidence_table_has_source_tests_and_firefox_adjacency() -> None:
    audit = build_audit()
    ids = {item["id"] for item in audit["evidence"]}
    assert "neqo-firefox-implementation-claim" in ids
    assert "neqo-firefox-version-linkage" in ids
    assert "neqo-firefox-local-server-recipe" in ids
    assert "neqo-migrate-api" in ids
    assert "neqo-peer-migration-handler" in ids
    assert "neqo-path-probe-and-primary-selection" in ids
    assert "neqo-path-response-validation" in ids
    assert "neqo-qlog-transport-parameters" in ids
    assert "neqo-rebinding-tests" in ids
    assert "neqo-graceful-migration-test" in ids
    assert "neqo-preferred-address-test" in ids
    assert "neqo-disable-migration-test" in ids
    assert "neqo-pmtud-migration-test" in ids
    assert "neqo-ecn-migration-test" in ids
    for item in audit["evidence"]:
        assert item["url"].startswith("https://")
        assert item["observation"]
        assert item["implication"]


def test_markdown_is_public_safe_and_names_boundary() -> None:
    markdown = emit_markdown(build_audit())
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Safe claim" in markdown
    assert "Unsafe claim" in markdown
    assert "Firefox browser runtime handover proven here" in markdown
    assert "Neqo transport tests are not the same as a Firefox browser network-change experiment" in markdown


def test_outputs_are_valid_markdown_and_json() -> None:
    audit = build_audit()
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "audit.md"
        jout = Path(tmpdir) / "audit.json"
        write_outputs(out, jout, audit)
        assert out.read_text(encoding="utf-8").startswith("# Firefox/Neqo Browser Boundary Audit")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["summary"]["evidence_items"] >= 15
        assert parsed["reporting_boundary"]["unsafe_claim"]


def main() -> int:
    test_audit_separates_neqo_transport_from_firefox_runtime()
    test_evidence_table_has_source_tests_and_firefox_adjacency()
    test_markdown_is_public_safe_and_names_boundary()
    test_outputs_are_valid_markdown_and_json()
    print("build_firefox_neqo_browser_boundary_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
