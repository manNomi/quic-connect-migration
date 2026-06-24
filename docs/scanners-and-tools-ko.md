# 스캐너와 도구 설명

작성일: 2026-06-24  
목적: 연구 과정에서 사용한 수동 검수 절차를 공개 repo에서 반복 가능한 스캐너와 요약 도구로 고정한다.

## 1. `tools/validate_publication_bundle.py`

공개 repo에 올리기 직전 실행하는 안전성/재현성 검증기다.

실행:

```bash
python3 tools/validate_publication_bundle.py
```

검사 항목:

| 항목 | 검사 내용 |
| --- | --- |
| forbidden artifacts | tracked 파일 중 keylog, qlog raw, pcap, pem, tarball 포함 여부 |
| secret patterns | AWS key, secret label, GitHub token, private key, IAM ARN 패턴 |
| CSV parse | `data/*.csv`, `harness/manifests/*.csv` 파싱 가능 여부 |
| Markdown links | repo 내부 Markdown link 존재 여부 |
| harness paths | 공개 repo에서 사용할 수 없는 과거 `experiments/` 경로 참조 여부 |

이 도구는 논문용 public artifact를 만들 때 반드시 먼저 통과해야 한다.

기본값은 git-tracked 파일만 검사한다. 로컬 ignored artifact까지 일부러 확인하려면 다음처럼 실행한다.

```bash
python3 tools/validate_publication_bundle.py --include-untracked
```

## 2. `tools/summarize_experiment_results.py`

[data/experiment-results.csv](../data/experiment-results.csv)를 읽어서 trial 상태를 요약한다.

실행:

```bash
python3 tools/summarize_experiment_results.py --format markdown
python3 tools/summarize_experiment_results.py --format json
```

출력:

- 전체 trial 수
- status별 count
- application success별 count
- trial별 implementation, deployment tier, protocol, failure layer

논문 표를 만들 때 이 도구의 출력과 원본 CSV를 함께 사용한다.

## 3. `tools/scan_implementation_evidence.py`

QUIC 구현체 repo를 대상으로 connection migration 관련 evidence를 찾는 scanner다.

실행 예시:

```bash
python3 tools/scan_implementation_evidence.py ../quic-go ../quiche ../s2n-quic --format markdown
```

출력 형식:

```bash
python3 tools/scan_implementation_evidence.py ../quic-go --format csv
python3 tools/scan_implementation_evidence.py ../quic-go --format json
```

스캔 범주:

| category | 대표 키워드 |
| --- | --- |
| `path_validation` | `PATH_CHALLENGE`, `PATH_RESPONSE`, `path validation` |
| `active_migration_api` | `AddPath`, `Probe`, `Switch`, `perform-migration`, `probe_path` |
| `passive_rebinding` | `NAT rebinding`, `rebinding`, `peer address`, `tuple change` |
| `disable_migration_policy` | `disable_active_migration`, `DisableActiveMigration` |
| `preferred_address` | `preferred address`, `preferred_address`, `PreferredAddress` |
| `cid_and_load_balancing` | `ConnectionIDGenerator`, `QuicServerId`, `QUIC-LB`, `Server ID` |
| `observability` | `qlog`, `PathEvent`, `NetLog`, `tracing` |
| `tests` | `migration test`, `rebinding test`, `path test` |

해석 규칙:

- match count가 높다고 성숙도가 높다는 뜻은 아니다.
- test-only API와 production API를 구분해야 한다.
- active migration, passive rebinding, preferred address는 서로 다른 능력이다.
- HTTP/3 client가 그 기능을 실제로 노출하는지 별도로 확인해야 한다.
- CDN/LB 환경에서는 CID routing과 backend affinity가 별도 검증 대상이다.

## 4. `tools/scan_qlog_events.py`

실험 후 생성된 qlog/qlog-derived text에서 migration evidence를 카운트한다.

실행:

```bash
python3 tools/scan_qlog_events.py repro/quic-go-min-repro/artifacts/local-h3-midflight-check --format markdown
```

카운트 항목:

| 항목 | 의미 |
| --- | --- |
| `path_challenge` | 새 path validation challenge |
| `path_response` | 새 path validation response |
| `connection_started` | connection 생성 evidence |
| `connection_closed` | connection 종료 evidence |
| `packet_sent` | packet sent event |
| `packet_received` | packet received event |
| `http3_frame` | HTTP/3 frame event |
| `chosen_alpn` | ALPN `h3` negotiation evidence |
| `migration` | migration 문자열 evidence |
| `path` | path 관련 event evidence |

주의:

이 도구는 qlog를 정식 schema parser로 해석하지 않고, 반복 가능한 keyword count를 만든다. 논문에는 qlog scanner 결과만 단독 근거로 쓰지 말고, client/server result JSON과 함께 사용한다.

## 5. `tools/classify_chrome_h3_artifacts.py`

Chrome browser 실험 artifact를 server result, Chrome NetLog, qlog 기준으로 분류한다.

실행:

```bash
python3 tools/classify_chrome_h3_artifacts.py \
  repro/quic-go-min-repro/artifacts/chrome-h3-poll-nochange-classifier-pass \
  --addr 127.0.0.1:4443 \
  --expected-requests 6 \
  --workload poll
```

주요 output:

| 항목 | 의미 |
| --- | --- |
| `classification` | browser workload와 migration evidence의 조합 판정 |
| `netlog_target_quic_session_count` | target origin에 대한 Chrome QUIC session 수 |
| `netlog_target_using_quic_job_count` | target origin HTTP stream job 중 QUIC 사용 수 |
| `server_remote_addr_count` | server가 본 client remote tuple 수 |
| `qlog_has_path_validation` | qlog의 `PATH_CHALLENGE`/`PATH_RESPONSE` evidence 여부 |
| `netlog_migration_event_class_counts` | NetLog migration 관련 event를 `mode`, `trigger`, `success`, `failure`, `other`로 분리한 count |

`QUIC_CONNECTION_MIGRATION_MODE` 같은 NetLog event는 설정 evidence로만 보고, 실제 migration evidence는 tuple change와 qlog path validation을 함께 요구한다.

`run-chrome-h3-local.sh`의 `WORKLOAD=downlink`는 같은 classifier를 사용한다.

```bash
cd repro/quic-go-min-repro
WORKLOAD=downlink DOWNLINK_HEARTBEAT=false ./scripts/run-chrome-h3-local.sh
WORKLOAD=downlink DOWNLINK_HEARTBEAT=true ADDR=127.0.0.1:4453 LISTEN_ADDR=127.0.0.1:4453 ORIGIN_ADDR=127.0.0.1:4453 ./scripts/run-chrome-h3-local.sh
```

해석:

| mode | expected request | 의미 |
| --- | --- | --- |
| `DOWNLINK_HEARTBEAT=false` | 2 | `GET /browser-downlink`와 streaming `GET /downlink-stream`만 관찰 |
| `DOWNLINK_HEARTBEAT=true` | 3 | 위 두 request에 더해 `GET /heartbeat`가 같은 H3 connection evidence chain에 포함 |

이 workload는 client-silent downlink와 application heartbeat variant를 비교하기 위한 것이다. path 변화가 없고 heartbeat가 없으면 정상 classification은 `no_path_change_baseline`이다.

downlink/heartbeat 실험에서 추가로 쓰는 classification:

| classification | 의미 |
| --- | --- |
| `multiple_quic_sessions_without_network_change` | network-change trigger 없이 heartbeat 등으로 target QUIC session/source tuple이 2개 이상 관찰됨 |
| `multiple_quic_sessions_without_client_path_change` | network-change command는 있었지만 client path snapshot이 active path 변화를 보이지 않았고, target QUIC session/source tuple이 2개 이상 관찰됨 |

이 두 classification은 migration 성공이 아니다. tuple 변화 단독 주장의 반례로 사용한다.

local UDP rebinding proxy 실험은 같은 downlink workload를 proxy 경유로 실행한다. Chrome은 proxy address에 접속하고, proxy가 첫 client packet 이후 `REBIND_AFTER`가 지나면 server-facing UDP socket A에서 B로 전환한다.

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-rebinding-noheartbeat-smoke-20260624 \
PROXY_ADDR=127.0.0.1:4547 \
SERVER_ADDR=127.0.0.1:4548 \
WORKLOAD=downlink \
DOWNLINK_HEARTBEAT=false \
REBIND_AFTER=2s \
./scripts/run-chrome-h3-rebinding-proxy.sh
```

이 실험은 실제 Wi-Fi/LTE handover가 아니라 NAT rebinding에 가까운 local control이다. qlog `PATH_CHALLENGE`/`PATH_RESPONSE`와 server tuple 변화가 있어도 Chrome NetLog에서 target QUIC session이 2개이면 session continuity claim으로 쓰면 안 된다.

## 5.1 `tools/run_chrome_cdp_navigation.js`

Chrome을 DevTools Protocol로 열고 지정한 real-time hold 구간 동안 page를 유지한 뒤 DOM과 body dataset을 저장한다. `--dump-dom` runner에서 JavaScript timer나 virtual time 때문에 heartbeat timing이 왜곡될 때 사용한다.

wrapper 실행:

```bash
cd repro/quic-go-min-repro
CHROME_RUNNER=cdp CHROME_HOLD_SECONDS=4 WORKLOAD=downlink DOWNLINK_HEARTBEAT=true ./scripts/run-chrome-h3-local.sh
```

생성 artifact:

| 파일 | 의미 |
| --- | --- |
| `chrome/netlog.json` | Chrome NetLog |
| `chrome/dump-dom.txt` | CDP 평가 시점의 DOM |
| `chrome/cdp-summary.json` | URL, hold time, body dataset, text/html size |

CDP runner는 Chrome 내부 관찰성을 보강하지만 migration을 판정하지 않는다. 최종 판정은 classifier의 server request log, qlog, NetLog, client path snapshot 조합을 따른다.

## 6. `tools/classify_chrome_alt_svc_artifacts.py`

Chrome natural Alt-Svc control artifact를 server protocol record, Chrome NetLog, qlog 기준으로 분류한다.

실행:

```bash
python3 tools/classify_chrome_alt_svc_artifacts.py \
  repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-local-20260624 \
  --addr 127.0.0.1:4443 \
  --expected-requests 2
```

주요 output:

| 항목 | 의미 |
| --- | --- |
| `classification` | natural Alt-Svc upgrade 관찰 여부 |
| `server_request_protos` | server가 기록한 request protocol |
| `h3_netlog_has_quic_candidate` | target origin에 대해 h3 candidate job이 있었는지 |
| `h3_netlog_has_confirmed_quic_session` | JSON NetLog에서 target QUIC session이 확정됐는지 |
| `qlog_has_h3` | server qlog에서 HTTP/3 frame evidence가 있는지 |
| `qlog_summary` | qlog connection close reason과 certificate/crypto error 여부 |

`h3_netlog_has_quic_candidate=true`만으로 HTTP/3 사용을 주장하지 않는다. server protocol record와 qlog evidence가 함께 필요하다.

주요 classification:

| classification | 의미 |
| --- | --- |
| `alt_svc_h3_upgrade_observed` | Alt-Svc 이후 실제 HTTP/3 application request가 관찰됨 |
| `alt_svc_quic_candidate_cert_rejected` | QUIC/H3 후보 연결은 열렸지만 certificate verification failure로 application request가 HTTP/3로 가지 않음 |
| `alt_svc_marked_broken_without_h3_request` | NetLog가 target QUIC alternative service를 broken으로 기록했고 application request는 HTTP/3가 아님 |
| `alt_svc_quic_candidate_without_h3_request` | QUIC/H3 후보 evidence는 있으나 application request는 HTTP/3가 아님 |
| `alt_svc_advertised_but_h3_not_observed` | Alt-Svc 광고 후에도 HTTP/3 후보/요청 evidence가 부족함 |

## 7. `tools/classify_chrome_public_h3_artifacts.py`

Chrome public WebPKI H3 discovery/application artifact를 NetLog 기준으로 분류한다.

실행:

```bash
python3 tools/classify_chrome_public_h3_artifacts.py \
  repro/quic-go-min-repro/artifacts/chrome-public-h3-google-generate204-20260624 \
  --url https://www.google.com/generate_204
```

주요 output:

| 항목 | 의미 |
| --- | --- |
| `classification` | public origin에서 H3 discovery 또는 application HTTP/3가 관찰됐는지 |
| `bootstrap_h3_observed` | bootstrap NetLog에서 target application HTTP/3 evidence가 있는지 |
| `second_h3_observed` | second NetLog에서 target application HTTP/3 evidence가 있는지 |
| `target_quic_session_count` | target host/port의 QUIC session 수 |
| `target_using_quic_job_count` | target host/port의 전체 `HTTP_STREAM_JOB using_quic=true` 수 |
| `target_dns_alpn_h3_job_count` | `dns_alpn_h3` discovery job 수 |
| `target_application_using_quic_job_count` | discovery가 아닌 application job 중 `using_quic=true` 수 |
| `target_main_non_quic_job_count` | main request job 중 non-QUIC 수 |
| `target_broken_alternative_service` | Alt-Svc가 broken으로 기록됐는지 |

classification:

| classification | 의미 |
| --- | --- |
| `public_natural_h3_observed` | public origin에서 target application HTTP/3 사용이 관찰됨 |
| `public_h3_discovery_without_application_h3` | H3 discovery 또는 QUIC session 단서는 있으나 application HTTP/3는 확인되지 않음 |
| `public_alt_svc_marked_broken` | target alternative service가 broken으로 기록됨 |
| `public_alt_svc_or_request_observed_but_h3_not_confirmed` | target request 또는 Alt-Svc evidence는 있으나 HTTP/3 사용은 확정 불가 |

이 도구는 local Alt-Svc negative control과 public WebPKI discovery control을 분리하기 위한 것이다. migration evidence는 판정하지 않는다.

## 8. `tools/scan_public_alt_svc.py`

public HTTPS endpoint가 HTTP/3 discovery 후보인지 보기 위해 `Alt-Svc: h3` 광고 여부를 반복 가능하게 확인한다.

실행:

```bash
python3 tools/scan_public_alt_svc.py \
  --url-file data/public-alt-svc-targets.txt \
  --format csv \
  --output data/public-alt-svc-survey-20260624.csv
```

지원 format:

| format | 용도 |
| --- | --- |
| `markdown` | 보고서에 붙일 표 |
| `csv` | 논문/분석용 데이터 |
| `json` | 후속 자동 분석 |

출력 항목:

| 항목 | 의미 |
| --- | --- |
| `final_status` | redirect follow 후 마지막 HTTP status line |
| `has_h3_alt_svc` | response header에 `h3` Alt-Svc가 있었는지 |
| `alt_svc_headers` | 관찰된 Alt-Svc header |
| `server_headers` | 관찰된 server header |
| `location_headers` | redirect chain |

이 도구는 Chrome이 실제 HTTP/3를 사용했는지 판정하지 않는다. target 후보를 줄인 뒤 `run-chrome-public-h3.sh`와 `classify_chrome_public_h3_artifacts.py`로 browser evidence를 별도 확인한다.

## 9. `tools/check_public_origin_readiness.py`

controlled public origin을 Chrome browser CM 실험에 쓰기 전에 DNS, WebPKI TLS, HTTP response, `Alt-Svc: h3` 광고 여부를 확인한다.

실행:

```bash
python3 tools/check_public_origin_readiness.py \
  --url https://h3.example.com/browser-slow?duration_ms=6000 \
  --require-h3-alt-svc \
  --format markdown
```

출력 항목:

| 항목 | 의미 |
| --- | --- |
| `dns_addresses` | hostname이 해석된 IP 목록 |
| `tcp_tls_ok` | Python SSL 또는 curl 기준 HTTPS 검증 성공 여부 |
| `python_tls_ok` | Python SSL trust store 기준 검증 성공 여부 |
| `curl_https_ok` | curl 기준 HTTPS 검증 성공 여부 |
| `final_status` | `curl -I -L` 기준 마지막 HTTP status |
| `has_h3_alt_svc` | response chain에서 `h3` Alt-Svc가 관찰됐는지 |
| `errors` | DNS/TLS/curl 오류 |

이 도구가 통과해도 migration이 증명되는 것은 아니다. Chrome NetLog와 server qlog를 포함한 no-change application H3 baseline을 추가로 통과해야 한다.

## 10. `tools/scan_public_origin_readiness.py`

여러 public endpoint에 대해 DNS/TLS/Alt-Svc/status readiness를 반복 측정한다.

실행:

```bash
python3 tools/scan_public_origin_readiness.py \
  --url-file data/public-alt-svc-targets.txt \
  --format csv \
  --output data/public-origin-readiness-survey-20260624.csv
```

추가 분류:

| 항목 | 의미 |
| --- | --- |
| `https_readiness_ok` | DNS/TLS/HTTPS response가 동작 |
| `browser_h3_candidate` | HTTPS OK이고 `Alt-Svc: h3`가 있음 |
| `workload_candidate` | browser H3 candidate이고 final status가 2xx |

## 11. `tools/classify_controlled_public_h3_baseline.py`

controlled public origin의 no-change application H3 baseline을 server request log, server qlog, Chrome public NetLog summary, readiness JSON으로 합쳐 판정한다.

실행:

```bash
python3 tools/classify_controlled_public_h3_baseline.py \
  repro/quic-go-min-repro/artifacts/controlled-public-h3-application-baseline-001 \
  --url 'https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow' \
  --output repro/quic-go-min-repro/artifacts/controlled-public-h3-application-baseline-001/results/controlled-public-h3-baseline-summary.json
```

주요 output:

| 항목 | 의미 |
| --- | --- |
| `server_requests.reached_expected_count` | server request log가 expected request count 이상을 기록했는지 |
| `server_qlog_has_application_h3` | server qlog에 `chosen_alpn`과 `http3:frame` evidence가 있는지 |
| `browser.application_using_quic_job_count` | Chrome NetLog에서 discovery가 아닌 application QUIC job 수 |
| `browser.dns_alpn_h3_job_count` | Chrome NetLog의 H3 discovery job 수 |
| `public_origin_readiness` | DNS/TLS/Alt-Svc/status readiness 요약 |

classification:

| classification | 의미 |
| --- | --- |
| `controlled_public_application_h3_confirmed` | server/qlog와 browser NetLog 모두 application H3를 지지 |
| `controlled_public_server_qlog_h3_confirmed_browser_netlog_inconclusive` | server/qlog는 application H3를 직접 증명하지만 browser NetLog는 확정적이지 않음 |
| `controlled_public_h3_discovery_without_server_application_h3` | browser discovery는 있으나 server/qlog application H3 evidence가 없음 |
| `controlled_public_application_h3_not_confirmed` | application H3 baseline이 확인되지 않음 |

local regression check:

- forced local H3 artifact는 `PASS_FEASIBILITY / controlled_public_server_qlog_h3_confirmed_browser_summary_missing`
- H1-only local Alt-Svc artifact는 `PASS_NEGATIVE_CONTROL / controlled_public_application_h3_not_confirmed`

## 12. `tools/check_handover_readiness.py`

Chrome/Cronet handover 실험을 실행해도 되는 로컬 상태인지 확인한다.

실행:

```bash
python3 tools/check_handover_readiness.py --format markdown
python3 tools/check_handover_readiness.py --format json --output data/handover-readiness-20260624.json
```

확인 항목:

| 항목 | 의미 |
| --- | --- |
| `chrome_found` | Chrome binary가 실행 가능한지 |
| `adb_found`, `adb_devices` | Android 실험 도구와 연결 device 여부 |
| `active_ipv4_interfaces` | active non-loopback IPv4 interface 목록 |
| `secondary_path_ready` | desktop path-change 실험에 필요한 두 번째 active path 여부 |
| `aws_identity_ok` | controlled public origin 자동 구축을 위한 AWS identity 여부 |
| `blockers` | 지금 handover를 실행하지 말아야 하는 이유 |

기본 출력은 공개 repo에 넣을 수 있도록 raw command output을 저장하지 않는다. 로컬 디버깅이 필요할 때만 `--include-command-output`을 사용한다.

## 13. `tools/check_controlled_public_experiment_readiness.py`

controlled public Chrome HTTP/3 network-change 실험을 실행해도 되는지 통합 점검한다.

실행:

```bash
python3 tools/check_controlled_public_experiment_readiness.py \
  --public-origin-url 'https://h3.example.com/browser-slow?duration_ms=15000&chunks=15&label=handover-slow' \
  --baseline-summary repro/quic-go-min-repro/artifacts/controlled-public-h3-application-baseline-001/results/controlled-public-h3-baseline-summary.json \
  --network-change-cmd '...' \
  --format markdown
```

주요 output:

| 항목 | 의미 |
| --- | --- |
| `controlled_public_origin_ready` | public URL의 DNS/TLS/HTTPS가 준비됐는지 |
| `application_h3_baseline_ready` | baseline summary가 `status=PASS`인지 |
| `secondary_path_ready` | active non-loopback IPv4 path가 2개 이상인지 |
| `network_change_command_present` | `NETWORK_CHANGE_CMD`가 제공됐는지 |
| `can_run_network_change` | 실제 network-change 실험 실행 가능 여부 |
| `blockers` | 실행 전 해결해야 할 항목 |

현재 2026-06-24 점검에서는 Chrome과 harness는 준비됐지만 controlled public URL, baseline PASS summary, secondary active path, `NETWORK_CHANGE_CMD`가 없어 `can_run_network_change=false`다.

## 14. `tools/check_browser_cm_observability.py`

Chrome/Safari browser-level CM 실험을 실행하기 전에 browser, driver, packet-capture 관찰성이 충분한지 확인한다.

실행:

```bash
python3 tools/check_browser_cm_observability.py --format markdown
python3 tools/check_browser_cm_observability.py --format json --output data/browser-cm-observability-20260624.json
```

확인 항목:

| 항목 | 의미 |
| --- | --- |
| `chrome_netlog_ready` | Chrome NetLog 기반 artifact 수집 가능 여부 |
| `safari_webdriver_ready` | Safari + safaridriver 실행 가능 여부 |
| `packet_capture_tooling_ready` | `tcpdump`, route, ifconfig 기반 packet/route 관찰 가능 여부 |
| `ios_remote_capture_candidate` | `rvictl` 기반 iOS remote capture 후보 여부 |
| `blockers` | browser별 관찰성 제한 |

기본 출력은 raw command stdout/stderr를 비운다. 공개 repo에 넣지 않는 로컬 디버깅 때만 `--include-command-output`을 사용한다.

## 15. `tools/run_safari_webdriver_navigation.py`

Safari를 WebDriver HTTP protocol로 controlled public URL에 navigate하고 결과 JSON을 남긴다.

실행:

```bash
python3 tools/run_safari_webdriver_navigation.py \
  --url 'https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=safari-public-slow' \
  --output /tmp/safari-navigation.json
```

이 도구는 Safari GUI를 실제로 열 수 있으므로 controlled public origin과 server artifact가 준비된 뒤 실행한다.

wrapper:

```bash
cd repro/quic-go-min-repro
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=safari-public-slow' \
./scripts/run-safari-controlled-public-baseline.sh
```

Safari baseline은 Chrome NetLog가 없으므로 `classify_controlled_public_h3_baseline.py --allow-missing-browser-summary` 경로를 사용한다. 실제 network-change 실험에서는 `scripts/run-safari-controlled-public-network-change.sh`를 사용하고, classifier에는 `--browser-kind safari --allow-missing-browser-netlog`를 전달한다.

Android Chrome은 `tools/run_android_chrome_navigation.py`와 `scripts/run-android-chrome-controlled-public-network-change.sh`를 사용한다. 이 경로도 browser-internal QUIC log가 없으므로 classifier에는 `--browser-kind android-chrome --allow-missing-browser-netlog`를 전달한다.

## 16. `tools/classify_controlled_public_h3_network_change.py`

controlled public origin에서 browser workload 중 network-change trigger를 넣은 결과를 분류한다. 기본은 Chrome NetLog를 포함한 Chrome mode이고, Safari/Android Chrome은 `--allow-missing-browser-netlog`로 server/qlog/client-path 또는 raw network snapshot 중심 판정을 수행한다.

실행:

```bash
python3 tools/classify_controlled_public_h3_network_change.py \
  repro/quic-go-min-repro/artifacts/controlled-public-h3-network-change-001 \
  --server-artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-h3-network-change-001 \
  --url 'https://h3.example.com/browser-slow?duration_ms=15000&chunks=15&label=handover-slow' \
  --output repro/quic-go-min-repro/artifacts/controlled-public-h3-network-change-001/results/controlled-public-h3-network-change-summary.json
```

Safari mode:

```bash
python3 tools/classify_controlled_public_h3_network_change.py \
  repro/quic-go-min-repro/artifacts/safari-controlled-public-h3-network-change-001 \
  --server-artifact-dir repro/quic-go-min-repro/artifacts/safari-controlled-public-h3-network-change-001 \
  --url 'https://h3.example.com/browser-slow?duration_ms=15000&chunks=15&label=safari-handover-slow' \
  --browser-kind safari \
  --allow-missing-browser-netlog \
  --output repro/quic-go-min-repro/artifacts/safari-controlled-public-h3-network-change-001/results/safari-controlled-public-h3-network-change-summary.json
```

Android Chrome mode:

```bash
python3 tools/classify_controlled_public_h3_network_change.py \
  repro/quic-go-min-repro/artifacts/android-chrome-controlled-public-h3-network-change-001 \
  --server-artifact-dir repro/quic-go-min-repro/artifacts/android-chrome-controlled-public-h3-network-change-001 \
  --url 'https://h3.example.com/browser-slow?duration_ms=15000&chunks=15&label=android-handover-slow' \
  --browser-kind android-chrome \
  --allow-missing-browser-netlog \
  --output repro/quic-go-min-repro/artifacts/android-chrome-controlled-public-h3-network-change-001/results/android-chrome-controlled-public-h3-network-change-summary.json
```

주요 output:

| 항목 | 의미 |
| --- | --- |
| `server_requests.remote_addr_count` | server가 본 client tuple 종류 수 |
| `server_qlog_has_path_validation` | server qlog의 PATH_CHALLENGE/PATH_RESPONSE evidence |
| `network_change.exit` | network-change command exit code |
| `client_path_change.classification` | client route/interface 변화 판정 |
| `netlog.target_quic_session_count` | Chrome NetLog target QUIC session 수 |
| `netlog_has_application_h3` | Chrome NetLog application H3 evidence |

classification:

| classification | 의미 |
| --- | --- |
| `possible_connection_migration` | client active path change, tuple change, qlog path validation, 단일 Chrome QUIC session evidence가 함께 관찰됨 |
| `possible_connection_migration_server_qlog_only` | Safari/Android처럼 browser-internal QUIC log가 없는 상태에서 client active path change, server tuple change, qlog path validation이 관찰됨 |
| `reconnect_or_multiple_sessions` | tuple change가 있으나 여러 QUIC session evidence |
| `tuple_changed_without_path_validation` | tuple change가 있으나 path validation evidence 없음 |
| `no_path_change_after_trigger` | network-change command 후에도 tuple 변화 없음 |
| `no_client_active_path_change_observed` | client path snapshot에서 active path 변화가 관찰되지 않음 |
| `path_snapshot_missing` | client path snapshot이 없어 active handover evidence 부족 |
| `controlled_public_network_change_workload_failed` | workload expected request count 미달 |

## 17. `tools/capture_network_path_snapshot.py`, `tools/compare_network_path_snapshots.py`, `tools/compare_android_path_snapshots.py`

browser network-change 실험에서 client 측 route/interface 변화가 실제로 있었는지 기록한다.

실행:

```bash
python3 tools/capture_network_path_snapshot.py \
  --url 'https://h3.example.com/browser-slow?duration_ms=15000' \
  --output /tmp/path-before.json

python3 tools/capture_network_path_snapshot.py \
  --url 'https://h3.example.com/browser-slow?duration_ms=15000' \
  --output /tmp/path-after.json

python3 tools/compare_network_path_snapshots.py \
  /tmp/path-before.json \
  /tmp/path-after.json
```

비교 classification:

| classification | 의미 |
| --- | --- |
| `client_active_path_changed` | default/target route, gateway, public IP 중 active path 변화 관찰 |
| `interface_set_changed_without_route_change` | active interface 목록만 바뀌고 route 변화는 없음 |
| `no_client_path_change_observed` | command 전후 client path 변화가 관찰되지 않음 |
| `path_snapshot_missing` | before/after snapshot 부족 |

이 도구는 server tuple/qlog evidence를 대체하지 않는다. inactive interface toggle 같은 no-op control을 분리하기 위한 보조 evidence다.

Android Chrome 실험은 macOS route snapshot 대신 ADB로 수집한 `ip route`, `ip addr show`, `dumpsys connectivity` 결과를 비교한다.

```bash
python3 tools/compare_android_path_snapshots.py \
  --before-route artifacts/RUN_ID/android/ip-route-command-before.txt \
  --after-route artifacts/RUN_ID/android/ip-route-command-after.txt \
  --before-addr artifacts/RUN_ID/android/ip-addr-command-before.txt \
  --after-addr artifacts/RUN_ID/android/ip-addr-command-after.txt \
  --before-connectivity artifacts/RUN_ID/android/connectivity-command-before.txt \
  --after-connectivity artifacts/RUN_ID/android/connectivity-command-after.txt \
  --output artifacts/RUN_ID/results/client-path-change-summary.json
```

`run-android-chrome-controlled-public-network-change.sh`는 이 summary를 자동 생성한다. 이 파일이 없거나 `client_active_path_changed`가 아니면 server tuple/qlog evidence만으로 Android P1 feasibility를 세지 않는다.

## 18. `harness/scripts/controlled-public-preflight.sh`

controlled public Chrome H3 network-change 실험의 local-only 설정을 읽어서 통합 readiness를 실행하는 wrapper다.

실행:

```bash
cp harness/config/controlled-public-origin.env.example harness/config/controlled-public-origin.env
bash harness/scripts/controlled-public-preflight.sh
```

동작:

| 항목 | 의미 |
| --- | --- |
| config load | `harness/config/controlled-public-origin.env`를 있으면 source |
| readiness JSON | ignored artifact directory에 `controlled-public-experiment-readiness.json` 생성 |
| readiness Markdown | 같은 directory에 사람이 읽을 summary 생성 |
| next commands | server, baseline, network-change command template 출력 |
| safety | 실제 `NETWORK_CHANGE_CMD`는 실행하지 않음 |

이 wrapper가 `controlled_public_preflight=ready`를 출력해야 `run-controlled-public-h3-network-change.sh`를 본 실험으로 실행할 수 있다. `blocked`이면 출력된 blockers를 실험 전제 미충족으로 기록한다.

## 19. 실험 실행 코드

핵심 코드는 [repro/quic-go-min-repro](../repro/quic-go-min-repro)에 있다.

| 파일 | 역할 |
| --- | --- |
| `cmd/client/main.go` | QUIC transport stream migration client |
| `cmd/server/main.go` | QUIC transport stream migration server |
| `cmd/h3client/main.go` | HTTP/3 workload migration client |
| `cmd/h3server/main.go` | HTTP/3 upload/download server, Chrome sequence/poll/slow baseline endpoint, optional TCP Alt-Svc bootstrap listener |
| `internal/common/aws_nlb_cid.go` | AWS NLB QUIC-LB plaintext CID generator |
| `internal/common/payload.go` | deterministic payload/checksum |
| `internal/common/logging.go` | JSONL/result JSON writer |
| `internal/common/tls.go` | self-signed TLS config, browser test cert/key injection |

로컬 wrapper:

| 파일 | 역할 |
| --- | --- |
| `scripts/run-local-happy-path.sh` | transport-level local migration |
| `scripts/run-local-h3-workload.sh` | HTTP/3 POST before, migrate, GET after |
| `scripts/run-local-h3-midflight.sh` | HTTP/3 upload/download body in-flight migration |
| `scripts/run-chrome-h3-local.sh` | Chrome browser local HTTP/3 single/sequence/poll/slow baseline and optional network-change hook |
| `scripts/run-chrome-h3-alt-svc.sh` | Chrome natural Alt-Svc HTTP/3 control |
| `scripts/run-chrome-public-h3.sh` | Chrome public WebPKI H3 discovery/application baseline |
| `scripts/run-controlled-public-h3-server.sh` | WebPKI cert/key를 사용하는 controlled public H3 origin server wrapper |
| `scripts/run-controlled-public-h3-browser-baseline.sh` | controlled public origin readiness + Chrome application H3 baseline wrapper |
| `scripts/run-controlled-public-h3-network-change.sh` | baseline PASS 이후 Chrome controlled public network-change 실험 wrapper |
| `scripts/run-safari-controlled-public-baseline.sh` | Safari WebDriver navigation + server/qlog 기반 controlled public H3 baseline wrapper |
| `scripts/run-safari-controlled-public-network-change.sh` | Safari WebDriver navigation + active network-change + server/qlog 기반 classifier wrapper |
| `scripts/run-android-chrome-controlled-public-network-change.sh` | ADB Android Chrome navigation + active network-change + server/qlog 기반 classifier wrapper |
| `scripts/run-ec2-client.sh` | AWS/NLB transport client runner |
| `scripts/run-h3-client.sh` | AWS/NLB HTTP/3 client runner |
| `scripts/run-h3-server.sh` | AWS/NLB HTTP/3 target server runner |
| `scripts/package-for-ec2.sh` | EC2 target 배포용 tarball 생성 |

AWS wrapper:

| 파일 | 역할 |
| --- | --- |
| `harness/scripts/aws-preflight.sh` | AWS CLI, region, VPC/subnet 사전 확인 |
| `harness/scripts/package-quic-go-ec2.sh` | public repo 구조 기준 EC2 package 생성 |
| `harness/scripts/run-aws-nlb-quic-data-plane.sh` | EC2 A/B, NLB, target group, client, cleanup end-to-end |
| `harness/scripts/run-local-quic-go.sh` | harness 결과 디렉터리에 local transport 실행 |
| `harness/scripts/validate-quic-go-artifacts.sh` | local transport artifact 검증 |
| `harness/scripts/run-local-s2n-nlb-cid-proof.sh` | NLB CID provider local proof wrapper |

## 20. 최소 검증 세트

논문용 결과를 갱신하기 전 최소한 다음은 통과시킨다.

```bash
python3 tools/verify_research_bundle.py --output docs/results/research-verification-report-20260624.md
python3 tools/validate_publication_bundle.py
python3 tools/summarize_experiment_results.py --format markdown
python3 tools/scan_implementation_evidence.py repro/quic-go-min-repro --format markdown
python3 tools/scan_public_alt_svc.py --url-file data/public-alt-svc-targets.txt --format markdown
python3 tools/scan_public_origin_readiness.py --url-file data/public-alt-svc-targets.txt --format markdown
python3 tools/check_public_origin_readiness.py --url https://www.google.com/generate_204 --require-h3-alt-svc --format markdown
python3 tools/check_handover_readiness.py --format markdown
python3 tools/check_browser_cm_observability.py --format markdown
python3 -m py_compile tools/run_safari_webdriver_navigation.py
# readiness가 false이면 exit code 1을 반환한다. 출력의 blockers를 확인한다.
python3 tools/check_controlled_public_experiment_readiness.py --format markdown || true
bash harness/scripts/controlled-public-preflight.sh || true
python3 tools/check_final_browser_handover_readiness.py --output docs/results/final-browser-handover-readiness-20260624.md || true
python3 tools/capture_network_path_snapshot.py --url https://www.google.com/generate_204 --output /tmp/quic-cm-path-before.json
python3 tools/compare_network_path_snapshots.py /tmp/quic-cm-path-before.json /tmp/quic-cm-path-before.json
python3 -m py_compile tools/classify_controlled_public_h3_network_change.py tools/run_android_chrome_navigation.py
python3 tools/audit_final_browser_handover_trials.py --output docs/results/final-browser-handover-trial-audit-20260624.md
python3 tools/test_final_browser_handover_trial_audit.py
bash -n repro/quic-go-min-repro/scripts/run-safari-controlled-public-network-change.sh
bash -n repro/quic-go-min-repro/scripts/run-android-chrome-controlled-public-network-change.sh

cd repro/quic-go-min-repro
go test ./...
RUN_ID=local-h3-workload-check ./scripts/run-local-h3-workload.sh
RUN_ID=local-h3-midflight-check ./scripts/run-local-h3-midflight.sh
RUN_ID=chrome-h3-local-spki-pass ./scripts/run-chrome-h3-local.sh
WORKLOAD=sequence RUN_ID=chrome-h3-sequence-vtime-pass ./scripts/run-chrome-h3-local.sh
cd ../..
python3 tools/classify_controlled_public_h3_baseline.py repro/quic-go-min-repro/artifacts/chrome-h3-sequence-vtime-pass --allow-missing-browser-summary
cd repro/quic-go-min-repro
WORKLOAD=poll POLL_COUNT=5 POLL_INTERVAL_MS=300 RUN_ID=chrome-h3-poll-nochange-classifier-pass ./scripts/run-chrome-h3-local.sh
WORKLOAD=slow SLOW_DURATION_MS=8000 SLOW_CHUNKS=8 RUN_ID=chrome-h3-slow-inactive-if-toggle ./scripts/run-chrome-h3-local.sh
LISTEN_ADDR=0.0.0.0:4443 ORIGIN_ADDR="$(ipconfig getifaddr en0):4443" WORKLOAD=slow RUN_ID=chrome-h3-slow-wifi-ip-nochange ./scripts/run-chrome-h3-local.sh
RUN_ID=chrome-h3-alt-svc-local-20260624 ./scripts/run-chrome-h3-alt-svc.sh
RUN_ID=chrome-public-h3-google-generate204-20260624 TARGET_URL=https://www.google.com/generate_204 ./scripts/run-chrome-public-h3.sh
```

AWS 결과를 갱신할 때는 [재현 가이드](reproducibility-guide-ko.md)의 cleanup 확인까지 포함한다.

## 21. `tools/build_paper_tables.py`

논문 본문에 붙일 수 있는 Markdown 표를 `data/experiment-results.csv`와 `data/evidence-chain-rubric.csv`에서 생성한다.

실행:

```bash
python3 tools/build_paper_tables.py --output docs/results/paper-tables-20260624.md
```

생성 표:

| 표 | 내용 |
| --- | --- |
| Table 1 | 전체 실험 corpus 요약 |
| Table 2 | browser CM claim을 위한 evidence chain rubric |
| Table 3 | positive/feasibility control 대표 결과 |
| Table 4 | negative control과 failure-layer evidence |
| Table 5 | browser/public web evidence |
| Table 6 | remaining evidence gaps |

이 파일은 raw qlog/NetLog artifact를 포함하지 않고 공개 CSV의 요약만 사용한다.

## 22. `tools/audit_research_bundle.py`

현재 research bundle이 논문 목표를 어느 정도 만족하는지 기계적으로 점검한다.

실행:

```bash
python3 tools/audit_research_bundle.py --output docs/results/research-bundle-audit-20260624.md
python3 tools/audit_research_bundle.py --require-complete
```

검사 항목:

| 항목 | 의미 |
| --- | --- |
| publication bundle | `validate_publication_bundle.py` 통과 여부 |
| required files | 논문/재현/하네스 핵심 파일 존재 여부 |
| experiment CSV | trial count, status count, trial id uniqueness |
| matrix CSV | item count, id uniqueness |
| paper tables | `build_paper_tables.py` 결과와 checked-in table 일치 여부 |
| final browser handover trials | `audit_final_browser_handover_trials.py` 기준 본 실험 필수 trial 충족 여부 |
| handover readiness | secondary path, Android, AWS, disk 상태 |
| observability readiness | Chrome NetLog, Safari WebDriver, packet capture tooling |

기본 실행은 blocker가 있어도 exit 0이다. CI나 최종 제출 전처럼 목표 완료가 반드시 필요할 때만 `--require-complete`를 사용한다.

## 23. `tools/report_artifact_storage.py`

로컬에 남아 있는 ignored experiment artifact의 용량을 요약한다. qlog, NetLog, pcap 같은 raw artifact는 공개 저장소에 올리지 않지만, 실험을 더 진행할 수 있는 디스크 상태와 cleanup 후보는 논문 재현성 로그에 남겨야 한다.

실행:

```bash
python3 tools/report_artifact_storage.py --output docs/results/artifact-storage-report-20260624.md
```

출력 항목:

| 항목 | 의미 |
| --- | --- |
| disk free | 현재 워크스페이스가 있는 볼륨의 여유 공간 |
| artifact roots | ignored artifact root별 용량, 파일 수, 디렉터리 수 |
| largest artifact directories | cleanup 우선순위를 판단할 수 있는 상위 artifact 디렉터리 |

이 도구는 파일을 삭제하지 않는다. 삭제는 결과 문서화 여부를 확인한 뒤 수동으로 수행해야 한다.

## 24. `tools/audit_final_browser_handover_trials.py`

최종 browser/mobile handover 본 실험이 논문 프로토콜을 만족할 만큼 채워졌는지 `data/final-browser-handover-required-trials.csv`와 `data/experiment-results.csv`를 대조한다.

실행:

```bash
python3 tools/audit_final_browser_handover_trials.py \
  --output docs/results/final-browser-handover-trial-audit-20260624.md

python3 tools/audit_final_browser_handover_trials.py --require-complete
```

현재 요구사항:

| requirement | 기준 |
| --- | --- |
| Chrome controlled public H3 baseline | 최소 1회 |
| Chrome downlink no-heartbeat active CM | 최소 3회 |
| Chrome downlink heartbeat active CM | 최소 3회 |
| Chrome downlink no-heartbeat no-change baseline | 최소 1회 |
| Chrome downlink heartbeat no-change baseline | 최소 1회 |
| Safari 또는 Android Chrome feasibility | 최소 1회 |

이 audit은 local Chrome forced-QUIC baseline이나 inactive interface toggle을 본 실험으로 세지 않는다. `controlled-public`, `network-change`, classification, negative-control exclusion 조건을 모두 만족해야 한다.

회귀 검증:

```bash
python3 tools/test_final_browser_handover_trial_audit.py
```

이 테스트는 synthetic complete fixture가 모든 requirement를 만족하는지, 그리고 `reconnect_or_multiple_sessions` negative control이 active CM requirement에 잘못 집계되지 않는지 확인한다.

## 25. `tools/verify_research_bundle.py`

논문 제출/공유 전에 안전하게 돌릴 수 있는 non-destructive 통합 검증 runner다. raw browser/network 실험을 새로 생성하지 않고, 공개 bundle, CSV, paper table, final trial audit, expected-incomplete gate, readiness scanner, wrapper 문법을 한 번에 확인한다.

실행:

```bash
python3 tools/verify_research_bundle.py \
  --output docs/results/research-verification-report-20260624.md
```

작업 트리를 더럽히지 않고 현재 상태만 확인하려면 output을 임시 경로로 둔다.

```bash
python3 tools/verify_research_bundle.py \
  --scratch-dir /tmp/quic-cm-verify \
  --output /tmp/quic-cm-research-verification.md
```

주요 특징:

| 항목 | 의미 |
| --- | --- |
| destructive action 없음 | network interface나 Android/Wi-Fi 상태를 바꾸지 않음 |
| expected-incomplete gate | `--require-complete`가 현재 exit 1을 내는 것을 정상으로 기록 |
| generated report | `docs/results/research-verification-report-20260624.md`에 모든 check exit code 기록 |
| final claim 보호 | 현재 미완료인 browser/mobile handover 본 실험을 완료로 오인하지 않음 |

## 26. `tools/check_final_browser_handover_readiness.py`

최종 browser/mobile handover 본 실험을 실행할 준비가 되었는지 config, baseline summary, local path readiness, Android ADB, Safari WebDriver, disk, final trial audit을 통합해 점검한다.

실행:

```bash
python3 tools/check_final_browser_handover_readiness.py \
  --output docs/results/final-browser-handover-readiness-20260624.md
```

기본 실행은 public origin에 네트워크 요청을 보내지 않는다. 실제 controlled public URL까지 검증하려면 명시적으로 `--check-public-origin`을 붙인다.

```bash
python3 tools/check_final_browser_handover_readiness.py \
  --check-public-origin \
  --output /tmp/final-browser-handover-readiness.md
```

현재 환경처럼 준비가 덜 된 상태에서는 exit 1을 반환한다. 이 실패는 본 실험 blocker를 드러내는 정상적인 readiness 결과다.

## 27. `tools/plan_final_browser_handover_runs.py`

최종 browser/mobile handover 본 실험을 완료하기 위해 어떤 trial을 어떤 순서와 명령으로 실행해야 하는지 생성한다. 이 도구는 실험을 실행하지 않으며, 기본 출력은 실제 도메인이나 network-change 명령이 새지 않도록 public template 값만 사용한다.

실행:

```bash
python3 tools/plan_final_browser_handover_runs.py \
  --output docs/results/final-browser-handover-run-plan-20260624.md
```

로컬 private config 값을 반영한 실행 계획은 추적 문서가 아니라 임시 경로에 생성한다.

```bash
python3 tools/plan_final_browser_handover_runs.py \
  --use-local-config \
  --output /tmp/final-browser-handover-run-plan.md
```

기본 계획은 다음 요구사항을 채운다.

| requirement | planned |
| --- | ---: |
| Chrome controlled public application H3 baseline | 1 |
| Chrome downlink no-heartbeat no-change baseline | 1 |
| Chrome downlink heartbeat no-change baseline | 1 |
| Chrome downlink no-heartbeat active CM | 3 |
| Chrome downlink heartbeat active CM | 3 |
| Safari P1 feasibility | 1 |

각 trial마다 origin/server terminal 명령과 browser/client terminal 명령을 분리해서 출력한다. 결과 row를 `data/experiment-results.csv`에 등록한 뒤 `audit_final_browser_handover_trials.py --require-complete`가 exit 0이 되어야 논문 Results에서 본 실험 완료를 주장할 수 있다.

## 28. `tools/draft_final_handover_result_row.py`

최종 handover artifact의 classifier summary를 읽어 `data/experiment-results.csv`에 붙일 row 초안을 생성한다. 이 도구는 결과를 자동으로 확정하지 않고, 등록 실수를 줄이는 보조 도구다.

실행:

```bash
python3 tools/draft_final_handover_result_row.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --format markdown \
  --output /tmp/final-handover-row.md
```

주요 분기:

| 입력 classification | CSV status/failure layer |
| --- | --- |
| `possible_connection_migration` + Chrome | `PASS / none` |
| `reconnect_or_multiple_sessions` | `PASS_NEGATIVE_CONTROL / browser-reconnect-or-multiple-sessions` |
| `possible_connection_migration_server_qlog_only` + Safari/Android | `PASS_FEASIBILITY / server-qlog-only` |
| no-change baseline trial_id | `PASS` row에 `no_path_change_baseline` note 추가 |

회귀 테스트:

```bash
python3 tools/test_draft_final_handover_result_row.py
```

테스트는 synthetic summary에서 생성한 row가 `audit_final_browser_handover_trials.py`의 matcher에 맞게 세어지는지 확인한다.

## 29. `tools/plan_artifact_cleanup.py`

heavy Chrome NetLog/qlog/pcap 실험 전 목표 디스크 여유 공간을 만족하려면 ignored artifact를 얼마나 정리해야 하는지 dry-run으로 계산한다. 이 도구는 삭제를 실행하지 않는다.

실행:

```bash
python3 tools/plan_artifact_cleanup.py \
  --target-free-gib 5 \
  --output docs/results/artifact-cleanup-dry-run-20260624.md
```

출력 항목:

| 항목 | 의미 |
| --- | --- |
| current free | 현재 볼륨 여유 공간 |
| selected candidates | 목표까지 필요한 artifact cleanup 후보 수 |
| projected free | 후보를 삭제한다고 가정했을 때 예상 여유 공간 |
| remaining external cleanup gap | repo artifact 정리만으로 목표를 못 채울 때 추가로 필요한 외부 정리 용량 |

2026-06-24 현재는 artifact root 전체를 정리해도 5 GiB 목표에 약 1.7 GiB가 부족하므로, 최종 browser handover capture 전에는 저장소 외부 파일도 정리해야 한다.

## 30. `tools/validate_final_handover_trial_artifact.py`

단일 최종 browser/mobile handover artifact가 `data/experiment-results.csv`에 등록 가능한지, 그리고 최종 protocol requirement에 실제로 카운트되는지를 검증한다. row 생성은 `draft_final_handover_result_row.py`가 담당하고, 이 도구는 그 row가 `audit_final_browser_handover_trials.py`의 matcher와 맞는지 확인한다.

실행:

```bash
python3 tools/validate_final_handover_trial_artifact.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --output /tmp/final-handover-artifact-validation.md
```

최종 protocol에 카운트되는 결과만 허용:

```bash
python3 tools/validate_final_handover_trial_artifact.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --require-final-countable
```

주요 출력:

| 항목 | 의미 |
| --- | --- |
| `appendable_to_experiment_results` | CSV row로 기록 가능한지 |
| `counts_toward_final_protocol` | final required trial로 카운트되는지 |
| `claim_strength` | `counts_toward_final_protocol`, `p1_feasibility_counts_toward_protocol`, `negative_control_record_only` 등 |
| `warnings` | overclaim 방지를 위한 경고 |

회귀 테스트:

```bash
python3 tools/test_validate_final_handover_trial_artifact.py
```

## 31. `tools/append_final_handover_result_row.py`

검증된 final handover artifact row를 `data/experiment-results.csv`에 추가한다. 기본은 dry-run이며, 실제 CSV를 수정하려면 `--apply`를 명시해야 한다. duplicate `trial_id`는 append하지 않는다. `--require-artifact-bundle`을 붙이면 classifier summary뿐 아니라 qlog, NetLog, client path summary 등 expected raw artifact bundle이 모두 있을 때만 append한다.

dry-run:

```bash
python3 tools/append_final_handover_result_row.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --require-final-countable \
  --require-artifact-bundle \
  --output /tmp/final-handover-append-dry-run.md
```

실제 append:

```bash
python3 tools/append_final_handover_result_row.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --require-final-countable \
  --require-artifact-bundle \
  --apply
```

보호 장치:

| 항목 | 동작 |
| --- | --- |
| 기본 dry-run | `data/experiment-results.csv`를 수정하지 않음 |
| duplicate trial id | append 차단 |
| `--require-final-countable` | final requirement에 매칭되지 않는 negative/control row append 차단 |
| `--require-artifact-bundle` | summary-only 결과 append 차단 |
| regression | 임시 CSV에서만 append 동작을 테스트 |

회귀 테스트:

```bash
python3 tools/test_append_final_handover_result_row.py
```

## 32. `tools/select_next_final_handover_trial.py`

현재 `data/experiment-results.csv`와 final required-trials CSV를 기준으로 다음에 실행해야 할 final browser handover trial을 선택한다. 전체 run plan의 실행 큐 순서를 따르므로 baseline 이후 no-change baseline을 먼저 실행하고, 그 다음 active 반복 trial로 넘어간다.

실행:

```bash
python3 tools/select_next_final_handover_trial.py \
  --output docs/results/final-handover-next-trial-20260624.md
```

출력 항목:

| 항목 | 의미 |
| --- | --- |
| `next_trial` | 다음 실행 대상 trial_id, requirement, phase, expected requests |
| server/origin terminal | public origin host에서 실행할 server wrapper 명령 |
| browser/client terminal | browser/navigation side에서 실행할 wrapper 명령 |
| post-trial registration commands | validation, dry-run append, apply, audit 명령 |

로컬 private config 값을 반영한 다음 trial은 추적 문서가 아니라 임시 경로에 생성한다.

```bash
python3 tools/select_next_final_handover_trial.py \
  --use-local-config \
  --output /tmp/final-handover-next-trial.md
```

회귀 테스트:

```bash
python3 tools/test_select_next_final_handover_trial.py
```

## 33. `tools/check_next_final_handover_trial_readiness.py`

`select_next_final_handover_trial.py`가 고른 다음 trial 하나에 필요한 readiness만 점검한다. 전체 final protocol readiness와 달리, baseline trial에서는 `NETWORK_CHANGE_CMD`, secondary path, baseline summary를 요구하지 않는다. active network-change trial로 넘어가면 그때 해당 gate들이 required가 된다.

실행:

```bash
python3 tools/check_next_final_handover_trial_readiness.py \
  --output docs/results/final-handover-next-trial-readiness-20260624.md
```

public origin에 실제 네트워크 요청까지 보내려면 명시적으로 붙인다.

```bash
python3 tools/check_next_final_handover_trial_readiness.py \
  --check-public-origin \
  --output /tmp/final-handover-next-trial-readiness.md
```

public origin host에서 TLS certificate/key 파일 존재까지 확인하려면 다음 옵션을 함께 쓴다. 이 옵션은 local Mac에서 remote origin path를 검사하면 false blocker가 될 수 있으므로 기본으로 켜지지 않는다.

```bash
python3 tools/check_next_final_handover_trial_readiness.py \
  --check-local-files \
  --output /tmp/final-handover-next-trial-readiness-origin-host.md
```

현재 다음 trial이 baseline이면 required gate는 대략 다음과 같다.

| gate | baseline에서 required |
| --- | --- |
| config present | yes |
| public origin host/url | yes |
| TLS cert/key config value | yes |
| disk ready | yes |
| Chrome ready | yes |
| baseline summary | no |
| network-change command | no |
| secondary path | no |

회귀 테스트:

```bash
python3 tools/test_check_next_final_handover_trial_readiness.py
```

## 34. `tools/check_controlled_public_config.py`

`harness/config/controlled-public-origin.env`가 controlled public baseline, active network-change, Android network-change 단계별로 준비됐는지 검사한다. public report에는 실제 도메인, certificate path, private key path, network-change command 값을 출력하지 않고 key별 상태만 기록한다.

실행:

```bash
python3 tools/check_controlled_public_config.py \
  --output docs/results/controlled-public-config-check-20260624.md
```

baseline config만 강제:

```bash
python3 tools/check_controlled_public_config.py --require-baseline-ready
```

active network-change config까지 강제:

```bash
python3 tools/check_controlled_public_config.py --require-active-ready
```

검사 항목:

| 단계 | 주요 key |
| --- | --- |
| baseline | `PUBLIC_ORIGIN_HOST`, `PUBLIC_ORIGIN_URL`, `TLS_CERT_FILE`, `TLS_KEY_FILE`, `ALT_SVC`, `CHROME_BIN` |
| active network-change | `PUBLIC_ORIGIN_NETWORK_CHANGE_URL`, `CONTROLLED_PUBLIC_BASELINE_SUMMARY`, `NETWORK_CHANGE_CMD` |
| Android | `ANDROID_NETWORK_CHANGE_CMD` |

회귀 테스트:

```bash
python3 tools/test_check_controlled_public_config.py
```

## 35. `tools/build_final_handover_operator_checklist.py`

최종 browser/mobile handover 본 실험으로 들어가기 직전, 현재 repo와 로컬 환경이 무엇 때문에 막혀 있는지 operator action list로 합친다. 내부적으로 controlled public config checker, next-trial readiness checker, artifact cleanup dry-run planner, final trial audit를 호출한다.

실행:

```bash
python3 tools/build_final_handover_operator_checklist.py \
  --output docs/results/final-handover-operator-checklist-20260624.md
```

출력 항목:

| 항목 | 의미 |
| --- | --- |
| next trial | 현재 CSV 기준 다음 실행 대상 |
| next trial ready | 그 trial을 지금 실행할 수 있는지 |
| config readiness | baseline, active network-change, Android 단계별 config 준비 여부 |
| storage readiness | 목표 여유 공간과 cleanup dry-run 후 남는 gap |
| actions | config, storage, next trial, active path, Android, final protocol 순서의 실행 항목 |

이 도구는 실험을 실행하지 않으며 exit 0을 반환한다. 목적은 실패해야 정상인 readiness gate를 사람이 실행 가능한 순서로 정렬하는 것이다.

회귀 테스트:

```bash
python3 tools/test_build_final_handover_operator_checklist.py
```

## 36. `tools/build_final_handover_trial_packet.py`

현재 CSV 기준 다음 final handover trial 하나를 실행하기 위한 packet을 만든다. `select_next_final_handover_trial.py`의 trial command, `check_next_final_handover_trial_readiness.py`의 gate, expected artifact 목록, post-trial validation/append/audit 명령을 한 문서에 모은다.

실행:

```bash
python3 tools/build_final_handover_trial_packet.py \
  --output docs/results/final-handover-trial-packet-20260624.md
```

local private config 값을 반영하려면 추적 문서가 아니라 임시 경로에 쓴다.

```bash
python3 tools/build_final_handover_trial_packet.py \
  --use-local-config \
  --check-public-origin \
  --output /tmp/final-handover-trial-packet.md
```

출력 항목:

| 항목 | 의미 |
| --- | --- |
| state | `ready_to_run`, `blocked_by_readiness`, `protocol_complete_or_no_next_trial` |
| missing required gates | 현재 trial 실행을 막는 gate |
| server/client terminal | 두 터미널에서 실행할 명령 |
| expected artifacts | 등록 전 확인해야 할 raw/summary artifact |
| post-trial registration | validation, dry-run append, apply, audit, verification 명령 |

이 도구는 실험을 실행하지 않는다. readiness가 막혀 있어도 exit 0으로 packet을 생성해, 왜 실행하면 안 되는지와 준비 후 어떤 순서로 실행할지를 함께 남긴다.

회귀 테스트:

```bash
python3 tools/test_build_final_handover_trial_packet.py
```

## 37. `tools/check_final_handover_trial_artifact_bundle.py`

trial 실행 후 expected raw artifact bundle이 모두 있는지 확인한다. `build_final_handover_trial_packet.py`와 같은 expected artifact 규칙을 사용하며, summary만 존재하는 결과가 CSV에 들어가는 일을 막기 위한 post-trial gate다.

실행:

```bash
python3 tools/check_final_handover_trial_artifact_bundle.py \
  --output docs/results/final-handover-trial-artifact-bundle-check-20260624.md
```

특정 trial을 검사:

```bash
python3 tools/check_final_handover_trial_artifact_bundle.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --require-final-countable \
  --output /tmp/final-handover-artifact-bundle-check.md
```

완료 gate로 사용:

```bash
python3 tools/check_final_handover_trial_artifact_bundle.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --require-final-countable \
  --require-complete
```

CSV 등록 단계에서 같은 gate를 강제하려면 `append_final_handover_result_row.py`에 `--require-artifact-bundle`을 붙인다.

확인 항목:

| 항목 | 의미 |
| --- | --- |
| artifact bundle complete | packet이 요구한 raw artifact가 모두 있는지 |
| registration ready | bundle complete이며 final protocol에 카운트되는 row로 검증되는지 |
| artifact checks | server result, qlog, public readiness, summary, NetLog/path snapshot 등 trial별 파일 존재 |
| validation | `validate_final_handover_trial_artifact.py` 결과 요약 |

회귀 테스트:

```bash
python3 tools/test_check_final_handover_trial_artifact_bundle.py
```

## 38. `tools/audit_artifact_cleanup_safety.py`

디스크 확보 전에 local artifact directory가 `data/experiment-results.csv`의 근거 row나 planned final handover trial id에 연결되는지 확인한다. 삭제를 수행하지 않는 감사 도구이며, raw artifact를 보존해야 하는지 먼저 분류한다.

실행:

```bash
python3 tools/audit_artifact_cleanup_safety.py \
  --output docs/results/artifact-cleanup-safety-audit-20260624.md
```

임시 경로로 확인:

```bash
python3 tools/audit_artifact_cleanup_safety.py \
  --output /tmp/artifact-cleanup-safety-audit.md
```

분류 기준:

| recommendation | 의미 |
| --- | --- |
| `keep-referenced` | `data/experiment-results.csv`에서 artifact path를 참조하므로 논문 근거 보존 대상 |
| `keep-planned-final-trial` | planned final browser handover trial id와 일치하므로 보존 대상 |
| `review-controlled-public` | controlled-public 준비 산출물일 수 있으므로 수동 검토 필요 |
| `review-unreferenced` | 현재 CSV/planned final id에는 연결되지 않지만 삭제 전 수동 검토 필요 |

회귀 테스트:

```bash
python3 tools/test_audit_artifact_cleanup_safety.py
```

## 39. `tools/build_controlled_public_config_worksheet.py`

`harness/config/controlled-public-origin.env`를 채우기 전에 어떤 값을 어느 단계에서 누가 준비해야 하는지 정리하는 public-safe worksheet를 생성한다. 실제 도메인, TLS 경로, private key 경로, `NETWORK_CHANGE_CMD` 값은 출력하지 않는다.

실행:

```bash
python3 tools/build_controlled_public_config_worksheet.py \
  --output docs/results/controlled-public-config-worksheet-20260624.md
```

local private config를 채운 뒤 임시 경로로 확인:

```bash
python3 tools/build_controlled_public_config_worksheet.py \
  --check-files \
  --output /tmp/controlled-public-config-worksheet.md
```

출력 항목:

| 항목 | 의미 |
| --- | --- |
| stage | `baseline`, `active`, `android` 중 어떤 실험 단계에서 필요한지 |
| owner | origin host, client, Android 중 누가 값을 준비해야 하는지 |
| privacy | 공개 문서에 남기면 안 되는 값인지 |
| expected shape | 실제 값 대신 필요한 형식 |
| next action | missing, placeholder, path mismatch 등을 해결하기 위한 다음 행동 |

회귀 테스트:

```bash
python3 tools/test_build_controlled_public_config_worksheet.py
```

## 40. `repro/quic-go-min-repro/scripts/ensure-min-disk-free.sh`

controlled-public wrapper가 heavy NetLog/qlog artifact를 만들기 전에 디스크 여유 공간 하한선을 확인한다. 삭제를 수행하지 않고, 기준 미달이면 exit 2로 중단한다.

기본 동작:

```bash
repro/quic-go-min-repro/scripts/ensure-min-disk-free.sh 5 repro/quic-go-min-repro
```

wrapper에서 사용하는 환경 변수:

| 변수 | 의미 |
| --- | --- |
| `MIN_ARTIFACT_FREE_GIB` | 최소 free space GiB. 기본값은 `5` |
| `MIN_ARTIFACT_FREE_GIB=0` | 작은 smoke test에서만 명시적으로 guard 우회 |

적용 wrapper:

| script | 적용 목적 |
| --- | --- |
| `run-controlled-public-h3-server.sh` | server qlog/log artifact 보호 |
| `run-controlled-public-h3-browser-baseline.sh` | Chrome baseline NetLog artifact 보호 |
| `run-controlled-public-h3-network-change.sh` | Chrome active network-change NetLog/path snapshot 보호 |
| `run-safari-controlled-public-baseline.sh` | Safari baseline navigation/path snapshot 보호 |
| `run-safari-controlled-public-network-change.sh` | Safari active network-change artifact 보호 |
| `run-android-chrome-controlled-public-network-change.sh` | Android snapshot/navigation artifact 보호 |

회귀 테스트:

```bash
python3 tools/test_artifact_disk_guard.py
```

## 41. `tools/build_final_handover_external_inputs.py`

최종 browser/mobile handover 본 실험을 재개하기 전에 사용자가 준비해야 할 외부 입력을 public-safe handoff packet으로 만든다. 실제 도메인, TLS 경로, private key, AWS account ID, Android device id, network-change command 본문은 출력하지 않는다.

실행:

```bash
python3 tools/build_final_handover_external_inputs.py \
  --output docs/results/final-handover-external-inputs-20260624.md
```

출력 항목:

| 항목 | 의미 |
| --- | --- |
| `disk-free-space` | heavy NetLog/qlog capture 전 필요한 free space |
| `controlled-public-baseline-config` | ignored local env에 채워야 하는 baseline config |
| `public-origin-host` | TCP HTTPS Alt-Svc bootstrap과 UDP H3를 제공하는 WebPKI origin |
| `active-network-change-path` | baseline 이후 active Chrome/Safari trial에 필요한 실제 path-change 조건 |
| `android-p1-feasibility` | Android Chrome을 P1 feasibility로 사용할 때 필요한 ADB/device 조건 |
| `aws-identity` | AWS 자동 provisioning이나 CloudFront follow-up에만 필요한 선택 입력 |
| `final-protocol-completion` | required final trial row가 모두 카운트될 때까지 반복해야 하는 loop |

회귀 테스트:

```bash
python3 tools/test_build_final_handover_external_inputs.py
```

## 42. `tools/check_aws_identity_public_safe.py`

AWS 자동 provisioning을 진행할 수 있는지 public-safe하게 확인한다. AWS account ID, ARN, access key, profile 이름, credential file path는 출력하지 않고 다음만 기록한다.

| 항목 | 의미 |
| --- | --- |
| `aws_cli_found` | AWS CLI 실행 파일 존재 여부 |
| `aws_cli_version_present` | AWS CLI가 정상 응답하는지 |
| `region_configured` | env 또는 AWS config에서 region이 확인되는지 |
| `credential_source_present` | credential source가 존재하는지 여부만 확인 |
| `sts_identity_ok` | `aws sts get-caller-identity` 성공 여부 |
| `sts_error_code` | 실패 시 `InvalidClientTokenId`, `ExpiredToken`, `NoCredentials` 같은 오류 코드 |

실행:

```bash
python3 tools/check_aws_identity_public_safe.py \
  --output docs/results/aws-identity-public-safe-check-20260624.md
```

현재 이 도구는 회귀 테스트 없이 lightweight preflight로 사용한다.

## 43. `tools/build_controlled_public_origin_deploy_packet.py`

controlled public WebPKI origin을 실제 host에 배포하기 위한 public-safe command packet을 생성한다. package 생성, SSH upload, remote bootstrap, server 실행, client readiness, final baseline 등록 명령을 한 문서로 묶는다.

이 도구는 실제 hostname, certificate path, private key path, SSH target, AWS account 값을 출력하지 않고 placeholder만 사용한다.

실행:

```bash
python3 tools/build_controlled_public_origin_deploy_packet.py \
  --output docs/results/controlled-public-origin-deploy-packet-20260624.md
```

필요하면 package도 동시에 만들 수 있다. 생성된 tarball은 ignored artifact이므로 commit하지 않는다.

```bash
python3 tools/build_controlled_public_origin_deploy_packet.py \
  --build-package \
  --output docs/results/controlled-public-origin-deploy-packet-20260624.md
```

회귀 테스트:

```bash
python3 tools/test_build_controlled_public_origin_deploy_packet.py
```

## 44. `tools/build_reproducibility_manifest.py`

논문 재현성 bundle의 현재 상태를 public-safe manifest로 묶는다. commit, experiment corpus count, verification status, research audit status, 다음 final trial readiness, 주요 authoritative document path를 한 곳에 모은다.

이 manifest는 qlog, keylog, pcap, NetLog, domain, private key path, AWS account, Android device id를 출력하지 않는다.

실행:

```bash
python3 tools/build_reproducibility_manifest.py \
  --include-ci \
  --output docs/results/reproducibility-manifest-20260624.md \
  --json-output data/reproducibility-manifest-20260624.json
```

CI나 scratch 검증에서는 `--include-ci` 없이 실행해도 된다.

회귀 테스트:

```bash
python3 tools/test_build_reproducibility_manifest.py
```

## 45. `tools/build_paper_evidence_gap_register.py`

논문 claim 단위로 현재 증거가 충분한지, 제한적으로만 쓸 수 있는지, 아직 주장하면 안 되는지를 정리한다. `data/evidence-chain-rubric.csv`와 final browser handover requirement audit을 연결해서 부족한 claim마다 필요한 trial requirement를 붙인다.

산출물:

| 파일 | 용도 |
| --- | --- |
| `docs/results/paper-evidence-gap-register-20260624.md` | 사람이 읽는 주장별 evidence gap register |
| `data/paper-evidence-gap-register-20260624.csv` | 논문 표/부록용 machine-readable register |

실행:

```bash
python3 tools/build_paper_evidence_gap_register.py \
  --output docs/results/paper-evidence-gap-register-20260624.md \
  --csv-output data/paper-evidence-gap-register-20260624.csv
```

회귀 테스트:

```bash
python3 tools/test_build_paper_evidence_gap_register.py
```

## 46. `tools/build_final_trial_acceptance_scorecard.py`

final browser handover trial을 논문 protocol에 count할 수 있는지 requirement별 acceptance 기준으로 정리한다. 각 requirement마다 필요한 최소 row 수, 현재 matched count, planned trial id, acceptance rule, reject rule, 필수 artifact role을 함께 출력한다.

이 도구는 실험 결과를 생성하지 않는다. 대신 결과를 논문 claim으로 받아들일 수 있는지 판단하는 기준을 public-safe하게 고정한다.

산출물:

| 파일 | 용도 |
| --- | --- |
| `docs/results/final-trial-acceptance-scorecard-20260624.md` | 사람이 읽는 final trial acceptance 기준표 |
| `data/final-trial-acceptance-scorecard-20260624.csv` | 논문 표/부록용 machine-readable scorecard |

실행:

```bash
python3 tools/build_final_trial_acceptance_scorecard.py \
  --output docs/results/final-trial-acceptance-scorecard-20260624.md \
  --csv-output data/final-trial-acceptance-scorecard-20260624.csv
```

회귀 테스트:

```bash
python3 tools/test_build_final_trial_acceptance_scorecard.py
```

## 47. `tools/build_final_protocol_readiness_matrix.py`

final browser handover protocol의 모든 planned execution을 현재 local readiness gate에 대입해 한 장의 matrix로 만든다. `next trial` 하나만 보는 것이 아니라 baseline, no-change baseline, active Chrome, P1 Safari/Android 후보 전체가 어떤 gate 때문에 막히는지 보여준다.

산출물:

| 파일 | 용도 |
| --- | --- |
| `docs/results/final-protocol-readiness-matrix-20260624.md` | 사람이 읽는 planned trial별 readiness matrix |
| `data/final-protocol-readiness-matrix-20260624.csv` | planned trial별 gate 상태를 담은 machine-readable matrix |

실행:

```bash
python3 tools/build_final_protocol_readiness_matrix.py \
  --output docs/results/final-protocol-readiness-matrix-20260624.md \
  --csv-output data/final-protocol-readiness-matrix-20260624.csv
```

회귀 테스트:

```bash
python3 tools/test_build_final_protocol_readiness_matrix.py
```

## 48. `tools/build_research_status_dashboard.py`

현재 연구 bundle 상태를 한 장으로 요약한다. reproducibility manifest, final protocol readiness matrix, final trial acceptance scorecard, CM operational friction matrix, experiment-results를 읽어서 trial 수, verifier/CI 상태, final browser handover 진행률, missing gate count, 다음 operator action, 논문 claim boundary를 출력한다.

이 도구는 private env 파일을 읽지 않는다. 이미 public-safe로 생성된 산출물만 요약한다.

산출물:

| 파일 | 용도 |
| --- | --- |
| `docs/results/research-status-dashboard-20260624.md` | 사람이 읽는 현재 연구 진행 dashboard |
| `data/research-status-dashboard-20260624.json` | dashboard의 machine-readable 상태 |

실행:

```bash
python3 tools/build_research_status_dashboard.py \
  --output docs/results/research-status-dashboard-20260624.md \
  --json-output data/research-status-dashboard-20260624.json
```

회귀 테스트:

```bash
python3 tools/test_build_research_status_dashboard.py
```

## 49. `tools/build_cm_operational_friction_matrix.py`

Connection Migration이 "좋은 기술인데 왜 널리 쓰이지 않는가"라는 질문을 계층별 friction matrix로 정리한다. `data/cm-operational-friction-rubric.csv`를 기준으로 `data/experiment-results.csv`와 `data/literature-review-tracker.csv`를 매칭하여 구현체, 브라우저, active path proof, LB/CDN/proxy, middlebox, 보안/운영, application workload, observability별 설명 근거를 만든다.

이 도구는 private origin 설정, network-change command, qlog, pcap, NetLog, credential을 읽거나 출력하지 않는다. 논문에는 최종 positive claim이 아니라 "왜 deployment가 어렵고 어떤 증거가 더 필요한가"를 설명하는 보수적 근거로 사용한다.

산출물:

| 파일 | 용도 |
| --- | --- |
| `docs/results/cm-operational-friction-matrix-20260624.md` | 사람이 읽는 operational friction matrix |
| `data/cm-operational-friction-matrix-20260624.csv` | 논문 표/부록용 machine-readable matrix |

실행:

```bash
python3 tools/build_cm_operational_friction_matrix.py \
  --output docs/results/cm-operational-friction-matrix-20260624.md \
  --csv-output data/cm-operational-friction-matrix-20260624.csv
```

회귀 테스트:

```bash
python3 tools/test_build_cm_operational_friction_matrix.py
```
