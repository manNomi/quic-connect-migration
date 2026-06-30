# non-iPhone Claim Readiness Dashboard

Generated: `2026-06-30`

This dashboard is public-safe. It maps current evidence to paper wording boundaries without copying raw qlogs, pcaps, keylogs, NetLogs, private hosts, device IDs, account IDs, or credentials.

## Summary

| field | value |
| --- | --- |
| claim count | `8` |
| claim allowed count | `5` |
| claim blocked count | `3` |
| bundle item count | `50` |
| missing evidence by claim | `{}` |
| paper decision | The current corpus is ready for a conservative maturity/gap report, but not for Chrome public CM success or live AWS+s2n success claims. |

## Gate Context

| field | value |
| --- | --- |
| open gates | `[]` |
| all key gates blocked | `True` |
| AWS identity classification | `invalid_client_token` |
| Safari session ready | `False` |
| public origin H3 Alt-Svc | `False` |
| non-iPhone desktop path ready | `False` |
| controlled-public active rows | `12` |
| controlled-public H3 baselines | `6` |
| controlled-public strong CM successes | `0` |
| QoE workload groups | `['buffered video playback', 'large byte-range download', 'large upload', 'music-like segment', 'video-like segment']` |

## Claim Readiness

| claim | status | allowed | safe wording | blockers | do not claim | next action |
| --- | --- | --- | --- | --- | --- | --- |
| `implementation_maturity`<br>Implementation-level CM maturity | `supported` | `true` | Several major QUIC implementations expose or test path validation, rebinding, migration, preferred-address, or related primitives; CM is not merely an unimplemented idea. | - | Do not claim every implementation exposes the same active migration API or production deployment behavior. | Use this as the paper's implementation-maturity foundation, then shift attention to deployment and browser gates. |
| `deployment_routing_boundary`<br>Deployment and routing boundary | `partially_supported` | `true` | Deployment support is separate from library support: CID-aware routing can preserve backend continuity, while proxy or mismatched-CID controls show that HTTP/3 availability alone is insufficient. | AWS NLB+s2n live forwarding is still credential-blocked.<br>nginx quic_bpf production-routing validation requires a Linux/root or capability environment. | Do not claim live AWS NLB+s2n migration success, CDN end-to-end CM, or Linux quic_bpf success from the current host. | Refresh AWS credentials first; if unavailable, run nginx quic_bpf or OpenLiteSpeed on a suitable Linux/EC2 host. |
| `local_chrome_workload_controls`<br>Local Chrome workload controls | `supported_local_only` | `true` | Local Chrome forced-H3 UDP-rebinding controls show that range/download and upload workloads can produce cleaner single-session evidence than streaming-like workloads, which require QoE and session-churn framing. | Local UDP rebinding is not the same as public Wi-Fi/LTE or desktop interface handover. | Do not call local forced-H3 rebinding a public browser handover result. | Use local rows to prioritize public workload order: range/upload first, buffered/music-like streaming with QoE metrics after. |
| `controlled_public_chrome_cm`<br>Controlled-public Chrome CM success | `not_supported_yet` | `false` | The current controlled-public Chrome corpus supports a negative/gap statement: no tracked active row combines application completion, client active path change, server tuple change, qlog path validation, and single target Chrome QUIC session. | No controlled-public strong CM success row exists yet.<br>The user-provided public HTTPS origin is not H3 Alt-Svc ready.<br>The current desktop host lacks a non-iPhone active secondary path. | Do not claim Chrome public-origin single-session Connection Migration success. | Open both gates: deploy an H3 Alt-Svc public origin and connect a non-iPhone secondary desktop path, then run the public workload trial packet and classify every row with the artifact contract. |
| `aws_s2n_live_claim`<br>AWS NLB + s2n live claim | `blocked` | `false` | The repository has a dedicated AWS NLB+s2n runner and local CID-provider prerequisite evidence, but the current live AWS gate is blocked before resource creation. | AWS identity classifies as invalid_client_token on the current host. | Do not claim live AWS NLB+s2n forwarding or active migration success. | Refresh AWS credentials and run the fail-closed live forwarding runner before any active migration variant. |
| `safari_cross_browser_claim`<br>Safari cross-browser feasibility | `blocked_feasibility` | `false` | Safari is currently a feasibility follow-up, not an evidence pillar: binaries exist, but WebDriver session creation is blocked by the local Safari remote-automation setting. | Safari Allow remote automation is not enabled. | Do not claim Safari H3 baseline, Safari handover, or Safari browser-internal session continuity. | Enable Safari Allow remote automation, rerun the session smoke, then treat Safari results as lower-ceiling feasibility evidence. |
| `streaming_qoe_claim`<br>Streaming/QoE framing | `supported_as_boundary` | `true` | Streaming workloads should be reported with QoE and session attribution, because playback completion can hide rebuffering, retry/reconnect behavior, and multiple target QUIC sessions. | Public streaming handover has not been executed. | Do not claim zero-impact video or music continuity, or single-session CM, from completion alone. | For public trials, collect startup delay, rebuffer count, retry count, session count, tuple change, qlog path validation, and task completion together. |
| `paper_scope_decision`<br>Paper scope decision | `partial_ready` | `true` | A defensible paper can now argue that CM maturity is multi-layered: implementation primitives are common, deployment/browser continuity remains gated, and workload-level continuity must be separated from transport/session continuity. | The paper should not yet present a successful public/browser CM result.<br>The paper should not yet present live AWS NLB+s2n success. | Do not frame the current work as proving that HTTP/3 CM guarantees web task continuity. | Ask for professor decision: either open AWS/public-origin/path gates for stronger positive results, or scope the paper around maturity gaps and conservative negative controls. |

## Evidence Trace

| claim | evidence found | evidence missing |
| --- | --- | --- |
| `implementation_maturity` | `cross-implementation-fresh-rerun`, `quiche-path-event-observability`, `lsquic-preferred-address-app-demo`, `lsquic-nat-rebinding-app-demo`, `quicly-focused-e2e-path-migration`, `nginx-active-client-migration-runtime`, `s2n-active-migration-api-audit`, `mvfst-source-audit` | - |
| `deployment_routing_boundary` | `aws-nlb-cid-aware-positive-control`, `aws-nlb-negative-controls`, `aws-nlb-http3-workload`, `haproxy-http3-negative-control`, `s2n-nlb-cid-provider-proof`, `s2n-nlb-live-readiness`, `aws-s2n-nlb-live-runner`, `nginx-quic-bpf-readiness`, `nginx-quic-bpf-linux-runner` | - |
| `local_chrome_workload_controls` | `chrome-local-rebinding-workload-controls`, `chrome-desktop-noniphone-media-local-refresh`, `chrome-desktop-noniphone-range-local-refresh`, `chrome-desktop-noniphone-upload-local-refresh`, `chrome-desktop-noniphone-musiclike-local-refresh`, `chrome-desktop-noniphone-buffered-media-local-refresh`, `noniphone-workload-qoe-synthesis` | - |
| `controlled_public_chrome_cm` | `controlled-public-chrome-bridge-synthesis`, `controlled-public-chrome-artifact-classifier-contract`, `controlled-public-chrome-contract-application-audit`, `user-provided-public-origin-readiness`, `noniphone-desktop-path-change-readiness`, `noniphone-public-workload-trial-packet`, `controlled-public-origin-workload-deploy-packet`, `non-iphone-gate-rerun-20260701` | - |
| `aws_s2n_live_claim` | `s2n-nlb-cid-provider-proof`, `s2n-nlb-live-readiness`, `aws-s2n-nlb-live-runner`, `s2n-active-migration-api-audit`, `non-iphone-gate-rerun-20260701` | - |
| `safari_cross_browser_claim` | `safari-webdriver-session-readiness`, `non-iphone-gate-rerun-20260701` | - |
| `streaming_qoe_claim` | `chrome-desktop-noniphone-musiclike-local-refresh`, `chrome-desktop-noniphone-buffered-media-local-refresh`, `noniphone-workload-qoe-synthesis` | - |
| `paper_scope_decision` | `cross-implementation-fresh-rerun`, `haproxy-http3-negative-control`, `controlled-public-chrome-bridge-synthesis`, `noniphone-workload-qoe-synthesis`, `non-iphone-gate-rerun-20260701` | - |

## Interpretation

- The current corpus is strong enough for implementation-maturity, deployment-boundary, local workload, and QoE-framing claims.
- It is not strong enough for controlled-public Chrome single-session CM success, Safari handover success, or live AWS NLB+s2n success.
- The next professor decision should be whether to open external gates for positive public/browser/AWS results, or scope the paper around maturity gaps and conservative negative controls.
