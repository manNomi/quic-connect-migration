# Current-Evidence Methods/Results Draft

Generated: `2026-06-29`

This draft is derived only from reproducible artifacts currently present in the repository. To avoid result-first writing, each positive statement is paired with an explicit claim boundary.

## Research Questions

1. How mature is QUIC Connection Migration across implementations and deployments?
2. Can browser HTTP/3 preserve a single QUIC session across Wi-Fi to iPhone USB/cellular failover?
3. How does task continuity differ across upload, download, polling, and streaming workloads?

## Method

The study separates three evidence layers.

- Implementation/deployment positive controls: quic-go, quiche, and AWS NLB/CID-aware paths are used to verify path validation, tuple change, and application completion under instrumented conditions.
- Browser evidence chain: application HTTP/3 use, client path change, server tuple change, qlog path validation, browser session continuity, and task completion must align in the same row before a browser CM success claim is allowed.
- Workload continuity: upload, download, polling, and media workloads are evaluated with workload-specific failure semantics, including retry, Range resume, buffering, rebuffering, and session churn.

## Current Corpus

| item | value |
| --- | --- |
| experiment status | PASS=32; PASS_FEASIBILITY=6; PASS_NEGATIVE_CONTROL=59 |
| final browser protocol | 3/6 requirements complete |
| final blockers | chrome-downlink-noheartbeat-active-cm: 0/3; chrome-downlink-heartbeat-active-cm: 0/3; p1-safari-or-android-feasibility: 0/1 |
| iPhone USB trigger | classification=latent_iphone_usb_failover_observed; ready=True; ready_at_ms=1321; path=en0->en8 |
| public origin | tcp=connection_refused; aws=invalid_client_token; recovery_path_ready=False |

## Claim Readiness

| claim | readiness | safe paper wording | do not claim |
| --- | --- | --- | --- |
| quic-cm-is-a-real-standard-feature | source-backed | QUIC provides standardized primitives for path validation and client-initiated migration, and at least some implementations expose explicit migration APIs. | Do not infer that HTTP/3 browsers automatically use those primitives during Wi-Fi/cellular handover. |
| controlled-implementations-can-migrate | supported-scoped | Controlled QUIC clients and deployment paths can demonstrate migration or CID-aware continuity under instrumented conditions. | Do not generalize controlled CLI/library success to Chrome/Safari browser handover. |
| iphone-usb-path-change-trigger-is-ready | supported-scoped | On this Mac, Wi-Fi-off can trigger a reproducible latent iPhone USB failover, suitable as a real client path-change trigger with an explicit claim boundary. | Do not call this simultaneous active multipath; it is delayed OS failover from Wi-Fi to iPhone USB. |
| public-origin-currently-blocks-final-runs | blocked-by-origin | The current inability to run final public trials is an infrastructure readiness blocker, not evidence that iPhone USB path change failed. | Do not report a failed final browser CM trial when the controlled origin did not accept HTTPS/H3 connections. |
| chrome-single-session-browser-cm-not-yet-proven | not-supported-yet | The current Chrome evidence supports workload failure/recovery and replacement-session observations, but not a publishable single-session browser CM success claim. | Do not state that Chrome successfully migrated the original HTTP/3 connection across Wi-Fi-to-iPhone-USB. |
| upload-download-app-recovery-is-strong | supported | For large upload/download, application retry or byte-range recovery can convert visible task failure into task completion, but this is not the same as single-session QUIC CM. | Do not use retry-completed rows as transport-layer CM success. |
| streaming-continuity-needs-qoe-metrics | supported-local-control | Streaming workloads require startup delay, rebuffer events, segment retry, and session churn metrics; completion alone hides the mechanism. | Do not say CM helps streaming unless the row also proves session continuity and path validation. |
| paper-direction-is-evidence-chain-and-workload-maturity | supported-as-framing | The defensible paper direction is a maturity and workload-continuity study: why CM is hard to observe/deploy, which workloads expose the gap, and what evidence is required before claiming browser CM. | Do not frame the paper as already proving browser/mobile HTTP/3 CM success. |

## Workload Results

| workload | representative task | primary result | CM evidence | next experiment |
| --- | --- | --- | --- | --- |
| large_upload | photo/video/field-record upload | retry0 failed 3/3; retry1 succeeded 3/3 after one failed first attempt | No single-session browser CM; one retry1 row had qlog path validation but Chrome used two sessions | Repeat with page-ready trigger if possible; compare resumable/multipart upload semantics |
| large_download | long file or export download | timeout-only retry0 failed 3/3; timeout+retry1 succeeded 3/3; local Range 6000ms no-retry 1/3 PASS and retry2 3/3 PASS | No single-session browser CM; Range retry rows used multiple Chrome QUIC sessions | Run public page-ready Range handover after controlled origin is reachable |
| polling_dashboard | repeated fetch dashboard | one valid no-retry public row failed after two poll requests; retry public rows invalid until page-ready runner | No qlog path validation in valid public failure row | Run page-ready no-retry and retry2 polling after the controlled origin is reachable |
| media_segments | live/low-latency video-like segment fetch | segment replication 3000ms/6000ms completed 3/3; buffered playback 3000ms completed 12/12 but low buffer had 14 rebuffer events while high buffer had ~15s startup delay and 0 rebuffer | Not single-session CM; every buffered playback row classified nat_rebinding_multiple_quic_sessions | Run public page-ready buffered-media handover after controlled origin is reachable |
| music_like_buffered | small low-bitrate buffered segments | 6000ms no-retry failed 3/3 after first segment; retry1 completed 3/3 with all eight segments | Not single-session CM; retry1 rows used three Chrome QUIC sessions and no qlog path validation | Run public page-ready media handover after the controlled origin is reachable; add larger buffer-depth model if media section becomes central |

## Interpretation

The current evidence supports the existence and maturity of QUIC CM primitives in controlled implementations and deployments. Instrumented controls show path validation, tuple change, and application completion. However, those controls cannot be generalized to Chrome or Safari browser handover behavior.

On the browser side, the iPhone USB failover trigger is ready, but the controlled public origin currently refuses TCP 443. Running final active Chrome rows in this state would create an origin-readiness failure artifact, not meaningful browser CM evidence.

Task continuity is workload-dependent. Large upload and download expose path disruption as direct task failure, while retry or Range resume can restore completion. Media workloads can complete while shifting user-visible cost into startup delay, rebuffer events, segment retry, and session churn. Therefore streaming continuity must be evaluated with QoE metrics and session attribution, not completion alone.

## Limitations

- Chrome single-session browser CM success has not yet been demonstrated.
- The iPhone USB trigger is delayed OS failover, not simultaneous active multipath.
- Local UDP rebinding controls must not be converted into public Wi-Fi/cellular threshold claims.
- A fresh controlled public H3 baseline is required after origin recovery.
- Safari or Android feasibility evidence is still missing.

## Next Execution Order

1. Restore the controlled public origin through AWS credentials or SSH.
2. Rerun a fresh Chrome controlled public H3 baseline.
3. Run three Chrome downlink no-heartbeat active path-change rows.
4. Run three Chrome downlink heartbeat active path-change rows.
5. Add public Range/resumable download and buffered-media handover rows.
6. Complete one Safari or Android Chrome feasibility row.
