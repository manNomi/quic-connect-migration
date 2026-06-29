# Cross-Browser Feasibility Readiness

Generated: `2026-06-29`

## Purpose

This report fixes the current Chrome/Safari/Android readiness boundary for the final browser handover protocol. It is a readiness and claim-boundary artifact, not migration evidence.

## Current Gates

| gate | value |
| --- | --- |
| final protocol | 3/6 |
| baseline | PASS; controlled_public_application_h3_confirmed |
| public origin | not_ready; h3_alt_svc=no |
| AWS identity | invalid_client_token |
| active path | macos_wifi_power_cutover: blocked: no active secondary non-loopback IPv4 path was detected; macos_wifi_to_iphone_usb_latent_failover: blocked: iPhone USB interface was not present in ifconfig output; macos_service_order_cutover: blocked: no active secondary service was detected; android_wifi_to_cellular_cutover: blocked: no ADB device is connected |
| Safari WebDriver | yes |
| Android ready | no |
| disk available GiB | 25.91 |

## Candidate Matrix

| candidate | paper role | local tooling | path-change gate | public-origin gate | protocol gap | next action |
| --- | --- | --- | --- | --- | --- | --- |
| Chrome active public handover | Main browser CM claim gate | Chrome NetLog=yes; Chrome binary=yes | desktop_path_ready=no; blocked: no active secondary non-loopback IPv4 path was detected; latent=blocked: iPhone USB interface was not present in ifconfig output | not_ready; h3_alt_svc=no | noheartbeat=0/3; heartbeat=0/3 | Recover public origin, restore a ready desktop path-change trigger, rerun fresh baseline, then run 3 no-heartbeat and 3 heartbeat rows. |
| Safari P1 feasibility | Cross-browser feasibility with weaker browser-internal observability | Safari WebDriver=yes; packet capture=yes; iOS rvictl=yes | desktop_path_ready=no; latent=blocked: iPhone USB interface was not present in ifconfig output | not_ready; h3_alt_svc=no | p1=0/1 | After public origin and Mac path-change are ready, run the Safari network-change wrapper and classify with missing-browser-netlog boundary. |
| Android Chrome P1 feasibility | True mobile-platform feasibility beyond Mac+iPhone tethered failover | ADB found=yes; Android device connected=no | android_path_ready=no; blocked: no ADB device is connected | not_ready; h3_alt_svc=no | p1=0/1 | Connect an Android device over ADB, verify cellular fallback, then run Android network-change wrapper after public origin recovery. |

## Claim Boundaries

| candidate | claim boundary |
| --- | --- |
| Chrome active public handover | Only counts as browser CM if application H3, client path change, server tuple change, qlog path validation, one Chrome target QUIC session, and task completion align in the same row. |
| Safari P1 feasibility | Safari lacks Chrome NetLog-equivalent evidence in this harness, so a PASS_FEASIBILITY row must be described as server/qlog/client-path evidence, not full browser-internal session proof. |
| Android Chrome P1 feasibility | Android Chrome rows need Android before/after route snapshots plus server/qlog evidence; without browser-internal NetLog they remain feasibility evidence unless stronger telemetry is added. |

## Safe Conclusion

Safari is currently closer than Android on local tooling, but neither can fill the P1 feasibility gate until the public origin and an active client path-change trigger are ready. Android additionally needs a connected ADB device.

## Regeneration

`python3 tools/build_cross_browser_feasibility_readiness.py`
