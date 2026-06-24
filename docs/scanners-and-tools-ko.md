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

`QUIC_CONNECTION_MIGRATION_MODE` 같은 NetLog event는 설정 evidence로만 보고, 실제 migration evidence는 tuple change와 qlog path validation을 함께 요구한다.

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

Chrome public WebPKI natural HTTP/3 baseline artifact를 NetLog 기준으로 분류한다.

실행:

```bash
python3 tools/classify_chrome_public_h3_artifacts.py \
  repro/quic-go-min-repro/artifacts/chrome-public-h3-google-generate204-20260624 \
  --url https://www.google.com/generate_204
```

주요 output:

| 항목 | 의미 |
| --- | --- |
| `classification` | public origin에서 natural HTTP/3가 관찰됐는지 |
| `bootstrap_h3_observed` | bootstrap NetLog에서 target HTTP/3 evidence가 있는지 |
| `second_h3_observed` | second NetLog에서 target HTTP/3 evidence가 있는지 |
| `target_quic_session_count` | target host/port의 QUIC session 수 |
| `target_using_quic_job_count` | target host/port의 `HTTP_STREAM_JOB using_quic=true` 수 |
| `target_broken_alternative_service` | Alt-Svc가 broken으로 기록됐는지 |

classification:

| classification | 의미 |
| --- | --- |
| `public_natural_h3_observed` | public origin에서 target HTTP/3 사용이 관찰됨 |
| `public_alt_svc_marked_broken` | target alternative service가 broken으로 기록됨 |
| `public_alt_svc_or_request_observed_but_h3_not_confirmed` | target request 또는 Alt-Svc evidence는 있으나 HTTP/3 사용은 확정 불가 |

이 도구는 local Alt-Svc negative control과 public WebPKI positive control을 분리하기 위한 것이다. migration evidence는 판정하지 않는다.

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

이 도구가 통과해도 migration이 증명되는 것은 아니다. Chrome NetLog와 server qlog를 포함한 no-change natural H3 baseline을 추가로 통과해야 한다.

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

## 11. `tools/check_handover_readiness.py`

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

## 12. 실험 실행 코드

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
| `scripts/run-chrome-public-h3.sh` | Chrome public WebPKI natural HTTP/3 baseline |
| `scripts/run-controlled-public-h3-server.sh` | WebPKI cert/key를 사용하는 controlled public H3 origin server wrapper |
| `scripts/run-controlled-public-h3-browser-baseline.sh` | controlled public origin readiness + Chrome natural H3 baseline wrapper |
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

## 13. 최소 검증 세트

논문용 결과를 갱신하기 전 최소한 다음은 통과시킨다.

```bash
python3 tools/validate_publication_bundle.py
python3 tools/summarize_experiment_results.py --format markdown
python3 tools/scan_implementation_evidence.py repro/quic-go-min-repro --format markdown
python3 tools/scan_public_alt_svc.py --url-file data/public-alt-svc-targets.txt --format markdown
python3 tools/scan_public_origin_readiness.py --url-file data/public-alt-svc-targets.txt --format markdown
python3 tools/check_public_origin_readiness.py --url https://www.google.com/generate_204 --require-h3-alt-svc --format markdown
python3 tools/check_handover_readiness.py --format markdown

cd repro/quic-go-min-repro
go test ./...
RUN_ID=local-h3-workload-check ./scripts/run-local-h3-workload.sh
RUN_ID=local-h3-midflight-check ./scripts/run-local-h3-midflight.sh
RUN_ID=chrome-h3-local-spki-pass ./scripts/run-chrome-h3-local.sh
WORKLOAD=sequence RUN_ID=chrome-h3-sequence-vtime-pass ./scripts/run-chrome-h3-local.sh
WORKLOAD=poll POLL_COUNT=5 POLL_INTERVAL_MS=300 RUN_ID=chrome-h3-poll-nochange-classifier-pass ./scripts/run-chrome-h3-local.sh
WORKLOAD=slow SLOW_DURATION_MS=8000 SLOW_CHUNKS=8 RUN_ID=chrome-h3-slow-inactive-if-toggle ./scripts/run-chrome-h3-local.sh
LISTEN_ADDR=0.0.0.0:4443 ORIGIN_ADDR="$(ipconfig getifaddr en0):4443" WORKLOAD=slow RUN_ID=chrome-h3-slow-wifi-ip-nochange ./scripts/run-chrome-h3-local.sh
RUN_ID=chrome-h3-alt-svc-local-20260624 ./scripts/run-chrome-h3-alt-svc.sh
RUN_ID=chrome-public-h3-google-generate204-20260624 TARGET_URL=https://www.google.com/generate_204 ./scripts/run-chrome-public-h3.sh
```

AWS 결과를 갱신할 때는 [재현 가이드](reproducibility-guide-ko.md)의 cleanup 확인까지 포함한다.
