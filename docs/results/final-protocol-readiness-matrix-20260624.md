# Final Protocol Readiness Matrix

Generated: `2026-06-25`

This matrix is public-safe. It evaluates every planned final browser handover execution against the current local readiness gates without printing private domains, TLS paths, or network-change commands.

## Summary

| field | value |
| --- | --- |
| final protocol complete | `no` |
| complete requirements | `0/6` |
| planned executions | `10` |
| config exists | `no` |
| public origin URL | `-` |
| state counts | `{'blocked': 10}` |

## Global Gates

| gate | value |
| --- | --- |
| `controlled_public_config_present` | `no` |
| `public_origin_host_configured` | `no` |
| `public_origin_url_configured` | `no` |
| `tls_config_present` | `no` |
| `tls_cert_file_exists` | `no` |
| `tls_key_file_exists` | `no` |
| `disk_ready` | `yes` |
| `chrome_ready` | `yes` |
| `safari_webdriver_ready` | `yes` |
| `android_adb_ready` | `no` |
| `desktop_secondary_path_ready` | `no` |
| `baseline_summary_ready` | `no` |
| `network_change_command_present` | `no` |
| `android_network_change_command_present` | `no` |

## Planned Trial Readiness

| order | trial | phase | browser | state | missing gates |
| ---: | --- | --- | --- | --- | --- |
| 1 | `controlled-public-chrome-h3-baseline-001` | baseline | Chrome | `blocked` | `controlled_public_config_present, public_origin_host_configured, public_origin_url_configured, tls_config_present` |
| 2 | `controlled-public-chrome-downlink-noheartbeat-nochange-001` | no-change-baseline | Chrome | `blocked` | `controlled_public_config_present, public_origin_host_configured, public_origin_url_configured, tls_config_present` |
| 3 | `controlled-public-chrome-downlink-heartbeat-nochange-001` | no-change-baseline | Chrome | `blocked` | `controlled_public_config_present, public_origin_host_configured, public_origin_url_configured, tls_config_present` |
| 4 | `controlled-public-chrome-downlink-noheartbeat-network-change-001` | active-network-change | Chrome | `blocked` | `controlled_public_config_present, public_origin_host_configured, public_origin_url_configured, tls_config_present, baseline_summary_ready, network_change_command_present, desktop_secondary_path_ready` |
| 5 | `controlled-public-chrome-downlink-noheartbeat-network-change-002` | active-network-change | Chrome | `blocked` | `controlled_public_config_present, public_origin_host_configured, public_origin_url_configured, tls_config_present, baseline_summary_ready, network_change_command_present, desktop_secondary_path_ready` |
| 6 | `controlled-public-chrome-downlink-noheartbeat-network-change-003` | active-network-change | Chrome | `blocked` | `controlled_public_config_present, public_origin_host_configured, public_origin_url_configured, tls_config_present, baseline_summary_ready, network_change_command_present, desktop_secondary_path_ready` |
| 7 | `controlled-public-chrome-downlink-heartbeat-network-change-001` | active-network-change | Chrome | `blocked` | `controlled_public_config_present, public_origin_host_configured, public_origin_url_configured, tls_config_present, baseline_summary_ready, network_change_command_present, desktop_secondary_path_ready` |
| 8 | `controlled-public-chrome-downlink-heartbeat-network-change-002` | active-network-change | Chrome | `blocked` | `controlled_public_config_present, public_origin_host_configured, public_origin_url_configured, tls_config_present, baseline_summary_ready, network_change_command_present, desktop_secondary_path_ready` |
| 9 | `controlled-public-chrome-downlink-heartbeat-network-change-003` | active-network-change | Chrome | `blocked` | `controlled_public_config_present, public_origin_host_configured, public_origin_url_configured, tls_config_present, baseline_summary_ready, network_change_command_present, desktop_secondary_path_ready` |
| 10 | `controlled-public-safari-downlink-network-change-001` | p1-feasibility | Safari | `blocked` | `controlled_public_config_present, public_origin_host_configured, public_origin_url_configured, tls_config_present, desktop_secondary_path_ready, baseline_summary_ready, network_change_command_present` |
