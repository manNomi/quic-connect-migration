#!/usr/bin/env python3
"""Run the safe, non-destructive verification suite for the research bundle."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    command: list[str]
    expected_exit_codes: list[int]
    exit_code: int
    duration_seconds: float
    ok: bool
    stdout_tail: str
    stderr_tail: str


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tail(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def run_check(name: str, command: list[str], expected_exit_codes: set[int], timeout: int) -> CheckResult:
    started = time.monotonic()
    env = dict(os.environ)
    env["TZ"] = "UTC"
    try:
        proc = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env=env,
        )
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = exc.stdout.decode("utf-8", errors="ignore") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="ignore") if isinstance(exc.stderr, bytes) else (exc.stderr or "timeout")
    duration = round(time.monotonic() - started, 3)
    return CheckResult(
        name=name,
        command=command,
        expected_exit_codes=sorted(expected_exit_codes),
        exit_code=exit_code,
        duration_seconds=duration,
        ok=exit_code in expected_exit_codes,
        stdout_tail=tail(stdout.strip()),
        stderr_tail=tail(stderr.strip()),
    )


def default_checks(python_bin: str, generated_dir: Path | None = None) -> list[tuple[str, list[str], set[int], int]]:
    paper_tables = "docs/results/paper-tables-20260624.md"
    application_recovery_tradeoff = "docs/results/application-recovery-tradeoff-20260624.md"
    application_recovery_tradeoff_csv = "data/application-recovery-tradeoff-20260624.csv"
    downlink_recovery_comparison = "docs/results/downlink-recovery-comparison-20260624.md"
    downlink_recovery_comparison_csv = "data/downlink-recovery-comparison-20260624.csv"
    workload_transition_zone = "docs/results/workload-transition-zone-synthesis-20260624.md"
    workload_transition_zone_csv = "data/workload-transition-zone-synthesis-20260624.csv"
    replication_sufficiency_audit = "docs/results/replication-sufficiency-audit-20260624.md"
    replication_sufficiency_audit_csv = "data/replication-sufficiency-audit-20260624.csv"
    replication_sufficiency_audit_input = "data/replication-sufficiency-audit-20260624.csv"
    paper_gap_register = "docs/results/paper-evidence-gap-register-20260624.md"
    paper_gap_register_csv = "data/paper-evidence-gap-register-20260624.csv"
    paper_claim_support_matrix = "docs/results/paper-claim-support-matrix-20260624.md"
    paper_claim_support_matrix_csv = "data/paper-claim-support-matrix-20260624.csv"
    paper_claim_support_matrix_input = "data/paper-claim-support-matrix-20260624.csv"
    cm_operational_friction_matrix = "docs/results/cm-operational-friction-matrix-20260624.md"
    cm_operational_friction_matrix_csv = "data/cm-operational-friction-matrix-20260624.csv"
    final_trial_acceptance_scorecard = "docs/results/final-trial-acceptance-scorecard-20260624.md"
    final_trial_acceptance_scorecard_csv = "data/final-trial-acceptance-scorecard-20260624.csv"
    final_protocol_readiness_matrix = "docs/results/final-protocol-readiness-matrix-20260624.md"
    final_protocol_readiness_matrix_csv = "data/final-protocol-readiness-matrix-20260624.csv"
    research_status_dashboard = "docs/results/research-status-dashboard-20260624.md"
    research_status_dashboard_json = "data/research-status-dashboard-20260624.json"
    final_trials = "docs/results/final-browser-handover-trial-audit-20260624.md"
    final_readiness = "docs/results/final-browser-handover-readiness-20260624.md"
    final_run_plan = "docs/results/final-browser-handover-run-plan-20260624.md"
    final_next_trial = "docs/results/final-handover-next-trial-20260624.md"
    final_next_trial_readiness = "docs/results/final-handover-next-trial-readiness-20260624.md"
    final_operator_checklist = "docs/results/final-handover-operator-checklist-20260624.md"
    final_external_inputs = "docs/results/final-handover-external-inputs-20260624.md"
    final_trial_packet = "docs/results/final-handover-trial-packet-20260624.md"
    final_trial_artifact_bundle = "docs/results/final-handover-trial-artifact-bundle-check-20260624.md"
    controlled_public_origin_deploy_packet = "docs/results/controlled-public-origin-deploy-packet-20260624.md"
    reproducibility_manifest = "docs/results/reproducibility-manifest-20260624.md"
    reproducibility_manifest_json = "data/reproducibility-manifest-20260624.json"
    controlled_public_config = "docs/results/controlled-public-config-check-20260624.md"
    controlled_public_config_worksheet = "docs/results/controlled-public-config-worksheet-20260624.md"
    controlled_public_baseline_unlock = "docs/results/controlled-public-baseline-unlock-check-20260624.md"
    storage_report = "docs/results/artifact-storage-report-20260624.md"
    cleanup_dry_run = "docs/results/artifact-cleanup-dry-run-20260624.md"
    cleanup_safety = "docs/results/artifact-cleanup-safety-audit-20260624.md"
    research_audit = "docs/results/research-bundle-audit-20260624.md"
    if generated_dir is not None:
        paper_tables = str(generated_dir / "paper-tables.md")
        application_recovery_tradeoff = str(generated_dir / "application-recovery-tradeoff.md")
        application_recovery_tradeoff_csv = str(generated_dir / "application-recovery-tradeoff.csv")
        downlink_recovery_comparison = str(generated_dir / "downlink-recovery-comparison.md")
        downlink_recovery_comparison_csv = str(generated_dir / "downlink-recovery-comparison.csv")
        workload_transition_zone = str(generated_dir / "workload-transition-zone-synthesis.md")
        workload_transition_zone_csv = str(generated_dir / "workload-transition-zone-synthesis.csv")
        replication_sufficiency_audit = str(generated_dir / "replication-sufficiency-audit.md")
        replication_sufficiency_audit_csv = str(generated_dir / "replication-sufficiency-audit.csv")
        replication_sufficiency_audit_input = replication_sufficiency_audit_csv
        paper_gap_register = str(generated_dir / "paper-evidence-gap-register.md")
        paper_gap_register_csv = str(generated_dir / "paper-evidence-gap-register.csv")
        paper_claim_support_matrix = str(generated_dir / "paper-claim-support-matrix.md")
        paper_claim_support_matrix_csv = str(generated_dir / "paper-claim-support-matrix.csv")
        paper_claim_support_matrix_input = paper_claim_support_matrix_csv
        cm_operational_friction_matrix = str(generated_dir / "cm-operational-friction-matrix.md")
        cm_operational_friction_matrix_csv = str(generated_dir / "cm-operational-friction-matrix.csv")
        final_trial_acceptance_scorecard = str(generated_dir / "final-trial-acceptance-scorecard.md")
        final_trial_acceptance_scorecard_csv = str(generated_dir / "final-trial-acceptance-scorecard.csv")
        final_protocol_readiness_matrix = str(generated_dir / "final-protocol-readiness-matrix.md")
        final_protocol_readiness_matrix_csv = str(generated_dir / "final-protocol-readiness-matrix.csv")
        research_status_dashboard = str(generated_dir / "research-status-dashboard.md")
        research_status_dashboard_json = str(generated_dir / "research-status-dashboard.json")
        final_trials = str(generated_dir / "final-browser-handover-trial-audit.md")
        final_readiness = str(generated_dir / "final-browser-handover-readiness.md")
        final_run_plan = str(generated_dir / "final-browser-handover-run-plan.md")
        final_next_trial = str(generated_dir / "final-handover-next-trial.md")
        final_next_trial_readiness = str(generated_dir / "final-handover-next-trial-readiness.md")
        final_operator_checklist = str(generated_dir / "final-handover-operator-checklist.md")
        final_external_inputs = str(generated_dir / "final-handover-external-inputs.md")
        final_trial_packet = str(generated_dir / "final-handover-trial-packet.md")
        final_trial_artifact_bundle = str(generated_dir / "final-handover-trial-artifact-bundle-check.md")
        controlled_public_origin_deploy_packet = str(generated_dir / "controlled-public-origin-deploy-packet.md")
        reproducibility_manifest = str(generated_dir / "reproducibility-manifest.md")
        reproducibility_manifest_json = str(generated_dir / "reproducibility-manifest.json")
        controlled_public_config = str(generated_dir / "controlled-public-config-check.md")
        controlled_public_config_worksheet = str(generated_dir / "controlled-public-config-worksheet.md")
        controlled_public_baseline_unlock = str(generated_dir / "controlled-public-baseline-unlock-check.md")
        storage_report = str(generated_dir / "artifact-storage-report.md")
        cleanup_dry_run = str(generated_dir / "artifact-cleanup-dry-run.md")
        cleanup_safety = str(generated_dir / "artifact-cleanup-safety-audit.md")
        research_audit = str(generated_dir / "research-bundle-audit.md")

    return [
        (
            "python_compile_core_tools",
            [
                python_bin,
                "-m",
                "py_compile",
                "tools/audit_final_browser_handover_trials.py",
                "tools/audit_artifact_cleanup_safety.py",
                "tools/audit_research_bundle.py",
                "tools/append_final_handover_result_row.py",
                "tools/build_application_recovery_tradeoff.py",
                "tools/build_downlink_recovery_comparison.py",
                "tools/build_final_handover_operator_checklist.py",
                "tools/build_final_handover_trial_packet.py",
                "tools/build_final_trial_acceptance_scorecard.py",
                "tools/build_final_protocol_readiness_matrix.py",
                "tools/build_research_status_dashboard.py",
                "tools/build_workload_transition_zone_table.py",
                "tools/build_replication_sufficiency_audit.py",
                "tools/build_cm_operational_friction_matrix.py",
                "tools/build_controlled_public_config_worksheet.py",
                "tools/build_controlled_public_origin_deploy_packet.py",
                "tools/build_paper_evidence_gap_register.py",
                "tools/build_paper_claim_support_matrix.py",
                "tools/build_reproducibility_manifest.py",
                "tools/build_final_handover_external_inputs.py",
                "tools/check_controlled_public_config.py",
                "tools/check_final_browser_handover_readiness.py",
                "tools/check_final_handover_trial_artifact_bundle.py",
                "tools/check_next_final_handover_trial_readiness.py",
                "tools/check_controlled_public_baseline_unlock.py",
                "tools/classify_chrome_h3_artifacts.py",
                "tools/classify_controlled_public_h3_network_change.py",
                "tools/compare_android_path_snapshots.py",
                "tools/draft_final_handover_result_row.py",
                "tools/plan_artifact_cleanup.py",
                "tools/plan_final_browser_handover_runs.py",
                "tools/select_next_final_handover_trial.py",
                "tools/summarize_chrome_rebinding_proxy_matrix.py",
                "tools/summarize_chrome_rebinding_upload_matrix.py",
                "tools/summarize_chrome_rebinding_timing_sensitivity.py",
                "tools/summarize_chrome_rebinding_old_path_drop.py",
                "tools/summarize_chrome_rebinding_stress_matrix.py",
                "tools/summarize_chrome_rebinding_return_path_drop_controls.py",
                "tools/summarize_chrome_rebinding_transient_return_path_sweep.py",
                "tools/summarize_quic_go_h3_midflight_matrix.py",
                "tools/validate_final_handover_trial_artifact.py",
                "tools/test_append_final_handover_result_row.py",
                "tools/test_artifact_disk_guard.py",
                "tools/test_audit_artifact_cleanup_safety.py",
                "tools/test_build_final_handover_operator_checklist.py",
                "tools/test_build_final_handover_trial_packet.py",
                "tools/test_build_final_trial_acceptance_scorecard.py",
                "tools/test_build_final_protocol_readiness_matrix.py",
                "tools/test_build_research_status_dashboard.py",
                "tools/test_build_replication_sufficiency_audit.py",
                "tools/test_build_cm_operational_friction_matrix.py",
                "tools/test_build_controlled_public_config_worksheet.py",
                "tools/test_build_controlled_public_origin_deploy_packet.py",
                "tools/test_build_paper_evidence_gap_register.py",
                "tools/test_build_paper_claim_support_matrix.py",
                "tools/test_build_reproducibility_manifest.py",
                "tools/test_build_final_handover_external_inputs.py",
                "tools/test_check_controlled_public_config.py",
                "tools/test_check_controlled_public_baseline_unlock.py",
                "tools/test_check_final_handover_trial_artifact_bundle.py",
                "tools/test_check_next_final_handover_trial_readiness.py",
                "tools/test_classify_chrome_h3_artifacts.py",
                "tools/test_classify_controlled_public_h3_network_change.py",
                "tools/test_compare_android_path_snapshots.py",
                "tools/test_draft_final_handover_result_row.py",
                "tools/test_final_browser_handover_trial_audit.py",
                "tools/test_validate_final_handover_trial_artifact.py",
                "tools/test_select_next_final_handover_trial.py",
                "tools/test_summarize_chrome_rebinding_proxy_matrix.py",
                "tools/test_summarize_chrome_rebinding_upload_matrix.py",
                "tools/test_summarize_chrome_rebinding_timing_sensitivity.py",
                "tools/test_summarize_chrome_rebinding_old_path_drop.py",
                "tools/test_summarize_chrome_rebinding_stress_matrix.py",
                "tools/test_summarize_chrome_rebinding_return_path_drop_controls.py",
                "tools/test_summarize_chrome_rebinding_transient_return_path_sweep.py",
                "tools/test_summarize_quic_go_h3_midflight_matrix.py",
                "tools/test_research_clock.py",
                "tools/test_verify_research_bundle.py",
                "tools/verify_research_bundle.py",
                "tools/run_android_chrome_navigation.py",
                "tools/run_safari_webdriver_navigation.py",
                "tools/research_clock.py",
            ],
            {0},
            30,
        ),
        ("publication_bundle", [python_bin, "tools/validate_publication_bundle.py"], {0}, 30),
        ("research_clock_regression", [python_bin, "tools/test_research_clock.py"], {0}, 30),
        ("verify_research_bundle_regression", [python_bin, "tools/test_verify_research_bundle.py"], {0}, 30),
        ("experiment_summary", [python_bin, "tools/summarize_experiment_results.py", "--format", "markdown"], {0}, 30),
        (
            "paper_tables_regeneration_check",
            [python_bin, "tools/build_paper_tables.py", "--output", paper_tables],
            {0},
            30,
        ),
        (
            "application_recovery_tradeoff",
            [
                python_bin,
                "tools/build_application_recovery_tradeoff.py",
                "--output",
                application_recovery_tradeoff,
                "--csv-output",
                application_recovery_tradeoff_csv,
            ],
            {0},
            30,
        ),
        (
            "downlink_recovery_comparison",
            [
                python_bin,
                "tools/build_downlink_recovery_comparison.py",
                "--output",
                downlink_recovery_comparison,
                "--csv-output",
                downlink_recovery_comparison_csv,
            ],
            {0},
            30,
        ),
        (
            "workload_transition_zone",
            [
                python_bin,
                "tools/build_workload_transition_zone_table.py",
                "--output",
                workload_transition_zone,
                "--csv-output",
                workload_transition_zone_csv,
            ],
            {0},
            30,
        ),
        (
            "replication_sufficiency_audit_regression",
            [python_bin, "tools/test_build_replication_sufficiency_audit.py"],
            {0},
            30,
        ),
        (
            "replication_sufficiency_audit",
            [
                python_bin,
                "tools/build_replication_sufficiency_audit.py",
                "--output",
                replication_sufficiency_audit,
                "--csv-output",
                replication_sufficiency_audit_csv,
            ],
            {0},
            30,
        ),
        (
            "paper_evidence_gap_register_regression",
            [python_bin, "tools/test_build_paper_evidence_gap_register.py"],
            {0},
            30,
        ),
        (
            "paper_evidence_gap_register",
            [
                python_bin,
                "tools/build_paper_evidence_gap_register.py",
                "--output",
                paper_gap_register,
                "--csv-output",
                paper_gap_register_csv,
            ],
            {0},
            30,
        ),
        (
            "paper_claim_support_matrix_regression",
            [python_bin, "tools/test_build_paper_claim_support_matrix.py"],
            {0},
            30,
        ),
        (
            "paper_claim_support_matrix",
            [
                python_bin,
                "tools/build_paper_claim_support_matrix.py",
                "--output",
                paper_claim_support_matrix,
                "--csv-output",
                paper_claim_support_matrix_csv,
            ],
            {0},
            30,
        ),
        (
            "cm_operational_friction_matrix_regression",
            [python_bin, "tools/test_build_cm_operational_friction_matrix.py"],
            {0},
            30,
        ),
        (
            "cm_operational_friction_matrix",
            [
                python_bin,
                "tools/build_cm_operational_friction_matrix.py",
                "--output",
                cm_operational_friction_matrix,
                "--csv-output",
                cm_operational_friction_matrix_csv,
            ],
            {0},
            30,
        ),
        (
            "final_trial_acceptance_scorecard_regression",
            [python_bin, "tools/test_build_final_trial_acceptance_scorecard.py"],
            {0},
            30,
        ),
        (
            "final_trial_acceptance_scorecard",
            [
                python_bin,
                "tools/build_final_trial_acceptance_scorecard.py",
                "--output",
                final_trial_acceptance_scorecard,
                "--csv-output",
                final_trial_acceptance_scorecard_csv,
            ],
            {0},
            30,
        ),
        (
            "final_protocol_readiness_matrix_regression",
            [python_bin, "tools/test_build_final_protocol_readiness_matrix.py"],
            {0},
            30,
        ),
        (
            "final_protocol_readiness_matrix",
            [
                python_bin,
                "tools/build_final_protocol_readiness_matrix.py",
                "--output",
                final_protocol_readiness_matrix,
                "--csv-output",
                final_protocol_readiness_matrix_csv,
            ],
            {0},
            60,
        ),
        (
            "research_status_dashboard_regression",
            [python_bin, "tools/test_build_research_status_dashboard.py"],
            {0},
            30,
        ),
        (
            "research_status_dashboard",
            [
                python_bin,
                "tools/build_research_status_dashboard.py",
                "--output",
                research_status_dashboard,
                "--json-output",
                research_status_dashboard_json,
                "--claim-support",
                paper_claim_support_matrix_input,
                "--replication-audit",
                replication_sufficiency_audit_input,
            ],
            {0},
            30,
        ),
        (
            "final_browser_handover_trial_audit",
            [
                python_bin,
                "tools/audit_final_browser_handover_trials.py",
                "--output",
                final_trials,
            ],
            {0},
            30,
        ),
        (
            "final_browser_handover_trial_audit_regression",
            [python_bin, "tools/test_final_browser_handover_trial_audit.py"],
            {0},
            30,
        ),
        (
            "final_handover_result_row_drafter_regression",
            [python_bin, "tools/test_draft_final_handover_result_row.py"],
            {0},
            30,
        ),
        (
            "final_handover_trial_artifact_validator_regression",
            [python_bin, "tools/test_validate_final_handover_trial_artifact.py"],
            {0},
            30,
        ),
        (
            "final_handover_result_row_append_regression",
            [python_bin, "tools/test_append_final_handover_result_row.py"],
            {0},
            30,
        ),
        (
            "final_handover_next_trial_selector_regression",
            [python_bin, "tools/test_select_next_final_handover_trial.py"],
            {0},
            30,
        ),
        (
            "final_handover_next_trial_readiness_regression",
            [python_bin, "tools/test_check_next_final_handover_trial_readiness.py"],
            {0},
            30,
        ),
        (
            "final_handover_operator_checklist_regression",
            [python_bin, "tools/test_build_final_handover_operator_checklist.py"],
            {0},
            30,
        ),
        (
            "final_handover_external_inputs_regression",
            [python_bin, "tools/test_build_final_handover_external_inputs.py"],
            {0},
            30,
        ),
        (
            "final_handover_trial_packet_regression",
            [python_bin, "tools/test_build_final_handover_trial_packet.py"],
            {0},
            30,
        ),
        (
            "final_handover_trial_artifact_bundle_regression",
            [python_bin, "tools/test_check_final_handover_trial_artifact_bundle.py"],
            {0},
            30,
        ),
        (
            "artifact_disk_guard_regression",
            [python_bin, "tools/test_artifact_disk_guard.py"],
            {0},
            30,
        ),
        (
            "chrome_h3_artifact_classifier_regression",
            [python_bin, "tools/test_classify_chrome_h3_artifacts.py"],
            {0},
            30,
        ),
        (
            "controlled_public_network_change_classifier_regression",
            [python_bin, "tools/test_classify_controlled_public_h3_network_change.py"],
            {0},
            30,
        ),
        (
            "android_path_snapshot_comparator_regression",
            [python_bin, "tools/test_compare_android_path_snapshots.py"],
            {0},
            30,
        ),
        (
            "chrome_rebinding_matrix_summary_regression",
            [python_bin, "tools/test_summarize_chrome_rebinding_proxy_matrix.py"],
            {0},
            30,
        ),
        (
            "chrome_rebinding_upload_summary_regression",
            [python_bin, "tools/test_summarize_chrome_rebinding_upload_matrix.py"],
            {0},
            30,
        ),
        (
            "chrome_rebinding_timing_sensitivity_summary_regression",
            [python_bin, "tools/test_summarize_chrome_rebinding_timing_sensitivity.py"],
            {0},
            30,
        ),
        (
            "chrome_rebinding_old_path_drop_summary_regression",
            [python_bin, "tools/test_summarize_chrome_rebinding_old_path_drop.py"],
            {0},
            30,
        ),
        (
            "chrome_rebinding_stress_summary_regression",
            [python_bin, "tools/test_summarize_chrome_rebinding_stress_matrix.py"],
            {0},
            30,
        ),
        (
            "chrome_rebinding_return_path_drop_controls_summary_regression",
            [python_bin, "tools/test_summarize_chrome_rebinding_return_path_drop_controls.py"],
            {0},
            30,
        ),
        (
            "chrome_rebinding_transient_return_path_sweep_summary_regression",
            [python_bin, "tools/test_summarize_chrome_rebinding_transient_return_path_sweep.py"],
            {0},
            30,
        ),
        (
            "quic_go_h3_midflight_matrix_summary_regression",
            [python_bin, "tools/test_summarize_quic_go_h3_midflight_matrix.py"],
            {0},
            30,
        ),
        (
            "controlled_public_baseline_unlock_regression",
            [python_bin, "tools/test_check_controlled_public_baseline_unlock.py"],
            {0},
            30,
        ),
        (
            "controlled_public_config_regression",
            [python_bin, "tools/test_check_controlled_public_config.py"],
            {0},
            30,
        ),
        (
            "controlled_public_config_worksheet_regression",
            [python_bin, "tools/test_build_controlled_public_config_worksheet.py"],
            {0},
            30,
        ),
        (
            "controlled_public_config_expected_incomplete",
            [python_bin, "tools/check_controlled_public_config.py", "--output", controlled_public_config],
            {1},
            30,
        ),
        (
            "controlled_public_baseline_unlock_expected_incomplete",
            [
                python_bin,
                "tools/check_controlled_public_baseline_unlock.py",
                "--require-unlocked",
                "--output",
                controlled_public_baseline_unlock,
            ],
            {1},
            30,
        ),
        (
            "controlled_public_config_worksheet",
            [python_bin, "tools/build_controlled_public_config_worksheet.py", "--output", controlled_public_config_worksheet],
            {0},
            30,
        ),
        (
            "controlled_public_origin_deploy_packet_regression",
            [python_bin, "tools/test_build_controlled_public_origin_deploy_packet.py"],
            {0},
            30,
        ),
        (
            "controlled_public_origin_deploy_packet",
            [
                python_bin,
                "tools/build_controlled_public_origin_deploy_packet.py",
                "--output",
                controlled_public_origin_deploy_packet,
            ],
            {0},
            30,
        ),
        (
            "reproducibility_manifest_regression",
            [python_bin, "tools/test_build_reproducibility_manifest.py"],
            {0},
            30,
        ),
        (
            "reproducibility_manifest",
            [
                python_bin,
                "tools/build_reproducibility_manifest.py",
                "--output",
                reproducibility_manifest,
                "--json-output",
                reproducibility_manifest_json,
            ],
            {0},
            30,
        ),
        (
            "final_browser_handover_readiness_expected_incomplete",
            [python_bin, "tools/check_final_browser_handover_readiness.py", "--output", final_readiness],
            {1},
            60,
        ),
        (
            "final_handover_next_trial_readiness_expected_incomplete",
            [python_bin, "tools/check_next_final_handover_trial_readiness.py", "--output", final_next_trial_readiness],
            {1},
            60,
        ),
        (
            "final_browser_handover_run_plan",
            [python_bin, "tools/plan_final_browser_handover_runs.py", "--output", final_run_plan],
            {0},
            30,
        ),
        (
            "final_handover_next_trial_selector",
            [python_bin, "tools/select_next_final_handover_trial.py", "--output", final_next_trial],
            {0},
            30,
        ),
        (
            "artifact_storage_report",
            [python_bin, "tools/report_artifact_storage.py", "--output", storage_report],
            {0},
            60,
        ),
        (
            "artifact_cleanup_dry_run_plan",
            [python_bin, "tools/plan_artifact_cleanup.py", "--output", cleanup_dry_run],
            {0},
            60,
        ),
        (
            "artifact_cleanup_safety_regression",
            [python_bin, "tools/test_audit_artifact_cleanup_safety.py"],
            {0},
            30,
        ),
        (
            "artifact_cleanup_safety_audit",
            [python_bin, "tools/audit_artifact_cleanup_safety.py", "--output", cleanup_safety],
            {0},
            60,
        ),
        (
            "final_handover_operator_checklist",
            [python_bin, "tools/build_final_handover_operator_checklist.py", "--output", final_operator_checklist],
            {0},
            60,
        ),
        (
            "final_handover_external_inputs",
            [python_bin, "tools/build_final_handover_external_inputs.py", "--output", final_external_inputs],
            {0},
            60,
        ),
        (
            "final_handover_trial_packet",
            [python_bin, "tools/build_final_handover_trial_packet.py", "--output", final_trial_packet],
            {0},
            60,
        ),
        (
            "final_handover_trial_artifact_bundle_check",
            [python_bin, "tools/check_final_handover_trial_artifact_bundle.py", "--output", final_trial_artifact_bundle],
            {0},
            60,
        ),
        (
            "final_handover_trial_artifact_bundle_require_complete_expected_incomplete",
            [python_bin, "tools/check_final_handover_trial_artifact_bundle.py", "--require-complete"],
            {1},
            30,
        ),
        (
            "research_bundle_audit",
            [python_bin, "tools/audit_research_bundle.py", "--output", research_audit],
            {0},
            60,
        ),
        (
            "research_bundle_require_complete_expected_incomplete",
            [python_bin, "tools/audit_research_bundle.py", "--require-complete"],
            {1},
            60,
        ),
        (
            "final_trials_require_complete_expected_incomplete",
            [python_bin, "tools/audit_final_browser_handover_trials.py", "--require-complete"],
            {1},
            30,
        ),
        ("handover_readiness", [python_bin, "tools/check_handover_readiness.py", "--format", "markdown"], {0}, 30),
        ("browser_observability", [python_bin, "tools/check_browser_cm_observability.py", "--format", "markdown"], {0}, 30),
        (
            "controlled_public_wrapper_script_syntax",
            [
                "bash",
                "-n",
                "harness/scripts/controlled-public-preflight.sh",
                "repro/quic-go-min-repro/scripts/ensure-min-disk-free.sh",
                "repro/quic-go-min-repro/scripts/run-controlled-public-h3-server.sh",
                "repro/quic-go-min-repro/scripts/run-controlled-public-h3-browser-baseline.sh",
                "repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh",
                "repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh",
                "repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy-matrix.sh",
                "repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh",
                "repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-transient-return-path-sweep.sh",
                "repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-upload-matrix.sh",
                "repro/quic-go-min-repro/scripts/run-local-h3-midflight-matrix.sh",
                "repro/quic-go-min-repro/scripts/run-safari-controlled-public-baseline.sh",
                "repro/quic-go-min-repro/scripts/run-safari-controlled-public-network-change.sh",
                "repro/quic-go-min-repro/scripts/run-android-chrome-controlled-public-network-change.sh",
            ],
            {0},
            30,
        ),
        ("git_diff_check", ["git", "diff", "--check"], {0}, 30),
    ]


def build_report(results: list[CheckResult]) -> dict[str, Any]:
    return {
        "generated_at": now_utc(),
        "check_count": len(results),
        "passed_count": sum(1 for result in results if result.ok),
        "ok": all(result.ok for result in results),
        "results": [asdict(result) for result in results],
    }


def emit_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Research Verification Report",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        "| check | value |",
        "| --- | --- |",
        f"| checks | `{report['check_count']}` |",
        f"| passed | `{report['passed_count']}` |",
        f"| verification ok | `{'yes' if report['ok'] else 'no'}` |",
        "",
        "## Checks",
        "",
        "| check | exit | expected | ok | duration s |",
        "| --- | ---: | --- | --- | ---: |",
    ]
    for result in report["results"]:
        expected = ",".join(str(code) for code in result["expected_exit_codes"])
        lines.append(
            f"| `{result['name']}` | {result['exit_code']} | `{expected}` | `{'yes' if result['ok'] else 'no'}` | {result['duration_seconds']} |"
        )
    lines.extend(["", "## Failed Output", ""])
    failures = [result for result in report["results"] if not result["ok"]]
    if not failures:
        lines.append("-")
    for result in failures:
        lines.extend(
            [
                f"### {result['name']}",
                "",
                "stdout:",
                "",
                "```text",
                result["stdout_tail"] or "",
                "```",
                "",
                "stderr:",
                "",
                "```text",
                result["stderr_tail"] or "",
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default="docs/results/research-verification-report-20260624.md")
    parser.add_argument(
        "--scratch-dir",
        help="write generated intermediate reports under this directory instead of tracked docs/results paths",
    )
    parser.add_argument("--continue-on-failure", action="store_true")
    args = parser.parse_args()

    scratch_dir = Path(args.scratch_dir) if args.scratch_dir else None
    if scratch_dir is not None:
        scratch_dir.mkdir(parents=True, exist_ok=True)

    results: list[CheckResult] = []
    for name, command, expected, timeout in default_checks(args.python, scratch_dir):
        result = run_check(name, command, expected, timeout)
        results.append(result)
        if not result.ok and not args.continue_on_failure:
            break

    report = build_report(results)
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
