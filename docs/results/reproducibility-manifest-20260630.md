# Reproducibility Manifest

Generated: `2026-06-30`

This manifest is public-safe. It summarizes reproducibility state without printing domains, credentials, private keys, device IDs, qlogs, keylogs, pcaps, or NetLogs.

## Summary

| field | value |
| --- | --- |
| source commit at generation | `90701ab` |
| branch | `docs/quinn-neqo-rerun-20260630` |
| total trials | `99` |
| status counts | `{'PASS': 33, 'PASS_FEASIBILITY': 6, 'PASS_NEGATIVE_CONTROL': 60}` |
| implementation survey rows | `18` |
| implementation evidence status counts | `{'fresh_app_demo_20260630': 1, 'fresh_build_partial_20260630': 1, 'fresh_negative_control_20260630': 1, 'fresh_rebind_demo_20260630': 1, 'fresh_rerun_20260630': 9, 'fresh_runtime_20260630': 1, 'partial_deferred': 2, 'source_and_local_browser_baseline': 1, 'source_inspected': 1}` |
| experiment matrix items | `119` |
| latest experiment matrix item | `s2n-nlb-live-readiness` |
| verification | `109/109 passed; ok=yes` |
| final browser handover | `3/6` |
| goal complete | `no` |
| next trial | `controlled-public-chrome-downlink-noheartbeat-network-change-001` |
| next trial ready | `no` |
| needed-now inputs | `0` |
| CI | `-/-` |

## Key Paths

| item | path |
| --- | --- |
| `audit` | `docs/results/research-bundle-audit-20260624.md` |
| `verification` | `docs/results/research-verification-report-20260624.md` |
| `status_dashboard` | `docs/results/research-status-dashboard-20260624.md` |
| `cm_operational_friction_matrix` | `docs/results/cm-operational-friction-matrix-20260624.md` |
| `final_protocol_readiness_matrix` | `docs/results/final-protocol-readiness-matrix-20260624.md` |
| `p0_unblock_status` | `docs/results/p0-unblock-status-20260624.md` |
| `p0_baseline_execution_packet` | `docs/results/p0-baseline-execution-packet-20260624.md` |
| `p0_baseline_preflight` | `docs/results/p0-baseline-preflight-check-20260624.md` |
| `p0_baseline_preflight_controls` | `docs/results/p0-baseline-preflight-control-report-20260624.md` |
| `p0_baseline_preflight_redaction_smoke` | `docs/results/final-p0-baseline-preflight-redaction-smoke-20260625.md` |
| `final_capture_storage_budget` | `docs/results/final-capture-storage-budget-20260624.md` |
| `artifact_cleanup_apply_report` | `docs/results/artifact-cleanup-apply-report-20260625.md` |
| `artifact_cleanup_execution_log` | `docs/results/artifact-cleanup-execution-log-20260625.md` |
| `final_trial_acceptance_scorecard` | `docs/results/final-trial-acceptance-scorecard-20260624.md` |
| `paper_gap_register` | `docs/results/paper-evidence-gap-register-20260624.md` |
| `paper_claim_support_matrix` | `docs/results/paper-claim-support-matrix-20260624.md` |
| `replication_sufficiency_audit` | `docs/results/replication-sufficiency-audit-20260624.md` |
| `replication_run_plan` | `docs/results/replication-run-plan-20260624.md` |
| `external_inputs` | `docs/results/final-handover-external-inputs-20260624.md` |
| `trial_packet` | `docs/results/final-handover-trial-packet-20260624.md` |
| `deploy_packet` | `docs/results/controlled-public-origin-deploy-packet-20260624.md` |
| `controlled_public_package_smoke` | `docs/results/controlled-public-package-smoke-20260625.md` |
| `aws_identity_readiness` | `docs/results/aws-identity-readiness-20260625.md` |
| `active_path_cookbook` | `docs/results/active-path-change-operator-cookbook-20260624.md` |

## 2026-06-30 Evidence Paths

| item | path | exists |
| --- | --- | --- |
| `implementation_rerun_results` | `docs/results/implementation-rerun-results-20260630.md` | `yes` |
| `implementation_survey_csv` | `data/implementation-survey.csv` | `yes` |
| `experiment_matrix` | `harness/manifests/experiment-matrix.csv` | `yes` |
| `non_iphone_gap_plan` | `docs/results/non-iphone-research-gap-plan-20260630.md` | `yes` |
| `nginx_haproxy_boundary` | `docs/results/nginx-haproxy-quic-cm-boundary-20260630.md` | `yes` |
| `nginx_runtime_demo` | `docs/results/nginx-quic-active-migration-runtime-20260630.md` | `yes` |
| `haproxy_negative_control` | `docs/results/haproxy-http3-negative-control-rerun-20260630.md` | `yes` |
| `lsquic_preferred_address_demo` | `docs/results/lsquic-preferred-address-app-demo-20260630.md` | `yes` |
| `lsquic_nat_rebinding_demo` | `docs/results/lsquic-nat-rebinding-app-demo-20260630.md` | `yes` |
| `openlitespeed_source_feasibility` | `docs/results/openlitespeed-quic-cm-source-feasibility-20260630.md` | `yes` |
| `openlitespeed_runtime_preflight` | `docs/results/openlitespeed-runtime-preflight-20260630.md` | `yes` |
| `openlitespeed_runtime_runner` | `docs/results/openlitespeed-active-migration-runner-20260630.md` | `yes` |
| `mvfst_source_audit` | `docs/results/mvfst-cm-source-audit-20260630.md` | `yes` |
| `s2n_nlb_cid_provider_rerun` | `docs/results/s2n-quic-nlb-cid-provider-rerun-20260630.md` | `yes` |
| `s2n_nlb_live_readiness` | `docs/results/s2n-nlb-live-readiness-20260630.md` | `yes` |
| `research_report_index` | `docs/research-report/README.md` | `yes` |

## Interpretation

- A green manifest does not mean the final browser handover protocol is complete.
- Completion still requires final browser handover rows to satisfy the required trial protocol.
- This manifest records the exact reproducibility state for the current commit and points to the authoritative audit documents.
