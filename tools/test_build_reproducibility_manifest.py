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
    assert "implementation_corpus" in manifest
    assert "evidence_paths_20260630" in manifest
    assert "final_browser_handover_trials" in manifest["research_audit"]
    assert manifest["implementation_corpus"]["total_implementations"] >= 18
    assert "PRIVATE KEY" not in markdown
    assert "AWS_" + "SECRET" not in markdown
    assert "AK" + "IA" not in markdown


def test_manifest_points_to_authoritative_artifacts() -> None:
    manifest = build_manifest(include_ci=False)
    paths = manifest["key_paths"]
    assert paths["audit"].endswith("research-bundle-audit-20260624.md")
    assert paths["verification"].endswith("research-verification-report-20260624.md")
    assert paths["trial_packet"].endswith("final-handover-trial-packet-20260624.md")
    assert paths["artifact_cleanup_execution_log"].endswith("artifact-cleanup-execution-log-20260625.md")
    assert paths["controlled_public_package_smoke"].endswith("controlled-public-package-smoke-20260625.md")
    assert paths["p0_baseline_preflight_redaction_smoke"].endswith("final-p0-baseline-preflight-redaction-smoke-20260625.md")


def test_manifest_points_to_current_implementation_evidence() -> None:
    manifest = build_manifest(include_ci=False)
    paths = manifest["evidence_paths_20260630"]
    assert paths["implementation_rerun_results"]["exists"] is True
    assert paths["sanitized_evidence_bundle"]["exists"] is True
    assert paths["sanitized_evidence_bundle_json"]["exists"] is True
    assert paths["openlitespeed_runtime_runner"]["exists"] is True
    assert paths["nginx_haproxy_boundary"]["exists"] is True
    assert paths["nginx_quic_bpf_readiness"]["exists"] is True
    assert paths["nginx_quic_bpf_linux_runner"]["exists"] is True
    assert paths["chrome_desktop_noniphone_media_local_refresh"]["exists"] is True
    assert paths["chrome_desktop_noniphone_media_local_refresh_csv"]["exists"] is True
    assert paths["chrome_desktop_noniphone_musiclike_local_refresh"]["exists"] is True
    assert paths["chrome_desktop_noniphone_musiclike_local_refresh_csv"]["exists"] is True
    assert paths["chrome_desktop_noniphone_buffered_media_local_refresh"]["exists"] is True
    assert paths["chrome_desktop_noniphone_buffered_media_local_refresh_csv"]["exists"] is True
    assert paths["noniphone_workload_qoe_synthesis"]["exists"] is True
    assert paths["noniphone_workload_qoe_synthesis_csv"]["exists"] is True
    assert paths["noniphone_public_workload_trial_packet"]["exists"] is True
    assert paths["noniphone_public_workload_trial_packet_json"]["exists"] is True
    assert paths["noniphone_claim_readiness_dashboard"]["exists"] is True
    assert paths["noniphone_claim_readiness_dashboard_json"]["exists"] is True
    assert paths["noniphone_professor_decision_packet"]["exists"] is True
    assert paths["noniphone_professor_decision_packet_json"]["exists"] is True
    assert paths["chrome_desktop_noniphone_range_local_refresh"]["exists"] is True
    assert paths["chrome_desktop_noniphone_range_local_refresh_csv"]["exists"] is True
    assert paths["chrome_desktop_noniphone_upload_local_refresh"]["exists"] is True
    assert paths["chrome_desktop_noniphone_upload_local_refresh_csv"]["exists"] is True
    assert paths["controlled_public_chrome_bridge_synthesis"]["exists"] is True
    assert paths["controlled_public_chrome_bridge_synthesis_json"]["exists"] is True
    assert paths["controlled_public_chrome_bridge_synthesis_csv"]["exists"] is True
    assert paths["quicly_e2e_path_migration"]["exists"] is True
    assert paths["s2n_nlb_live_readiness"]["exists"] is True
    assert paths["aws_s2n_nlb_live_runner"]["exists"] is True
    assert paths["s2n_active_migration_api_audit"]["exists"] is True
    assert paths["s2n_active_migration_api_audit_json"]["exists"] is True
    assert paths["browser_cm_observability_refresh"]["exists"] is True
    assert paths["browser_cm_observability_refresh_json"]["exists"] is True
    assert paths["safari_webdriver_session_readiness"]["exists"] is True
    assert paths["user_provided_public_origin_readiness"]["exists"] is True
    assert paths["user_provided_public_origin_readiness_json"]["exists"] is True
    assert paths["controlled_public_origin_workload_deploy_packet"]["exists"] is True
    assert paths["controlled_public_origin_workload_deploy_packet_json"]["exists"] is True
    assert paths["noniphone_desktop_path_change_readiness"]["exists"] is True
    assert paths["noniphone_desktop_path_change_readiness_json"]["exists"] is True
    assert paths["non_iphone_gate_rerun"]["exists"] is True
    assert paths["non_iphone_gate_rerun_json"]["exists"] is True
    assert paths["non_iphone_next_research_decision"]["exists"] is True
    assert paths["non_iphone_next_research_decision_json"]["exists"] is True
    assert paths["mvfst_migration_test_readiness"]["exists"] is True
    assert paths["mvfst_migration_test_readiness_json"]["exists"] is True
    assert manifest["experiment_matrix"]["latest_item"] == "noniphone-professor-decision-packet"


def test_generated_date_uses_utc_day() -> None:
    assert utc_date_iso() == datetime.now(timezone.utc).date().isoformat()


def main() -> int:
    test_manifest_contains_core_public_safe_fields()
    test_manifest_points_to_authoritative_artifacts()
    test_manifest_points_to_current_implementation_evidence()
    test_generated_date_uses_utc_day()
    print("build_reproducibility_manifest=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
