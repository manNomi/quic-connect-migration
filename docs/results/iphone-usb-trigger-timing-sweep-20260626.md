# iPhone USB Trigger Timing Sweep

작성일: 2026-06-26

## 목적

`8s/32KB` downlink workload는 iPhone USB pre-cutover no-change에서 완료됐지만, active `en0 -> en8` 전환에서는 2초 trigger 조건에서 3/3 미완료였다. 이번 sweep은 trigger 시점을 4초, 6초, 7초로 늦춰도 application completion이 복구되는지 확인하기 위해 수행했다.

## 공통 조건

| 항목 | 값 |
| --- | --- |
| browser | Chrome headless CDP runner |
| origin | controlled public EC2 quic-go H3 origin |
| workload | `GET /browser-downlink?duration_ms=8000&chunks=8&bytes=32768` + streaming `GET /downlink-stream` |
| network command | `networksetup -setairportpower en0 off` |
| path observation | before/after/final route snapshot |
| expected server requests | 5 |

## 결과

| trigger | repetition | app result | bytes | path change | target H3 addr count | qlog PATH |
| ---: | ---: | --- | ---: | --- | ---: | --- |
| 4s | 1 | incomplete | 12363 | `en0 -> en8` | 1 | 0/0 |
| 4s | 2 | incomplete | 12363 | `en0 -> en8` | 1 | 0/0 |
| 4s | 3 | incomplete | 16484 | `en0 -> en8` | 1 | 0/0 |
| 6s | 1 | incomplete | 24726 | `en0 -> en8` | 1 | 0/0 |
| 6s | 2 | incomplete | 20605 | `en0 -> en8` | 1 | 0/0 |
| 6s | 3 | incomplete | 24726 | `en0 -> en8` | 1 | 0/0 |
| 7s | 1 | incomplete | 24726 | `en0 -> en8` | 1 | 0/0 |
| 7s | 2 | incomplete | 24726 | `en0 -> en8` | 1 | 0/0 |
| 7s | 3 | incomplete | 24726 | `en0 -> en8` | 1 | 0/0 |

상세 CSV: `data/iphone-usb-trigger-timing-sweep-20260626.csv`

## 해석

trigger를 2초에서 4초, 6초, 7초로 늦춰도 active path-change 중 application completion은 회복되지 않았다. 수신된 bytes는 늦은 trigger에서 늘어나는 경향이 있지만, 모든 반복에서 `downlinkComplete`가 없고 explicit `downlinkError`도 없는 incomplete 상태로 남았다.

서버와 qlog 관점에서는 모든 반복에서 application H3는 확인됐지만, target H3 remote addr count는 1이고 qlog `PATH_CHALLENGE/PATH_RESPONSE`는 0/0이었다. 즉 route는 `en0 -> en8`로 바뀌지만 Chrome의 in-flight H3 stream이 QUIC path validation을 통해 새 path로 이어지는 증거는 없다.

## 논문상 의미

- no-change baseline이 안정적인 workload에서도 active desktop tethering path-change가 application continuity로 이어지지 않았다.
- trigger timing을 workload 후반부까지 늦춰도 결과가 유지되어, 단순히 너무 이른 전환이라 실패했다는 설명은 약해졌다.
- 이번 결과는 browser-level CM readiness를 평가할 때 OS route-change, QUIC path validation, application task completion을 분리해야 한다는 근거가 된다.

## 다음 단계

1. 같은 stable workload에 retry/heartbeat를 붙여 application-level recovery가 incomplete 상태를 회복하는지 별도 측정한다.
2. Android Chrome 또는 Safari/iOS처럼 OS-native handover 환경에서 같은 workload를 재실험한다.
3. Chrome NetLog에서 migration mode event와 실제 path validation 부재 사이의 의미를 더 세밀하게 해석한다.
