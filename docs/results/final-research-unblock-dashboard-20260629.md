# Final Research Unblock Dashboard

Generated: `2026-06-29`

## Summary

| field | value |
| --- | --- |
| next trial | controlled-public-chrome-downlink-noheartbeat-network-change-001 |
| next trial ready | no |
| missing required gates | desktop_path_change_ready, public_origin_live_ready |
| P0 blockers | aws_identity_or_manual_origin_access, public_origin_live_h3, desktop_path_change_ready |
| final protocol | 3/6 |
| public origin | not_ready |
| iPhone USB | iphone_usb_service_configured_hardware_absent |

## Unblock Actions

| priority | gate | status | owner | evidence | next action | success gate |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | aws_identity_or_manual_origin_access | blocked | operator | aws=invalid_client_token; ssh_ready=no; local_tls_ready=no | python3 tools/import_aws_credentials_csv.py ~/Downloads/YOUR_AWS_CREDENTIALS.csv<br>python3 tools/import_aws_credentials_csv.py ~/Downloads/YOUR_AWS_CREDENTIALS.csv \<br>  --profile default \<br>  --region ap-northeast-2 \<br>  --write \<br>  --validate<br>bash harness/scripts/aws-preflight.sh | AWS identity ready, SSH recovery ready, or local TLS/origin material ready. |
| P0 | public_origin_live_h3 | blocked | operator+codex | public_origin=not_ready; tcp=connection_refused; h3_alt_svc=no | Recover/restart the controlled public origin, then rerun public origin readiness. | check_public_origin_readiness ok=true and has_h3_alt_svc=true. |
| P0 | desktop_path_change_ready | blocked | operator+codex | mode=not-ready; iphone=iphone_usb_service_configured_hardware_absent; secondary=no | Reconnect the USB-C cable and unlock the iPhone. | desktop_path_change_ready=yes or latent_iphone_usb_failover_observed with --allow-latent-secondary-path. |
| P1 | fresh_public_h3_baseline | waiting | codex | historical_baseline=PASS; public_origin_ok=no | Rerun the controlled public Chrome H3 no-change baseline after origin recovery. | new controlled-public baseline summary status PASS with application HTTP/3 confirmed. |
| P1 | next_chrome_active_row | waiting | codex | next_trial=controlled-public-chrome-downlink-noheartbeat-network-change-001; missing=desktop_path_change_ready,public_origin_live_ready; final=3/6 | Run the selected Chrome no-heartbeat active public row only after all P0 gates are ready. | artifact bundle validates and final trial audit count increases for no-heartbeat active CM. |
| P2 | p1_cross_browser_feasibility | waiting | codex | safari_webdriver=yes; android_adb=no | After Chrome active rows, run Safari feasibility first unless an Android ADB device is connected. | At least one Safari or Android feasibility row is countable in final audit. |

## Execution Rule

- Do not run the selected Chrome active public row until every P0 gate is `ready`.
- After P0 is ready, refresh the public H3 baseline before appending new active rows.
- Treat this dashboard as readiness evidence only, not as QUIC CM success evidence.

## Claim Boundary

This dashboard is an execution/unblock artifact. It is not QUIC migration evidence; only validated final trial artifacts can support browser CM claims.

## Regenerate

`python3 tools/build_final_research_unblock_dashboard.py`
