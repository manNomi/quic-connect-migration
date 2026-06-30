# Chapter 5. 브라우저 Connection Migration 관찰성 기준

작성일: `2026-06-30`

## 1. 이 챕터의 목적

Chapter 3와 Chapter 4는 controlled QUIC client/server와 CID-aware deployment path에서 Connection Migration이 실제로 성립할 수 있음을 보여줬다. 하지만 논문 질문은 브라우저 기반 웹 애플리케이션의 작업 연속성이다. 따라서 Chapter 5의 질문은 다음이다.

> 브라우저 실험에서 어떤 artifact가 있어야 "HTTP/3 Connection Migration이 관찰됐다"고 말할 수 있는가?

이 챕터의 결론은 브라우저별로 claim ceiling을 다르게 잡아야 한다는 것이다. Chrome desktop은 NetLog로 browser-internal QUIC session attribution이 가능하다. Safari와 Android Chrome은 자동화 자체는 가능해도, 현재 harness 기준으로 Chrome NetLog와 같은 수준의 browser-internal QUIC session artifact가 아직 확보되지 않았다.

## 2. 관찰성 레벨

브라우저 CM 실험은 단일 로그 하나로 판정하면 위험하다. 본 연구에서는 다음 레벨을 분리한다.

| 레벨 | 증거 | 의미 | 단독 claim 한계 |
| --- | --- | --- | --- |
| L0 | page/task completion | 페이지 로딩, 업로드, 다운로드, media task가 끝남 | CM 성공의 증거는 아님 |
| L1 | HTTP/3 application proof | NetLog `using_quic=true`, qlog `chosen_alpn`/HTTP/3 frame | HTTP/3 사용 증거이지 migration 증거는 아님 |
| L2 | client/server path change proof | server remote tuple 증가, client path snapshot 변화, local rebinding proxy switch | 재연결 또는 multiple session 가능성 배제 불가 |
| L3 | QUIC path validation proof | qlog 또는 NetLog의 `PATH_CHALLENGE`/`PATH_RESPONSE` | path validation은 transport 절차이지 작업 보장의 충분조건은 아님 |
| L4 | browser session attribution | Chrome target QUIC session count/source id | browser CM claim의 핵심 경계 |
| L5 | application task continuity | L1-L4와 workload completion을 함께 만족 | 논문에서 가장 근거가 충분한 browser-level claim |

따라서 "작업이 완료됐다"와 "같은 QUIC connection에서 migration됐다"는 별도 outcome이다.

## 3. 브라우저별 현재 판정

| 대상 | 자동화 경로 | 내부 QUIC session 관찰성 | 현재 claim ceiling | 다음 필요 증거 |
| --- | --- | --- | --- | --- |
| Chrome desktop | CDP + Chrome NetLog | 가능 | controlled public origin + active path change가 충족되면 browser CM 후보 | single target QUIC session, server tuple change, qlog path validation, application completion |
| Android Chrome | ADB navigation | 현재 harness에서는 미확정 | not countable | Android Chrome/Cronet session log path, Wi-Fi/cellular path change, server qlog |
| Safari macOS | safaridriver WebDriver | Chrome NetLog equivalent 없음 | `PASS_FEASIBILITY` | packet capture, server qlog, controlled public H3 baseline |
| Safari iOS | iOS automation + remote capture 후보 | 현재 harness에서는 없음 | not countable | iOS device automation, `rvictl`/pcap, server qlog |
| quic-go controlled client | custom Go client + qlog | 가능 | implementation positive control | browser policy claim으로 일반화 금지 |

이번 정리에서 fresh readiness scanner를 재실행했다.

| check | value |
| --- | --- |
| Chrome found | `true` |
| Chrome version | `149.0.7827.199` |
| Chrome NetLog ready | `true` |
| Safari found | `true` |
| Safari version | `26.2` |
| Safari TP found | `false` |
| Safari TP version | `-` |
| safaridriver | `exit=0` |
| Safari WebDriver binary ready | `true` |
| Safari WebDriver session checked | `true` |
| Safari WebDriver session ready | `false` |
| Safari WebDriver session error | `Could not create a session: You must enable 'Allow remote automation' in the Developer section of Safari Settings to control Safari via WebDriver.` |
| Safari WebDriver ready | `false` |
| tcpdump | `exit=0` |
| rvictl | `exit=0` |
| packet capture tooling ready | `true` |
| iOS remote capture candidate | `true` |
| blockers | `Safari WebDriver session creation failed; enable Allow remote automation before Safari trials; Safari does not provide a Chrome NetLog-equivalent artifact in this harness; use packet capture and server-side qlog` |

해석:

> 로컬 장비는 Chrome NetLog와 packet capture 도구를 갖추고 있고 Safari/safaridriver binary도 존재한다. 그러나 현재 Safari 설정에서는 WebDriver session creation이 실패하므로 Safari controlled-public trial을 바로 실행할 수 없다. 이 설정을 켠 뒤에도 Safari 계열은 browser-internal QUIC session continuity를 직접 보여주는 artifact가 없으므로 Chrome과 같은 등급으로 판정하면 안 된다.

## 4. Chrome에서만 강한 판정이 가능한 이유

Chrome desktop harness는 다음을 동시에 만들 수 있다.

| artifact | 생성/분석 코드 | 역할 |
| --- | --- | --- |
| Chrome NetLog | `tools/run_chrome_cdp_navigation.js` | Chrome 실행 시 `--log-net-log`, `--enable-quic`, CDP control |
| NetLog parser | `tools/classify_chrome_h3_artifacts.py` | target QUIC session, HTTP stream job, migration event class count |
| server qlog | quic-go H3 server artifact | `PATH_CHALLENGE`/`PATH_RESPONSE`, `chosen_alpn`, HTTP/3 frame |
| server request log | quic-go H3 server artifact | request 도달 여부, remote tuple 변화 |
| DOM dump | Chrome dump-dom artifact | workload completion/error timing |

중요한 guardrail은 `QUIC_CONNECTION_MIGRATION_MODE` 같은 mode evidence만으로 migration success를 판정하지 않는다는 점이다. classifier는 request 도달, HTTP/3 사용, qlog path validation, remote tuple count, Chrome target QUIC session count를 조합한다.

## 5. Safari와 Android에서 낮은 claim ceiling이 필요한 이유

Safari/macOS는 `safaridriver`로 navigation automation은 가능하다. 그러나 현재 harness는 Safari 내부 QUIC session id나 migration event를 Chrome NetLog처럼 얻지 못한다. 따라서 Safari 실험이 성공해도 다음처럼 써야 한다.

> Safari/macOS showed HTTP/3 task feasibility under the controlled origin, but browser-internal QUIC session continuity was not directly observable in this harness.

Android Chrome도 ADB로 Chrome 앱을 열 수는 있다. 하지만 현재 harness는 Android Chrome 또는 Cronet의 session/migration log path를 확정하지 못했다. Android platform/Cronet에는 connection migration 관련 API와 option이 있으나, 그것이 Android Chrome 앱의 실험 artifact로 자동 노출된다는 뜻은 아니다.

## 6. 논문에 쓸 수 있는 주장

안전한 주장:

> Browser-level CM evidence requires more than task completion or server tuple changes. Chrome desktop can provide browser-internal QUIC session attribution through NetLog, while Safari and Android Chrome require additional capture or logging paths before single-session CM claims can be counted.

조건부 주장:

> A Chrome run can be classified as a browser CM candidate only when the same target QUIC session, H3 request evidence, qlog path validation, path-change evidence, and application task completion are jointly observed.

피해야 할 주장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| page load/upload가 성공했으므로 CM도 성공했다 | completion은 L0 evidence다. reconnect/retry 가능성을 배제하지 못한다. |
| server remote tuple이 바뀌었으므로 CM이다 | multiple QUIC sessions 또는 request-level artifact 한계가 있다. |
| Chrome NetLog의 migration mode event만으로 migration 발생이다 | mode/config evidence와 trigger/success evidence는 다르다. |
| Safari WebDriver 성공은 Safari CM 성공이다 | WebDriver는 navigation automation artifact이지 QUIC session artifact가 아니다. |
| Android Cronet API가 있으므로 Android Chrome 앱 CM도 검증됐다 | API availability와 browser app runtime policy/logging은 별도다. |

## 7. 검수 결과

| 검수 항목 | 결과 |
| --- | --- |
| 브라우저별 claim ceiling을 분리했는가? | PASS |
| Chrome NetLog와 Safari WebDriver를 같은 artifact로 취급하지 않았는가? | PASS |
| scanner trigger와 classifier 조건을 문서화했는가? | PASS, `chapter-05-reference-and-evidence.md`와 scanner trigger table 참조 |
| fresh readiness scanner를 재실행했는가? | PASS, `2026-06-30` 실행, Safari session smoke 포함 |
| 테스트를 실행했는가? | PASS, `test_classify_chrome_h3_artifacts.py`, `test_classify_controlled_public_h3_network_change.py`, `test_check_final_browser_handover_readiness.py` 직접 실행 |
| `pytest` 부재를 기록했는가? | PASS, 시스템 `pytest`는 없었고 test script direct execution으로 대체 |
