#!/usr/bin/env python3
"""Regression tests for the Quinn migration API boundary audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_quinn_migration_api_boundary_audit import build_audit, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def test_audit_has_source_linked_claim_boundaries() -> None:
    audit = build_audit(Path("/private/tmp/quic-cm-scan-repos/quinn"))
    assert audit["public_safe"] is True
    assert audit["implementation"] == "Quinn"
    assert audit["evidence_item_count"] >= 18
    assert audit["summary"]["endpoint_rebind_api"] == "present_endpoint_wide"
    assert audit["summary"]["quic_go_style_addpath_probe_switch"] == "not_established"
    assert "endpoint_wide_socket_rebind" in audit["conclusion"]["api_boundary"]
    ids = {item["evidence_id"] for item in audit["evidence"]}
    assert "endpoint-rebind-api" in ids
    assert "runtime-rebind-receive-test" in ids
    assert "proto-migration-test" in ids
    assert "local-address-changed-hook" in ids


def test_missing_clone_is_public_safe_and_still_emits_source_audit() -> None:
    audit = build_audit(Path("/tmp/definitely-missing-quinn-clone"))
    assert audit["local_clone"]["observed"] is False
    assert audit["local_clone"]["matches_expected_commit"] == "no"
    assert audit["source_commit"]
    assert audit["evidence_item_count"] >= 18


def test_markdown_is_public_safe_and_names_do_not_claim_boundary() -> None:
    markdown = emit_markdown(build_audit(Path("/tmp/definitely-missing-quinn-clone")))
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Safe claim" in markdown
    assert "Unsafe claim" in markdown
    assert "Endpoint::rebind" in markdown
    assert "AddPath/Probe/Switch" in markdown
    assert "browser/deployment workload continuity" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    audit = build_audit(Path("/tmp/definitely-missing-quinn-clone"))
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "audit.md"
        jout = Path(tmpdir) / "audit.json"
        write_outputs(out, jout, audit)
        assert out.read_text(encoding="utf-8").startswith("# Quinn Migration API Boundary Audit")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["implementation"] == "Quinn"


def main() -> int:
    test_audit_has_source_linked_claim_boundaries()
    test_missing_clone_is_public_safe_and_still_emits_source_audit()
    test_markdown_is_public_safe_and_names_do_not_claim_boundary()
    test_outputs_are_valid_json_and_markdown()
    print("build_quinn_migration_api_boundary_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
