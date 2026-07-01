# Chapter 5 Reference And Evidence

작성일: `2026-06-30`

이 문서는 Chapter 5 "브라우저 CM 관찰성 기준"의 실제 구현 코드, scanner trigger, 결과 문서, 공식 reference link를 정리한다. 목적은 브라우저별 claim ceiling을 근거와 함께 검증 가능하게 만드는 것이다.

## 1. 현재 repo의 구현/실행 근거

| 역할 | 링크 | 설명 |
| --- | --- | --- |
| browser observability readiness scanner | [tools/check_browser_cm_observability.py](../../tools/check_browser_cm_observability.py) | Chrome/Safari/packet capture/iOS remote capture 후보 도구 준비 여부 확인 |
| Chrome CDP navigation runner | [tools/run_chrome_cdp_navigation.js](../../tools/run_chrome_cdp_navigation.js) | headless Chrome, NetLog, CDP, forced QUIC 옵션 실행 |
| Chrome artifact classifier | [tools/classify_chrome_h3_artifacts.py](../../tools/classify_chrome_h3_artifacts.py) | local Chrome H3/rebinding artifact에서 browser CM 후보 판정 |
| controlled public network-change classifier | [tools/classify_controlled_public_h3_network_change.py](../../tools/classify_controlled_public_h3_network_change.py) | public origin Chrome/Safari/Android network-change artifact 판정 |
| Android Chrome navigation runner | [tools/run_android_chrome_navigation.py](../../tools/run_android_chrome_navigation.py) | ADB로 Android Chrome URL open, serial redaction |
| Safari WebDriver runner | [tools/run_safari_webdriver_navigation.py](../../tools/run_safari_webdriver_navigation.py) | safaridriver WebDriver HTTP protocol navigation |
| network path snapshot | [tools/capture_network_path_snapshot.py](../../tools/capture_network_path_snapshot.py) | active/default/target route snapshot 수집 |
| path snapshot comparator | [tools/compare_network_path_snapshots.py](../../tools/compare_network_path_snapshots.py) | before/after path snapshot에서 active path change 여부 분류 |

## 2. Scanner Trigger Map

자세한 line-level trigger는 별도 표에 고정했다.

- [tables/chapter-05-scanner-trigger-map-20260630.md](tables/chapter-05-scanner-trigger-map-20260630.md)

요약:

| scanner/classifier | 핵심 trigger | 과장 방지 장치 |
| --- | --- | --- |
| `check_browser_cm_observability.py` | Chrome executable, safaridriver, tcpdump, rvictl, route, ifconfig | readiness만 판정하고 CM 성공 판정은 하지 않음 |
| `classify_chrome_h3_artifacts.py` | server request, NetLog target QUIC session, HTTP stream job `using_quic`, qlog path frames, DOM completion | `MODE` event만으로 success 처리하지 않음 |
| `classify_controlled_public_h3_network_change.py` | active client path change, target H3 remote tuple count, qlog H3/path evidence, NetLog session count, application result | active path change가 없으면 `PASS_NEGATIVE_CONTROL`로 낮춤 |
| `run_chrome_cdp_navigation.js` | `--enable-quic`, `--log-net-log`, `--origin-to-force-quic-on`, CDP navigation | artifact 생성용 runner이며 판정은 classifier에 위임 |
| `run_safari_webdriver_navigation.py` | safaridriver session create/navigate/title/current_url | WebDriver success를 QUIC session evidence로 쓰지 않음 |
| `run_android_chrome_navigation.py` | ADB device selection, `am start` with Chrome package, sanitized serial | navigation success만 기록하고 Android CM claim은 하지 않음 |

## 3. 공식 reference links

| source | 링크 | Chapter 5에서의 역할 |
| --- | --- | --- |
| Chromium NetLog capture guide | [Providing Network Details for bug reports](https://www.chromium.org/for-testers/providing-network-details/) | Chrome NetLog capture 방식 근거 |
| Chromium NetLog event types | [net_log_event_type_list.h](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h) | QUIC session/network/migration event 관찰 기준 |
| Chromium QUIC client session | [quic_chromium_client_session.h](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/net/quic/quic_chromium_client_session.h) | Chrome stack에 migration primitive/hook이 존재한다는 source 근거 |
| Chromium QUIC context | [quic_context.h](https://chromium.googlesource.com/chromium/src/+/master/net/quic/quic_context.h) | Chromium QUIC runtime context/policy source 근거 |
| Cronet URLRequestContextConfig | [url_request_context_config.cc](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/components/cronet/url_request_context_config.cc) | Cronet policy와 Chrome browser policy를 구분해야 하는 근거 |
| Android Cronet CM options | [Cronet ConnectionMigrationOptions](https://developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/ConnectionMigrationOptions) | Android/Cronet API-level migration option reference |
| Android platform HTTP CM builder | [ConnectionMigrationOptions.Builder](https://developer.android.com/reference/android/net/http/ConnectionMigrationOptions.Builder) | Android platform HTTP stack option reference |
| WebKit Safari WebDriver | [WebDriver Support in Safari 10](https://webkit.org/blog/6900/webdriver-support-in-safari-10/) | Safari automation 가능성 근거 |
| Selenium Safari docs | [Selenium Safari documentation](https://www.selenium.dev/documentation/webdriver/browsers/safari/) | Safari WebDriver enablement/logging reference |
| W3C WebDriver | [WebDriver specification](https://www.w3.org/TR/webdriver2/) | WebDriver가 browser automation protocol이지 QUIC observability protocol은 아니라는 기준 |
| RFC 9000 | [QUIC: A UDP-Based Multiplexed and Secure Transport](https://datatracker.ietf.org/doc/html/rfc9000) | connection migration/path validation 기준 |
| RFC 9114 | [HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114) | application HTTP/3 request 기준 |
| qlog schema | [qlog main schema](https://quicwg.org/qlog/draft-ietf-quic-qlog-main-schema.html) | qlog event artifact 기준 |

## 4. 결과 문서와 데이터 링크

| 결과/데이터 | 의미 |
| --- | --- |
| [docs/results/browser-cm-observability-matrix-20260624.md](../results/browser-cm-observability-matrix-20260624.md) | browser별 observability matrix 원본 |
| [data/browser-cm-observability-matrix-20260624.csv](../../data/browser-cm-observability-matrix-20260624.csv) | browser별 automation/evidence/claim ceiling CSV |
| [docs/results/browser-cm-observability-readiness-20260624.md](../results/browser-cm-observability-readiness-20260624.md) | 기존 readiness scanner output |
| [docs/results/browser-cm-observability-readiness-refresh-20260630.md](../results/browser-cm-observability-readiness-refresh-20260630.md) | Safari session smoke를 포함한 fresh browser observability readiness |
| [data/browser-cm-observability-refresh-20260630.json](../../data/browser-cm-observability-refresh-20260630.json) | fresh browser observability readiness JSON |
| [docs/results/safari-webdriver-session-readiness-20260630.md](../results/safari-webdriver-session-readiness-20260630.md) | Safari WebDriver binary readiness와 real session readiness 분리 결과 |
| [docs/results/chromium-cronet-source-evidence-20260624.md](../results/chromium-cronet-source-evidence-20260624.md) | Chromium/Cronet source evidence 정리 |
| [docs/results/evidence-chain-and-gap-synthesis-20260624.md](../results/evidence-chain-and-gap-synthesis-20260624.md) | 전체 evidence chain과 gap synthesis |
| [docs/results/literature-refresh-wild-cm-and-netlog-boundary-20260624.md](../results/literature-refresh-wild-cm-and-netlog-boundary-20260624.md) | Wild CM/NetLog claim boundary literature refresh |

## 5. Fresh Scanner Run

실행 명령:

```bash
python3 tools/check_browser_cm_observability.py --format markdown --safari-session-smoke
```

결과:

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

## 6. Verification Commands

`pytest`는 현재 시스템 Python에서 발견되지 않았다.

```text
/opt/local/bin/python3: No module named pytest
```

대신 test script를 직접 실행했다.

```bash
PYTHONPATH=tools python3 tools/test_classify_chrome_h3_artifacts.py
PYTHONPATH=tools python3 tools/test_classify_controlled_public_h3_network_change.py
PYTHONPATH=tools python3 tools/test_check_final_browser_handover_readiness.py
```

결과:

| test | result |
| --- | --- |
| `test_classify_chrome_h3_artifacts.py` | `classify_chrome_h3_artifacts=ok` |
| `test_classify_controlled_public_h3_network_change.py` | `classify_controlled_public_h3_network_change=ok` |
| `test_check_final_browser_handover_readiness.py` | `check_final_browser_handover_readiness=ok` |

## 7. Claim Boundary

쓸 수 있는 주장:

> Chrome desktop provides the strongest browser-level observability in this harness because NetLog can be combined with server qlog, server request logs, client path snapshots, and DOM completion artifacts.

쓸 수 없는 주장:

| 주장 | 이유 |
| --- | --- |
| Safari automation success is Safari CM success | WebDriver artifact는 navigation automation이지 QUIC session continuity artifact가 아니다. |
| Android Chrome navigation success is Android CM success | ADB navigation artifact만으로 Chrome/Cronet session continuity를 알 수 없다. |
| NetLog migration mode event is migration success | mode/configuration evidence와 trigger/success evidence를 분리해야 한다. |
| qlog path validation alone proves application continuity | task completion, browser session attribution, path-change evidence가 함께 필요하다. |
