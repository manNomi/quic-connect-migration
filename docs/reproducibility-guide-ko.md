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

CDP real-time runner:

```bash
cd repro/quic-go-min-repro
WORKLOAD=downlink \
DOWNLINK_DURATION_MS=1200 \
DOWNLINK_CHUNKS=3 \
DOWNLINK_BYTES=4096 \
DOWNLINK_HEARTBEAT=true \
DOWNLINK_HEARTBEAT_DELAY_MS=400 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=4 \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
ADDR=127.0.0.1:4465 \
LISTEN_ADDR=127.0.0.1:4465 \
ORIGIN_ADDR=127.0.0.1:4465 \
RUN_ID=chrome-h3-downlink-heartbeat-cdp-nochange-grace-20260624 \
./scripts/run-chrome-h3-local.sh
```

이 실행의 정상 판정은 `multiple_quic_sessions_without_network_change`다. heartbeat fetch가 no-change 환경에서도 별도 QUIC session/source port를 만들 수 있으므로, tuple 변화만으로 migration을 주장하면 안 된다.

inactive interface toggle + client path snapshot:

```bash
cd repro/quic-go-min-repro
WORKLOAD=downlink \
DOWNLINK_DURATION_MS=8000 \
DOWNLINK_CHUNKS=8 \
DOWNLINK_BYTES=8192 \
DOWNLINK_HEARTBEAT=true \
DOWNLINK_HEARTBEAT_DELAY_MS=3000 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=11 \
CHROME_TIMEOUT_SECONDS=25 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
NETWORK_CHANGE_AFTER_SECONDS=2 \
NETWORK_CHANGE_CMD='networksetup -setnetworkserviceenabled "Thunderbolt Bridge" off; sleep 1; networksetup -setnetworkserviceenabled "Thunderbolt Bridge" on' \
ADDR=127.0.0.1:4467 \
LISTEN_ADDR=127.0.0.1:4467 \
ORIGIN_ADDR=127.0.0.1:4467 \
RUN_ID=chrome-h3-downlink-heartbeat-cdp-inactive-if-toggle-20260624 \
./scripts/run-chrome-h3-local.sh
```

정상 판정:

- `classification=multiple_quic_sessions_without_client_path_change`
- `client_path_change.classification=no_client_path_change_observed`
- qlog `path_challenge`, `path_response` 없음

이 실험은 실제 handover가 아니다. path-change trigger가 no-op일 때 생기는 browser multiple-session artifact를 분리하는 대조군이다.

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

## 13. 최종 browser handover trial loop

논문 본 실험으로 카운트되는 browser/mobile handover 결과는 단일 wrapper 실행 결과를 바로 CSV에 붙이지 않는다. 다음 loop를 통과해야 한다.

현재 상태와 private config 작성 항목을 먼저 확인한다.

```bash
python3 tools/build_controlled_public_config_worksheet.py \
  --output docs/results/controlled-public-config-worksheet-20260624.md

python3 tools/build_final_handover_operator_checklist.py \
  --output docs/results/final-handover-operator-checklist-20260624.md
```

다음 실행할 trial 하나를 선택하고 packet을 만든다.

```bash
python3 tools/select_next_final_handover_trial.py \
  --output docs/results/final-handover-next-trial-20260624.md

python3 tools/check_next_final_handover_trial_readiness.py \
  --output docs/results/final-handover-next-trial-readiness-20260624.md

python3 tools/build_final_handover_trial_packet.py \
  --output docs/results/final-handover-trial-packet-20260624.md
```

`final-handover-trial-packet`의 server/client 명령만 실행한다. controlled-public wrapper는 기본적으로 `MIN_ARTIFACT_FREE_GIB=5`를 요구하며, 디스크가 부족하면 artifact를 만들기 전에 중단한다. 작은 smoke test가 아닌 본 실험에서 `MIN_ARTIFACT_FREE_GIB=0`으로 우회하지 않는다.

trial 실행 후 raw artifact bundle부터 확인한다.

```bash
python3 tools/check_final_handover_trial_artifact_bundle.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --require-final-countable \
  --require-complete
```

그 다음 단일 artifact validation과 CSV dry-run append를 실행한다.

```bash
python3 tools/validate_final_handover_trial_artifact.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --require-final-countable

python3 tools/append_final_handover_result_row.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --require-final-countable \
  --require-artifact-bundle \
  --output /tmp/final-handover-append-dry-run.md
```

dry-run에서 `duplicate trial_id=no`, `counts toward final protocol=yes`, `artifact bundle complete=yes`를 확인한 뒤에만 `--apply`를 붙인다.

```bash
python3 tools/append_final_handover_result_row.py \
  --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
  --require-final-countable \
  --require-artifact-bundle \
  --apply
```

등록 후에는 final protocol audit와 전체 bundle verify를 다시 실행한다.

```bash
python3 tools/audit_final_browser_handover_trials.py \
  --output docs/results/final-browser-handover-trial-audit-20260624.md

python3 tools/verify_research_bundle.py \
  --output docs/results/research-verification-report-20260624.md
```

`python3 tools/audit_final_browser_handover_trials.py --require-complete`가 exit 0이 되기 전에는 final browser/mobile handover 본 실험 완료를 주장하지 않는다.

## 14. Safari controlled public H3 baseline

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

## 15. AWS NLB 실험 설정

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

## 16. AWS NLB transport 재현

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

## 17. AWS NLB HTTP/3 post-migration 재현

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

## 18. AWS NLB HTTP/3 mid-flight 재현

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

## 19. Negative control 재현

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

## 20. AWS cleanup 확인

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

## 21. Chrome local old-path-drop stress 재현

Chrome forced-H3 local NAT rebinding에서 old path가 더 이상 return path로 쓸 수 없는 상황을 흉내내기 위해 UDP rebinding proxy가 upstream B로 전환한 뒤 upstream A의 server-to-client packet을 drop한다. 이 실험은 실제 Wi-Fi/LTE handover가 아니라 local old-path-unavailable control이다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-old-path-drop-stress-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-old-path-drop-stress-20260624 \
BASE_PORT=6200 \
REBIND_AFTER=500ms \
TIMEOUT=40s \
CHROME_TIMEOUT_SECONDS=35 \
CHROME_HOLD_SECONDS=16 \
./scripts/run-chrome-h3-rebinding-old-path-drop-stress.sh
```

주의:

- `BASE_PORT=6000`은 Chrome restricted port라 서버에 request가 도달하지 않는다.
- raw Chrome profile, NetLog, qlog artifact가 크므로 실행 전 디스크 여유를 확인한다.
- 이 결과를 actual browser handover success로 쓰지 않는다.

성공 기준:

- stress row 5개가 모두 `PASS`
- qlog path validation 5/5
- Chrome target NetLog path validation 5/5
- proxy switched 5/5
- old-path drop enabled 5/5
- 1MiB/4MiB upload가 `/upload-sink`에 도달

논문용 summary 재생성:

```bash
cd ../..
python3 tools/summarize_chrome_rebinding_stress_matrix.py \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-old-path-drop-stress-20260624/downlink-1m-noheartbeat \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-old-path-drop-stress-20260624/downlink-1m-heartbeat \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-old-path-drop-stress-20260624/downlink-4m-noheartbeat \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-old-path-drop-stress-20260624/upload-1m \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-old-path-drop-stress-20260624/upload-4m \
  --output docs/results/chrome-h3-rebinding-old-path-drop-stress-20260624.md \
  --csv-output data/chrome-h3-rebinding-old-path-drop-stress-20260624.csv
```

## 22. Chrome local return-path drop control 재현

old-path-drop stress가 “성공”만 보여주지 않도록, return path를 단계적으로 차단하는 대조군을 실행한다. B-only drop은 새 경로 응답만 막고 old return path는 남긴다. A+B drop은 switch 이후 old/new return path를 모두 막아 expected failure boundary를 만든다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-return-path-drop-controls-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-return-path-drop-controls-20260624 \
BASE_PORT=6700 \
REBIND_AFTER=500ms \
TIMEOUT=35s \
CHROME_TIMEOUT_SECONDS=28 \
CHROME_HOLD_SECONDS=14 \
./scripts/run-chrome-h3-rebinding-return-path-drop-controls.sh
```

성공 기준:

- B-only drop downlink/upload 2개 row는 `PASS`
- A+B drop downlink/upload 2개 row는 `FAIL`
- A+B failure row의 classification은 `browser_application_task_failed`
- failure row에서도 server request와 qlog/Chrome NetLog evidence가 남을 수 있음을 확인

논문용 summary 재생성:

```bash
cd ../..
python3 tools/summarize_chrome_rebinding_return_path_drop_controls.py \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-return-path-drop-controls-20260624/downlink-1m-drop-b-only \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-return-path-drop-controls-20260624/upload-1m-drop-b-only \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-return-path-drop-controls-20260624/downlink-1m-drop-a-and-b \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-return-path-drop-controls-20260624/upload-1m-drop-a-and-b \
  --output docs/results/chrome-h3-rebinding-return-path-drop-controls-20260624.md \
  --csv-output data/chrome-h3-rebinding-return-path-drop-controls-20260624.csv
```

## 23. Chrome local transient return-path outage sweep 재현

A+B return path를 영구적으로 차단하는 대신 일정 시간 뒤 복구시켜, local browser workload가 어느 outage window까지 버티는지 측정한다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-transient-return-path-sweep-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624 \
BASE_PORT=6800 \
REBIND_AFTER=500ms \
TIMEOUT=42s \
CHROME_TIMEOUT_SECONDS=36 \
CHROME_HOLD_SECONDS=18 \
./scripts/run-chrome-h3-rebinding-transient-return-path-sweep.sh
```

성공/실패 기준:

- 250ms, 1500ms, 3000ms, 4000ms window의 downlink/upload row는 `PASS`
- 5000ms, 6000ms, 9000ms window의 downlink/upload row는 `FAIL`
- 실패 row의 classification은 `browser_application_task_failed`
- 이 결과는 local outage-tolerance control이며 실제 public handover evidence가 아니다.

논문용 summary 재생성:

```bash
cd ../..
python3 tools/summarize_chrome_rebinding_transient_return_path_sweep.py \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/downlink-1m-drop-ab-250ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/upload-1m-drop-ab-250ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/downlink-1m-drop-ab-1500ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/upload-1m-drop-ab-1500ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/downlink-1m-drop-ab-3000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/upload-1m-drop-ab-3000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/downlink-1m-drop-ab-4000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/upload-1m-drop-ab-4000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/downlink-1m-drop-ab-5000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/upload-1m-drop-ab-5000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/downlink-1m-drop-ab-6000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/upload-1m-drop-ab-6000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/downlink-1m-drop-ab-9000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624/upload-1m-drop-ab-9000ms \
  --output docs/results/chrome-h3-rebinding-transient-return-path-sweep-20260624.md \
  --csv-output data/chrome-h3-rebinding-transient-return-path-sweep-20260624.csv
```

## 24. Chrome local transient boundary repetition 재현

4초와 5초 사이의 단일 경계 주장만으로는 부족하므로, 4000ms/4500ms/5000ms window를 downlink/upload 각각 3회 반복한다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-transient-boundary-repetition-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-transient-boundary-repetition-20260624 \
BASE_PORT=7100 \
REBIND_AFTER=500ms \
TIMEOUT=42s \
CHROME_TIMEOUT_SECONDS=36 \
CHROME_HOLD_SECONDS=18 \
REPETITIONS=3 \
./scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh
```

논문용 summary 등록:

```bash
cd ../..
cp repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-boundary-repetition-20260624/results/transient-boundary-repetition-summary.md \
  docs/results/chrome-h3-rebinding-transient-boundary-repetition-20260624.md
cp repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-boundary-repetition-20260624/results/transient-boundary-repetition-summary.csv \
  data/chrome-h3-rebinding-transient-boundary-repetition-20260624.csv
```

현재 관찰된 기준:

- 4000ms와 4500ms window는 각각 `6/6 PASS`
- 5000ms window는 downlink `3/3 PASS`, upload `0/3 PASS`
- 5초 근처는 단일 threshold가 아니라 workload-sensitive transition zone으로 해석한다.
- 이 결과도 local outage-tolerance control이며 실제 public handover evidence가 아니다.

## 25. Chrome local downlink fine boundary 재현

5000ms 근처의 downlink 결과가 단일 threshold인지 mixed transition zone인지 확인한다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-transient-downlink-fine-boundary-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624 \
BASE_PORT=8800 \
WORKLOADS=downlink \
DROP_WINDOWS_MS="5000 5500 6000" \
REPETITIONS=3 \
TIMEOUT=90s \
CHROME_TIMEOUT_SECONDS=80 \
CHROME_HOLD_SECONDS=42 \
./scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh
```

논문용 summary 등록:

```bash
python3 tools/summarize_chrome_rebinding_transient_return_path_sweep.py \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624/rep01-downlink-1m-drop-ab-5000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624/rep01-downlink-1m-drop-ab-5500ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624/rep01-downlink-1m-drop-ab-6000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624/rep02-downlink-1m-drop-ab-5000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624/rep02-downlink-1m-drop-ab-5500ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624/rep02-downlink-1m-drop-ab-6000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624/rep03-downlink-1m-drop-ab-5000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624/rep03-downlink-1m-drop-ab-5500ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624/rep03-downlink-1m-drop-ab-6000ms \
  --output docs/results/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624.md \
  --csv-output data/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624.csv
```

현재 관찰된 기준:

- 5000ms downlink는 `2/3 PASS`
- 5500ms downlink는 `2/3 PASS`
- 6000ms downlink는 `0/3 PASS`
- 모든 row가 qlog H3/path evidence를 남겼으므로, downlink DOM completion도 transport evidence와 별도로 봐야 한다.

## 26. Chrome local upload fine boundary 재현

5000ms에서 upload만 반복 실패했으므로, upload workload만 더 촘촘하게 측정한다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-transient-upload-fine-boundary-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-transient-upload-fine-boundary-20260624 \
BASE_PORT=7500 \
REBIND_AFTER=500ms \
TIMEOUT=42s \
CHROME_TIMEOUT_SECONDS=36 \
CHROME_HOLD_SECONDS=18 \
REPETITIONS=3 \
DROP_WINDOWS_MS="4600 4750 4900 5000" \
WORKLOADS="upload" \
./scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh
```

논문용 summary 등록:

```bash
cd ../..
python3 tools/summarize_chrome_rebinding_transient_return_path_sweep.py \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-fine-boundary-20260624/rep01-upload-1m-drop-ab-4600ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-fine-boundary-20260624/rep01-upload-1m-drop-ab-4750ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-fine-boundary-20260624/rep01-upload-1m-drop-ab-4900ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-fine-boundary-20260624/rep01-upload-1m-drop-ab-5000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-fine-boundary-20260624/rep02-upload-1m-drop-ab-4600ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-fine-boundary-20260624/rep02-upload-1m-drop-ab-4750ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-fine-boundary-20260624/rep02-upload-1m-drop-ab-4900ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-fine-boundary-20260624/rep02-upload-1m-drop-ab-5000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-fine-boundary-20260624/rep03-upload-1m-drop-ab-4600ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-fine-boundary-20260624/rep03-upload-1m-drop-ab-4750ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-fine-boundary-20260624/rep03-upload-1m-drop-ab-4900ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-fine-boundary-20260624/rep03-upload-1m-drop-ab-5000ms \
  --output docs/results/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.md \
  --csv-output data/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.csv
```

현재 관찰된 기준:

- 4600ms upload는 `3/3 PASS`
- 4750ms upload는 `1/3 PASS`
- 4900ms와 5000ms upload는 `6/6 FAIL`
- 이 결과도 local upload-specific transition-zone control이며 public handover evidence가 아니다.

## 27. Chrome local upload retry recovery boundary 재현

4900ms/5000ms upload는 no-retry 조건에서 반복 실패했으므로, 동일한 outage window에서 application-level retry가 작업 완료를 회복하는지 확인한다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-transient-upload-retry-boundary-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-transient-upload-retry-boundary-20260624 \
BASE_PORT=7900 \
REBIND_AFTER=500ms \
TIMEOUT=52s \
CHROME_TIMEOUT_SECONDS=46 \
CHROME_HOLD_SECONDS=24 \
REPETITIONS=3 \
DROP_WINDOWS_MS="4900 5000" \
WORKLOADS="upload" \
UPLOAD_RETRY_ATTEMPTS=1 \
UPLOAD_RETRY_DELAY_MS=1000 \
EXPECTED_REQUESTS=3 \
./scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh
```

논문용 summary 등록:

```bash
cd ../..
python3 tools/summarize_chrome_rebinding_transient_return_path_sweep.py \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-boundary-20260624/rep01-upload-1m-drop-ab-4900ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-boundary-20260624/rep01-upload-1m-drop-ab-5000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-boundary-20260624/rep02-upload-1m-drop-ab-4900ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-boundary-20260624/rep02-upload-1m-drop-ab-5000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-boundary-20260624/rep03-upload-1m-drop-ab-4900ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-boundary-20260624/rep03-upload-1m-drop-ab-5000ms \
  --output docs/results/chrome-h3-rebinding-transient-upload-retry-boundary-20260624.md \
  --csv-output data/chrome-h3-rebinding-transient-upload-retry-boundary-20260624.csv
```

현재 관찰된 기준:

- 4900ms retry upload는 `3/3 PASS`
- 5000ms retry upload는 `3/3 PASS`
- 모든 row가 `/upload-sink` request 2개와 최종 1MiB 수신을 기록했다.
- 모든 row가 `nat_rebinding_multiple_quic_sessions`였으므로, 이는 application retry/reconnect recovery control이며 single-session browser CM success가 아니다.
- 이 결과도 local recovery control이며 public active handover evidence가 아니다.

## 28. Chrome local upload retry long outage 재현

동일한 retry strategy가 6000ms/9000ms처럼 더 긴 outage에서도 작업 완료를 회복하는지 확인한다. 9000ms row는 완료 시간이 길어지므로 Chrome hold/timeout과 server timeout을 더 길게 둔다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-transient-upload-retry-long-outage-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-transient-upload-retry-long-outage-20260624 \
BASE_PORT=8100 \
REBIND_AFTER=500ms \
TIMEOUT=75s \
CHROME_TIMEOUT_SECONDS=65 \
CHROME_HOLD_SECONDS=34 \
REPETITIONS=3 \
DROP_WINDOWS_MS="6000 9000" \
WORKLOADS="upload" \
UPLOAD_RETRY_ATTEMPTS=1 \
UPLOAD_RETRY_DELAY_MS=1000 \
EXPECTED_REQUESTS=3 \
./scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh
```

논문용 summary 등록:

```bash
cd ../..
python3 tools/summarize_chrome_rebinding_transient_return_path_sweep.py \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-long-outage-20260624/rep01-upload-1m-drop-ab-6000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-long-outage-20260624/rep01-upload-1m-drop-ab-9000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-long-outage-20260624/rep02-upload-1m-drop-ab-6000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-long-outage-20260624/rep02-upload-1m-drop-ab-9000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-long-outage-20260624/rep03-upload-1m-drop-ab-6000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-long-outage-20260624/rep03-upload-1m-drop-ab-9000ms \
  --output docs/results/chrome-h3-rebinding-transient-upload-retry-long-outage-20260624.md \
  --csv-output data/chrome-h3-rebinding-transient-upload-retry-long-outage-20260624.csv
```

현재 관찰된 기준:

- 6000ms retry upload는 `3/3 PASS`
- 9000ms retry upload는 `3/3 PASS`
- 6000ms row는 약 15.5초, 9000ms row는 약 19.7초에 완료됐다.
- Chrome target QUIC session count는 2-3개였으므로, 이 결과도 application retry/reconnect recovery control이며 single-session browser CM success가 아니다.

## 29. Chrome local upload retry stress boundary 재현

1회 retry recovery도 무제한 보장이 아니므로, 12000ms/15000ms에서 failure-side boundary를 확인한다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624 \
BASE_PORT=8300 \
REBIND_AFTER=500ms \
TIMEOUT=95s \
CHROME_TIMEOUT_SECONDS=85 \
CHROME_HOLD_SECONDS=45 \
REPETITIONS=3 \
DROP_WINDOWS_MS="12000 15000" \
WORKLOADS="upload" \
UPLOAD_RETRY_ATTEMPTS=1 \
UPLOAD_RETRY_DELAY_MS=1000 \
EXPECTED_REQUESTS=3 \
./scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh
```

논문용 summary 등록:

```bash
cd ../..
python3 tools/summarize_chrome_rebinding_transient_return_path_sweep.py \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624/rep01-upload-1m-drop-ab-12000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624/rep01-upload-1m-drop-ab-15000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624/rep02-upload-1m-drop-ab-12000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624/rep02-upload-1m-drop-ab-15000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624/rep03-upload-1m-drop-ab-12000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624/rep03-upload-1m-drop-ab-15000ms \
  --output docs/results/chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624.md \
  --csv-output data/chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624.csv
```

현재 관찰된 기준:

- 12000ms retry upload는 `3/3 PASS`
- 15000ms retry upload는 `0/3 PASS`
- 15000ms 실패 row는 DOM error timing이 15936-15943ms였고 두 번째 `/upload-sink`가 서버에 도달하지 못했다.
- 이 local 1MiB upload workload에서 1회 retry recovery boundary는 12초와 15초 사이로 관찰됐다.

## 30. Chrome local upload retry2 15000ms recovery 재현

1회 retry가 실패한 15000ms outage에서 retry budget을 2회로 늘려 application-level recovery가 어디까지 확장되는지 확인한다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-transient-upload-retry2-15000ms-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-transient-upload-retry2-15000ms-20260624 \
BASE_PORT=8500 \
WORKLOADS=upload \
DROP_WINDOWS_MS="15000" \
REPETITIONS=3 \
UPLOAD_RETRY_ATTEMPTS=2 \
UPLOAD_RETRY_DELAY_MS=1000 \
EXPECTED_REQUESTS=3 \
TIMEOUT=120s \
CHROME_TIMEOUT_SECONDS=105 \
CHROME_HOLD_SECONDS=65 \
./scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh
```

논문용 summary 등록:

```bash
cd ../..
python3 tools/summarize_chrome_rebinding_transient_return_path_sweep.py \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry2-15000ms-20260624/rep01-upload-1m-drop-ab-15000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry2-15000ms-20260624/rep02-upload-1m-drop-ab-15000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry2-15000ms-20260624/rep03-upload-1m-drop-ab-15000ms \
  --output docs/results/chrome-h3-rebinding-transient-upload-retry2-15000ms-20260624.md \
  --csv-output data/chrome-h3-rebinding-transient-upload-retry2-15000ms-20260624.csv
```

현재 관찰된 기준:

- 15000ms retry2 upload는 `3/3 PASS`
- DOM complete timing은 24484-24503ms였다.
- Chrome target QUIC session count는 4개였으므로, 이 결과는 retry/reconnect 기반 task recovery이며 single-session browser CM success가 아니다.
- 1회 retry 실패 region을 2회 retry가 회복했지만, recovery latency와 session churn cost가 함께 증가했다.

## 31. Chrome local upload retry2 stress boundary 재현

2회 retry recovery도 무제한 보장이 아니므로, 18000ms/21000ms에서 failure-side boundary를 확인한다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624 \
BASE_PORT=8600 \
WORKLOADS=upload \
DROP_WINDOWS_MS="18000 21000" \
REPETITIONS=3 \
UPLOAD_RETRY_ATTEMPTS=2 \
UPLOAD_RETRY_DELAY_MS=1000 \
EXPECTED_REQUESTS=2 \
TIMEOUT=160s \
CHROME_TIMEOUT_SECONDS=140 \
CHROME_HOLD_SECONDS=90 \
./scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh
```

논문용 summary 등록:

```bash
cd ../..
python3 tools/summarize_chrome_rebinding_transient_return_path_sweep.py \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624/rep01-upload-1m-drop-ab-18000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624/rep01-upload-1m-drop-ab-21000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624/rep02-upload-1m-drop-ab-18000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624/rep02-upload-1m-drop-ab-21000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624/rep03-upload-1m-drop-ab-18000ms \
  upload:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624/rep03-upload-1m-drop-ab-21000ms \
  --output docs/results/chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624.md \
  --csv-output data/chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624.csv
```

현재 관찰된 기준:

- 18000ms retry2 upload는 `3/3 PASS`
- 21000ms retry2 upload는 `3/3 FAIL`
- PASS row의 DOM complete timing은 28196-28199ms였고, FAIL row의 DOM error timing은 20950-20955ms였다.
- 모든 row의 Chrome target QUIC session count는 4개였으므로, 이 결과도 browser CM success가 아니라 application recovery boundary evidence다.

## 32. Application recovery tradeoff 표 재생성

no-retry, 1회 retry, 2회 retry upload boundary CSV를 논문용 tradeoff 표로 합친다.

```bash
python3 tools/build_application_recovery_tradeoff.py \
  --output docs/results/application-recovery-tradeoff-20260624.md \
  --csv-output data/application-recovery-tradeoff-20260624.csv
```

현재 관찰된 기준:

- no-retry 최신 all-pass window는 4600ms, first later all-fail window는 4900ms다.
- 1회 retry 최신 all-pass window는 12000ms, first later all-fail window는 15000ms다.
- 2회 retry 최신 all-pass window는 18000ms, first later all-fail window는 21000ms다.
- retry budget 증가는 recovery boundary를 오른쪽으로 이동시키지만 completion latency와 Chrome QUIC session count도 함께 증가한다.

## 33. Workload transition-zone 표 재생성

downlink/upload fine-boundary CSV를 workload-sensitive transition-zone 표로 합친다.

```bash
python3 tools/build_workload_transition_zone_table.py \
  --output docs/results/workload-transition-zone-synthesis-20260624.md \
  --csv-output data/workload-transition-zone-synthesis-20260624.csv
```

현재 관찰된 기준:

- downlink는 5000ms/5500ms에서 각각 2/3 PASS, 6000ms에서 0/3 PASS다.
- upload는 4600ms에서 3/3 PASS, 4750ms에서 1/3 PASS, 4900ms/5000ms에서 0/6 PASS다.
- workload direction에 따라 transition zone이 달라지므로 단일 threshold로 보고하지 않는다.

## 34. Chrome transient downlink retry boundary 재현

downlink page의 stream retry를 1회 허용해 6000ms/9000ms outage window에서 작업 완료가 회복되는지 확인한다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-transient-downlink-retry-boundary-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624 \
BASE_PORT=7600 \
DROP_WINDOWS_MS="6000 9000" \
WORKLOADS="downlink" \
DOWNLINK_RETRY_ATTEMPTS=1 \
DOWNLINK_RETRY_DELAY_MS=500 \
TIMEOUT=52s \
CHROME_TIMEOUT_SECONDS=42 \
CHROME_HOLD_SECONDS=26 \
./scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh
```

논문용 summary 등록:

```bash
python3 tools/summarize_chrome_rebinding_transient_return_path_sweep.py \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624/rep01-downlink-1m-drop-ab-6000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624/rep01-downlink-1m-drop-ab-9000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624/rep02-downlink-1m-drop-ab-6000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624/rep02-downlink-1m-drop-ab-9000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624/rep03-downlink-1m-drop-ab-6000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624/rep03-downlink-1m-drop-ab-9000ms \
  --output docs/results/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624.md \
  --csv-output data/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624.csv
```

현재 관찰된 기준:

- 6000ms/9000ms downlink retry control은 `6/6 PASS`였다.
- `retries_used=0` row가 3개, `retries_used=1` row가 3개였다.
- retry 미사용 PASS는 단일 Chrome target QUIC session으로 완료됐고, retry 사용 PASS는 target session 2개로 완료됐다.
- 따라서 이 결과는 retransmission-only completion과 application retry/multiple-session recovery를 분리해서 보고해야 한다.

## 35. Chrome transient downlink wait-only 및 comparison 재현

downlink retry control과 같은 6000ms/9000ms window, 같은 hold/grace 조건에서 retry만 끈다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-transient-downlink-wait-boundary-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-transient-downlink-wait-boundary-20260624 \
BASE_PORT=7800 \
DROP_WINDOWS_MS="6000 9000" \
WORKLOADS="downlink" \
DOWNLINK_RETRY_ATTEMPTS=0 \
DOWNLINK_RETRY_DELAY_MS=500 \
DOWNLINK_COMPLETION_GRACE_MS=17500 \
TIMEOUT=52s \
CHROME_TIMEOUT_SECONDS=42 \
CHROME_HOLD_SECONDS=26 \
./scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh
```

논문용 summary 등록:

```bash
python3 tools/summarize_chrome_rebinding_transient_return_path_sweep.py \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-wait-boundary-20260624/rep01-downlink-1m-drop-ab-6000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-wait-boundary-20260624/rep01-downlink-1m-drop-ab-9000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-wait-boundary-20260624/rep02-downlink-1m-drop-ab-6000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-wait-boundary-20260624/rep02-downlink-1m-drop-ab-9000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-wait-boundary-20260624/rep03-downlink-1m-drop-ab-6000ms \
  downlink:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-downlink-wait-boundary-20260624/rep03-downlink-1m-drop-ab-9000ms \
  --output docs/results/chrome-h3-rebinding-transient-downlink-wait-boundary-20260624.md \
  --csv-output data/chrome-h3-rebinding-transient-downlink-wait-boundary-20260624.csv
```

retry/wait comparison 재생성:

```bash
python3 tools/build_downlink_recovery_comparison.py \
  --output docs/results/downlink-recovery-comparison-20260624.md \
  --csv-output data/downlink-recovery-comparison-20260624.csv
```

현재 관찰된 기준:

- wait-only no-retry는 6000ms/9000ms 모두 `0/3 PASS`였다.
- retry-enabled control은 6000ms/9000ms 모두 `3/3 PASS`였다.
- wait-only 실패 row의 DOM error timing은 6923-6935ms로 모였다.
- 이 비교는 downlink recovery PASS가 단순한 wait-time artifact가 아님을 보여주지만, retry-enabled PASS 역시 single-session browser CM evidence는 아니다.

## 36. Chrome transient polling/dashboard boundary 재현

dashboard형 반복 fetch workload가 short outage에서 어떻게 보이는지 측정한다. 이 실험은 교수님 피드백의 "대시보드 데이터 갱신 복구 시간"류 지표를 transport CM과 분리해 다루기 위한 local control이다.

실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-transient-poll-boundary-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-transient-poll-boundary-20260624 \
BASE_PORT=9000 \
DROP_WINDOWS_MS="250 1500 3000" \
WORKLOADS="poll" \
POLL_COUNT=6 \
POLL_INTERVAL_MS=1000 \
POLL_COMPLETION_GRACE_MS=15000 \
EXPECTED_REQUESTS=2 \
TIMEOUT=45s \
CHROME_TIMEOUT_SECONDS=32 \
CHROME_HOLD_SECONDS=18 \
./scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh
```

논문용 summary 등록:

```bash
python3 tools/summarize_chrome_rebinding_transient_return_path_sweep.py \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-boundary-20260624/rep01-poll-1m-drop-ab-250ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-boundary-20260624/rep01-poll-1m-drop-ab-1500ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-boundary-20260624/rep01-poll-1m-drop-ab-3000ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-boundary-20260624/rep02-poll-1m-drop-ab-250ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-boundary-20260624/rep02-poll-1m-drop-ab-1500ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-boundary-20260624/rep02-poll-1m-drop-ab-3000ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-boundary-20260624/rep03-poll-1m-drop-ab-250ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-boundary-20260624/rep03-poll-1m-drop-ab-1500ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-boundary-20260624/rep03-poll-1m-drop-ab-3000ms \
  --output docs/results/chrome-h3-rebinding-transient-poll-boundary-20260624.md \
  --csv-output data/chrome-h3-rebinding-transient-poll-boundary-20260624.csv
```

현재 관찰된 기준:

- 250ms/1500ms/3000ms polling control은 모두 `3/3 PASS`였다.
- 각 row는 `GET /browser-poll` 1회와 `/poll` 6회를 합쳐 server request 7개를 남겼다.
- 모든 row가 server remote addr count 2와 Chrome target QUIC session count 2로 분류됐다.
- qlog PATH_CHALLENGE/PATH_RESPONSE count는 0/0이었으므로, 이 결과는 single-session browser CM success가 아니라 repeated fetch replacement/multiple-session continuity evidence다.

long-boundary 실행:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chrome-h3-rebinding-transient-poll-long-boundary-20260624 \
ARTIFACT_ROOT=artifacts/chrome-h3-rebinding-transient-poll-long-boundary-20260624 \
BASE_PORT=9200 \
DROP_WINDOWS_MS="4000 6000 9000" \
WORKLOADS="poll" \
POLL_COUNT=6 \
POLL_INTERVAL_MS=1000 \
POLL_COMPLETION_GRACE_MS=22000 \
EXPECTED_REQUESTS=2 \
TIMEOUT=60s \
CHROME_TIMEOUT_SECONDS=42 \
CHROME_HOLD_SECONDS=28 \
./scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh
```

long-boundary summary 등록:

```bash
python3 tools/summarize_chrome_rebinding_transient_return_path_sweep.py \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-long-boundary-20260624/rep01-poll-1m-drop-ab-4000ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-long-boundary-20260624/rep01-poll-1m-drop-ab-6000ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-long-boundary-20260624/rep01-poll-1m-drop-ab-9000ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-long-boundary-20260624/rep02-poll-1m-drop-ab-4000ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-long-boundary-20260624/rep02-poll-1m-drop-ab-6000ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-long-boundary-20260624/rep02-poll-1m-drop-ab-9000ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-long-boundary-20260624/rep03-poll-1m-drop-ab-4000ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-long-boundary-20260624/rep03-poll-1m-drop-ab-6000ms \
  poll:repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-poll-long-boundary-20260624/rep03-poll-1m-drop-ab-9000ms \
  --output docs/results/chrome-h3-rebinding-transient-poll-long-boundary-20260624.md \
  --csv-output data/chrome-h3-rebinding-transient-poll-long-boundary-20260624.csv
```

현재 관찰된 기준:

- 4000ms polling은 `1/3 PASS`로 혼재했다.
- 6000ms/9000ms polling은 모두 `0/3 PASS`였다.
- 실패 row는 `/browser-poll`과 첫 `/poll`까지만 서버에 도달했고 DOM `pollComplete`가 false였다.
- 유일한 4000ms PASS row도 Chrome target QUIC session count가 2였으므로 single-session browser CM success가 아니다.

polling transition-zone synthesis 재생성:

```bash
python3 tools/build_polling_transition_zone_table.py \
  --output docs/results/polling-transition-zone-synthesis-20260624.md \
  --csv-output data/polling-transition-zone-synthesis-20260624.csv
```

현재 관찰된 기준:

- polling workload는 3000ms까지 9/9 PASS였다.
- 4000ms는 1/3 PASS로 transition zone이다.
- 6000ms/9000ms는 0/6 PASS로 반복 실패 구간이다.
- 모든 PASS row가 Chrome target QUIC session 2개였으므로, dashboard continuity는 session attribution과 함께 보고해야 한다.

## 37. Paper claim support matrix 재생성

논문 문장을 쓰기 전, 현재 CSV 결과가 뒷받침하는 claim과 아직 금지해야 할 claim을 분리한다.

```bash
python3 tools/build_paper_claim_support_matrix.py \
  --output docs/results/paper-claim-support-matrix-20260624.md \
  --csv-output data/paper-claim-support-matrix-20260624.csv
```

성공 기준:

- `supported_scoped` claim은 구현체 survey, quic-go direct-origin, AWS NLB controlled 실험처럼 범위가 명확한 positive evidence다.
- `supported_local_control` claim은 Chrome forced-H3 local UDP rebinding control에 한정한다.
- `negative_control_supported` claim은 HTTP/3 지원, tuple change, qlog event, browser session evidence가 각각 단독으로는 충분하지 않다는 방어 근거다.
- `not_supported_yet` claim은 최종 browser/mobile active handover protocol이 채워지기 전까지 초록이나 결론에서 성공으로 쓰면 안 된다.

현재 관찰된 기준:

- controlled implementation/deployment claim은 논문에 제한적으로 쓸 수 있다.
- workload boundary와 application retry recovery는 local control 결과로 쓸 수 있다.
- Chrome/Safari/Android 실제 Wi-Fi/LTE handover 성공 claim은 아직 pending이다.

## 38. Replication sufficiency audit 재생성

local 반복 실험의 반복수가 논문 문장 강도를 얼마나 뒷받침하는지 계산한다.

```bash
python3 tools/build_replication_sufficiency_audit.py \
  --output docs/results/replication-sufficiency-audit-20260624.md \
  --csv-output data/replication-sufficiency-audit-20260624.csv
```

성공 기준:

- 각 조건별 `PASS/runs`와 Wilson 95% confidence interval이 생성된다.
- all-pass row는 `stable_candidate`, all-fail row는 `failure_candidate`, mixed row는 `transition_zone`으로 분류된다.
- n이 작은 all-pass/all-fail row에는 strong local condition wording을 위해 필요한 추가 반복수가 계산된다.

현재 관찰된 기준:

- n=3 all-pass/all-fail row는 방향성 근거로는 유용하지만 reliability probability나 guarantee로 쓰기에는 부족하다.
- mixed row는 threshold가 아니라 transition zone 근거로 써야 한다.
- 본 audit는 새 실험 결과를 만들지 않고, 기존 local control 결과의 논문 표현 강도를 제한한다.

## 39. Replication run plan 재생성

replication sufficiency audit를 기반으로 추가 local 반복 실험 우선순위를 생성한다.

```bash
python3 tools/build_replication_run_plan.py \
  --input data/replication-sufficiency-audit-20260624.csv \
  --output docs/results/replication-run-plan-20260624.md \
  --csv-output data/replication-run-plan-20260624.csv
```

성공 기준:

- P0는 final controlled-public/browser handover protocol로 유지된다.
- L1은 mixed transition-zone row를 우선 반복 대상으로 둔다.
- L2는 논문에서 더 강한 local reliability wording이 필요할 때만 boundary anchor row를 반복 대상으로 둔다.

현재 관찰된 기준:

- public/browser handover가 열리면 local 반복보다 그 실험이 우선이다.
- public/browser handover가 계속 blocked라면 L1 transition-zone row가 가장 높은 가치의 local 반복 대상이다.
- L2 anchor row는 선택 사항이며, 현재 논문 표현을 guarantee나 probability로 높일 때만 필요하다.

## 40. P0 unblock status 재생성

final protocol readiness matrix에서 P0 controlled-public/browser handover를 막는 gate를 압축한다.

```bash
python3 tools/build_p0_unblock_status.py \
  --matrix data/final-protocol-readiness-matrix-20260624.csv \
  --scorecard data/final-trial-acceptance-scorecard-20260624.csv \
  --output docs/results/p0-unblock-status-20260624.md \
  --csv-output data/p0-unblock-status-20260624.csv
```

성공 기준:

- next trial이 `controlled-public-chrome-h3-baseline-001`로 표시된다.
- next trial을 직접 막는 gate는 `needed-now`로 표시된다.
- active network-change 전용 gate는 baseline 이후 단계로 남는다.

현재 관찰된 기준:

- `controlled_public_config_present`, `public_origin_host_configured`, `public_origin_url_configured`, `tls_config_present`가 P0 baseline을 막는 now gate다.
- `baseline_summary_ready`, `network_change_command_present`, `desktop_secondary_path_ready`는 baseline 등록 이후 active trial gate다.

## 41. P0 baseline execution packet 재생성

P0 baseline trial을 private config 작성부터 artifact 등록까지 stage별로 실행 가능한 패킷으로 만든다.

```bash
python3 tools/build_p0_baseline_execution_packet.py \
  --matrix data/final-protocol-readiness-matrix-20260624.csv \
  --scorecard data/final-trial-acceptance-scorecard-20260624.csv \
  --output docs/results/p0-baseline-execution-packet-20260624.md \
  --csv-output data/p0-baseline-execution-packet-20260624.csv
```

성공 기준:

- stage 0은 private config 작성이고, needed-now gate가 남아 있으면 blocked다.
- stage 1은 preflight이며, required gate가 남아 있으면 server/client capture로 넘어가지 않는다.
- stage 2 이후는 origin server, browser client, artifact validation, CSV append 순서를 유지한다.

현재 관찰된 기준:

- P0 baseline은 아직 `blocked_by_readiness`다.
- server/client capture는 private config와 public origin baseline preflight가 통과한 뒤에만 실행해야 한다.

## 42. Artifact 정책

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
