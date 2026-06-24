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

Safari baseline은 Chrome NetLog가 없으므로 `classify_controlled_public_h3_baseline.py --allow-missing-browser-summary` 경로를 사용한다.

## 16. `tools/classify_controlled_public_h3_network_change.py`

controlled public origin에서 Chrome workload 중 network-change trigger를 넣은 결과를 분류한다.

실행:

```bash
python3 tools/classify_controlled_public_h3_network_change.py \
  repro/quic-go-min-repro/artifacts/controlled-public-h3-network-change-001 \
  --server-artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-h3-network-change-001 \
  --url 'https://h3.example.com/browser-slow?duration_ms=15000&chunks=15&label=handover-slow' \
  --output repro/quic-go-min-repro/artifacts/controlled-public-h3-network-change-001/results/controlled-public-h3-network-change-summary.json
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
| `possible_connection_migration` | tuple change와 qlog path validation이 함께 관찰됨 |
| `reconnect_or_multiple_sessions` | tuple change가 있으나 여러 QUIC session evidence |
| `tuple_changed_without_path_validation` | tuple change가 있으나 path validation evidence 없음 |
| `no_path_change_after_trigger` | network-change command 후에도 tuple 변화 없음 |
| `controlled_public_network_change_workload_failed` | workload expected request count 미달 |

## 17. `tools/capture_network_path_snapshot.py`, `tools/compare_network_path_snapshots.py`

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
python3 tools/capture_network_path_snapshot.py --url https://www.google.com/generate_204 --output /tmp/quic-cm-path-before.json
python3 tools/compare_network_path_snapshots.py /tmp/quic-cm-path-before.json /tmp/quic-cm-path-before.json
python3 -m py_compile tools/classify_controlled_public_h3_network_change.py

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
