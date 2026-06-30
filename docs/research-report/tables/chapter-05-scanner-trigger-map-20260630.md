# Chapter 5 Scanner Trigger Map

작성일: `2026-06-30`

이 표는 브라우저 CM 관찰성 챕터에서 사용한 scanner/classifier가 실제로 어떤 코드에서 어떤 조건을 읽어 판정하는지 정리한다. 링크는 GitHub Markdown에서 line anchor로 바로 확인할 수 있게 구성했다.

## 1. Readiness Scanner

| 코드 위치 | trigger/input | 출력 필드 | 해석 |
| --- | --- | --- | --- |
| [check_browser_cm_observability.py#L93-L143](../../../tools/check_browser_cm_observability.py#L93-L143) | Chrome/Safari/Safari TP path, `safaridriver`, `tcpdump`, `rvictl`, `networksetup`, `route`, `ifconfig` | `chrome_netlog_ready`, `safari_webdriver_ready`, `packet_capture_tooling_ready`, `ios_remote_capture_candidate`, `blockers` | 실험 도구 준비 상태만 판단 |
| [check_browser_cm_observability.py#L109-L125](../../../tools/check_browser_cm_observability.py#L109-L125) | executable/command availability | blockers | Safari는 NetLog equivalent가 없으므로 server qlog/pcap 필요 |
| [check_browser_cm_observability.py#L156-L176](../../../tools/check_browser_cm_observability.py#L156-L176) | readiness object | markdown report table | 공개 보고용으로 stdout/stderr raw output을 제외 |

## 2. Chrome Artifact Classifier

| 코드 위치 | trigger/input | 출력/분류 | 해석 |
| --- | --- | --- | --- |
| [classify_chrome_h3_artifacts.py#L13-L24](../../../tools/classify_chrome_h3_artifacts.py#L13-L24) | qlog 문자열 `path_challenge`, `path_response`, `chosen_alpn`, `http3:frame` 등 | qlog count | qlog artifact에서 path/application H3 evidence 추출 |
| [classify_chrome_h3_artifacts.py#L27-L39](../../../tools/classify_chrome_h3_artifacts.py#L27-L39) | NetLog event name에 `MIGRAT`, `MODE`, `SUCCESS`, `FAIL`, `TRIGGER` 포함 여부 | migration event class | mode/trigger/success/failure를 분리 |
| [classify_chrome_h3_artifacts.py#L88-L141](../../../tools/classify_chrome_h3_artifacts.py#L88-L141) | NetLog JSON constants/events, target host:port | target QUIC session count, source id, HTTP stream job, migration/network event count | Chrome browser-internal session attribution |
| [classify_chrome_h3_artifacts.py#L144-L171](../../../tools/classify_chrome_h3_artifacts.py#L144-L171) | NetLog JSON이 덜 닫힌 경우의 raw text | conservative fallback counts | 깨진 NetLog를 성공으로 과장하지 않기 위한 fallback |
| [classify_chrome_h3_artifacts.py#L193-L206](../../../tools/classify_chrome_h3_artifacts.py#L193-L206) | DOM dump data attributes | workload completion boolean | upload/downlink/poll/media/range completion 분리 |
| [classify_chrome_h3_artifacts.py#L247-L290](../../../tools/classify_chrome_h3_artifacts.py#L247-L290) | request reached server, qlog path validation/probe, remote tuple count, Chrome QUIC session count, network-change flag, client path classification, proxy switch, DOM completion | `nat_rebinding_possible_session_continuity`, `multiple_quic_sessions_without_network_change`, `browser_application_task_failed` 등 | single-session CM 후보와 reconnect/multiple-session/failed-task를 분리 |
| [classify_chrome_h3_artifacts.py#L304-L317](../../../tools/classify_chrome_h3_artifacts.py#L304-L317) | artifact files `server.json`, `network-change.json`, `client-path-change-summary.json`, `rebinding-proxy.json`, `chrome/netlog.json`, `dump-dom.txt`, `qlog/` | summary inputs | scanner가 실제로 읽는 artifact 파일 목록 |

## 3. Controlled Public Network-Change Classifier

| 코드 위치 | trigger/input | 출력/분류 | 해석 |
| --- | --- | --- | --- |
| [classify_controlled_public_h3_network_change.py#L16-L31](../../../tools/classify_controlled_public_h3_network_change.py#L16-L31) | workload labels | target H3 workload filter | browser workload와 helper request를 구분 |
| [classify_controlled_public_h3_network_change.py#L54-L68](../../../tools/classify_controlled_public_h3_network_change.py#L54-L68) | client path summary JSON | `active_path_changed`, interface/gateway/public IP changed | network-change command와 실제 active path change를 분리 |
| [classify_controlled_public_h3_network_change.py#L71-L84](../../../tools/classify_controlled_public_h3_network_change.py#L71-L84) | server request list, workload/proto/alpn | target H3 remote addr count | HTTP/3 workload tuple 변화만 별도 집계 |
| [classify_controlled_public_h3_network_change.py#L87-L152](../../../tools/classify_controlled_public_h3_network_change.py#L87-L152) | server_ok, qlog H3/path evidence, network-change command, client active path change, application success, browser kind, NetLog session count | `PASS`, `PASS_FEASIBILITY`, `PASS_NEGATIVE_CONTROL`, `FAIL` | Chrome/Safari/Android별 claim ceiling을 다르게 적용 |
| [classify_controlled_public_h3_network_change.py#L168-L225](../../../tools/classify_controlled_public_h3_network_change.py#L168-L225) | `server.json`, `public-origin-readiness.json`, `qlog/`, NetLog, DOM dump, network/path summaries | classification summary object | public-origin handover artifact 통합 |

## 4. Browser Runners

| 코드 위치 | trigger/input | 생성 artifact | 해석 |
| --- | --- | --- | --- |
| [run_chrome_cdp_navigation.js#L163-L186](../../../tools/run_chrome_cdp_navigation.js#L163-L186) | Chrome launch args `--enable-quic`, `--log-net-log`, `--net-log-capture-mode`, `--remote-debugging-port`, optional forced QUIC/SPKI | Chrome NetLog, profile, CDP-controlled navigation | Chrome artifact 생성 |
| [run_chrome_cdp_navigation.js#L201-L260](../../../tools/run_chrome_cdp_navigation.js#L201-L260) | ready expression polling | ready expression result JSON | workload가 준비/완료됐는지 DOM 기준으로 대기 |
| [run_safari_webdriver_navigation.py#L84-L164](../../../tools/run_safari_webdriver_navigation.py#L84-L164) | safaridriver status/session/navigate/current_url/title/delete_session | Safari navigation JSON, safaridriver log | automation success만 의미 |
| [run_android_chrome_navigation.py#L84-L164](../../../tools/run_android_chrome_navigation.py#L84-L164) | `adb devices`, optional serial, `am start` Chrome package | Android navigation JSON with redacted device label | navigation success만 의미 |

## 5. False-Positive Guards

| guard | 코드 근거 | 방지하는 오해 |
| --- | --- | --- |
| request 실패 우선 | [classify_chrome_h3_artifacts.py#L262-L265](../../../tools/classify_chrome_h3_artifacts.py#L262-L265) | H3 request가 실패했는데 migration으로 해석하는 것 |
| DOM task failure 우선 | [classify_chrome_h3_artifacts.py#L264-L265](../../../tools/classify_chrome_h3_artifacts.py#L264-L265) | transport evidence가 있어도 application task 실패를 PASS로 처리하는 것 |
| active client path change gate | [classify_controlled_public_h3_network_change.py#L121-L128](../../../tools/classify_controlled_public_h3_network_change.py#L121-L128) | network-change 명령만으로 handover라고 주장하는 것 |
| non-Chrome claim demotion | [classify_controlled_public_h3_network_change.py#L138-L140](../../../tools/classify_controlled_public_h3_network_change.py#L138-L140) | Safari/Android server qlog evidence를 Chrome single-session evidence처럼 취급하는 것 |
| multiple session demotion | [classify_controlled_public_h3_network_change.py#L140-L143](../../../tools/classify_controlled_public_h3_network_change.py#L140-L143) | tuple change가 있지만 여러 QUIC session이면 single-session CM으로 과장하는 것 |
