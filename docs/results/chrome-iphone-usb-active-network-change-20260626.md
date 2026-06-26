# Chrome iPhone USB Active Network-Change Trial

작성일: 2026-06-26

## 목적

Chrome controlled-public HTTP/3 downlink workload 중 macOS Wi-Fi를 끄고 iPhone USB tethering으로 경로가 넘어가는지 검수했다. 이 trial은 final active CM 성공 row가 아니라, 실제 active path-change 조건을 만들기 위한 장비/OS 전환 검증이다.

## 실행 조건

| 항목 | 값 |
| --- | --- |
| browser | Chrome headless CDP runner |
| origin | controlled public WebPKI origin |
| server | EC2 quic-go `h3server`, TCP HTTPS Alt-Svc + UDP H3 |
| workload | `GET /browser-downlink` + streaming `GET /downlink-stream` |
| bootstrap | `GET /browser-slow` + streaming `GET /slow-js` |
| network command | `networksetup -setairportpower en0 off` |
| restore | outer shell trap으로 `networksetup -setairportpower en0 on` |
| expected server requests | 5 |
| local artifacts | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001`, `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-iphone-usb-network-change-002` |

## 하네스 보정

실행 전 readiness/snapshot 도구의 IPv4 판정을 보정했다.

- `169.254.0.0/16` link-local IPv4를 usable secondary path로 세지 않도록 수정했다.
- active runner에 same-profile bootstrap navigation을 추가했다.
- active classifier가 CDP body dataset을 읽어 application success/error를 요약하도록 수정했다.
- final result row의 tuple change는 전체 bootstrap remote addr count가 아니라 target H3 workload remote addr count를 우선 사용하도록 수정했다.

## 결과 1: 15초 Downlink Trial

| 관찰 | 결과 |
| --- | --- |
| server expected count | 5/5 도달 |
| application H3 | server qlog와 Chrome NetLog에서 확인 |
| Chrome target QUIC session count | 1 |
| immediate client path-change summary | `interface_set_changed_without_route_change` |
| eventual client path-change summary | `client_active_path_changed` |
| eventual target/default route | `en0`에서 `en8`로 변경 |
| target H3 remote addr count | 1 |
| qlog PATH_CHALLENGE/PATH_RESPONSE | 0/0 |
| application result | `downlinkError=Error: TypeError: network error` |
| final classifier | `PASS_NEGATIVE_CONTROL / application_task_failed_without_quic_path_validation` |
| final protocol count | count 안 함 |

## 결과 2: 45초 Downlink + Multi-Snapshot Trial

| 관찰 | 결과 |
| --- | --- |
| server expected count | 5/5 도달 |
| application H3 | server qlog와 Chrome NetLog에서 확인 |
| Chrome target QUIC session count | 1 |
| immediate client path-change summary | `client_active_path_changed` |
| eventual client path-change summary | `client_active_path_changed` |
| route change timing | command 후 multi-snapshot 내 `en0` -> `en8` 전환 관찰 |
| target H3 remote addr count | 1 |
| qlog PATH_CHALLENGE/PATH_RESPONSE | 0/0 |
| application result | `downlinkBytes=1460`, `downlinkError=Error: TypeError: network error` |
| final classifier | `PASS_NEGATIVE_CONTROL / application_task_failed_without_quic_path_validation` |
| final protocol count | count 안 함 |

## 해석

이번 결과는 “Chrome이 CM을 못 했다”라고 단정하기보다, macOS/iPhone USB tethering 경로 전환이 실제로 발생해도 Chrome의 해당 in-flight HTTP/3 downlink task가 복구되지 않았다는 negative-control이다. 첫 trial에서는 Wi-Fi off 직후 snapshot이 너무 빨라 active interface set이 비는 상태만 기록됐지만 final snapshot에서는 iPhone USB가 `172.20.10.x` 주소를 받고 target/default route가 `en8`로 바뀌었다. 두 번째 trial에서는 multi-snapshot으로 `client_active_path_changed`를 직접 잡았고, 그래도 qlog PATH_CHALLENGE/PATH_RESPONSE는 없었으며 downlink는 약 15초에 실패했다.

애플리케이션 관점에서는 첫 trial이 약 13KB, 두 번째 trial이 약 1.46KB를 받은 뒤 `TypeError: network error`로 실패했다. 따라서 이 trial 묶음은 HTTP/3 전제와 artifact 수집 체인은 검증했지만, connection migration 성숙도 판단을 위한 positive active handover evidence는 제공하지 않는다.

## 논문상 의미

- CM 검증은 QUIC 구현체 지원 여부만으로 끝나지 않고, OS/network manager가 실제 active path-change를 언제 만들어주는지와 browser가 그 변화를 QUIC path validation으로 연결하는지에 크게 의존한다.
- “Wi-Fi를 끄면 tethering이 될 것”이라는 운영자 직관은 실험 증거로 충분하지 않다. before/after route, target route, qlog PATH validation, application completion을 함께 봐야 한다.
- 이번 결과는 unmanaged/desktop tethering 환경에서 active path-change 재현성이 낮을 수 있음을 보여주는 negative-control 근거다.

## 다음 조치

1. iPhone USB가 default route가 될 때까지 대기한 뒤 workload를 시작하는 pre-cutover control을 추가해 “tethering 자체 품질”과 “mid-flight migration”을 분리한다. 실행 결과는 `docs/results/chrome-iphone-usb-precutover-nochange-20260626.md`에 기록했다.
2. Android Chrome ADB 또는 Safari/iOS처럼 OS가 더 자연스럽게 cellular handover를 수행하는 P1 feasibility path를 병행한다.
3. active CM final row는 `possible_connection_migration`, qlog path validation, client active path-change, application success가 함께 관찰될 때만 등록한다.
