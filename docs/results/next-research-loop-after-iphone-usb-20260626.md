# Next Research Loop After iPhone USB Controls

작성일: 2026-06-26

## 현재 결론

Chrome + macOS + iPhone USB tethering 경로는 HTTP/3 자체가 불가능한 경로는 아니다. pre-cutover short downlink control에서 default/target route가 `en8`인 상태로 HTTP/3 application traffic과 application completion을 확인했다.

하지만 같은 pre-cutover 조건의 long downlink control은 application completion에 실패했다. active network-change trial도 route는 `en8`로 넘어갔지만 qlog PATH_CHALLENGE/PATH_RESPONSE 없이 downlink application task가 실패했다. 따라서 현재 iPhone USB setup은 browser CM positive evidence를 얻기 위한 주력 환경이라기보다, OS/network-manager timing과 application workload sensitivity를 보여주는 negative/control 환경으로 쓰는 것이 안전하다.

## 다음 우선순위

1. Android Chrome cellular handover feasibility

   Android 기기가 ADB로 잡히면 가장 먼저 수행한다. macOS가 아니라 모바일 OS 자체가 Wi-Fi/cellular path change를 처리하므로, desktop tethering보다 browser CM 검증 조건에 더 가깝다. 목표는 server qlog PATH validation, client path-change snapshot, application completion을 함께 얻는 것이다.

2. Safari/iOS feasibility

   iPhone에서 Safari를 직접 쓰거나 iOS 원격 관측을 붙이는 방향이다. Chrome NetLog 같은 browser-internal artifact는 부족하므로 server qlog, route/packet capture, application result를 중심으로 feasibility evidence로 취급한다.

3. iPhone USB workload boundary repetition

   이미 short 3초/8KB는 성공했고 long 15초/64KB는 실패했다. 중간 구간, 예를 들어 5초/16KB, 8초/32KB, 12초/64KB를 반복해 no-change tethering baseline의 안정 구간을 먼저 찾는다. 이 baseline이 안정적인 구간에서만 active network-change를 다시 시도한다.

4. Active short-workload network-change control

   iPhone USB pre-cutover short control이 성공했으므로, active network-change도 같은 short workload로 줄여서 한 번 검수한다. 만약 short active에서도 실패하면 path validation 미관측 또는 OS handover timing 문제가 더 강해진다. short active가 성공하면 long workload 실패와 active CM 실패를 분리할 수 있다.

5. Application-level recovery separation

   retry/heartbeat는 CM 성공 증거와 섞으면 안 된다. 먼저 no-retry/no-heartbeat로 transport/browser behavior를 본 뒤, 별도 row에서 retry/heartbeat가 사용자 작업 연속성을 얼마나 회복하는지 측정한다.

## 진행된 실행

2026-06-26에 `iPhone USB workload boundary repetition`의 1차 실행을 진행했다.

- 5s/16KB no-change: application completion 성공
- 8s/32KB no-change: application completion 성공
- 12s/64KB no-change: application completion 성공
- 8s/32KB active network-change: 3/3 반복 모두 route `en0 -> en8` 전환은 성공했지만 application은 미완료, qlog PATH_CHALLENGE/PATH_RESPONSE 0/0
- 8s/32KB trigger timing sweep: 4s/6s/7s trigger 모두 3/3 미완료, qlog PATH_CHALLENGE/PATH_RESPONSE 0/0
- 8s/32KB heartbeat diagnostic: heartbeat fetch는 3/3 HTTP 200, downlink는 1/3 completion, 하지만 qlog PATH_CHALLENGE/PATH_RESPONSE 0/0

상세 결과는 `docs/results/iphone-usb-boundary-and-active-short-20260626.md`, `docs/results/iphone-usb-trigger-timing-sweep-20260626.md`, `docs/results/iphone-usb-heartbeat-diagnostic-20260626.md`에 기록했다.

## 다음 실행 추천

가장 가까운 다음 실행은 `boundary8000-32kb explicit retry/timeout recovery`다. heartbeat는 별도 fetch 응답성은 보여줬지만 in-flight downlink completion을 안정적으로 회복하지 못했으므로, stream timeout과 retry를 application layer에 넣은 조건을 분리 측정하는 것이 좋다.

권장 matrix:

| duration_ms | bytes | chunks | repetition | 목적 |
| ---: | ---: | ---: | ---: | --- |
| 8000 | 32768 | 8 | 3 | retry_attempts=1 recovery |
| 8000 | 32768 | 8 | 3 | retry_attempts=2 recovery |
| 8000 | 32768 | 8 | 3 | stream timeout + retry recovery |

판정 기준:

- route: pre-cutover default/target route가 모두 `en8`
- protocol: server qlog `chosen_alpn > 0` and `http3_frame > 0`
- application: CDP dataset `downlinkComplete=true`
- failure separation: qlog H3는 있으나 application 실패면 `application_fetch_stream_error_on_iphone_usb_nochange`

## 논문 반영 방향

이 루프는 "CM이 안 된다"라는 단정용이 아니라, browser CM 검증에서 baseline stability를 먼저 만족해야 한다는 방법론 근거로 쓰는 편이 좋다. 즉 positive CM evidence를 찾기 전에, 같은 경로에서 no-change application completion이 안정적인 workload window를 확보해야 한다는 주장이다.
