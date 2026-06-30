# P0 Baseline Preflight Check

Generated: `2026-06-30`

This check is public-safe. It decides whether the P0 controlled-public Chrome baseline may start server/client artifact capture.

## Summary

| field | value |
| --- | --- |
| go for capture | `no` |
| allowed next action | `fill-private-controlled-public-config` |
| next trial | `controlled-public-chrome-downlink-noheartbeat-network-change-001` |
| packet state | `blocked_by_readiness` |
| needed-now gates | `baseline_summary_ready; network_change_command_present` |
| missing required gates | `baseline_summary_ready; network_change_command_present; desktop_path_change_ready` |

## Checks

| check | required | ok | evidence | next action |
| --- | --- | --- | --- | --- |
| `next_trial_selected` | `yes` | `yes` | `trial_id=controlled-public-chrome-downlink-noheartbeat-network-change-001` | - |
| `next_trial_is_p0_baseline` | `yes` | `no` | `trial_id=controlled-public-chrome-downlink-noheartbeat-network-change-001` | do not use this guard for non-P0 trials |
| `baseline_config_ready` | `yes` | `yes` | `config_exists=True; baseline_config_ready=True` | fill harness/config/controlled-public-origin.env and rerun check_controlled_public_config.py |
| `needed_now_gates_cleared` | `yes` | `no` | `needed_now=baseline_summary_ready;network_change_command_present` | clear all needed-now gates in p0-unblock-status |
| `next_trial_ready` | `yes` | `no` | `missing_required=baseline_summary_ready;network_change_command_present;desktop_path_change_ready` | run check_next_final_handover_trial_readiness.py and fix missing gates |
| `disk_ready` | `yes` | `yes` | `disk_ready=yes` | free disk before heavy NetLog/qlog capture |
| `chrome_ready` | `yes` | `yes` | `chrome_ready=yes` | install or configure Chrome binary |

## Interpretation

- If `go for capture` is `no`, do not start the origin server or Chrome client capture stages.
- This guard should be run immediately before stage 2 of the P0 baseline execution packet.
- A `yes` here still only permits the baseline trial; it does not claim browser connection migration.
