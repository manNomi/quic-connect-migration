# 현재 증거 기반 Methods/Results 장 초안

생성일: `2026-06-29`

이 문서는 현재 repository에 남아 있는 재현 가능한 artifact만 기준으로 작성한 논문 본문용 초안이다. 결론을 미리 정하지 않기 위해, 각 주장은 `claim readiness`와 `do not claim` 경계를 함께 적는다.

## 연구 질문

1. QUIC Connection Migration은 구현체 관점에서 어느 정도 성숙했는가?
2. 브라우저 HTTP/3 환경에서 Wi-Fi에서 iPhone USB/cellular로 전환될 때 single-session CM을 관찰할 수 있는가?
3. 작업 연속성은 upload, download, polling, streaming workload별로 어떻게 다르게 나타나는가?

## 방법

본 연구는 세 층의 증거를 분리한다.

- 구현체/배포 positive control: quic-go, quiche, AWS NLB/CID-aware path에서 path validation, tuple change, application completion을 확인한다.
- 브라우저 evidence chain: application HTTP/3 사용, client path change, server tuple change, qlog path validation, browser session continuity, task completion을 한 row에서 함께 요구한다.
- workload continuity: upload/download/polling/media를 동일한 성공/실패 기준으로 보지 않고, retry, Range resume, buffering, rebuffer, session churn을 분리해 측정한다.

## 현재 실험 corpus

| 항목 | 값 |
| --- | --- |
| experiment status | PASS=32; PASS_FEASIBILITY=6; PASS_NEGATIVE_CONTROL=59 |
| final browser protocol | 3/6 requirements complete |
| final blockers | chrome-downlink-noheartbeat-active-cm: 0/3; chrome-downlink-heartbeat-active-cm: 0/3; p1-safari-or-android-feasibility: 0/1 |
| iPhone USB trigger | classification=latent_iphone_usb_failover_observed; ready=True; ready_at_ms=1321; path=en0->en8 |
| public origin | tcp=connection_refused; aws=invalid_client_token; recovery_path_ready=False |

## Claim Readiness

| claim | readiness | 논문에 쓸 수 있는 표현 | 금지할 표현 |
| --- | --- | --- | --- |
| quic-cm-is-a-real-standard-feature | source-backed | QUIC은 path validation과 client-initiated migration을 위한 표준 primitive를 제공하며, 일부 구현체는 이를 명시적 API로 노출한다. | HTTP/3 브라우저가 Wi-Fi/cellular 전환에서 이 primitive를 자동으로 사용한다고 단정하지 않는다. |
| controlled-implementations-can-migrate | supported-scoped | 통제된 QUIC client와 deployment path에서는 migration 또는 CID-aware continuity를 계측된 조건에서 재현할 수 있다. | CLI/library positive control을 Chrome/Safari 브라우저 handover 성공으로 일반화하지 않는다. |
| iphone-usb-path-change-trigger-is-ready | supported-scoped | 이 Mac에서는 Wi-Fi off 명령이 재현 가능한 latent iPhone USB failover를 만들며, 명확한 claim boundary 안에서 실제 client path-change trigger로 사용할 수 있다. | 이를 simultaneous active multipath로 부르지 않는다. 이 결과는 Wi-Fi에서 iPhone USB로 넘어가는 delayed OS failover다. |
| public-origin-currently-blocks-final-runs | blocked-by-origin | 현재 final public trial을 실행하지 못하는 이유는 infrastructure readiness blocker이며, iPhone USB path change 실패 증거가 아니다. | controlled origin이 HTTPS/H3 connection을 받지 않는 상태에서 나온 실패를 browser CM 실패로 보고하지 않는다. |
| chrome-single-session-browser-cm-not-yet-proven | not-supported-yet | 현재 Chrome 증거는 workload failure/recovery와 replacement-session behavior를 보여주지만, publishable single-session browser CM success claim은 아직 지원하지 않는다. | Chrome이 Wi-Fi에서 iPhone USB로 전환되는 동안 원래 HTTP/3 connection을 성공적으로 migration했다고 쓰지 않는다. |
| upload-download-app-recovery-is-strong | supported | 대용량 upload/download에서는 application retry 또는 byte-range recovery가 visible task failure를 completion으로 바꿀 수 있지만, 이는 single-session QUIC CM과 다르다. | retry로 완료된 row를 transport-layer CM 성공으로 사용하지 않는다. |
| streaming-continuity-needs-qoe-metrics | supported-local-control | Streaming workload는 startup delay, rebuffer event, segment retry, session churn을 함께 측정해야 하며, completion만으로 mechanism을 설명할 수 없다. | session continuity와 path validation을 동시에 증명하지 못한 row에서 CM이 streaming을 개선했다고 말하지 않는다. |
| paper-direction-is-evidence-chain-and-workload-maturity | supported-as-framing | 현재 논문 방향은 CM maturity와 workload-continuity study로 잡는 것이 방어 가능하다. 즉 CM이 왜 관측/배포하기 어려운지, 어떤 workload가 gap을 드러내는지, browser CM claim 전에 어떤 evidence chain이 필요한지를 다룬다. | 논문을 이미 browser/mobile HTTP/3 CM success를 증명한 연구처럼 구성하지 않는다. |

## Workload별 결과

| workload | 대표 작업 | 주요 결과 | CM evidence | 다음 실험 |
| --- | --- | --- | --- | --- |
| large_upload | photo/video/field-record upload | retry0 failed 3/3; retry1 succeeded 3/3 after one failed first attempt | No single-session browser CM; one retry1 row had qlog path validation but Chrome used two sessions | Repeat with page-ready trigger if possible; compare resumable/multipart upload semantics |
| large_download | long file or export download | timeout-only retry0 failed 3/3; timeout+retry1 succeeded 3/3; local Range 6000ms no-retry 1/3 PASS and retry2 3/3 PASS | No single-session browser CM; Range retry rows used multiple Chrome QUIC sessions | Run public page-ready Range handover after controlled origin is reachable |
| polling_dashboard | repeated fetch dashboard | one valid no-retry public row failed after two poll requests; retry public rows invalid until page-ready runner | No qlog path validation in valid public failure row | Run page-ready no-retry and retry2 polling after the controlled origin is reachable |
| media_segments | live/low-latency video-like segment fetch | segment replication 3000ms/6000ms completed 3/3; buffered playback 3000ms completed 12/12 but low buffer had 14 rebuffer events while high buffer had ~15s startup delay and 0 rebuffer | Not single-session CM; every buffered playback row classified nat_rebinding_multiple_quic_sessions | Run public page-ready buffered-media handover after controlled origin is reachable |
| music_like_buffered | small low-bitrate buffered segments | 6000ms no-retry failed 3/3 after first segment; retry1 completed 3/3 with all eight segments | Not single-session CM; retry1 rows used three Chrome QUIC sessions and no qlog path validation | Run public page-ready media handover after the controlled origin is reachable; add larger buffer-depth model if media section becomes central |

## 현재 결과 해석

현재 증거는 QUIC CM이 표준과 구현체 수준에서 실재하는 기능임을 보여준다. 특히 controlled implementation 및 deployment control에서는 path validation과 tuple change가 관찰되고, application task completion도 확인된다. 그러나 이 결과를 Chrome/Safari 브라우저의 Wi-Fi/cellular handover 성공으로 일반화할 수는 없다.

브라우저 쪽에서는 iPhone USB failover trigger가 준비되었지만, controlled public origin이 현재 `connection_refused` 상태다. 따라서 지금 final Chrome active network-change row를 실행하면 CM 실패가 아니라 origin readiness 실패를 만들 가능성이 높다.

작업 연속성 결과는 workload-dependent하다. 대용량 upload/download는 중단이 곧 task failure로 나타나며, retry나 Range resume이 completion을 회복할 수 있다. 반면 media workload는 segment retry와 buffer depth에 따라 completion, startup delay, rebuffer event가 분리된다. 따라서 streaming은 단순 completion이 아니라 QoE metric과 session attribution을 함께 보고해야 한다.

## 한계

- Chrome single-session browser CM 성공은 아직 증명되지 않았다.
- iPhone USB trigger는 simultaneous active multipath가 아니라 delayed OS failover다.
- local UDP rebinding control은 public Wi-Fi/cellular handover threshold로 직접 일반화할 수 없다.
- controlled public origin 복구 후 fresh baseline이 필요하다.
- Safari 또는 Android feasibility row가 아직 없다.

## 다음 실행 순서

1. AWS credential 또는 SSH를 복구해 controlled public origin을 다시 연다.
2. fresh Chrome controlled public H3 baseline을 재실행한다.
3. Chrome downlink no-heartbeat active path-change 3회를 수행한다.
4. Chrome downlink heartbeat active path-change 3회를 수행한다.
5. Range/resumable download와 buffered-media public handover를 추가한다.
6. Safari 또는 Android Chrome feasibility row를 채운다.
