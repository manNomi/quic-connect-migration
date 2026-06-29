# Paper Claim Readiness Audit

Generated: `2026-06-29`

This audit records what the current evidence can and cannot support. It is intentionally conservative: application recovery, tuple change, or task completion is not upgraded to browser single-session QUIC Connection Migration unless the full evidence chain is present.

## Summary

| field | value |
| --- | --- |
| final browser protocol complete | `no` |
| final browser requirements | `3/6` |
| final blockers | `chrome-downlink-noheartbeat-active-cm: 0/3; chrome-downlink-heartbeat-active-cm: 0/3; p1-safari-or-android-feasibility: 0/1` |
| experiment status counts | `PASS=32; PASS_FEASIBILITY=6; PASS_NEGATIVE_CONTROL=58` |

## Claim Audit

| claim | readiness | safe paper wording | do not claim | next step |
| --- | --- | --- | --- | --- |
| `quic-cm-is-a-real-standard-feature` | `source-backed` | QUIC provides standardized primitives for path validation and client-initiated migration, and at least some implementations expose explicit migration APIs. | Do not infer that HTTP/3 browsers automatically use those primitives during Wi-Fi/cellular handover. | Use RFC 9000 and implementation docs as background, then rely on local artifacts for runtime behavior. |
| `controlled-implementations-can-migrate` | `supported-scoped` | Controlled QUIC clients and deployment paths can demonstrate migration or CID-aware continuity under instrumented conditions. | Do not generalize controlled CLI/library success to Chrome/Safari browser handover. | Keep controlled implementation results as positive controls and contrast them with browser/runtime policy evidence. |
| `controlled-public-browser-h3-baseline-exists` | `supported-historical` | The study already established that the controlled public origin was previously usable for Chrome HTTP/3 application traffic and no-change comparisons. | Do not treat the previous baseline as proof that the public origin is currently online. | After origin recovery, rerun a fresh baseline before final active path-change rows. |
| `iphone-usb-path-change-trigger-is-ready` | `supported-scoped` | On this Mac, Wi-Fi-off can trigger a reproducible latent iPhone USB failover, suitable as a real client path-change trigger with an explicit claim boundary. | Do not call this simultaneous active multipath; it is delayed OS failover from Wi-Fi to iPhone USB. | Use NETWORK_CHANGE_CMD="networksetup -setairportpower 'en0' off" in page-ready public trials once the origin is reachable. |
| `public-origin-currently-blocks-final-runs` | `blocked-by-origin` | The current inability to run final public trials is an infrastructure readiness blocker, not evidence that iPhone USB path change failed. | Do not report a failed final browser CM trial when the controlled origin did not accept HTTPS/H3 connections. | Refresh AWS credentials or provide SSH/cert access, restart the controlled origin, and rerun baseline plus active trials. |
| `chrome-single-session-browser-cm-not-yet-proven` | `not-supported-yet` | The current Chrome evidence supports workload failure/recovery and replacement-session observations, but not a publishable single-session browser CM success claim. | Do not state that Chrome successfully migrated the original HTTP/3 connection across Wi-Fi-to-iPhone-USB. | Complete 3 no-heartbeat active rows, 3 heartbeat active rows, and one Safari/Android feasibility row with the full evidence chain. |
| `upload-download-app-recovery-is-strong` | `supported` | For large upload/download, application retry or byte-range recovery can convert visible task failure into task completion, but this is not the same as single-session QUIC CM. | Do not use retry-completed rows as transport-layer CM success. | When public origin is restored, rerun page-ready upload/download with retry0 and retry1/range variants. |
| `streaming-continuity-needs-qoe-metrics` | `supported-local-control` | Streaming workloads require startup delay, rebuffer events, segment retry, and session churn metrics; completion alone hides the mechanism. | Do not say CM helps streaming unless the row also proves session continuity and path validation. | Run public page-ready buffered-media handover after origin recovery and compare it against local buffered-media controls. |
| `paper-direction-is-evidence-chain-and-workload-maturity` | `supported-as-framing` | The defensible paper direction is a maturity and workload-continuity study: why CM is hard to observe/deploy, which workloads expose the gap, and what evidence is required before claiming browser CM. | Do not frame the paper as already proving browser/mobile HTTP/3 CM success. | Write the paper around evidence chain, workload sensitivity, and controlled recovery; add final public handover rows when infrastructure is restored. |

## Evidence Notes

- `quic-cm-is-a-real-standard-feature`: RFC 9000 defines path validation and connection migration; quic-go documents AddPath/Probe/Switch as client-side path migration primitives.
- `controlled-implementations-can-migrate`: 13 PASS rows have both path validation and tuple-change evidence; AWS NLB/CID-related evidence rows=9. Key rows include quic-go direct origin and quiche local migration controls.
- `controlled-public-browser-h3-baseline-exists`: Final audit still has the controlled public Chrome application H3 baseline requirement complete; no-change downlink baselines are also complete.
- `iphone-usb-path-change-trigger-is-ready`: Rerun classification=latent_iphone_usb_failover_observed; ready=True; ready_at_ms=1321; before=en0; after=en8.
- `public-origin-currently-blocks-final-runs`: Origin TCP classification=connection_refused; AWS identity classification=invalid_client_token; any recovery path ready=False.
- `chrome-single-session-browser-cm-not-yet-proven`: Final protocol complete=False; complete requirements=3/6; blockers=chrome-downlink-noheartbeat-active-cm: 0/3; chrome-downlink-heartbeat-active-cm: 0/3; p1-safari-or-android-feasibility: 0/1; public iPhone network-change rows observed=20.
- `upload-download-app-recovery-is-strong`: Upload: retry0 failed 3/3; retry1 succeeded 3/3 after one failed first attempt; Download: timeout-only retry0 failed 3/3; timeout+retry1 succeeded 3/3; local Range 6000ms no-retry 1/3 PASS and retry2 3/3 PASS.
- `streaming-continuity-needs-qoe-metrics`: Media: segment replication 3000ms/6000ms completed 3/3; buffered playback 3000ms completed 12/12 but low buffer had 14 rebuffer events while high buffer had ~15s startup delay and 0 rebuffer; Music-like: 6000ms no-retry failed 3/3 after first segment; retry1 completed 3/3 with all eight segments.
- `paper-direction-is-evidence-chain-and-workload-maturity`: Implementation positives, browser negative controls, iPhone path-change readiness, workload recovery controls, and origin readiness gates now form a coherent evidence-boundary story.

## Source Anchors

- [RFC 9000, QUIC transport](https://datatracker.ietf.org/doc/html/rfc9000): Normative connection migration and path validation semantics.
- [quic-go connection migration docs](https://quic-go.net/docs/quic/connection-migration/): Implementation-level AddPath/Probe/Switch control model.
- [curl issue 7695](https://github.com/curl/curl/issues/7695): Practitioner report that HTTP/3 support did not imply automatic connection migration in curl.
- [An Analysis of QUIC Connection Migration in the Wild](https://arxiv.org/abs/2410.06066): Measurement anchor for uneven Internet CM support among HTTP/3-capable destinations.

## Paper Decision

Proceed with the paper as a workload-sensitive CM maturity study, not as a success-only browser CM paper. The current evidence is strong enough to argue that HTTP/3 application continuity depends on workload semantics and recovery policy, while browser single-session CM remains unproven until the controlled public handover rows are completed.
