# Research Status Dashboard

Generated: `2026-06-26`

This dashboard is public-safe. It summarizes tracked, redacted research state without printing private domains, TLS paths, network-change commands, qlogs, NetLogs, pcaps, device IDs, or credentials.

## Summary

| field | value |
| --- | --- |
| experiment trials | `71` |
| experiment status counts | `{'PASS': 28, 'PASS_FEASIBILITY': 6, 'PASS_NEGATIVE_CONTROL': 37}` |
| verification | `109/109 passed; ok=yes` |
| CI | `-/- (-)` |
| final browser handover | `3/6` |
| needed-now external inputs | `[]` |
| planned execution states | `{'blocked': 7, 'recorded': 3}` |
| claim support | `{'negative_control_supported': 1, 'not_supported_yet': 2, 'supported_local_control': 4, 'supported_scoped': 2}` |
| replication roles | `{'failure_candidate': 11, 'stable_candidate': 14, 'transition_zone': 5}` |
| paper-use scorecard | `{'baseline/control evidence available': 3, 'pending; do not claim browser CM success': 3}` |
| operational friction | `{'cautious explanatory support': 2, 'related-work support only': 1, 'source-backed explanation with repo evidence': 10}` |

## Next Operator Action

Prepare an active secondary path and an operator-approved NETWORK_CHANGE_CMD.

## Needed-Now External Inputs

| input id |
| --- |
| - |

## Missing Gate Counts

| gate | blocked planned executions |
| --- | ---: |
| `desktop_secondary_path_ready` | 7 |
| `network_change_command_present` | 7 |

## Claim Boundary

Do not claim Chrome/Safari/Android browser handover CM success until the final browser handover protocol has countable rows.

## Key Paths

| item | path |
| --- | --- |
| `manifest` | `data/reproducibility-manifest-20260624.json` |
| `readiness_matrix` | `data/final-protocol-readiness-matrix-20260624.csv` |
| `p0_unblock_status` | `data/p0-unblock-status-20260624.csv` |
| `p0_baseline_execution_packet` | `data/p0-baseline-execution-packet-20260624.csv` |
| `p0_baseline_preflight` | `data/p0-baseline-preflight-check-20260624.csv` |
| `p0_baseline_preflight_controls` | `data/p0-baseline-preflight-control-report-20260624.csv` |
| `final_capture_storage_budget` | `data/final-capture-storage-budget-20260624.csv` |
| `artifact_cleanup_apply_report` | `docs/results/artifact-cleanup-apply-report-20260625.md` |
| `external_inputs` | `docs/results/final-handover-external-inputs-20260624.md` |
| `aws_identity_readiness` | `data/aws-identity-readiness-20260625.json` |
| `acceptance_scorecard` | `data/final-trial-acceptance-scorecard-20260624.csv` |
| `operational_friction_matrix` | `data/cm-operational-friction-matrix-20260624.csv` |
| `paper_claim_support_matrix` | `data/paper-claim-support-matrix-20260624.csv` |
| `replication_sufficiency_audit` | `data/replication-sufficiency-audit-20260624.csv` |
| `replication_run_plan` | `data/replication-run-plan-20260624.csv` |
| `experiment_results` | `data/experiment-results.csv` |
