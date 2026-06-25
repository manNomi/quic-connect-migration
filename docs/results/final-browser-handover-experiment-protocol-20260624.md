# Final browser handover experiment protocol

작성일: 2026-06-24

## 1. 목적

논문 본 실험으로 채택할 browser-level HTTP/3 Connection Migration 결과를 얻기 위한 최종 실행 프로토콜이다.

현재 저장소는 local/AWS positive control, Chrome local browser baseline, negative control, controlled public origin gate, Chrome/Safari/Android network-change harness를 갖췄다. 하지만 실제 active Wi-Fi/LTE 또는 active interface handover 결과는 아직 없다. 따라서 본 프로토콜은 장비가 준비됐을 때 어떤 순서로 실험하고, 어떤 결과만 논문 claim으로 인정할지 고정한다.

## 2. 공통 preflight

실험 전에 다음이 모두 참이어야 한다.

| gate | 통과 기준 |
| --- | --- |
| publication bundle | `python3 tools/validate_publication_bundle.py` 통과 |
| storage | `python3 tools/report_artifact_storage.py` 기준 disk free 7 GiB 이상 권장 |
| controlled public origin | DNS, WebPKI TLS, TCP/UDP 443, Alt-Svc 준비 |
| baseline | controlled public application H3 baseline summary가 `PASS` 또는 browser별 허용 `PASS_FEASIBILITY` |
| active path-change | command 전후 실제 default/target path 또는 Android active network가 바뀜 |
| artifacts | server request log, server qlog, browser artifact, network-change JSON, client/network snapshot 확보 |

현재 2026-06-24 상태에서는 disk free 약 2.44 GiB, active desktop interface 1개, Android device 없음, AWS identity 없음으로 본 실험 실행 조건을 만족하지 않는다.

## 3. Chrome desktop 본 실험

Chrome은 가장 강한 browser-side observability를 제공하므로 P0 실험이다.

실험 matrix:

| trial group | workload | heartbeat | expected requests | claim strength |
| --- | --- | --- | ---: | --- |
| Chrome-D1 | `/browser-downlink` | false | 2 | strong if NetLog + qlog + tuple evidence align |
| Chrome-D2 | `/browser-downlink` | true | 3 | compare recovery/session behavior with D1 |
| Chrome-S1 | `/browser-slow` | false | 2 | compatibility with prior slow-subresource controls |

반복:

- 각 trial group은 최소 3회 반복한다.
- no-change baseline 1회 이상을 같은 origin/profile 조건에서 먼저 실행한다.
- heartbeat variant는 no-heartbeat 결과와 비교해서만 해석한다.

채택 가능한 성공:

```text
classification = possible_connection_migration
client_path_change.classification = client_active_path_changed
server_qlog_has_path_validation = true
server_requests.remote_addr_count > 1
Chrome NetLog target QUIC session evidence가 reconnect/multiple-session 해석을 배제하거나 약화하지 않음
```

채택 불가:

- `reconnect_or_multiple_sessions`
- `tuple_changed_without_path_validation`
- `no_path_change_after_trigger`
- client path가 바뀌지 않은 inactive interface toggle
- application H3 baseline이 실패한 trial

## 4. Safari 본 실험

Safari는 browser-internal QUIC log가 현재 harness에 없으므로 P1 실험이다.

실행 wrapper:

```bash
./scripts/run-safari-controlled-public-network-change.sh
```

채택 가능한 결과:

```text
classification = possible_connection_migration_server_qlog_only
status = PASS_FEASIBILITY
server_requests.remote_addr_count > 1
server_qlog_has_path_validation = true
Safari navigation_ok = true
```

논문 claim 제한:

- “Safari에서 browser-internal evidence까지 확보한 CM 성공”이라고 쓰지 않는다.
- “server/qlog 관점에서 CM-compatible behavior가 관찰됐다”로 쓴다.
- packet capture를 추가하면 별도 보조 evidence로 표기한다.

## 5. Android Chrome 본 실험

Android Chrome은 실제 Wi-Fi/LTE handover 연구의 핵심 대상이지만, 현재 ADB device가 없어 실행되지 않았다.

실행 wrapper:

```bash
./scripts/run-android-chrome-controlled-public-network-change.sh
```

필수 환경:

| 항목 | 예시 |
| --- | --- |
| ADB device | `adb devices`에서 `device` 상태 |
| network-change command | `ANDROID_NETWORK_CHANGE_CMD='adb shell svc wifi disable'` |
| workload | public WebPKI `/browser-downlink` 또는 `/browser-slow` |
| Android raw snapshot | `android/connectivity-*.txt`, `android/ip-route-*.txt`, `android/ip-addr-*.txt` |

채택 가능한 결과:

```text
classification = possible_connection_migration_server_qlog_only
status = PASS_FEASIBILITY
Android Chrome navigation_ok = true
server_qlog_has_path_validation = true
server remote tuple changed
```

논문 claim 제한은 Safari와 같다. Android 내부 QUIC session log나 packet capture가 없으면 feasibility evidence로만 둔다.

## 6. 결과 기록 절차

각 trial이 끝나면 다음 순서로 기록한다.

1. raw artifact는 ignored `repro/quic-go-min-repro/artifacts/<run-id>`에 유지한다.
2. classifier summary를 확인한다.
3. 공개 가능한 요약만 `data/experiment-results.csv`에 추가한다.
4. `harness/manifests/experiment-matrix.csv`에 trial group 상태를 갱신한다.
5. `python3 tools/build_paper_tables.py --output docs/results/paper-tables-20260624.md` 실행.
6. `python3 tools/audit_research_bundle.py --output docs/results/research-bundle-audit-20260624.md` 실행.
7. `python3 tools/validate_publication_bundle.py` 실행.

## 7. 논문 판단 규칙

| 결과 유형 | 논문 표현 |
| --- | --- |
| Chrome `possible_connection_migration` | browser-level HTTP/3 CM 후보 성공 |
| Chrome `reconnect_or_multiple_sessions` | workload continuity may occur, but CM not established |
| Chrome/Safari/Android server-qlog-only success | CM-compatible feasibility evidence |
| tuple change without qlog path validation | reconnect/NAT/path artifact; CM claim 불가 |
| no client active path change | no-op trigger negative control |
| baseline H3 failure | deployment/precondition failure, CM failure가 아님 |

## 8. 완료 조건

논문 Results를 “본 실험 완료”로 갱신하려면 최소한 다음이 필요하다.

1. Chrome controlled public active path-change no-heartbeat 3회
2. Chrome controlled public active path-change heartbeat 3회
3. 각 Chrome trial의 no-change baseline
4. Safari 또는 Android 중 하나 이상의 P1 feasibility run
5. 실패 trial도 negative/control로 같은 기준에 따라 기록

이 조건 전까지는 현재 결론을 유지한다.

> QUIC/HTTP/3 Connection Migration은 controlled 환경에서는 동작하지만, 실제 browser/mobile deployment에서의 작업 연속성은 client policy, deployment path, active network-change evidence, application recovery까지 함께 검증해야 한다.
