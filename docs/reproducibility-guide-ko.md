# 재현 가이드

작성일: 2026-06-24  
목적: QUIC/HTTP/3 Connection Migration 실험을 다른 사람이 같은 저장소에서 다시 실행할 수 있도록 절차, 입력값, 성공 기준을 고정한다.

## 1. 재현 범위

이 저장소에서 바로 재현 가능한 범위:

1. quic-go transport-level active migration 로컬 실험
2. quic-go HTTP/3 post-migration request continuity 로컬 실험
3. quic-go HTTP/3 mid-flight upload/download continuity 로컬 실험
4. Chrome browser local HTTP/3 baseline과 sequence baseline
5. AWS NLB QUIC/TCP_QUIC passthrough 실험용 하네스
6. 구현체별 connection migration evidence scanner
7. qlog event scanner
8. CSV 결과 요약과 공개 번들 검증

이 저장소만으로 자동 재현하지 않는 범위:

1. Chrome/Android 실제 Wi-Fi/LTE handover
2. CloudFront viewer-edge continuity
3. 기존 실험의 raw qlog, keylog, pcap, AWS 계정 artifact

위 3가지는 보안과 개인정보, 계정 정보 문제 때문에 공개 repo에 raw artifact를 넣지 않았다.

## 2. 준비물

필수:

- Go 1.24 이상
- Python 3.10 이상
- Bash

선택:

- `rg`: qlog grep 보조용. 없으면 스크립트가 `grep`을 사용한다.
- AWS CLI v2: AWS NLB 실험에 필요
- AWS default VPC와 최소 2개 default subnet
- AWS 권한: EC2, ELBv2, SSM parameter read, CloudWatch metric read

## 3. Clone 후 공개 번들 검증

```bash
git clone https://github.com/manNomi/quic-connect-migration.git
cd quic-connect-migration
python3 tools/validate_publication_bundle.py
```

성공 기준:

```text
forbidden_artifacts=ok
secret_patterns=ok
csv_files=ok
markdown_links=ok
public_harness_paths=ok
publication_bundle=ok
```

이 검증기는 다음을 확인한다.

- 공개 repo의 tracked 파일에 keylog, qlog raw file, pcap, pem, tarball이 들어가지 않았는지
- AWS access key, secret label, GitHub token, private key 패턴이 없는지
- CSV가 파싱되는지
- Markdown local link가 깨지지 않았는지
- 공개 repo의 AWS 하네스가 과거 연구 폴더 경로인 `experiments/quic-go-min-repro`를 참조하지 않는지

로컬 실험 실행 후 ignored artifact까지 포함해서 훑고 싶으면 다음을 사용한다.

```bash
python3 tools/validate_publication_bundle.py --include-untracked
```

이 모드는 `artifacts/`에 생성된 qlog/keylog를 의도적으로 검출하므로, 로컬 실험 직후에는 실패하는 것이 정상이다.

## 4. 실험 결과 CSV 요약

```bash
python3 tools/summarize_experiment_results.py --input data/experiment-results.csv --format markdown
```

성공 기준:

- 총 trial 수가 출력된다.
- `PASS`, `PASS_NEGATIVE_CONTROL`, `PASS_FEASIBILITY`가 구분된다.
- 각 trial의 implementation, deployment tier, protocol, application success가 표로 출력된다.

논문에 표를 넣을 때는 이 출력과 [data/experiment-results.csv](../data/experiment-results.csv)를 기준 데이터로 사용한다.

## 5. 구현체 evidence scanner

구현체 repo를 별도로 clone한 뒤 scanner를 실행한다.

예시:

```bash
cd ..
git clone https://github.com/quic-go/quic-go.git
git clone https://github.com/cloudflare/quiche.git
git clone https://github.com/aws/s2n-quic.git
cd quic-connect-migration
python3 tools/scan_implementation_evidence.py ../quic-go ../quiche ../s2n-quic --format markdown
```

scanner가 보는 범주:

| category | 의미 |
| --- | --- |
| `path_validation` | `PATH_CHALLENGE`, `PATH_RESPONSE`, path validation evidence |
| `active_migration_api` | active migration API나 테스트용 migration trigger |
| `passive_rebinding` | NAT rebinding, peer address change 처리 |
| `disable_migration_policy` | `disable_active_migration`과 policy flag |
| `preferred_address` | QUIC preferred address 지원 흔적 |
| `cid_and_load_balancing` | Connection ID generator, QUIC-LB, Server ID |
| `observability` | qlog, NetLog, PathEvent, tracing |
| `tests` | migration/rebinding/path 관련 테스트 흔적 |

주의:

이 scanner는 성숙도 판정을 자동으로 내려주지 않는다. 논문에는 scanner output을 1차 근거로 사용하고, 실제 파일과 테스트를 읽어서 다음처럼 사람이 판정해야 한다.

- 구현 primitive가 있는가
- active migration API가 public인지 internal/test-only인지
- qlog/PathEvent 등 관찰성이 있는가
- HTTP/3 client/server path와 실제로 연결되는가
- load balancer/CDN 배포 경로에서 continuity를 유지할 수 있는가

## 6. 로컬 QUIC transport 재현

```bash
cd repro/quic-go-min-repro
go test ./...
RUN_ID=local-quic-transport-check ./scripts/run-local-happy-path.sh
```

성공 기준:

- client result `ok=true`
- server result `ok=true`
- client가 socket A에서 socket B로 migration
- probe 전 `Switch()`는 `ErrPathNotValidated` 계열로 실패
- `Probe()` 이후 `Switch()` 성공
- before/after stream checksum 일치

artifact:

```text
repro/quic-go-min-repro/artifacts/local-quic-transport-check/
```

이 디렉터리는 `.gitignore` 대상이므로 commit하지 않는다.

## 7. 로컬 HTTP/3 post-migration request 재현

```bash
cd repro/quic-go-min-repro
RUN_ID=local-h3-workload-check ./scripts/run-local-h3-workload.sh
```

실험 흐름:

```text
POST /upload before migration
  -> AddPath
  -> Probe
  -> Switch
  -> GET /download after migration
```

성공 기준:

- client result `ok=true`
- server result `ok=true`
- client task count 2
- server request count 2
- final local addr가 socket B
- qlog에서 `path_challenge`, `path_response`, `http3:frame`, `chosen_alpn` evidence 확인

qlog scanner:

```bash
python3 ../../tools/scan_qlog_events.py artifacts/local-h3-workload-check/qlog --format markdown
```

## 8. 로컬 HTTP/3 mid-flight upload/download 재현

```bash
cd repro/quic-go-min-repro
RUN_ID=local-h3-midflight-check ./scripts/run-local-h3-midflight.sh
```

기본 파라미터:

| 변수 | 기본값 |
| --- | --- |
| `PAYLOAD_BYTES` | `1048576` |
| `MIGRATION_AT_BYTES` | `0`, 대략 payload 절반 |
| `CHUNK_BYTES` | `16384` |
| `CHUNK_DELAY` | `2ms` |
| `TIMEOUT` | `45s` |

성공 기준:

- `midflight-upload`와 `midflight-download` 두 case 모두 `PASS`
- 각 case client result `ok=true`
- 각 case server result `ok=true`
- 각 case에서 `migration_triggered=true`
- server/client payload decode success
- final local addr가 socket B
- manual retry 없이 task 완료

qlog scanner:

```bash
python3 ../../tools/scan_qlog_events.py artifacts/local-h3-midflight-check --format markdown
```

## 9. Chrome local HTTP/3 baseline 재현

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-local-spki-pass ./scripts/run-chrome-h3-local.sh
```

성공 기준:

- summary status `PASS`
- server result `ok=true`
- server request count 1
- Chrome NetLog에 `QUIC_SESSION` 존재
- target origin `HTTP_STREAM_JOB`에 `using_quic=true`
- qlog에 `chosen_alpn`, `http3:frame` evidence 존재

주의:

- 이 실험은 browser HTTP/3 baseline이며 connection migration 실험은 아니다.
- Chrome headless가 response 이후 clean exit하지 않아 `chrome_exit=124`를 남길 수 있다.
- server request, NetLog, qlog evidence가 모두 있으면 baseline은 PASS로 분류한다.

sequence baseline:

```bash
cd repro/quic-go-min-repro
WORKLOAD=sequence RUN_ID=chrome-h3-sequence-vtime-pass ./scripts/run-chrome-h3-local.sh
```

성공 기준:

- summary status `PASS`
- server result `ok=true`
- server request count 3
- Chrome NetLog에 target `QUIC_SESSION` 1개 이상 존재
- target origin `HTTP_STREAM_JOB`에 `using_quic=true` 3개 이상 존재
- qlog에 `chosen_alpn`, `http3:frame` evidence 존재
- `path_challenge`, `path_response`는 없어야 정상이다. 이 실험은 migration을 시도하지 않는다.

polling no-change baseline:

```bash
cd repro/quic-go-min-repro
WORKLOAD=poll POLL_COUNT=5 POLL_INTERVAL_MS=300 RUN_ID=chrome-h3-poll-nochange-classifier-pass ./scripts/run-chrome-h3-local.sh
```

성공 기준:

- summary status `PASS`
- `classification=no_path_change_baseline`
- server request count 6
- server remote addr count 1
- Chrome NetLog에 target `QUIC_SESSION` 1개 이상 존재
- target origin `HTTP_STREAM_JOB`에 `using_quic=true` 6개 이상 존재
- qlog에 `chosen_alpn`, `http3:frame` evidence 존재
- qlog에 `path_challenge`, `path_response`는 없어야 정상이다.

network-change hook:

```bash
cd repro/quic-go-min-repro
WORKLOAD=poll \
POLL_COUNT=10 \
POLL_INTERVAL_MS=1000 \
NETWORK_CHANGE_AFTER_SECONDS=3 \
NETWORK_CHANGE_CMD='your-network-change-command' \
RUN_ID=chrome-h3-poll-network-change-manual \
./scripts/run-chrome-h3-local.sh
```

주의:

- `NETWORK_CHANGE_CMD`는 사용자가 명시적으로 넣은 command만 실행한다.
- local loopback origin에서는 실제 Wi-Fi/LTE handover를 재현하지 않는다.
- network-change 실험 결과는 `classification`을 기준으로 해석한다.
- `QUIC_CONNECTION_MIGRATION_MODE` NetLog event만으로 migration 발생을 주장하면 안 된다.

slow subresource limited control:

```bash
cd repro/quic-go-min-repro
WORKLOAD=slow \
SLOW_DURATION_MS=8000 \
SLOW_CHUNKS=8 \
CHROME_VIRTUAL_TIME_BUDGET_MS=0 \
CHROME_TIMEOUT_SECONDS=18 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
NETWORK_CHANGE_AFTER_SECONDS=2 \
NETWORK_CHANGE_CMD='networksetup -setnetworkserviceenabled "Thunderbolt Bridge" off; sleep 1; networksetup -setnetworkserviceenabled "Thunderbolt Bridge" on' \
RUN_ID=chrome-h3-slow-inactive-if-toggle \
./scripts/run-chrome-h3-local.sh
```

성공 기준:

- summary status `PASS`
- `network_change_exit=0`
- `classification=no_path_change_baseline`
- server request count 2
- server remote addr count 1
- qlog에 `path_challenge`, `path_response` 없음

이 실험은 inactive service toggle이므로 실제 active path migration을 만들지 못하는 것이 정상이다. Wi-Fi/LTE handover 근거로 사용하지 않는다.

Wi-Fi IP origin baseline:

```bash
cd repro/quic-go-min-repro
WIFI_IP="$(ipconfig getifaddr en0)"
WORKLOAD=slow \
LISTEN_ADDR=0.0.0.0:4443 \
ORIGIN_ADDR="${WIFI_IP}:4443" \
SLOW_DURATION_MS=6000 \
SLOW_CHUNKS=6 \
CHROME_VIRTUAL_TIME_BUDGET_MS=0 \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
RUN_ID=chrome-h3-slow-wifi-ip-nochange \
./scripts/run-chrome-h3-local.sh
```

Wi-Fi IP inactive interface toggle control:

```bash
cd repro/quic-go-min-repro
WIFI_IP="$(ipconfig getifaddr en0)"
WORKLOAD=slow \
LISTEN_ADDR=0.0.0.0:4443 \
ORIGIN_ADDR="${WIFI_IP}:4443" \
SLOW_DURATION_MS=8000 \
SLOW_CHUNKS=8 \
CHROME_VIRTUAL_TIME_BUDGET_MS=0 \
CHROME_TIMEOUT_SECONDS=18 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
NETWORK_CHANGE_AFTER_SECONDS=2 \
NETWORK_CHANGE_CMD='networksetup -setnetworkserviceenabled "Thunderbolt Bridge" off; sleep 1; networksetup -setnetworkserviceenabled "Thunderbolt Bridge" on' \
RUN_ID=chrome-h3-slow-wifi-ip-inactive-if-toggle \
./scripts/run-chrome-h3-local.sh
```

이 실험은 `127.0.0.1`이 아닌 local Wi-Fi IP를 origin으로 사용한다. 다만 inactive service toggle은 active Wi-Fi path를 바꾸지 않으므로 실제 handover 근거로 사용하지 않는다.

downlink-dominant no-change baseline:

```bash
cd repro/quic-go-min-repro
WORKLOAD=downlink \
DOWNLINK_DURATION_MS=1200 \
DOWNLINK_CHUNKS=3 \
DOWNLINK_BYTES=4096 \
DOWNLINK_HEARTBEAT=false \
CHROME_TIMEOUT_SECONDS=12 \
CHROME_VIRTUAL_TIME_BUDGET_MS=3000 \
RUN_ID=chrome-h3-downlink-noheartbeat-20260624 \
./scripts/run-chrome-h3-local.sh
```

downlink-dominant heartbeat baseline:

```bash
cd repro/quic-go-min-repro
WORKLOAD=downlink \
DOWNLINK_DURATION_MS=1200 \
DOWNLINK_CHUNKS=3 \
DOWNLINK_BYTES=4096 \
DOWNLINK_HEARTBEAT=true \
DOWNLINK_HEARTBEAT_DELAY_MS=400 \
CHROME_TIMEOUT_SECONDS=12 \
CHROME_VIRTUAL_TIME_BUDGET_MS=3000 \
ADDR=127.0.0.1:4453 \
LISTEN_ADDR=127.0.0.1:4453 \
ORIGIN_ADDR=127.0.0.1:4453 \
RUN_ID=chrome-h3-downlink-heartbeat-20260624-rerun \
./scripts/run-chrome-h3-local.sh
```

성공 기준:

- no-heartbeat: `classification=no_path_change_baseline`, server request count 2, target `using_quic=true` job count 2
- heartbeat: `classification=no_path_change_baseline`, server request count 3, target `using_quic=true` job count 3
- 두 경우 모두 qlog에 `chosen_alpn`과 `http3:frame` evidence가 있어야 한다.
- 이 baseline은 migration 성공 근거가 아니다. 실제 network-change 실험 전에 downlink streaming workload와 optional application heartbeat가 Chrome/quic-go H3에서 정상 관측되는지 확인하는 gate다.

Alt-Svc natural HTTP/3 control:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-alt-svc-local-20260624 ./scripts/run-chrome-h3-alt-svc.sh
```

localhost 대조:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-alt-svc-localhost-20260624 \
ADDR=localhost:4443 \
LISTEN_ADDR=127.0.0.1:4443 \
TCP_ADDR=127.0.0.1:4443 \
./scripts/run-chrome-h3-alt-svc.sh
```

성공 기준:

- natural upgrade가 성공하려면 `classification=alt_svc_h3_upgrade_observed`
- server request에 `HTTP/1.1` bootstrap request와 `HTTP/3` request가 모두 존재해야 함
- target NetLog에 confirmed `QUIC_SESSION`이 있어야 함
- qlog에 `http3:frame` evidence가 있어야 함

현재 local self-signed control 결과:

- `127.0.0.1`과 `localhost` 모두 `classification=alt_svc_advertised_but_h3_not_observed`
- 두 server request 모두 `HTTP/1.1`
- qlog `http3_frame=0`
- 이 결과는 forced-QUIC Chrome baseline과 natural browser deployment baseline을 분리해야 함을 보여준다.

HTML/subresource diagnostic:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-alt-svc-html-local-20260624 \
EXPECTED_REQUESTS=4 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_VIRTUAL_TIME_BUDGET_MS=3000 \
BOOTSTRAP_PATH='/browser-sequence?resources=1&bytes=64&label=alt-svc-bootstrap-html' \
H3_PATH='/browser-sequence?resources=1&bytes=64&label=alt-svc-h3-html' \
./scripts/run-chrome-h3-alt-svc.sh
```

진단 결과:

- `classification=alt_svc_quic_candidate_cert_rejected`
- server request 4개 모두 `HTTP/1.1`
- qlog에는 QUIC connection과 HTTP/3 SETTINGS frame이 있었지만 request stream은 없었음
- qlog close reason은 `certificate unknown / CERTIFICATE_VERIFY_FAILED`

mkcert localhost diagnostic:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-alt-svc-html-mkcert-localhost-v2-20260624 \
CERT_MODE=mkcert \
CHROME_USE_SPKI_EXCEPTION=0 \
ADDR=localhost:4443 \
LISTEN_ADDR=127.0.0.1:4443 \
TCP_ADDR=127.0.0.1:4443 \
EXPECTED_REQUESTS=4 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_VIRTUAL_TIME_BUDGET_MS=3000 \
BOOTSTRAP_PATH='/browser-sequence?resources=1&bytes=64&label=alt-svc-bootstrap-html-mkcert' \
H3_PATH='/browser-sequence?resources=1&bytes=64&label=alt-svc-h3-html-mkcert' \
./scripts/run-chrome-h3-alt-svc.sh
```

mkcert IP literal diagnostic:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-alt-svc-html-mkcert-ip-20260624 \
CERT_MODE=mkcert \
CHROME_USE_SPKI_EXCEPTION=0 \
ADDR=127.0.0.1:4443 \
LISTEN_ADDR=127.0.0.1:4443 \
TCP_ADDR=127.0.0.1:4443 \
EXPECTED_REQUESTS=4 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_VIRTUAL_TIME_BUDGET_MS=3000 \
BOOTSTRAP_PATH='/browser-sequence?resources=1&bytes=64&label=alt-svc-bootstrap-html-mkcert-ip' \
H3_PATH='/browser-sequence?resources=1&bytes=64&label=alt-svc-h3-html-mkcert-ip' \
./scripts/run-chrome-h3-alt-svc.sh
```

mkcert 진단 결과:

- `localhost`: `classification=alt_svc_marked_broken_without_h3_request`
- `127.0.0.1`: `classification=alt_svc_quic_candidate_cert_rejected`
- 두 경우 모두 application request는 `HTTP/1.1`
- public WebPKI origin으로 H3 discovery baseline을 다시 확인하되, application HTTP/3 여부는 별도 기준으로 판정해야 한다.

## 10. Chrome public WebPKI H3 discovery baseline 재현

local Alt-Svc control이 실패했을 때, Chrome 자체가 H3 discovery를 못 하는지 또는 local origin/trust 조건이 문제인지 분리한다. 단, public third-party endpoint의 NetLog만으로 application request가 HTTP/3로 처리됐다고 단정하지 않는다.

Cloudflare QUIC trace endpoint:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-public-h3-cloudflare-quic-trace-20260624 \
TARGET_URL=https://cloudflare-quic.com/cdn-cgi/trace \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_VIRTUAL_TIME_BUDGET_MS=1000 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
./scripts/run-chrome-public-h3.sh
```

Google generate_204 endpoint:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-public-h3-google-generate204-20260624 \
TARGET_URL=https://www.google.com/generate_204 \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_VIRTUAL_TIME_BUDGET_MS=1000 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
./scripts/run-chrome-public-h3.sh
```

YouTube generate_204 endpoint:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-public-h3-youtube-generate204-20260624 \
TARGET_URL=https://www.youtube.com/generate_204 \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_VIRTUAL_TIME_BUDGET_MS=1000 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
./scripts/run-chrome-public-h3.sh
```

Discovery control 기준:

- `classification=public_h3_discovery_without_application_h3` 또는 `public_natural_h3_observed`
- target host에 대한 `dns_alpn_h3` job 또는 `QUIC_SESSION` evidence가 있음
- `broken_alternative_service=false`

Application HTTP/3 확정 기준:

- `classification=public_natural_h3_observed`
- target host에 대한 `QUIC_SESSION`이 1개 이상
- target host의 application `HTTP_STREAM_JOB` 중 `using_quic=true`가 1개 이상
- `dns_alpn_h3` discovery job만으로는 application HTTP/3 성공이라고 보지 않음

주의:

- 이 실험은 connection migration 실험이 아니다.
- 목적은 browser가 target origin에 대해 forced QUIC 없이 H3 discovery 후보를 만드는지, 그리고 가능하면 application HTTP/3까지 도달하는지 분리해 확인하는 것이다.
- public endpoint 결과는 시간, region, server policy에 따라 바뀔 수 있으므로 실행일과 target URL을 CSV에 함께 기록한다.

public endpoint 후보를 먼저 줄이려면 다음을 실행한다.

```bash
python3 tools/scan_public_alt_svc.py \
  --url-file data/public-alt-svc-targets.txt \
  --format markdown
```

이 스캐너는 `Alt-Svc: h3` 광고 여부만 본다. Chrome이 H3 discovery 또는 application HTTP/3까지 도달했는지는 `run-chrome-public-h3.sh` 결과와 NetLog classifier로 별도 확인해야 한다.

## 11. Controlled public WebPKI origin gate

third-party public endpoint는 browser discovery control에는 유용하지만, upload/download/dashboard workload를 제어할 수 없다. 실제 browser CM 실험 전에는 연구자가 제어하는 public origin을 준비한다.

local-only config:

```bash
cp harness/config/controlled-public-origin.env.example harness/config/controlled-public-origin.env
```

먼저 안전한 preflight를 실행한다. 이 command는 실제 network-change를 수행하지 않고 ignored artifact directory에 readiness JSON/Markdown만 만든다.

```bash
bash harness/scripts/controlled-public-preflight.sh
```

Server side:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-h3-application-baseline-001 \
ARTIFACT_DIR=artifacts/controlled-public-h3-application-baseline-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
PUBLIC_ORIGIN_PORT=443 \
EXPECTED_REQUESTS=2 \
./scripts/run-controlled-public-h3-server.sh
```

Browser side:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-h3-application-baseline-001 \
ARTIFACT_DIR=artifacts/controlled-public-h3-application-baseline-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-h3-application-baseline-001 \
REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3=1 \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow' \
CHROME_TIMEOUT_SECONDS=20 \
CHROME_VIRTUAL_TIME_BUDGET_MS=0 \
./scripts/run-controlled-public-h3-browser-baseline.sh
```

Browser wrapper는 같은 artifact directory에 `results/server.json`이 있으면 다음 combined classifier를 자동 실행한다.

```bash
cd ../..
python3 tools/classify_controlled_public_h3_baseline.py \
  repro/quic-go-min-repro/artifacts/controlled-public-h3-application-baseline-001 \
  --url 'https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow' \
  --output repro/quic-go-min-repro/artifacts/controlled-public-h3-application-baseline-001/results/controlled-public-h3-baseline-summary.json
```

사전 readiness check:

```bash
python3 tools/check_public_origin_readiness.py \
  --url 'https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow' \
  --require-h3-alt-svc \
  --format markdown
```

성공 기준:

- DNS가 public host를 해석한다.
- WebPKI TLS handshake와 hostname verification이 성공한다.
- response에 `Alt-Svc: h3`가 있다.
- Chrome classifier가 `public_natural_h3_observed`를 반환하거나, server request log와 qlog가 workload request의 HTTP/3 처리를 직접 증명한다.
- server request log와 qlog가 workload request를 기록한다.
- combined classifier가 `controlled_public_application_h3_confirmed` 또는 `controlled_public_server_qlog_h3_confirmed_browser_netlog_inconclusive`를 반환한다.

## 12. Controlled public Chrome H3 network-change

application H3 baseline summary가 `status=PASS`인 뒤에만 실행한다.

먼저 readiness를 확인한다.

```bash
bash harness/scripts/controlled-public-preflight.sh
```

수동으로 직접 확인할 수도 있다.

```bash
python3 tools/check_controlled_public_experiment_readiness.py \
  --public-origin-url 'https://h3.example.com/browser-slow?duration_ms=15000&chunks=15&label=handover-slow' \
  --baseline-summary repro/quic-go-min-repro/artifacts/controlled-public-h3-application-baseline-001/results/controlled-public-h3-baseline-summary.json \
  --network-change-cmd '...' \
  --format markdown
```

Server side:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-h3-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-h3-network-change-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
PUBLIC_ORIGIN_PORT=443 \
EXPECTED_REQUESTS=2 \
./scripts/run-controlled-public-h3-server.sh
```

Browser/network side:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-h3-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-h3-network-change-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-h3-network-change-001 \
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/controlled-public-h3-application-baseline-001/results/controlled-public-h3-baseline-summary.json \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=15000&chunks=15&label=handover-slow' \
NETWORK_CHANGE_AFTER_SECONDS=3 \
NETWORK_CHANGE_CMD='...' \
./scripts/run-controlled-public-h3-network-change.sh
```

결과 파일:

```text
artifacts/controlled-public-h3-network-change-001/results/controlled-public-h3-network-change-summary.json
artifacts/controlled-public-h3-network-change-001/results/client-path-change-summary.json
```

주요 판정:

- `possible_connection_migration`: tuple change와 qlog path validation이 함께 관찰됨
- `reconnect_or_multiple_sessions`: 여러 QUIC session 단서가 있어 reconnect 가능성이 큼
- `tuple_changed_without_path_validation`: tuple은 바뀌었으나 QUIC migration evidence 부족
- `no_path_change_after_trigger`: network-change command는 실행됐지만 active path 변화가 관찰되지 않음
- `client-path-change-summary.json`의 `client_active_path_changed`: client route/interface 관점에서 command가 실제 path 변화를 만들었는지 확인

## 13. Safari controlled public H3 baseline

Safari는 Chrome NetLog와 같은 browser-internal QUIC artifact가 없으므로 별도 baseline wrapper를 사용한다.

```bash
cd repro/quic-go-min-repro
RUN_ID=safari-controlled-public-h3-baseline-001 \
ARTIFACT_DIR=artifacts/safari-controlled-public-h3-baseline-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/safari-controlled-public-h3-baseline-001 \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=safari-public-slow' \
SAFARI_WAIT_SECONDS=8 \
./scripts/run-safari-controlled-public-baseline.sh
```

성공 기준:

- `results/safari-navigation.json`에서 `navigation_ok=true`
- server artifact의 expected request count 충족
- server qlog에 `chosen_alpn=h3`와 HTTP/3 frame evidence
- `results/safari-controlled-public-h3-baseline-summary.json`이 `PASS` 또는 `PASS_FEASIBILITY`

이 실험은 Safari handover가 아니다. Safari real interface-change 실험은 이 baseline과 packet-capture 계획이 준비된 뒤 실행한다.

## 14. AWS NLB 실험 설정

로컬 설정 파일을 만든다.

```bash
cp harness/config/aws.env.example harness/config/aws.env
cp harness/config/experiment.env.example harness/config/experiment.env
```

`harness/config/aws.env` 예시:

```bash
AWS_PROFILE=your-profile
AWS_REGION=ap-northeast-2
RESOURCE_PREFIX=quic-cm-lab
CLIENT_PUBLIC_CIDR=
```

주의:

- `harness/config/aws.env`와 `harness/config/experiment.env`는 commit하지 않는다.
- access key CSV를 repo에 넣지 않는다.
- AWS credential은 `aws configure`, SSO, 환경변수, profile 중 하나로 로컬에만 둔다.

preflight:

```bash
./harness/scripts/aws-preflight.sh
```

성공 기준:

- AWS caller identity 확인
- region opt-in 상태 확인
- default VPC/subnet 조회 가능

## 15. AWS NLB transport 재현

```bash
WORKLOAD=transport \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
PAYLOAD_BYTES=65536 \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

성공 기준:

- client result `ok=true`
- successful server target이 1개
- 같은 target에서 before/after stream 2개 수신
- client source port가 바뀜
- summary status `PASS`
- cleanup status `deleted-listener-lb-tg-instances-sg-keypair`

## 16. AWS NLB HTTP/3 post-migration 재현

```bash
WORKLOAD=h3 \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
PAYLOAD_BYTES=65536 \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

성공 기준:

- HTTP/3 POST `/upload` 완료
- migration 완료
- HTTP/3 GET `/download` 완료
- 같은 target이 두 request를 모두 수신
- summary status `PASS`

## 17. AWS NLB HTTP/3 mid-flight 재현

Upload:

```bash
WORKLOAD=h3-midflight-upload \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
PAYLOAD_BYTES=1048576 \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

Download:

```bash
WORKLOAD=h3-midflight-download \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
PAYLOAD_BYTES=1048576 \
CLIENT_START_DELAY_SECONDS=8 \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

성공 기준:

- target 하나만 successful server로 분류
- 해당 target이 full 1MiB body를 처리
- client final addr가 socket B
- qlog에 path validation evidence가 있음
- summary status `PASS`

## 18. Negative control 재현

잘못된 Server ID를 의도적으로 넣는다.

```bash
WORKLOAD=transport \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
TARGET_A_SERVER_ID=0xa1b2c3d4e5f65890 \
TARGET_B_SERVER_ID=0xa1b2c3d4e5f65999 \
SERVER_A_CID_SERVER_ID=0x1111111111111111 \
SERVER_B_CID_SERVER_ID=0x2222222222222222 \
EXPECTED_OUTCOME=client-failure \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

성공 기준:

- client가 성공하면 안 된다.
- summary status가 `PASS_NEGATIVE_CONTROL`이어야 한다.
- target health가 정상이어도 application payload가 통과하지 못한다.

이 negative control은 “HTTP/3가 켜져 있다”와 “migration continuity가 된다”가 같은 말이 아님을 보여주는 배포 계층 근거다.

## 19. AWS cleanup 확인

하네스는 정상 종료와 실패 종료 모두에서 cleanup trap을 실행한다. 실행 후 다음을 확인한다.

```bash
aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=quic-connection-migration" \
  --query 'Reservations[].Instances[?State.Name!=`terminated`].[InstanceId,State.Name,Tags[?Key==`RunId`].Value|[0]]' \
  --output table

aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?contains(LoadBalancerName, `qcm-nlb`)].[LoadBalancerName,State.Code,DNSName]' \
  --output table

aws ec2 describe-security-groups \
  --filters "Name=tag:Project,Values=quic-connection-migration" \
  --query 'SecurityGroups[].[GroupId,GroupName,Tags[?Key==`RunId`].Value|[0]]' \
  --output table
```

정상 기준:

- active EC2 instance 없음
- `qcm-nlb-*` load balancer 없음
- 실험 tag가 붙은 security group 없음
- key pair 없음

## 20. Artifact 정책

commit 가능한 것:

- source code
- markdown result summary
- CSV summary
- scanner script
- config `.example`

commit하지 않는 것:

- `harness/config/aws.env`
- `harness/config/experiment.env`
- `*.keys`
- `*.sqlog`
- `*.pcap`, `*.pcapng`
- `*.pem`
- `*.tgz`, `*.tar.gz`
- `artifacts/`
- `harness/results/`

실험 실행 후 공개 repo에 올리기 전 항상 다음을 실행한다.

```bash
python3 tools/validate_publication_bundle.py
```
