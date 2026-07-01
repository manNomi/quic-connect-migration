# Controlled Public Chrome Bridge Synthesis

Generated: `2026-06-30`

This public-safe synthesis reads tracked Chrome controlled-public validation documents and classifies what they can and cannot prove. It intentionally excludes raw qlogs, NetLogs, pcaps, hostnames, IP addresses, credentials, and untracked local validation notes.

## Summary

| field | value |
| --- | --- |
| source scope | `tracked git files matching docs/results/controlled-public-chrome-*-validation.md` |
| trial count | `18` |
| active network-change rows | `12` |
| no-change baseline rows | `6` |
| baseline H3 confirmed rows | `6` |
| strong controlled-public CM success rows | `0` |
| active task success without path validation rows | `2` |
| active task failure without path validation rows | `10` |

## Counts

| category | counts |
| --- | --- |
| status | `{'PASS': 6, 'PASS_NEGATIVE_CONTROL': 12}` |
| classification | `{'application_task_failed_without_quic_path_validation': 9, 'controlled_public_application_h3_confirmed': 6, 'no_client_active_path_change_observed': 1, 'tuple_changed_without_path_validation': 2}` |
| claim strength | `{'counts_toward_final_protocol': 2, 'negative_control_record_only': 12, 'record_only_not_final_counting': 4}` |
| trigger | `{'active_network_change': 12, 'nochange_baseline': 6}` |
| workload | `{'byte_range_download': 7, 'downlink': 10, 'origin_smoke': 1}` |

## Interpretation

- Supported: Tracked controlled-public Chrome records confirm that the public origin could serve HTTP/3 browser workloads in no-change baselines, and that active path-change trials were executed and classified conservatively.
- Not supported: This corpus does not contain a controlled-public Chrome single-session Connection Migration success: no active-network-change row combines application success, tuple change, and QUIC path validation evidence.
- Paper use: Use these rows as deployment/browser bridge gap evidence and negative controls, not as final browser CM success evidence.

## Trial Rows

| trial | status | class | workload | trigger | app success | path validation | tuple change | claim strength |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-001` | `PASS_NEGATIVE_CONTROL` | `application_task_failed_without_quic_path_validation` | `downlink` | `active_network_change` | `False` | `False` | `False` | `negative_control_record_only` |
| `controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-002` | `PASS_NEGATIVE_CONTROL` | `application_task_failed_without_quic_path_validation` | `downlink` | `active_network_change` | `False` | `False` | `False` | `negative_control_record_only` |
| `controlled-public-chrome-downlink-full-nochange-fresh-20260629-001` | `PASS` | `controlled_public_application_h3_confirmed` | `downlink` | `nochange_baseline` | `True` | `False` | `True` | `record_only_not_final_counting` |
| `controlled-public-chrome-downlink-heartbeat-network-change-20260629-001` | `PASS_NEGATIVE_CONTROL` | `no_client_active_path_change_observed` | `downlink` | `active_network_change` | `False` | `False` | `False` | `negative_control_record_only` |
| `controlled-public-chrome-downlink-heartbeat-nochange-20260629-001` | `PASS` | `controlled_public_application_h3_confirmed` | `downlink` | `nochange_baseline` | `True` | `False` | `True` | `counts_toward_final_protocol` |
| `controlled-public-chrome-downlink-noheartbeat-network-change-20260629-001` | `PASS_NEGATIVE_CONTROL` | `application_task_failed_without_quic_path_validation` | `downlink` | `active_network_change` | `False` | `False` | `False` | `negative_control_record_only` |
| `controlled-public-chrome-downlink-noheartbeat-network-change-20260629-002` | `PASS_NEGATIVE_CONTROL` | `application_task_failed_without_quic_path_validation` | `downlink` | `active_network_change` | `False` | `False` | `False` | `negative_control_record_only` |
| `controlled-public-chrome-downlink-noheartbeat-network-change-20260629-003` | `PASS_NEGATIVE_CONTROL` | `application_task_failed_without_quic_path_validation` | `downlink` | `active_network_change` | `False` | `False` | `False` | `negative_control_record_only` |
| `controlled-public-chrome-downlink-noheartbeat-network-change-page-ready-20260629-001` | `PASS_NEGATIVE_CONTROL` | `application_task_failed_without_quic_path_validation` | `downlink` | `active_network_change` | `False` | `False` | `False` | `negative_control_record_only` |
| `controlled-public-chrome-downlink-noheartbeat-nochange-20260629-003` | `PASS` | `controlled_public_application_h3_confirmed` | `downlink` | `nochange_baseline` | `True` | `False` | `True` | `counts_toward_final_protocol` |
| `controlled-public-chrome-fresh-origin-smoke-20260629-005` | `PASS` | `controlled_public_application_h3_confirmed` | `origin_smoke` | `nochange_baseline` | `True` | `False` | `True` | `record_only_not_final_counting` |
| `controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-001` | `PASS_NEGATIVE_CONTROL` | `application_task_failed_without_quic_path_validation` | `byte_range_download` | `active_network_change` | `False` | `False` | `False` | `negative_control_record_only` |
| `controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-002` | `PASS_NEGATIVE_CONTROL` | `application_task_failed_without_quic_path_validation` | `byte_range_download` | `active_network_change` | `False` | `False` | `False` | `negative_control_record_only` |
| `controlled-public-chrome-range-noretry-nochange-fresh-20260629-001` | `PASS` | `controlled_public_application_h3_confirmed` | `byte_range_download` | `nochange_baseline` | `True` | `False` | `True` | `record_only_not_final_counting` |
| `controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001` | `PASS_NEGATIVE_CONTROL` | `tuple_changed_without_path_validation` | `byte_range_download` | `active_network_change` | `True` | `False` | `True` | `negative_control_record_only` |
| `controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-002` | `PASS_NEGATIVE_CONTROL` | `application_task_failed_without_quic_path_validation` | `byte_range_download` | `active_network_change` | `False` | `False` | `False` | `negative_control_record_only` |
| `controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-003` | `PASS_NEGATIVE_CONTROL` | `tuple_changed_without_path_validation` | `byte_range_download` | `active_network_change` | `True` | `False` | `True` | `negative_control_record_only` |
| `controlled-public-chrome-range-retry-nochange-fresh-20260629-001` | `PASS` | `controlled_public_application_h3_confirmed` | `byte_range_download` | `nochange_baseline` | `True` | `False` | `True` | `record_only_not_final_counting` |

## Claim Boundary

These records are useful because they show that the controlled public browser harness can produce both H3 baselines and conservative negative controls. They do not yet close the paper's strongest browser/deployment claim, because the active path-change rows do not show QUIC path validation and application continuity together.
