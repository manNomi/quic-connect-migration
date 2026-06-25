#!/usr/bin/env python3
"""Regression tests for the reproducibility manifest builder."""

from __future__ import annotations

from datetime import datetime, timezone

from build_reproducibility_manifest import build_manifest, emit_markdown
from research_clock import utc_date_iso


def test_manifest_contains_core_public_safe_fields() -> None:
    manifest = build_manifest(include_ci=False)
    markdown = emit_markdown(manifest)
    assert manifest["public_safe"] is True
    assert manifest["experiment_corpus"]["total_trials"] >= 1
    assert "verification" in manifest
    assert "research_audit" in manifest
    assert "final_browser_handover_trials" in manifest["research_audit"]
    assert "PRIVATE KEY" not in markdown
    assert "AWS_SECRET" not in markdown
    assert "AKIA" not in markdown


def test_manifest_points_to_authoritative_artifacts() -> None:
    manifest = build_manifest(include_ci=False)
    paths = manifest["key_paths"]
    assert paths["audit"].endswith("research-bundle-audit-20260624.md")
    assert paths["verification"].endswith("research-verification-report-20260624.md")
    assert paths["trial_packet"].endswith("final-handover-trial-packet-20260624.md")
    assert paths["artifact_cleanup_execution_log"].endswith("artifact-cleanup-execution-log-20260625.md")
    assert paths["controlled_public_package_smoke"].endswith("controlled-public-package-smoke-20260625.md")


def test_generated_date_uses_utc_day() -> None:
    assert utc_date_iso() == datetime.now(timezone.utc).date().isoformat()


def main() -> int:
    test_manifest_contains_core_public_safe_fields()
    test_manifest_points_to_authoritative_artifacts()
    test_generated_date_uses_utc_day()
    print("build_reproducibility_manifest=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
