# Controlled Public Chrome Contract Application Audit

Generated: `2026-07-01`

This public-safe audit applies the controlled-public Chrome artifact classifier contract to the tracked bridge synthesis rows. It does not inspect raw qlogs, NetLogs, pcaps, hostnames, IP addresses, credentials, or untracked local notes.

## Summary

| field | value |
| --- | --- |
| source bridge | `data/controlled-public-chrome-bridge-synthesis-20260701.json` |
| source contract | `data/controlled-public-chrome-artifact-classifier-contract-20260701.json` |
| contract id | `controlled-public-chrome-artifact-classifier-contract` |
| source record count | `18` |
| active rows | `12` |
| baseline rows | `6` |
| contract class counts | `{'application_recovery_or_reconnect': 2, 'negative_control_record': 10, 'public_h3_baseline_positive': 6}` |
| paper use counts | `{'use_as_negative_or_gap_evidence': 10, 'use_as_public_h3_baseline': 6, 'use_as_task_completion_without_cm_success': 2}` |
| active missing strong gate counts | `{'application_completion_metric_true': 10, 'chrome_single_target_quic_session': 12, 'client_active_path_changed': 1, 'server_qlog_path_validation': 12, 'server_target_h3_tuple_changed': 10}` |
| strong single-session CM rows | `[]` |
| application completion without CM rows | `['controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001', 'controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-003']` |

## Interpretation

- Supported: Applying the contract to tracked bridge rows yields public H3 baselines and conservative gap/negative-control evidence.
- Not supported: No tracked row satisfies the full strong single-session public Chrome CM contract.
- Paper use: Use this audit as the current public Chrome claim ledger until new raw artifacts pass the source classifier and the contract.

## Contract-Applied Rows

| trial | source class | trigger | workload | app | client path | tuple | qlog path | contract class | missing strong gates | paper use |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-001` | `application_task_failed_without_quic_path_validation` | `active_network_change` | `downlink` | `False` | `True` | `False` | `False` | `negative_control_record` | `application_completion_metric_true;server_target_h3_tuple_changed;server_qlog_path_validation;chrome_single_target_quic_session` | `use_as_negative_or_gap_evidence` |
| `controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-002` | `application_task_failed_without_quic_path_validation` | `active_network_change` | `downlink` | `False` | `True` | `False` | `False` | `negative_control_record` | `application_completion_metric_true;server_target_h3_tuple_changed;server_qlog_path_validation;chrome_single_target_quic_session` | `use_as_negative_or_gap_evidence` |
| `controlled-public-chrome-downlink-full-nochange-fresh-20260629-001` | `controlled_public_application_h3_confirmed` | `nochange_baseline` | `downlink` | `True` | `False` | `False` | `False` | `public_h3_baseline_positive` | `-` | `use_as_public_h3_baseline` |
| `controlled-public-chrome-downlink-heartbeat-network-change-20260629-001` | `no_client_active_path_change_observed` | `active_network_change` | `downlink` | `False` | `False` | `False` | `False` | `negative_control_record` | `application_completion_metric_true;client_active_path_changed;server_target_h3_tuple_changed;server_qlog_path_validation;chrome_single_target_quic_session` | `use_as_negative_or_gap_evidence` |
| `controlled-public-chrome-downlink-heartbeat-nochange-20260629-001` | `controlled_public_application_h3_confirmed` | `nochange_baseline` | `downlink` | `True` | `False` | `False` | `False` | `public_h3_baseline_positive` | `-` | `use_as_public_h3_baseline` |
| `controlled-public-chrome-downlink-noheartbeat-network-change-20260629-001` | `application_task_failed_without_quic_path_validation` | `active_network_change` | `downlink` | `False` | `True` | `False` | `False` | `negative_control_record` | `application_completion_metric_true;server_target_h3_tuple_changed;server_qlog_path_validation;chrome_single_target_quic_session` | `use_as_negative_or_gap_evidence` |
| `controlled-public-chrome-downlink-noheartbeat-network-change-20260629-002` | `application_task_failed_without_quic_path_validation` | `active_network_change` | `downlink` | `False` | `True` | `False` | `False` | `negative_control_record` | `application_completion_metric_true;server_target_h3_tuple_changed;server_qlog_path_validation;chrome_single_target_quic_session` | `use_as_negative_or_gap_evidence` |
| `controlled-public-chrome-downlink-noheartbeat-network-change-20260629-003` | `application_task_failed_without_quic_path_validation` | `active_network_change` | `downlink` | `False` | `True` | `False` | `False` | `negative_control_record` | `application_completion_metric_true;server_target_h3_tuple_changed;server_qlog_path_validation;chrome_single_target_quic_session` | `use_as_negative_or_gap_evidence` |
| `controlled-public-chrome-downlink-noheartbeat-network-change-page-ready-20260629-001` | `application_task_failed_without_quic_path_validation` | `active_network_change` | `downlink` | `False` | `True` | `False` | `False` | `negative_control_record` | `application_completion_metric_true;server_target_h3_tuple_changed;server_qlog_path_validation;chrome_single_target_quic_session` | `use_as_negative_or_gap_evidence` |
| `controlled-public-chrome-downlink-noheartbeat-nochange-20260629-003` | `controlled_public_application_h3_confirmed` | `nochange_baseline` | `downlink` | `True` | `False` | `False` | `False` | `public_h3_baseline_positive` | `-` | `use_as_public_h3_baseline` |
| `controlled-public-chrome-fresh-origin-smoke-20260629-005` | `controlled_public_application_h3_confirmed` | `nochange_baseline` | `origin_smoke` | `True` | `False` | `False` | `False` | `public_h3_baseline_positive` | `-` | `use_as_public_h3_baseline` |
| `controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-001` | `application_task_failed_without_quic_path_validation` | `active_network_change` | `byte_range_download` | `False` | `True` | `False` | `False` | `negative_control_record` | `application_completion_metric_true;server_target_h3_tuple_changed;server_qlog_path_validation;chrome_single_target_quic_session` | `use_as_negative_or_gap_evidence` |
| `controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-002` | `application_task_failed_without_quic_path_validation` | `active_network_change` | `byte_range_download` | `False` | `True` | `False` | `False` | `negative_control_record` | `application_completion_metric_true;server_target_h3_tuple_changed;server_qlog_path_validation;chrome_single_target_quic_session` | `use_as_negative_or_gap_evidence` |
| `controlled-public-chrome-range-noretry-nochange-fresh-20260629-001` | `controlled_public_application_h3_confirmed` | `nochange_baseline` | `byte_range_download` | `True` | `False` | `False` | `False` | `public_h3_baseline_positive` | `-` | `use_as_public_h3_baseline` |
| `controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001` | `tuple_changed_without_path_validation` | `active_network_change` | `byte_range_download` | `True` | `True` | `True` | `False` | `application_recovery_or_reconnect` | `server_qlog_path_validation;chrome_single_target_quic_session` | `use_as_task_completion_without_cm_success` |
| `controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-002` | `application_task_failed_without_quic_path_validation` | `active_network_change` | `byte_range_download` | `False` | `True` | `False` | `False` | `negative_control_record` | `application_completion_metric_true;server_target_h3_tuple_changed;server_qlog_path_validation;chrome_single_target_quic_session` | `use_as_negative_or_gap_evidence` |
| `controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-003` | `tuple_changed_without_path_validation` | `active_network_change` | `byte_range_download` | `True` | `True` | `True` | `False` | `application_recovery_or_reconnect` | `server_qlog_path_validation;chrome_single_target_quic_session` | `use_as_task_completion_without_cm_success` |
| `controlled-public-chrome-range-retry-nochange-fresh-20260629-001` | `controlled_public_application_h3_confirmed` | `nochange_baseline` | `byte_range_download` | `True` | `False` | `False` | `False` | `public_h3_baseline_positive` | `-` | `use_as_public_h3_baseline` |

## Claim Boundary

The two tracked active rows with application completion still miss qlog path validation and Chrome single-session evidence, so they remain task-completion-without-CM-support rows. The other active rows remain negative/gap records. The no-change rows are useful H3 baselines, but they are not active Connection Migration evidence.
