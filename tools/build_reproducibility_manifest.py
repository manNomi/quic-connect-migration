#!/usr/bin/env python3
"""Build a public-safe reproducibility manifest for the research bundle."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/reproducibility-manifest-20260624.md"
DEFAULT_JSON_OUTPUT = "data/reproducibility-manifest-20260624.json"


@dataclass
class GitState:
    commit: str
    branch: str


def run(args: list[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def git_state() -> GitState:
    commit = run(["git", "rev-parse", "--short", "HEAD"]).stdout.strip() or "unknown"
    branch = run(["git", "branch", "--show-current"]).stdout.strip() or "unknown"
    return GitState(commit=commit, branch=branch)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def parse_markdown_summary(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    summary: dict[str, str] = {}
    in_summary = False
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if line == "## Summary":
            in_summary = True
            continue
        if in_summary and line.startswith("## "):
            break
        if not in_summary or not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) == 2 and cells[0] != "field" and cells[0] != "check":
            summary[cells[0]] = cells[1]
    return summary


def count_by(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    counts = Counter(row.get(field, "") or "-" for row in rows)
    return dict(sorted(counts.items()))


def path_status(paths: dict[str, str]) -> dict[str, dict[str, Any]]:
    return {
        key: {
            "path": path,
            "exists": Path(path).exists(),
        }
        for key, path in paths.items()
    }


def newest_ci_summary() -> dict[str, str]:
    gh = run(["gh", "run", "list", "--repo", "manNomi/quic-connect-migration", "--limit", "1"], timeout=20)
    if gh.returncode != 0 or not gh.stdout.strip():
        return {"available": "no", "status": "unknown", "conclusion": "unknown", "run_id": "-"}
    # Format: status conclusion title workflow branch event id duration created
    line = gh.stdout.splitlines()[0]
    parts = line.split("\t")
    return {
        "available": "yes",
        "status": parts[0] if len(parts) > 0 else "unknown",
        "conclusion": parts[1] if len(parts) > 1 and parts[1] else "-",
        "workflow": parts[3] if len(parts) > 3 else "-",
        "branch": parts[4] if len(parts) > 4 else "-",
        "event": parts[5] if len(parts) > 5 else "-",
        "run_id": parts[6] if len(parts) > 6 else "-",
        "duration": parts[7] if len(parts) > 7 else "-",
    }


def build_manifest(include_ci: bool = False) -> dict[str, Any]:
    root = Path(".")
    git = git_state()
    experiments = read_csv(root / "data" / "experiment-results.csv")
    implementation_survey = read_csv(root / "data" / "implementation-survey.csv")
    experiment_matrix = read_csv(root / "harness" / "manifests" / "experiment-matrix.csv")
    requirements = read_csv(root / "data" / "final-browser-handover-required-trials.csv")
    status_counts = Counter(row.get("status", "") for row in experiments)
    final_summary = parse_markdown_summary(root / "docs" / "results" / "research-bundle-audit-20260624.md")
    verification_summary = parse_markdown_summary(root / "docs" / "results" / "research-verification-report-20260624.md")
    external_inputs = parse_markdown_summary(root / "docs" / "results" / "final-handover-external-inputs-20260624.md")
    ci = newest_ci_summary() if include_ci else {"available": "not-requested"}
    evidence_paths_20260630 = {
        "implementation_rerun_results": "docs/results/implementation-rerun-results-20260630.md",
        "implementation_survey_csv": "data/implementation-survey.csv",
        "experiment_matrix": "harness/manifests/experiment-matrix.csv",
        "sanitized_evidence_bundle": "docs/results/sanitized-evidence-bundle-20260630.md",
        "sanitized_evidence_bundle_json": "data/sanitized-evidence-bundle-20260630.json",
        "non_iphone_gap_plan": "docs/results/non-iphone-research-gap-plan-20260630.md",
        "nginx_haproxy_boundary": "docs/results/nginx-haproxy-quic-cm-boundary-20260630.md",
        "nginx_runtime_demo": "docs/results/nginx-quic-active-migration-runtime-20260630.md",
        "nginx_quic_bpf_readiness": "docs/results/nginx-quic-bpf-readiness-20260630.md",
        "nginx_quic_bpf_linux_runner": "docs/results/nginx-quic-bpf-linux-runner-20260630.md",
        "chrome_desktop_noniphone_media_local_refresh": "docs/results/chrome-desktop-noniphone-media-local-refresh-20260630.md",
        "chrome_desktop_noniphone_media_local_refresh_csv": "data/chrome-desktop-noniphone-media-local-refresh-20260630.csv",
        "chrome_desktop_noniphone_musiclike_local_refresh": "docs/results/chrome-desktop-noniphone-musiclike-local-refresh-20260701.md",
        "chrome_desktop_noniphone_musiclike_local_refresh_csv": "data/chrome-desktop-noniphone-musiclike-local-refresh-20260701.csv",
        "chrome_desktop_noniphone_buffered_media_local_refresh": "docs/results/chrome-desktop-noniphone-buffered-media-local-refresh-20260701.md",
        "chrome_desktop_noniphone_buffered_media_local_refresh_csv": "data/chrome-desktop-noniphone-buffered-media-local-refresh-20260701.csv",
        "noniphone_workload_qoe_synthesis": "docs/results/noniphone-workload-qoe-continuity-synthesis-20260701.md",
        "noniphone_workload_qoe_synthesis_csv": "data/noniphone-workload-qoe-continuity-synthesis-20260701.csv",
        "controlled_public_origin_workload_deploy_packet": "docs/results/controlled-public-origin-workload-deploy-packet-20260701.md",
        "controlled_public_origin_workload_deploy_packet_json": "data/controlled-public-origin-workload-deploy-packet-20260701.json",
        "noniphone_desktop_path_change_readiness": "docs/results/noniphone-desktop-path-change-readiness-20260701.md",
        "noniphone_desktop_path_change_readiness_json": "data/noniphone-desktop-path-change-readiness-20260701.json",
        "noniphone_public_workload_trial_packet": "docs/results/noniphone-public-workload-trial-packet-20260701.md",
        "noniphone_public_workload_trial_packet_json": "data/noniphone-public-workload-trial-packet-20260701.json",
        "noniphone_claim_readiness_dashboard": "docs/results/noniphone-claim-readiness-dashboard-20260701.md",
        "noniphone_claim_readiness_dashboard_json": "data/noniphone-claim-readiness-dashboard-20260701.json",
        "noniphone_professor_decision_packet": "docs/results/noniphone-professor-decision-packet-20260701.md",
        "noniphone_professor_decision_packet_json": "data/noniphone-professor-decision-packet-20260701.json",
        "noniphone_reviewer_risk_audit": "docs/results/noniphone-reviewer-risk-audit-20260701.md",
        "noniphone_reviewer_risk_audit_json": "data/noniphone-reviewer-risk-audit-20260701.json",
        "noniphone_paper_wording_guard": "docs/results/noniphone-paper-wording-guard-20260701.md",
        "noniphone_paper_wording_guard_json": "data/noniphone-paper-wording-guard-20260701.json",
        "noniphone_paper_section_scaffold": "docs/results/noniphone-paper-section-scaffold-20260701.md",
        "noniphone_paper_section_scaffold_json": "data/noniphone-paper-section-scaffold-20260701.json",
        "non_quicgo_implementation_findings": "docs/results/non-quicgo-implementation-findings-20260701.md",
        "non_quicgo_implementation_findings_json": "data/non-quicgo-implementation-findings-20260701.json",
        "non_quicgo_execution_depth_audit": "docs/results/non-quicgo-execution-depth-audit-20260701.md",
        "non_quicgo_execution_depth_audit_json": "data/non-quicgo-execution-depth-audit-20260701.json",
        "non_quicgo_execution_depth_audit_csv": "data/non-quicgo-execution-depth-audit-20260701.csv",
        "msquic_migration_api_boundary_audit": "docs/results/msquic-migration-api-boundary-audit-20260701.md",
        "msquic_migration_api_boundary_audit_json": "data/msquic-migration-api-boundary-audit-20260701.json",
        "xquic_full_suite_linux_audit": "docs/results/xquic-full-suite-linux-audit-20260701.md",
        "xquic_full_suite_linux_audit_json": "data/xquic-full-suite-linux-audit-20260701.json",
        "xquic_full_suite_linux_runner": "harness/scripts/run-xquic-full-suite-linux.sh",
        "chrome_desktop_noniphone_range_local_refresh": "docs/results/chrome-desktop-noniphone-range-local-refresh-20260630.md",
        "chrome_desktop_noniphone_range_local_refresh_csv": "data/chrome-desktop-noniphone-range-local-refresh-20260630.csv",
        "chrome_desktop_noniphone_upload_local_refresh": "docs/results/chrome-desktop-noniphone-upload-local-refresh-20260630.md",
        "chrome_desktop_noniphone_upload_local_refresh_csv": "data/chrome-desktop-noniphone-upload-local-refresh-20260630.csv",
        "controlled_public_chrome_bridge_synthesis": "docs/results/controlled-public-chrome-bridge-synthesis-20260701.md",
        "controlled_public_chrome_bridge_synthesis_json": "data/controlled-public-chrome-bridge-synthesis-20260701.json",
        "controlled_public_chrome_bridge_synthesis_csv": "data/controlled-public-chrome-bridge-synthesis-20260701.csv",
        "controlled_public_chrome_artifact_classifier_contract": "docs/results/controlled-public-chrome-artifact-classifier-contract-20260701.md",
        "controlled_public_chrome_artifact_classifier_contract_json": "data/controlled-public-chrome-artifact-classifier-contract-20260701.json",
        "controlled_public_chrome_contract_application_audit": "docs/results/controlled-public-chrome-contract-application-audit-20260701.md",
        "controlled_public_chrome_contract_application_audit_json": "data/controlled-public-chrome-contract-application-audit-20260701.json",
        "controlled_public_chrome_contract_application_audit_csv": "data/controlled-public-chrome-contract-application-audit-20260701.csv",
        "haproxy_negative_control": "docs/results/haproxy-http3-negative-control-rerun-20260630.md",
        "lsquic_preferred_address_demo": "docs/results/lsquic-preferred-address-app-demo-20260630.md",
        "lsquic_nat_rebinding_demo": "docs/results/lsquic-nat-rebinding-app-demo-20260630.md",
        "quicly_e2e_path_migration": "docs/results/quicly-e2e-path-migration-20260630.md",
        "openlitespeed_source_feasibility": "docs/results/openlitespeed-quic-cm-source-feasibility-20260630.md",
        "openlitespeed_runtime_preflight": "docs/results/openlitespeed-runtime-preflight-20260630.md",
        "openlitespeed_runtime_runner": "docs/results/openlitespeed-active-migration-runner-20260630.md",
        "mvfst_source_audit": "docs/results/mvfst-cm-source-audit-20260630.md",
        "mvfst_migration_test_readiness": "docs/results/mvfst-migration-test-readiness-20260630.md",
        "mvfst_migration_test_readiness_json": "data/mvfst-migration-test-readiness-20260630.json",
        "mvfst_focused_linux_runner_audit": "docs/results/mvfst-focused-linux-runner-audit-20260701.md",
        "mvfst_focused_linux_runner_audit_json": "data/mvfst-focused-linux-runner-audit-20260701.json",
        "mvfst_focused_linux_runner": "harness/scripts/run-mvfst-focused-migration-tests-linux.sh",
        "s2n_nlb_cid_provider_rerun": "docs/results/s2n-quic-nlb-cid-provider-rerun-20260630.md",
        "s2n_nlb_live_readiness": "docs/results/s2n-nlb-live-readiness-20260630.md",
        "aws_s2n_nlb_live_runner": "docs/results/aws-s2n-nlb-live-runner-20260630.md",
        "aws_s2n_live_runner_safety_audit": "docs/results/aws-s2n-live-runner-safety-audit-20260701.md",
        "aws_s2n_live_runner_safety_audit_json": "data/aws-s2n-live-runner-safety-audit-20260701.json",
        "aws_s2n_phase2_path_change_design": "docs/results/aws-s2n-phase2-path-change-design-20260701.md",
        "aws_s2n_phase2_path_change_design_json": "data/aws-s2n-phase2-path-change-design-20260701.json",
        "aws_s2n_phase2_rebinding_preflight_fixture": "data/aws-s2n-phase2-rebinding-preflight-20260701.txt",
        "aws_s2n_phase2_rebinding_runner_audit": "docs/results/aws-s2n-phase2-rebinding-runner-audit-20260701.md",
        "aws_s2n_phase2_rebinding_runner_audit_json": "data/aws-s2n-phase2-rebinding-runner-audit-20260701.json",
        "aws_s2n_phase2_artifact_classifier_contract": "docs/results/aws-s2n-phase2-artifact-classifier-contract-20260701.md",
        "aws_s2n_phase2_artifact_classifier_contract_json": "data/aws-s2n-phase2-artifact-classifier-contract-20260701.json",
        "s2n_active_migration_api_audit": "docs/results/s2n-active-migration-api-audit-20260630.md",
        "s2n_active_migration_api_audit_json": "data/s2n-active-migration-api-audit-20260630.json",
        "browser_cm_observability_refresh": "docs/results/browser-cm-observability-readiness-refresh-20260630.md",
        "browser_cm_observability_refresh_json": "data/browser-cm-observability-refresh-20260630.json",
        "safari_webdriver_session_readiness": "docs/results/safari-webdriver-session-readiness-20260630.md",
        "user_provided_public_origin_readiness": "docs/results/user-provided-public-origin-readiness-20260630.md",
        "user_provided_public_origin_readiness_json": "data/user-provided-public-origin-readiness-20260630.json",
        "non_iphone_gate_rerun": "docs/results/non-iphone-gate-rerun-20260701.md",
        "non_iphone_gate_rerun_json": "data/non-iphone-gate-rerun-20260701.json",
        "non_iphone_next_research_decision": "docs/results/non-iphone-next-research-decision-20260630.md",
        "non_iphone_next_research_decision_json": "data/non-iphone-next-research-decision-20260630.json",
        "research_report_index": "docs/research-report/README.md",
    }

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "tracked_manifest_note": "The source commit is the commit used when generating this tracked manifest. Regenerate the manifest after checkout to bind it to a later commit.",
        "git": asdict(git),
        "experiment_corpus": {
            "total_trials": len(experiments),
            "status_counts": dict(sorted(status_counts.items())),
            "final_required_rows": len(requirements),
        },
        "implementation_corpus": {
            "total_implementations": len(implementation_survey),
            "evidence_status_counts": count_by(implementation_survey, "evidence_status"),
            "current_level_counts": count_by(implementation_survey, "current_level"),
            "top_priority_names": [row.get("name", "-") for row in implementation_survey[:5]],
        },
        "experiment_matrix": {
            "total_items": len(experiment_matrix),
            "status_counts": count_by(experiment_matrix, "status"),
            "latest_item": experiment_matrix[-1].get("id", "-") if experiment_matrix else "-",
        },
        "verification": {
            "checks": verification_summary.get("checks", "-"),
            "passed": verification_summary.get("passed", "-"),
            "ok": verification_summary.get("verification ok", "-"),
        },
        "research_audit": {
            "publication_bundle_ok": final_summary.get("publication bundle ok", "-"),
            "required_files_ok": final_summary.get("required files ok", "-"),
            "paper_tables_current": final_summary.get("paper tables current", "-"),
            "final_browser_handover_trials": final_summary.get("final browser handover trials", "-"),
            "goal_complete": final_summary.get("goal complete", "-"),
        },
        "readiness": {
            "next_trial": external_inputs.get("next trial", "-"),
            "next_trial_ready": external_inputs.get("next trial ready", "-"),
            "codex_can_run_next_trial_now": external_inputs.get("Codex can run next trial now", "-"),
            "needed_now_inputs": external_inputs.get("needed-now inputs", "-"),
        },
        "ci": ci,
        "key_paths": {
            "audit": "docs/results/research-bundle-audit-20260624.md",
            "verification": "docs/results/research-verification-report-20260624.md",
            "status_dashboard": "docs/results/research-status-dashboard-20260624.md",
            "cm_operational_friction_matrix": "docs/results/cm-operational-friction-matrix-20260624.md",
            "final_protocol_readiness_matrix": "docs/results/final-protocol-readiness-matrix-20260624.md",
            "p0_unblock_status": "docs/results/p0-unblock-status-20260624.md",
            "p0_baseline_execution_packet": "docs/results/p0-baseline-execution-packet-20260624.md",
            "p0_baseline_preflight": "docs/results/p0-baseline-preflight-check-20260624.md",
            "p0_baseline_preflight_controls": "docs/results/p0-baseline-preflight-control-report-20260624.md",
            "p0_baseline_preflight_redaction_smoke": "docs/results/final-p0-baseline-preflight-redaction-smoke-20260625.md",
            "final_capture_storage_budget": "docs/results/final-capture-storage-budget-20260624.md",
            "artifact_cleanup_apply_report": "docs/results/artifact-cleanup-apply-report-20260625.md",
            "artifact_cleanup_execution_log": "docs/results/artifact-cleanup-execution-log-20260625.md",
            "final_trial_acceptance_scorecard": "docs/results/final-trial-acceptance-scorecard-20260624.md",
            "paper_gap_register": "docs/results/paper-evidence-gap-register-20260624.md",
            "paper_claim_support_matrix": "docs/results/paper-claim-support-matrix-20260624.md",
            "replication_sufficiency_audit": "docs/results/replication-sufficiency-audit-20260624.md",
            "replication_run_plan": "docs/results/replication-run-plan-20260624.md",
            "external_inputs": "docs/results/final-handover-external-inputs-20260624.md",
            "trial_packet": "docs/results/final-handover-trial-packet-20260624.md",
            "deploy_packet": "docs/results/controlled-public-origin-deploy-packet-20260624.md",
            "controlled_public_package_smoke": "docs/results/controlled-public-package-smoke-20260625.md",
            "aws_identity_readiness": "docs/results/aws-identity-readiness-20260625.md",
            "active_path_cookbook": "docs/results/active-path-change-operator-cookbook-20260624.md",
        },
        "evidence_paths_20260630": path_status(evidence_paths_20260630),
    }


def emit_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Reproducibility Manifest",
        "",
        f"Generated: `{manifest['generated']}`",
        "",
        "This manifest is public-safe. It summarizes reproducibility state without printing domains, credentials, private keys, device IDs, qlogs, keylogs, pcaps, or NetLogs.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| source commit at generation | `{manifest['git']['commit']}` |",
        f"| branch | `{manifest['git']['branch']}` |",
        f"| total trials | `{manifest['experiment_corpus']['total_trials']}` |",
        f"| status counts | `{manifest['experiment_corpus']['status_counts']}` |",
        f"| implementation survey rows | `{manifest['implementation_corpus']['total_implementations']}` |",
        f"| implementation evidence status counts | `{manifest['implementation_corpus']['evidence_status_counts']}` |",
        f"| experiment matrix items | `{manifest['experiment_matrix']['total_items']}` |",
        f"| latest experiment matrix item | `{manifest['experiment_matrix']['latest_item']}` |",
        f"| verification | `{manifest['verification']['passed']}/{manifest['verification']['checks']} passed; ok={manifest['verification']['ok']}` |",
        f"| final browser handover | `{manifest['research_audit']['final_browser_handover_trials']}` |",
        f"| goal complete | `{manifest['research_audit']['goal_complete']}` |",
        f"| next trial | `{manifest['readiness']['next_trial']}` |",
        f"| next trial ready | `{manifest['readiness']['next_trial_ready']}` |",
        f"| needed-now inputs | `{manifest['readiness']['needed_now_inputs']}` |",
        f"| CI | `{manifest['ci'].get('status', '-')}/{manifest['ci'].get('conclusion', '-')}` |",
        "",
        "## Key Paths",
        "",
        "| item | path |",
        "| --- | --- |",
    ]
    for key, path in manifest["key_paths"].items():
        lines.append(f"| `{key}` | `{path}` |")
    lines.extend(
        [
            "",
            "## 2026-06-30 Evidence Paths",
            "",
            "| item | path | exists |",
            "| --- | --- | --- |",
        ]
    )
    for key, item in manifest["evidence_paths_20260630"].items():
        lines.append(f"| `{key}` | `{item['path']}` | `{'yes' if item['exists'] else 'no'}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A green manifest does not mean the final browser handover protocol is complete.",
            "- Completion still requires final browser handover rows to satisfy the required trial protocol.",
            "- This manifest records the exact reproducibility state for the current commit and points to the authoritative audit documents.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--include-ci", action="store_true")
    args = parser.parse_args()

    manifest = build_manifest(include_ci=args.include_ci)
    markdown = emit_markdown(manifest)
    json_text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"

    if args.json_output:
        json_output = Path(args.json_output)
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json_text, encoding="utf-8")

    text = json_text if args.format == "json" else markdown
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
