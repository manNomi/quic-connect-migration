# Research Status Dashboard

Generated: `2026-06-24`

This dashboard is public-safe. It summarizes tracked, redacted research state without printing private domains, TLS paths, network-change commands, qlogs, NetLogs, pcaps, device IDs, or credentials.

## Summary

| field | value |
| --- | --- |
| experiment trials | `51` |
| experiment status counts | `{'PASS': 25, 'PASS_FEASIBILITY': 6, 'PASS_NEGATIVE_CONTROL': 20}` |
| verification | `69/69 passed; ok=yes` |
| CI | `-/- (-)` |
| final browser handover | `0/6` |
| planned execution states | `{'blocked': 10}` |
| paper-use scorecard | `{'pending; do not claim browser CM success': 3, 'pending; required before active CM claim': 3}` |
| operational friction | `{'cautious explanatory support': 2, 'related-work support only': 1, 'source-backed explanation with repo evidence': 10}` |

## Next Operator Action

Create and fill the ignored controlled-public origin env file, then validate baseline config.

## Missing Gate Counts

| gate | blocked planned executions |
| --- | ---: |
| `baseline_summary_ready` | 7 |
| `controlled_public_config_present` | 10 |
| `desktop_secondary_path_ready` | 7 |
| `network_change_command_present` | 7 |
| `public_origin_host_configured` | 10 |
| `public_origin_url_configured` | 10 |
| `tls_config_present` | 10 |

## Claim Boundary

Do not claim Chrome/Safari/Android browser handover CM success until the final browser handover protocol has countable rows.

## Key Paths

| item | path |
| --- | --- |
| `manifest` | `data/reproducibility-manifest-20260624.json` |
| `readiness_matrix` | `data/final-protocol-readiness-matrix-20260624.csv` |
| `acceptance_scorecard` | `data/final-trial-acceptance-scorecard-20260624.csv` |
| `operational_friction_matrix` | `data/cm-operational-friction-matrix-20260624.csv` |
| `experiment_results` | `data/experiment-results.csv` |
