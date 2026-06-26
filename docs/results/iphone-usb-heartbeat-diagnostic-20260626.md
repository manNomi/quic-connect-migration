# iPhone USB Heartbeat Diagnostic

작성일: 2026-06-26

## 목적

active `en0 -> en8` path-change에서 stable `8s/32KB` downlink가 반복적으로 미완료였기 때문에, 같은 조건에 `heartbeat=true`를 추가해 별도 application fetch가 살아나는지 확인했다. 이 실험은 QUIC CM 성공 증거가 아니라 application-level recovery/diagnostic evidence로만 취급한다.

## 조건

| 항목 | 값 |
| --- | --- |
| workload | `GET /browser-downlink?duration_ms=8000&chunks=8&bytes=32768&heartbeat=true&heartbeat_delay_ms=5000` |
| trigger | workload 시작 후 2초에 `networksetup -setairportpower en0 off` |
| expected server requests | 6 |
| route observation | `client_active_path_changed`, `en0 -> en8` |

## 결과

| rep | downlink result | heartbeat | target H3 addr | qlog PATH | classifier |
| ---: | --- | --- | --- | --- | --- |
| 1 | failed, `8242 bytes`, `TypeError` | 200 | `211.60.158.171:54995` | 0/0 | `application_task_failed_without_quic_path_validation` |
| 2 | failed, `4121 bytes`, `TypeError` | 200 | `211.60.158.171:50810` | 0/0 | `application_task_failed_without_quic_path_validation` |
| 3 | complete, `32973 bytes` | 200 | `106.101.2.80:44830` | 0/0 | `application_task_succeeded_without_observed_quic_migration` |

상세 CSV: `data/iphone-usb-heartbeat-diagnostic-20260626.csv`

## 해석

heartbeat fetch는 3/3에서 HTTP 200을 받았다. 그러나 qlog `PATH_CHALLENGE/PATH_RESPONSE`는 모든 반복에서 0/0이고, target H3 remote addr count도 1이었다. 따라서 heartbeat 성공 또는 3회차 downlink completion을 QUIC connection migration 성공으로 해석하면 안 된다.

3회차는 downlink까지 완료됐지만 target H3 addr가 cellular public IP 하나로만 관측됐다. 이는 in-flight stream migration 증거라기보다, workload timing과 route-change timing이 맞물려 request가 cellular path에서 처리된 negative/control 사례로 보는 것이 안전하다.

## 논문상 의미

- application-level 추가 요청은 일부 조건에서 사용자 관점의 응답성을 회복할 수 있다.
- 하지만 application success는 QUIC CM success와 다르다.
- browser CM 성숙도 평가에서는 `application_success`, `target_h3_tuple_change`, `qlog_path_validation`을 분리해야 한다.

## 다음 단계

1. explicit retry/timeout을 application layer에 넣어 downlink stream 자체를 재시도할 수 있는지 측정한다.
2. heartbeat success가 HTTP/1.1인지 HTTP/3인지와 public IP 경로를 더 명확히 분류한다.
3. Android Chrome 또는 Safari/iOS에서 같은 heartbeat diagnostic을 비교한다.
