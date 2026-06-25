#!/usr/bin/env python3
"""Audit the current research bundle against the paper experiment goal."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any

from build_paper_tables import build_markdown, load_rows
from audit_final_browser_handover_trials import build_audit as build_final_trial_audit
from check_browser_cm_observability import build_readiness as build_observability_readiness
from check_handover_readiness import build_readiness as build_handover_readiness
from report_artifact_storage import build_report as build_storage_report
from report_artifact_storage import human_size


REQUIRED_FILES = [
    "README.md",
    "data/experiment-results.csv",
    "data/evidence-chain-rubric.csv",
    "data/cm-operational-friction-rubric.csv",
    "data/paper-evidence-gap-register-20260624.csv",
    "data/paper-claim-support-matrix-20260624.csv",
    "data/cm-operational-friction-matrix-20260624.csv",
    "data/final-trial-acceptance-scorecard-20260624.csv",
    "data/final-protocol-readiness-matrix-20260624.csv",
    "data/p0-unblock-status-20260624.csv",
    "data/p0-baseline-execution-packet-20260624.csv",
    "data/p0-baseline-preflight-check-20260624.csv",
    "data/p0-baseline-preflight-control-report-20260624.csv",
    "data/final-capture-storage-budget-20260624.csv",
    "data/research-status-dashboard-20260624.json",
    "data/active-path-change-command-candidates-20260625.json",
    "data/aws-identity-readiness-20260625.json",
    "data/chrome-h3-rebinding-repetition-summary-20260624.csv",
    "data/chrome-h3-rebinding-upload-summary-20260624.csv",
    "data/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624.csv",
    "data/chrome-h3-rebinding-transient-downlink-wait-boundary-20260624.csv",
    "data/downlink-recovery-comparison-20260624.csv",
    "data/chrome-h3-rebinding-transient-downlink-5000-5500-replication-20260625.csv",
    "data/chrome-h3-rebinding-transient-upload-4750-replication-20260625.csv",
    "data/chrome-h3-rebinding-transient-poll-boundary-20260624.csv",
    "data/chrome-h3-rebinding-transient-poll-long-boundary-20260624.csv",
    "data/chrome-h3-rebinding-transient-poll-4000-replication-20260625.csv",
    "data/polling-transition-zone-synthesis-20260624.csv",
    "data/replication-sufficiency-audit-20260624.csv",
    "data/replication-run-plan-20260624.csv",
    "data/quic-go-h3-midflight-repetition-summary-20260624.csv",
    "data/browser-cm-observability-matrix-20260624.csv",
    "data/final-browser-handover-required-trials.csv",
    "data/implementation-survey.csv",
    "docs/reproducibility-guide-ko.md",
    "docs/scanners-and-tools-ko.md",
    "docs/results/controlled-public-config-check-20260624.md",
    "docs/results/controlled-public-config-worksheet-20260624.md",
    "docs/results/controlled-public-baseline-unlock-check-20260624.md",
    "docs/results/artifact-cleanup-dry-run-20260624.md",
    "docs/results/artifact-cleanup-plan-20260624.md",
    "docs/results/artifact-cleanup-safety-audit-20260624.md",
    "docs/results/evidence-chain-and-gap-synthesis-20260624.md",
    "docs/results/literature-refresh-latest-cm-boundary-20260624.md",
    "docs/results/paper-evidence-gap-register-20260624.md",
    "docs/results/paper-claim-support-matrix-20260624.md",
    "docs/results/cm-operational-friction-matrix-20260624.md",
    "docs/results/chrome-h3-rebinding-proxy-results-20260624.md",
    "docs/results/chrome-h3-rebinding-repetition-summary-20260624.md",
    "docs/results/chrome-h3-rebinding-upload-summary-20260624.md",
    "docs/results/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624.md",
    "docs/results/chrome-h3-rebinding-transient-downlink-wait-boundary-20260624.md",
    "docs/results/downlink-recovery-comparison-20260624.md",
    "docs/results/chrome-h3-rebinding-transient-downlink-5000-5500-replication-20260625.md",
    "docs/results/chrome-h3-rebinding-transient-upload-4750-replication-20260625.md",
    "docs/results/chrome-h3-rebinding-transient-poll-boundary-20260624.md",
    "docs/results/chrome-h3-rebinding-transient-poll-long-boundary-20260624.md",
    "docs/results/chrome-h3-rebinding-transient-poll-4000-replication-20260625.md",
    "docs/results/polling-transition-zone-synthesis-20260624.md",
    "docs/results/replication-sufficiency-audit-20260624.md",
    "docs/results/replication-run-plan-20260624.md",
    "docs/results/quic-go-h3-midflight-repetition-summary-20260624.md",
    "docs/results/browser-cm-observability-matrix-20260624.md",
    "docs/results/final-handover-trial-artifact-validator-20260624.md",
    "docs/results/final-handover-next-trial-20260624.md",
    "docs/results/final-handover-next-trial-readiness-20260624.md",
    "docs/results/final-handover-operator-checklist-20260624.md",
    "docs/results/final-handover-external-inputs-20260624.md",
    "docs/results/final-handover-trial-packet-20260624.md",
    "docs/results/final-handover-trial-artifact-bundle-check-20260624.md",
    "docs/results/final-trial-acceptance-scorecard-20260624.md",
    "docs/results/final-protocol-readiness-matrix-20260624.md",
    "docs/results/p0-unblock-status-20260624.md",
    "docs/results/p0-baseline-execution-packet-20260624.md",
    "docs/results/p0-baseline-preflight-check-20260624.md",
    "docs/results/p0-baseline-preflight-control-report-20260624.md",
    "docs/results/final-capture-storage-budget-20260624.md",
    "docs/results/research-status-dashboard-20260624.md",
    "docs/results/reproducibility-manifest-20260624.md",
    "docs/results/active-path-change-command-candidates-20260625.md",
    "docs/results/aws-identity-readiness-20260625.md",
    "docs/results/final-browser-handover-experiment-protocol-20260624.md",
    "docs/results/final-browser-handover-readiness-20260624.md",
    "docs/results/final-browser-handover-run-plan-20260624.md",
    "docs/results/final-browser-handover-result-registration-guide-20260624.md",
    "docs/results/final-browser-handover-trial-audit-20260624.md",
    "docs/results/paper-tables-20260624.md",
    "docs/results/research-completion-audit-20260624.md",
    "docs/results/research-verification-report-20260624.md",
    "paper/results-section-ko.md",
    "paper/results-section-en.md",
    "tools/test_final_browser_handover_trial_audit.py",
    "tools/test_draft_final_handover_result_row.py",
    "tools/test_validate_final_handover_trial_artifact.py",
    "tools/test_append_final_handover_result_row.py",
    "tools/test_artifact_disk_guard.py",
    "tools/test_audit_artifact_cleanup_safety.py",
    "tools/test_select_next_final_handover_trial.py",
    "tools/test_suggest_active_path_change_commands.py",
    "tools/test_check_aws_identity_readiness.py",
    "tools/test_check_next_final_handover_trial_readiness.py",
    "tools/test_build_final_handover_operator_checklist.py",
    "tools/test_build_final_handover_trial_packet.py",
    "tools/test_build_final_trial_acceptance_scorecard.py",
    "tools/test_build_final_protocol_readiness_matrix.py",
    "tools/test_build_p0_unblock_status.py",
    "tools/test_build_p0_baseline_execution_packet.py",
    "tools/test_check_p0_baseline_preflight.py",
    "tools/test_build_p0_preflight_control_report.py",
    "tools/test_build_final_capture_storage_budget.py",
    "tools/test_final_chrome_nochange_run_wrapper.py",
    "tools/test_final_chrome_network_change_run_wrapper.py",
    "tools/test_final_handover_run_next_wrapper.py",
    "tools/test_final_p0_baseline_preflight_wrapper.py",
    "tools/test_final_p0_baseline_run_wrapper.py",
    "tools/test_final_handover_register_trial_wrapper.py",
    "tools/test_init_controlled_public_config_wrapper.py",
    "tools/test_build_research_status_dashboard.py",
    "tools/test_build_application_recovery_tradeoff.py",
    "tools/test_build_workload_transition_zone_table.py",
    "tools/test_build_replication_sufficiency_audit.py",
    "tools/test_build_replication_run_plan.py",
    "tools/test_build_polling_transition_zone_table.py",
    "tools/test_build_controlled_public_config_worksheet.py",
    "tools/test_build_paper_evidence_gap_register.py",
    "tools/test_build_paper_claim_support_matrix.py",
    "tools/test_build_cm_operational_friction_matrix.py",
    "tools/test_build_reproducibility_manifest.py",
    "tools/test_build_final_handover_external_inputs.py",
    "tools/test_check_final_handover_trial_artifact_bundle.py",
    "tools/test_check_controlled_public_baseline_unlock.py",
    "tools/test_classify_chrome_h3_artifacts.py",
    "tools/test_summarize_chrome_rebinding_proxy_matrix.py",
    "tools/test_summarize_chrome_rebinding_upload_matrix.py",
    "tools/test_summarize_chrome_rebinding_transient_return_path_sweep.py",
    "tools/test_summarize_quic_go_h3_midflight_matrix.py",
    "tools/test_classify_controlled_public_h3_network_change.py",
    "tools/test_compare_android_path_snapshots.py",
    "tools/test_check_controlled_public_config.py",
    "tools/verify_research_bundle.py",
    "tools/classify_chrome_h3_artifacts.py",
    "tools/summarize_chrome_rebinding_proxy_matrix.py",
    "tools/summarize_chrome_rebinding_upload_matrix.py",
    "tools/summarize_chrome_rebinding_transient_return_path_sweep.py",
    "tools/summarize_quic_go_h3_midflight_matrix.py",
    "tools/build_paper_tables.py",
    "tools/build_downlink_recovery_comparison.py",
    "tools/build_polling_transition_zone_table.py",
    "tools/build_replication_sufficiency_audit.py",
    "tools/build_replication_run_plan.py",
    "tools/build_paper_evidence_gap_register.py",
    "tools/build_paper_claim_support_matrix.py",
    "tools/build_cm_operational_friction_matrix.py",
    "tools/build_controlled_public_config_worksheet.py",
    "tools/build_reproducibility_manifest.py",
    "tools/build_final_handover_external_inputs.py",
    "tools/build_final_trial_acceptance_scorecard.py",
    "tools/build_final_protocol_readiness_matrix.py",
    "tools/build_p0_unblock_status.py",
    "tools/build_p0_baseline_execution_packet.py",
    "tools/check_p0_baseline_preflight.py",
    "tools/build_p0_preflight_control_report.py",
    "tools/build_final_capture_storage_budget.py",
    "tools/build_research_status_dashboard.py",
    "tools/audit_final_browser_handover_trials.py",
    "tools/audit_artifact_cleanup_safety.py",
    "tools/draft_final_handover_result_row.py",
    "tools/validate_final_handover_trial_artifact.py",
    "tools/append_final_handover_result_row.py",
    "tools/build_final_handover_operator_checklist.py",
    "tools/build_final_handover_trial_packet.py",
    "tools/check_final_handover_trial_artifact_bundle.py",
    "tools/select_next_final_handover_trial.py",
    "tools/suggest_active_path_change_commands.py",
    "tools/check_aws_identity_readiness.py",
    "tools/check_controlled_public_config.py",
    "tools/check_controlled_public_baseline_unlock.py",
    "tools/check_next_final_handover_trial_readiness.py",
    "tools/classify_controlled_public_h3_network_change.py",
    "tools/compare_android_path_snapshots.py",
    "tools/check_final_browser_handover_readiness.py",
    "tools/plan_final_browser_handover_runs.py",
    "tools/plan_artifact_cleanup.py",
    "tools/report_artifact_storage.py",
    "tools/validate_publication_bundle.py",
    "harness/scripts/init-controlled-public-config.sh",
    "harness/scripts/aws-preflight.sh",
    "harness/scripts/final-handover-run-next.sh",
    "harness/scripts/final-chrome-nochange-run.sh",
    "harness/scripts/final-chrome-network-change-run.sh",
    "harness/scripts/final-p0-baseline-preflight.sh",
    "harness/scripts/final-p0-baseline-run.sh",
    "harness/scripts/final-handover-register-trial.sh",
    "repro/quic-go-min-repro/cmd/h3server/main.go",
    "repro/quic-go-min-repro/cmd/udprebindproxy/main.go",
    "repro/quic-go-min-repro/scripts/run-chrome-h3-local.sh",
    "repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh",
    "repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy-matrix.sh",
    "repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-upload-matrix.sh",
    "repro/quic-go-min-repro/scripts/run-local-h3-midflight-matrix.sh",
    "repro/quic-go-min-repro/scripts/ensure-min-disk-free.sh",
    "repro/quic-go-min-repro/scripts/run-controlled-public-h3-server.sh",
    "repro/quic-go-min-repro/scripts/run-controlled-public-h3-browser-baseline.sh",
    "repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh",
    "repro/quic-go-min-repro/scripts/run-safari-controlled-public-baseline.sh",
    "repro/quic-go-min-repro/scripts/run-safari-controlled-public-network-change.sh",
    "repro/quic-go-min-repro/scripts/run-android-chrome-controlled-public-network-change.sh",
]


def run_command(args: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "command": args,
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="ignore") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="ignore") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "command": args,
            "exit_code": 124,
            "stdout": stdout.strip(),
            "stderr": stderr.strip() or "timeout",
        }


def duplicate_values(rows: list[dict[str, str]], key: str) -> list[str]:
    counts = Counter(row[key] for row in rows)
    return sorted(value for value, count in counts.items() if count > 1)


def file_checks(root: Path) -> list[dict[str, Any]]:
    checks = []
    for rel in REQUIRED_FILES:
        path = root / rel
        checks.append({"path": rel, "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0})
    return checks


def paper_tables_current(root: Path, experiments: list[dict[str, str]], rubric: list[dict[str, str]]) -> bool:
    generated = build_markdown(experiments, rubric)
    table_path = root / "docs" / "results" / "paper-tables-20260624.md"
    if not table_path.exists():
        return False
    return table_path.read_text(encoding="utf-8", errors="ignore") == generated


def build_audit(root: Path) -> dict[str, Any]:
    publication = run_command([sys.executable, "tools/validate_publication_bundle.py"], timeout=30)
    experiments = load_rows(root / "data" / "experiment-results.csv")
    rubric = load_rows(root / "data" / "evidence-chain-rubric.csv")
    matrix = load_rows(root / "harness" / "manifests" / "experiment-matrix.csv")
    handover = build_handover_readiness("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    observability = build_observability_readiness(
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Safari.app/Contents/MacOS/Safari",
        "/Applications/Safari Technology Preview.app/Contents/MacOS/Safari Technology Preview",
    )
    storage = build_storage_report(
        ["repro/quic-go-min-repro/artifacts", "harness/results"],
        max_entries=10,
    )
    final_trials = build_final_trial_audit(
        root / "data" / "final-browser-handover-required-trials.csv",
        root / "data" / "experiment-results.csv",
    )
    files = file_checks(root)
    required_files_ok = all(item["exists"] for item in files)
    experiment_ids_unique = not duplicate_values(experiments, "trial_id")
    matrix_ids_unique = not duplicate_values(matrix, "id")
    paper_tables_ok = paper_tables_current(root, experiments, rubric)
    public_browser_network_change_done = any(
        row["status"] in {"PASS", "PASS_NEGATIVE_CONTROL"}
        and "network-change" in row["trial_id"]
        and ("chrome" in row["trial_id"] or "safari" in row["trial_id"] or "browser" in row["deployment_tier"].lower())
        for row in experiments
    )
    controlled_public_result_done = any(
        row["status"] in {"PASS", "PASS_NEGATIVE_CONTROL"}
        and "controlled-public" in row["trial_id"]
        and "network-change" in row["trial_id"]
        for row in experiments
    )
    blockers: list[str] = []
    if publication["exit_code"] != 0:
        blockers.append("publication bundle validation failed")
    if not required_files_ok:
        blockers.append("required paper/reproducibility files are missing")
    if not experiment_ids_unique:
        blockers.append("experiment trial_id values are not unique")
    if not matrix_ids_unique:
        blockers.append("experiment matrix id values are not unique")
    if not paper_tables_ok:
        blockers.append("paper tables are not current with CSV inputs")
    if not handover.secondary_path_ready:
        blockers.append("desktop active secondary path is not ready")
    if not handover.android_ready:
        blockers.append("Android device is not connected over ADB")
    if not handover.aws_identity_ok:
        blockers.append("AWS identity is not available")
    if handover.disk_available_gib < 5:
        blockers.append("disk free space is below 5 GiB; large NetLog/pcap experiments should wait")
    if not public_browser_network_change_done:
        blockers.append("browser active network-change result is not done")
    if not controlled_public_result_done:
        blockers.append("controlled-public network-change result is not done")
    if not final_trials["complete"]:
        blockers.append("final browser handover trial protocol is not complete")

    goal_complete = not blockers
    return {
        "check_date": utc_date_iso(),
        "publication_bundle_ok": publication["exit_code"] == 0,
        "required_files_ok": required_files_ok,
        "experiment_trial_count": len(experiments),
        "experiment_status_counts": dict(Counter(row["status"] for row in experiments)),
        "experiment_ids_unique": experiment_ids_unique,
        "matrix_item_count": len(matrix),
        "matrix_ids_unique": matrix_ids_unique,
        "paper_tables_current": paper_tables_ok,
        "handover": {
            "desktop_handover_ready": handover.desktop_handover_ready,
            "android_ready": handover.android_ready,
            "secondary_path_ready": handover.secondary_path_ready,
            "active_ipv4_interfaces": [asdict(item) for item in handover.active_ipv4_interfaces],
            "aws_identity_ok": handover.aws_identity_ok,
            "disk_available_gib": handover.disk_available_gib,
        },
        "observability": {
            "chrome_netlog_ready": observability.chrome_netlog_ready,
            "safari_webdriver_ready": observability.safari_webdriver_ready,
            "packet_capture_tooling_ready": observability.packet_capture_tooling_ready,
            "ios_remote_capture_candidate": observability.ios_remote_capture_candidate,
            "blockers": observability.blockers,
        },
        "storage": {
            "disk_free_gib": storage["disk"]["free_gib"],
            "total_artifact_bytes": storage["total_artifact_bytes"],
            "total_artifact_human": human_size(int(storage["total_artifact_bytes"])),
            "top_artifact_dirs": storage["top_artifact_dirs"],
        },
        "final_browser_handover_trials": {
            "complete": final_trials["complete"],
            "requirement_count": final_trials["requirement_count"],
            "complete_count": final_trials["complete_count"],
            "blockers": final_trials["blockers"],
        },
        "goal_complete": goal_complete,
        "blockers": blockers,
        "required_files": files,
        "publication_validator": {
            "exit_code": publication["exit_code"],
            "stdout": publication["stdout"],
            "stderr": publication["stderr"],
        },
    }


def markdown_bool(value: bool) -> str:
    return "yes" if value else "no"


def emit_markdown(audit: dict[str, Any]) -> str:
    handover = audit["handover"]
    observability = audit["observability"]
    storage = audit["storage"]
    final_trials = audit["final_browser_handover_trials"]
    active = ", ".join(
        f"{item['name']}({','.join(item['ipv4'])})"
        for item in handover["active_ipv4_interfaces"]
    ) or "-"
    blockers = audit["blockers"] or ["-"]
    lines = [
        "# Research Bundle Audit",
        "",
        f"Generated: `{audit['check_date']}`",
        "",
        "## Summary",
        "",
        "| check | value |",
        "| --- | --- |",
        f"| publication bundle ok | `{markdown_bool(audit['publication_bundle_ok'])}` |",
        f"| required files ok | `{markdown_bool(audit['required_files_ok'])}` |",
        f"| experiment trials | `{audit['experiment_trial_count']}` |",
        f"| experiment status counts | `{audit['experiment_status_counts']}` |",
        f"| experiment ids unique | `{markdown_bool(audit['experiment_ids_unique'])}` |",
        f"| matrix items | `{audit['matrix_item_count']}` |",
        f"| matrix ids unique | `{markdown_bool(audit['matrix_ids_unique'])}` |",
        f"| paper tables current | `{markdown_bool(audit['paper_tables_current'])}` |",
        f"| final browser handover trials | `{final_trials['complete_count']}/{final_trials['requirement_count']}` |",
        f"| goal complete | `{markdown_bool(audit['goal_complete'])}` |",
        "",
        "## Readiness",
        "",
        "| check | value |",
        "| --- | --- |",
        f"| active IPv4 interfaces | `{active}` |",
        f"| secondary path ready | `{markdown_bool(handover['secondary_path_ready'])}` |",
        f"| desktop handover ready | `{markdown_bool(handover['desktop_handover_ready'])}` |",
        f"| Android ready | `{markdown_bool(handover['android_ready'])}` |",
        f"| AWS identity OK | `{markdown_bool(handover['aws_identity_ok'])}` |",
        f"| disk available GiB | `{handover['disk_available_gib']}` |",
        f"| local artifact roots total | `{storage['total_artifact_human']}` |",
        f"| Chrome NetLog ready | `{markdown_bool(observability['chrome_netlog_ready'])}` |",
        f"| Safari WebDriver ready | `{markdown_bool(observability['safari_webdriver_ready'])}` |",
        f"| packet capture tooling ready | `{markdown_bool(observability['packet_capture_tooling_ready'])}` |",
        "",
        "## Final Browser Handover Trials",
        "",
        "| check | value |",
        "| --- | --- |",
        f"| complete | `{markdown_bool(final_trials['complete'])}` |",
        f"| requirements complete | `{final_trials['complete_count']}/{final_trials['requirement_count']}` |",
        "",
        "Incomplete final trial requirements:",
        "",
    ]
    lines.extend(f"- {blocker}" for blocker in (final_trials["blockers"] or ["-"]))
    lines.extend(
        [
            "",
            "## Blockers",
            "",
        ]
    )
    lines.extend(f"- {blocker}" for blocker in blockers)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    audit = build_audit(root)
    if args.format == "json":
        text = json.dumps(audit, indent=2, ensure_ascii=False) + "\n"
    else:
        text = emit_markdown(audit)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.require_complete and not audit["goal_complete"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
