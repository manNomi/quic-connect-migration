# Threats To Validity And Reviewer Defense

Generated: `2026-06-29`

## Purpose

This chapter is not meant to make the current results look stronger than they are. It does the opposite: it lists likely reviewer questions and separates what the current evidence supports from what it does not yet support.

The defensible central claim is:

> HTTP/3/QUIC Connection Migration exists as a mature standard primitive in some implementations, but web-browser task continuity depends on implementation maturity, runtime policy, deployment path, workload semantics, and application recovery. CM evaluation therefore needs an evidence chain and workload-sensitive recovery analysis, not a single connection-survival check.

## Current Final Gate State

| item | value |
| --- | --- |
| final protocol | 3/6 |
| next trial | controlled-public-chrome-downlink-noheartbeat-network-change-001 |
| packet state | blocked_by_readiness |
| missing gate | public_origin_live_ready |
| public origin | not_ready |
| next recovery step | aws-credentials |

## Reviewer Defense Matrix

| id | reviewer question | current answer | claim boundary | next action |
| --- | --- | --- | --- | --- |
| RQ-claim-browser-cm | Can the study claim Chrome successfully performs HTTP/3 QUIC Connection Migration during Wi-Fi-to-cellular failover? | No. The current evidence supports workload failure/recovery and replacement-session behavior, not publishable single-session browser CM success. | Do not claim Chrome single-session CM until application H3, client path change, server tuple change, qlog path validation, one Chrome target QUIC session, and task completion are present in the same row. | Recover public origin, rerun baseline, then execute no-heartbeat and heartbeat active rows. |
| RQ-implementation-maturity | Is CM unused because it is not implemented? | No. The implementation survey and controls show CM primitives exist, but deployment/runtime/observability friction limits visible web use. | Do not collapse underuse into a single cause such as missing implementation. | Use the current friction matrix as paper framing and add final browser rows when infrastructure is restored. |
| RQ-iphone-usb-generalization | Does Mac+iPhone USB failover represent mobile network handover in general? | No. It is a reproducible real client path-change trigger, but it is delayed OS failover rather than simultaneous active multipath or a complete mobile-network model. | Name the setup as latent Wi-Fi-loss-to-iPhone-USB cellular failover. | Fill Safari or Android feasibility after public origin recovery. |
| RQ-workload-continuity | Why evaluate upload, download, Range, media, and polling instead of only connection survival? | Because user-visible continuity is workload-dependent and can be produced by application retry, range resume, buffering, or replacement sessions. | Task completion is not transport CM unless session continuity and path evidence also align. | Run public page-ready Range and buffered-media trials after the first Chrome active rows. |
| RQ-streaming | Is streaming the most important CM use case? | It is important, but it is also the easiest workload to misinterpret because buffering and segment retry can hide transport disruption. | Do not state CM improves streaming unless single-session evidence and QoE metrics are both present. | Treat media as a QoE-aware workload after upload/download active rows. |
| RQ-public-origin-blocker | Does the current inability to run final public trials weaken the result? | It limits browser CM success claims but does not invalidate controlled implementation results or local workload-recovery controls. | Do not report origin-readiness failure as browser CM failure. | Import valid AWS credentials or restore SSH access, then rerun recovery planner. |
| RQ-third-party-sites | Can public H3 sites such as Google or Cloudflare replace a controlled origin? | No. They can show browser H3 discovery/capability, but they cannot provide server qlog, tuple, workload, or path validation evidence. | Use third-party sites only as discovery/capability controls. | Keep third-party results out of CM success table. |
| RQ-cdn-lb-scope | How should CDN/LB deployments be interpreted? | Managed CDN/LB environments can terminate QUIC at the edge or route by CID, so continuity claims may be edge-level or deployment-scoped rather than end-to-end browser-origin CM. | Distinguish end-to-end QUIC CM from edge-level connection continuity or CID-aware data-plane continuity. | Present CDN/LB as deployment discussion, not final browser CM proof. |

## Claim Readiness Summary

| claim | readiness | safe wording | do not claim |
| --- | --- | --- | --- |
| quic-cm-is-a-real-standard-feature | source-backed | QUIC provides standardized primitives for path validation and client-initiated migration, and at least some implementations expose explicit migration APIs. | Do not infer that HTTP/3 browsers automatically use those primitives during Wi-Fi/cellular handover. |
| controlled-implementations-can-migrate | supported-scoped | Controlled QUIC clients and deployment paths can demonstrate migration or CID-aware continuity under instrumented conditions. | Do not generalize controlled CLI/library success to Chrome/Safari browser handover. |
| controlled-public-browser-h3-baseline-exists | supported-historical | The study already established that the controlled public origin was previously usable for Chrome HTTP/3 application traffic and no-change comparisons. | Do not treat the previous baseline as proof that the public origin is currently online. |
| iphone-usb-path-change-trigger-is-ready | supported-scoped | On this Mac, Wi-Fi-off can trigger a reproducible latent iPhone USB failover, suitable as a real client path-change trigger with an explicit claim boundary. | Do not call this simultaneous active multipath; it is delayed OS failover from Wi-Fi to iPhone USB. |
| public-origin-currently-blocks-final-runs | blocked-by-origin | The current inability to run final public trials is an infrastructure readiness blocker, not evidence that iPhone USB path change failed. | Do not report a failed final browser CM trial when the controlled origin did not accept HTTPS/H3 connections. |
| chrome-single-session-browser-cm-not-yet-proven | not-supported-yet | The current Chrome evidence supports workload failure/recovery and replacement-session observations, but not a publishable single-session browser CM success claim. | Do not state that Chrome successfully migrated the original HTTP/3 connection across Wi-Fi-to-iPhone-USB. |
| upload-download-app-recovery-is-strong | supported | For large upload/download, application retry or byte-range recovery can convert visible task failure into task completion, but this is not the same as single-session QUIC CM. | Do not use retry-completed rows as transport-layer CM success. |
| streaming-continuity-needs-qoe-metrics | supported-local-control | Streaming workloads require startup delay, rebuffer events, segment retry, and session churn metrics; completion alone hides the mechanism. | Do not say CM helps streaming unless the row also proves session continuity and path validation. |
| paper-direction-is-evidence-chain-and-workload-maturity | supported-as-framing | The defensible paper direction is a maturity and workload-continuity study: why CM is hard to observe/deploy, which workloads expose the gap, and what evidence is required before claiming browser CM. | Do not frame the paper as already proving browser/mobile HTTP/3 CM success. |

## Workload-Specific Threats

| workload | current result | CM evidence | next experiment |
| --- | --- | --- | --- |
| large_upload | retry0 failed 3/3; retry1 succeeded 3/3 after one failed first attempt | No single-session browser CM; one retry1 row had qlog path validation but Chrome used two sessions | Repeat with page-ready trigger if possible; compare resumable/multipart upload semantics |
| large_download | timeout-only retry0 failed 3/3; timeout+retry1 succeeded 3/3; local Range 6000ms no-retry 1/3 PASS and retry2 3/3 PASS | No single-session browser CM; Range retry rows used multiple Chrome QUIC sessions | Run public page-ready Range handover after controlled origin is reachable |
| polling_dashboard | one valid no-retry public row failed after two poll requests; retry public rows invalid until page-ready runner | No qlog path validation in valid public failure row | Run page-ready no-retry and retry2 polling after the controlled origin is reachable |
| media_segments | segment replication 3000ms/6000ms completed 3/3; buffered playback 3000ms completed 12/12 but low buffer had 14 rebuffer events while high buffer had ~15s startup delay and 0 rebuffer | Not single-session CM; every buffered playback row classified nat_rebinding_multiple_quic_sessions | Run public page-ready buffered-media handover after controlled origin is reachable |
| music_like_buffered | 6000ms no-retry failed 3/3 after first segment; retry1 completed 3/3 with all eight segments | Not single-session CM; retry1 rows used three Chrome QUIC sessions and no qlog path validation | Run public page-ready media handover after the controlled origin is reachable; add larger buffer-depth model if media section becomes central |

## Threats To Validity

### Construct Validity

Defining CM success using only server tuple changes or task completion would overclaim the result. This study separates application HTTP/3, client path change, server tuple changes, qlog path validation, browser session continuity, and task completion.

### Internal Validity

Local UDP rebinding, iPhone USB failover, and application retry are different mechanisms. Rows must therefore be classified as single-session CM, replacement-session continuity, application-level recovery, or origin-readiness failure.

### External Validity

Mac+iPhone USB failover is a real client path-change trigger, but it does not represent all mobile handover behavior. Safari or Android feasibility is still needed, and a fresh public baseline must precede final active rows.

### Measurement Validity

Chrome NetLog, server qlog, server request logs, and DOM datasets observe different layers. A single layer cannot prove CM success alone. Streaming especially requires completion, startup delay, rebuffering, retry, and session-churn metrics.

### Infrastructure Validity

The current public-origin `connection_refused` and AWS `invalid_client_token` states block final browser CM trials. A failure observed under this condition would be an origin-readiness failure, not a browser CM failure.

## Limitations To Acknowledge Up Front

- Chrome single-session browser CM success is not yet proven.
- The current iPhone USB trigger is delayed OS failover, not simultaneous multipath.
- Local rebinding proxy rows should not be directly generalized to public Wi-Fi/cellular handover.
- Managed CDN/LB deployments require separating edge-level continuity from end-to-end CM.
- Streaming completion can be QoE-continuity evidence without being transport-CM evidence.

## Safe Conclusion For The Paper

The strongest current conclusion is neither that CM is useless nor that Chrome already performs CM successfully. The safe conclusion is that evaluating CM as web task continuity requires implementation maturity and workload recovery analysis, and that single-session browser CM claims require a stronger evidence chain.

## Source Anchors

- RFC 9000: <https://datatracker.ietf.org/doc/html/rfc9000>
- RFC 9114: <https://datatracker.ietf.org/doc/html/rfc9114>
- ACM CCR 2025, `An Analysis of QUIC Connection Migration in the Wild`: <https://dl.acm.org/doi/10.1145/3727063.3727066>
- IETF Media over QUIC WG: <https://datatracker.ietf.org/wg/moq/about/>

Regenerate with: `python3 tools/build_threats_and_reviewer_defense.py`
