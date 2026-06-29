# 현재 증거 기반 논문 Skeleton

생성일: `2026-06-29`

## 추천 제목

HTTP/3/QUIC Connection Migration의 구현 성숙도와 웹 작업 연속성: Evidence Chain 및 Workload-Sensitive Recovery 분석

## 대체 제목

- Wi-Fi-to-Cellular Failover 환경에서 HTTP/3/QUIC Connection Migration 성숙도와 웹 작업 연속성 평가
- QUIC Connection Migration은 왜 웹에서 잘 보이지 않는가: 구현체 성숙도, 배포 friction, 작업 연속성 분석

## 초록 초안

QUIC Connection Migration은 endpoint의 IP 주소나 포트가 바뀌어도 connection continuity를 유지할 수 있도록 설계된 transport 기능이다. 그러나 HTTP/3 웹 애플리케이션에서 이 기능이 실제 작업 연속성으로 이어지는지는 구현체, 브라우저 runtime policy, endpoint discovery, load balancer routing, proxy/CDN termination, client path-change proof, application recovery strategy에 의해 달라진다. 본 연구는 QUIC 구현체와 배포 경로의 CM 성숙도를 조사하고, Chrome HTTP/3 workload에서 upload, download, polling, streaming 작업이 path disruption과 application-level recovery에 어떻게 반응하는지 분석한다. 현재 증거는 controlled QUIC implementation과 deployment에서는 path validation과 tuple change가 재현 가능함을 보여주지만, Chrome single-session browser CM 성공은 아직 증명하지 못한다. 반면 대용량 upload/download, Range resume, media buffering 실험은 작업 연속성이 transport CM뿐 아니라 retry, replacement session, buffering, QoE tradeoff에 의해 결정됨을 보여준다. 따라서 본 연구는 HTTP/3 CM 평가가 단순 connection 유지 여부가 아니라 evidence chain과 workload semantics를 함께 포함해야 한다고 주장한다.

## 핵심 기여

1. QUIC CM 구현체 성숙도를 active/passive migration, API 노출, qlog/trace, test, deployment suitability 기준으로 정리했다.
2. browser CM claim에 필요한 evidence chain을 application H3, client path change, server tuple, qlog path validation, browser session continuity, task completion으로 정의했다.
3. CM이 덜 쓰이는 이유를 구현체 부재가 아니라 runtime policy, endpoint discovery, session attribution, CID-aware routing, proxy/CDN, middlebox, security, workload recovery, observability friction으로 분해했다.
4. upload/download/Range/media workload 결과를 통해 작업 연속성이 retry, Range resume, buffering, replacement-session behavior와 결합되어 나타남을 보였다.
5. 현재 Mac+iPhone 실험에서는 `latent Wi-Fi-loss-to-iPhone-USB cellular failover` trigger가 준비됐지만, controlled public origin 복구 전까지 final browser CM success claim은 보류해야 함을 명확히 했다.

## 현재 주요 결과

- iPhone USB trigger: `latent_iphone_usb_failover_observed, en0 -> en8, 1321 ms`
- public origin blocker: `TCP connection_refused, AWS invalid_client_token`
- upload: retry0 failed 3/3; retry1 succeeded 3/3 after one failed first attempt
- download: timeout-only retry0 failed 3/3; timeout+retry1 succeeded 3/3; local Range 6000ms no-retry 1/3 PASS and retry2 3/3 PASS
- media segments/buffered playback: segment replication 3000ms/6000ms completed 3/3; buffered playback 3000ms completed 12/12 but low buffer had 14 rebuffer events while high buffer had ~15s startup delay and 0 rebuffer
- music-like buffered media: 6000ms no-retry failed 3/3 after first segment; retry1 completed 3/3 with all eight segments
- Chrome single-session browser CM: not-supported-yet

## 권장 논문 구조

1. Introduction
   - QUIC CM의 promise와 HTTP/3 웹 작업 연속성 gap
   - 왜 `HTTP/3 지원`과 `CM 지원`을 분리해야 하는가
2. Background
   - RFC 9000 CM, Connection ID, path validation
   - HTTP/3 discovery와 browser/runtime policy
3. Implementation And Deployment Maturity
   - 구현체 survey
   - quic-go/quiche/AWS NLB positive controls
4. Evidence Chain Methodology
   - CM success 판정 기준
   - negative controls와 overclaim 방지
5. Workload Continuity Experiments
   - upload/download
   - Range/resumable download
   - polling/dashboard
   - media segments/buffered playback
6. Why CM Is Underused
   - layered friction matrix
   - browser/session/deployment/application/observability 원인
7. Discussion
   - application recovery와 transport CM의 관계
   - managed CDN/LB 환경의 claim boundary
8. Limitations And Future Work
   - public origin recovery, fresh baseline, final active rows
   - Safari/Android/Cronet follow-up

## 표/그림 후보

- Table 1: QUIC implementation CM maturity survey
- Table 2: Browser CM evidence chain rubric
- Table 3: Operational friction matrix
- Table 4: Workload sensitivity synthesis
- Figure 1: Transport CM vs application-level recovery boundary
- Figure 2: Browser final handover evidence chain
- Figure 3: Streaming buffer depth vs rebuffer/startup tradeoff

## 지금 쓰면 안 되는 문장

- Chrome은 Wi-Fi-to-cellular failover 중 HTTP/3 connection migration에 성공했다.
- HTTP/3를 지원하는 서버는 Connection Migration도 지원한다.
- tuple이 바뀌었으므로 CM이 성공했다.
- streaming workload completion은 CM이 잘 작동한다는 증거다.

## 다음 실험이 채워야 할 빈칸

- controlled public origin fresh baseline
- Chrome no-heartbeat active path-change 3회
- Chrome heartbeat active path-change 3회
- public Range handover
- public buffered-media handover
- Safari 또는 Android feasibility row
