# Non-iPhone Next Research Decision Brief

Generated: `2026-06-30`

This document chooses the next research step using only public-safe committed evidence IDs. It intentionally does not include credentials, IP addresses, hostnames, qlogs, pcaps, keylogs, or NetLogs.

## Summary

| field | value |
| --- | --- |
| source bundle | `data/sanitized-evidence-bundle-20260630.json` |
| source bundle exists | `True` |
| source bundle item count | `28` |
| candidate tracks | `6` |
| runnable now | `[]` |
| blocked track count | `6` |
| missing evidence IDs | `{}` |

## Recommendation

| rank | recommendation |
| ---: | --- |
| 1 | Refresh AWS credentials and run AWS NLB + s2n-quic live forwarding echo. |
| 2 | If AWS remains blocked, prepare a controlled public Chrome origin for media/range/upload page-ready trials. |
| 3 | Use Safari only as PASS_FEASIBILITY after Allow remote automation is enabled. |

> Do not keep expanding generic implementation survey now; the next paper-critical gain is a deployment/browser bridge.

## Candidate Tracks

| rank | track | current state | can run now | blocker | paper value | decision |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `aws-s2n-nlb-live-forwarding`<br>AWS NLB + s2n-quic live forwarding echo | `runner_ready_but_credential_blocked` | `false` | AWS identity still classifies as invalid_client_token on the current host. | Highest: directly answers the deployment/AWS part of the professor decision without needing iPhone. | Primary next step once AWS credentials are valid. |
| 2 | `chrome-controlled-public-workloads`<br>Chrome desktop controlled-public media/range/upload handover | `local_controls_pass_user_origin_not_h3_ready` | `false` | The user-provided public HTTPS origin is reachable but currently has no `Alt-Svc: h3`; a controlled H3 origin and active desktop path-change gate are still needed. | High: bridges local browser evidence to real public-origin web workload continuity without iPhone. | Best browser-facing next step after public origin is available. |
| 3 | `nginx-quic-bpf-linux`<br>nginx `quic_bpf` Linux production-routing check | `linux_runner_ready_local_host_blocked` | `false` | Current host is macOS; Linux/root/writable `/sys/fs/bpf` gate is required. | Medium-high: strengthens production server routing discussion and separates loopback runtime from deployment routing. | Good EC2/Linux follow-up if AWS is available but s2n live is deferred. |
| 4 | `openlitespeed-production-like`<br>OpenLiteSpeed production-like active-migration runtime | `runner_ready_local_binary_disk_blocked` | `false` | Local OpenLiteSpeed binary is missing and current macOS/disk conditions are not the right runtime environment. | Medium: upgrades LSQUIC example app evidence toward a production-like server stack. | Useful, but lower priority than AWS NLB+s2n for the professor's current decision. |
| 5 | `safari-desktop-baseline`<br>Safari desktop controlled-public baseline | `binary_ready_session_blocked` | `false` | Safari `Allow remote automation` is not enabled, so real WebDriver session creation fails. | Medium: adds cross-browser feasibility, but claim ceiling remains lower than Chrome because there is no NetLog-equivalent artifact. | Worth doing after one settings toggle, but not enough as the main paper contribution. |
| 6 | `mvfst-focused-tests`<br>mvfst focused migration tests on Linux/Buck | `source_test_map_ready_build_blocked` | `false` | Current host lacks the expected Buck/getdeps/disk setup for focused mvfst test execution. | Medium-low for immediate paper direction: it strengthens implementation maturity, which is already fairly well covered. | Defer unless the paper needs one more large-scale implementation appendix. |

## Evidence Trace

| track | evidence IDs | missing | next action |
| --- | --- | --- | --- |
| `aws-s2n-nlb-live-forwarding` | `s2n-nlb-cid-provider-proof`, `s2n-nlb-live-readiness`, `aws-s2n-nlb-live-runner`, `s2n-active-migration-api-audit`, `non-iphone-gate-rerun-20260701` | - | Refresh AWS credentials, then run `harness/scripts/run-aws-s2n-nlb-live-data-plane.sh`. |
| `chrome-controlled-public-workloads` | `chromium-cronet-policy-evidence`, `user-provided-public-origin-readiness`, `non-iphone-gate-rerun-20260701`, `chrome-desktop-noniphone-media-local-refresh`, `chrome-desktop-noniphone-range-local-refresh`, `chrome-desktop-noniphone-upload-local-refresh` | - | Prepare public origin, then run the controlled public Chrome media/range/upload wrappers. |
| `nginx-quic-bpf-linux` | `nginx-active-client-migration-runtime`, `nginx-quic-bpf-readiness`, `nginx-quic-bpf-linux-runner` | - | Run `harness/scripts/run-nginx-quic-bpf-linux-demo.sh` on a suitable Linux host. |
| `openlitespeed-production-like` | `lsquic-preferred-address-app-demo`, `lsquic-nat-rebinding-app-demo`, `openlitespeed-runtime-runner` | - | Run `harness/scripts/run-openlitespeed-active-migration-demo.sh` on Linux/EC2. |
| `safari-desktop-baseline` | `safari-webdriver-session-readiness`, `non-iphone-gate-rerun-20260701` | - | Rerun `tools/check_browser_cm_observability.py --safari-session-smoke`, then controlled-public Safari baseline. |
| `mvfst-focused-tests` | `mvfst-source-audit`, `mvfst-migration-test-readiness` | - | Run focused BUCK targets identified by `tools/check_mvfst_migration_test_readiness.py`. |

## Interpretation For The Paper

1. Implementation maturity is no longer the weakest section; the repository already has broad implementation tests, app demos, server runtime evidence, and negative controls.
2. The next missing proof is whether the mature primitives survive a realistic deployment or browser public-origin boundary.
3. AWS NLB+s2n is the most valuable non-iPhone path because it directly addresses the professor's AWS deployment decision, but it is blocked by credentials on this host.
4. Chrome controlled-public workload trials are the best browser-facing fallback because local media/range/upload controls already define the artifact contract.
5. Safari is worth adding for cross-browser feasibility only after WebDriver session creation is enabled, and its claim ceiling must stay below Chrome NetLog-based evidence.
