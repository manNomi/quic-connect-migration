# Threats To Validity 및 Reviewer Defense

생성일: `2026-06-29`

## 목적

이 장은 현재 연구 결과를 더 강하게 보이도록 포장하기 위한 문서가 아니다. 반대로, 논문 심사자가 물을 가능성이 높은 질문을 먼저 적고, 현재 증거가 허용하는 주장과 허용하지 않는 주장을 분리하기 위한 방어선이다.

현재 논문의 방어 가능한 중심 주장은 다음이다.

> HTTP/3/QUIC Connection Migration은 표준과 일부 구현체에서는 성숙한 primitive로 존재하지만, 웹 브라우저와 실제 작업 연속성에서는 구현체 성숙도, runtime policy, deployment path, workload semantics, application recovery가 함께 작동한다. 따라서 CM 평가는 단일 connection survival이 아니라 evidence chain과 workload-sensitive recovery로 설계되어야 한다.

## 현재 최종 Gate 상태

| 항목 | 값 |
| --- | --- |
| final protocol | 3/6 |
| next trial | controlled-public-chrome-downlink-noheartbeat-network-change-001 |
| packet state | blocked_by_readiness |
| missing gate | public_origin_live_ready |
| public origin | not_ready |
| next recovery step | aws-credentials |

## Reviewer Defense Matrix

| id | 리뷰어 질문 | 현재 답변 | claim boundary | 다음 행동 |
| --- | --- | --- | --- | --- |
| RQ-claim-browser-cm | Can the study claim Chrome successfully performs HTTP/3 QUIC Connection Migration during Wi-Fi-to-cellular failover? | No. The current evidence supports workload failure/recovery and replacement-session behavior, not publishable single-session browser CM success. | Do not claim Chrome single-session CM until application H3, client path change, server tuple change, qlog path validation, one Chrome target QUIC session, and task completion are present in the same row. | Recover public origin, rerun baseline, then execute no-heartbeat and heartbeat active rows. |
| RQ-implementation-maturity | Is CM unused because it is not implemented? | No. The implementation survey and controls show CM primitives exist, but deployment/runtime/observability friction limits visible web use. | Do not collapse underuse into a single cause such as missing implementation. | Use the current friction matrix as paper framing and add final browser rows when infrastructure is restored. |
| RQ-iphone-usb-generalization | Does Mac+iPhone USB failover represent mobile network handover in general? | No. It is a reproducible real client path-change trigger, but it is delayed OS failover rather than simultaneous active multipath or a complete mobile-network model. | Name the setup as latent Wi-Fi-loss-to-iPhone-USB cellular failover. | Fill Safari or Android feasibility after public origin recovery. |
| RQ-workload-continuity | Why evaluate upload, download, Range, media, and polling instead of only connection survival? | Because user-visible continuity is workload-dependent and can be produced by application retry, range resume, buffering, or replacement sessions. | Task completion is not transport CM unless session continuity and path evidence also align. | Run public page-ready Range and buffered-media trials after the first Chrome active rows. |
| RQ-streaming | Is streaming the most important CM use case? | It is important, but it is also the easiest workload to misinterpret because buffering and segment retry can hide transport disruption. | Do not state CM improves streaming unless single-session evidence and QoE metrics are both present. | Treat media as a QoE-aware workload after upload/download active rows. |
| RQ-public-origin-blocker | Does the current inability to run final public trials weaken the result? | It limits browser CM success claims but does not invalidate controlled implementation results or local workload-recovery controls. | Do not report origin-readiness failure as browser CM failure. | Import valid AWS credentials or restore SSH access, then rerun recovery planner. |
| RQ-third-party-sites | Can public H3 sites such as Google or Cloudflare replace a controlled origin? | No. They can show browser H3 discovery/capability, but they cannot provide server qlog, tuple, workload, or path validation evidence. | Use third-party sites only as discovery/capability controls. | Keep third-party results out of CM success table. |
| RQ-cdn-lb-scope | How should CDN/LB deployments be interpreted? | Managed CDN/LB environments can terminate QUIC at the edge or route by CID, so continuity claims may be edge-level or deployment-scoped rather than end-to-end browser-origin CM. | Distinguish end-to-end QUIC CM from edge-level connection continuity or CID-aware data-plane continuity. | Present CDN/LB as deployment discussion, not final browser CM proof. |

## Claim Readiness 요약

| claim | readiness | 쓸 수 있는 표현 | 쓰면 안 되는 표현 |
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

## Workload별 Threats

| workload | 현재 결과 | CM evidence | 다음 실험 |
| --- | --- | --- | --- |
| large_upload | retry0 failed 3/3; retry1 succeeded 3/3 after one failed first attempt | No single-session browser CM; one retry1 row had qlog path validation but Chrome used two sessions | Repeat with page-ready trigger if possible; compare resumable/multipart upload semantics |
| large_download | timeout-only retry0 failed 3/3; timeout+retry1 succeeded 3/3; local Range 6000ms no-retry 1/3 PASS and retry2 3/3 PASS | No single-session browser CM; Range retry rows used multiple Chrome QUIC sessions | Run public page-ready Range handover after controlled origin is reachable |
| polling_dashboard | one valid no-retry public row failed after two poll requests; retry public rows invalid until page-ready runner | No qlog path validation in valid public failure row | Run page-ready no-retry and retry2 polling after the controlled origin is reachable |
| media_segments | segment replication 3000ms/6000ms completed 3/3; buffered playback 3000ms completed 12/12 but low buffer had 14 rebuffer events while high buffer had ~15s startup delay and 0 rebuffer | Not single-session CM; every buffered playback row classified nat_rebinding_multiple_quic_sessions | Run public page-ready buffered-media handover after controlled origin is reachable |
| music_like_buffered | 6000ms no-retry failed 3/3 after first segment; retry1 completed 3/3 with all eight segments | Not single-session CM; retry1 rows used three Chrome QUIC sessions and no qlog path validation | Run public page-ready media handover after the controlled origin is reachable; add larger buffer-depth model if media section becomes central |

## Threats To Validity

### Construct Validity

Connection Migration 성공을 server remote tuple 변화나 작업 완료만으로 정의하면 과대해석이 된다. 본 연구는 application HTTP/3, client path change, server tuple, qlog path validation, browser session continuity, task completion을 분리해 보고한다.

### Internal Validity

local UDP rebinding, iPhone USB failover, application retry는 서로 다른 mechanism이다. 따라서 각 row는 `single-session CM`, `replacement-session continuity`, `application-level recovery`, `origin-readiness failure`로 분류해야 한다.

### External Validity

Mac+iPhone USB failover는 실제 client path-change trigger이지만 일반적인 모든 mobile handover를 대표하지 않는다. Safari 또는 Android feasibility row가 필요하며, public origin 복구 후 fresh baseline을 먼저 실행해야 한다.

### Measurement Validity

Chrome NetLog, server qlog, server request log, DOM dataset은 서로 다른 계층을 관찰한다. 하나의 계층만 성공해도 CM 성공이라고 말하지 않는다. 특히 streaming은 completion, startup delay, rebuffer, retry, session churn을 함께 본다.

### Infrastructure Validity

현재 public origin `connection_refused`와 AWS `invalid_client_token`은 final browser CM 실험의 blocker다. 이 상태에서 실행한 실패는 browser CM 실패가 아니라 origin readiness 실패다.

## Reviewer에게 먼저 인정할 한계

- Chrome single-session browser CM success는 아직 증명되지 않았다.
- 현재 iPhone USB trigger는 delayed OS failover이지 simultaneous multipath가 아니다.
- local rebinding proxy 결과는 public Wi-Fi/cellular handover로 직접 일반화하지 않는다.
- managed CDN/LB 환경은 edge-level continuity와 end-to-end CM을 분리해야 한다.
- streaming completion은 QoE continuity evidence일 수 있지만 transport CM success evidence는 아니다.

## 논문에 넣을 안전한 결론

현재까지 가장 방어 가능한 결론은 `CM이 쓸모없다`도, `Chrome에서 CM이 된다`도 아니다. 결론은 `CM을 웹 작업 연속성으로 평가하려면 구현체 성숙도와 workload recovery를 함께 봐야 하며, single-session browser CM claim에는 더 강한 evidence chain이 필요하다`이다.

## Source Anchors

- RFC 9000: <https://datatracker.ietf.org/doc/html/rfc9000>
- RFC 9114: <https://datatracker.ietf.org/doc/html/rfc9114>
- ACM CCR 2025, `An Analysis of QUIC Connection Migration in the Wild`: <https://dl.acm.org/doi/10.1145/3727063.3727066>
- IETF Media over QUIC WG: <https://datatracker.ietf.org/wg/moq/about/>

재생성 명령: `python3 tools/build_threats_and_reviewer_defense.py`
