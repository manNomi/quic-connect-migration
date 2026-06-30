# Chapter 3 Reference And Evidence

작성일: `2026-06-30`

이 문서는 Chapter 3 “구현체 Positive Control”의 실제 구현 코드, 실행 스크립트, 결과 문서, 외부 구현체 링크를 정리한다. 목적은 “controlled implementation에서는 CM이 된다”는 주장을 과장하지 않고, 어떤 근거가 현재 repo에 있고 어떤 근거는 요약 문서로만 남아 있는지 분리하는 것이다.

## 1. 현재 repo의 재현 코드

| 역할 | 링크 | 설명 |
| --- | --- | --- |
| quic-go client | [repro/quic-go-min-repro/cmd/client/main.go](../../repro/quic-go-min-repro/cmd/client/main.go) | UDP socket A로 dial, socket B 추가, `AddPath`, `Probe`, `Switch`, after payload 전송 |
| quic-go server | [repro/quic-go-min-repro/cmd/server/main.go](../../repro/quic-go-min-repro/cmd/server/main.go) | 같은 accepted QUIC connection에서 before/after stream payload 수신 |
| local run script | [repro/quic-go-min-repro/scripts/run-local-happy-path.sh](../../repro/quic-go-min-repro/scripts/run-local-happy-path.sh) | server/client 실행, qlog/keylog/result 생성 |
| harness wrapper | [harness/scripts/run-local-quic-go.sh](../../harness/scripts/run-local-quic-go.sh) | repo-level local quic-go run wrapper |
| artifact validator | [harness/scripts/validate-quic-go-artifacts.sh](../../harness/scripts/validate-quic-go-artifacts.sh) | client/server `ok=true`와 qlog path validation evidence 검사 |
| qlog scanner | [tools/scan_qlog_events.py](../../tools/scan_qlog_events.py) | `.sqlog`에서 `path_challenge`, `path_response`, packet event count 요약 |
| scanner trigger map | [tables/chapter-03-scanner-trigger-map-20260630.md](tables/chapter-03-scanner-trigger-map-20260630.md) | client/server/runner/validator/qlog trigger line anchor |
| HTTP/3 client extension | [repro/quic-go-min-repro/cmd/h3client/main.go](../../repro/quic-go-min-repro/cmd/h3client/main.go) | HTTP/3 workload에서 active path switch를 수행하는 확장 client |
| HTTP/3 server extension | [repro/quic-go-min-repro/cmd/h3server/main.go](../../repro/quic-go-min-repro/cmd/h3server/main.go) | upload/download/browser workload를 제공하는 H3 server |
| LSQUIC preferred-address runner | [harness/scripts/run-lsquic-preferred-address-demo.sh](../../harness/scripts/run-lsquic-preferred-address-demo.sh) | LSQUIC `http_client`/`http_server` preferred-address app demo 재현 |
| LSQUIC NAT rebinding runner | [harness/scripts/run-lsquic-nat-rebinding-demo.sh](../../harness/scripts/run-lsquic-nat-rebinding-demo.sh) | LSQUIC `http_client`/`http_server` local UDP proxy NAT rebinding app demo 재현 |
| nginx QUIC active migration runner | [harness/scripts/run-nginx-quic-active-migration-demo.sh](../../harness/scripts/run-nginx-quic-active-migration-demo.sh) | nginx HTTP/3 server와 quiche client active migration runtime demo 재현 |

## 2. quic-go Fresh Rerun

이번 Chapter 3 정리 중 fresh rerun을 수행했다.

```bash
RUN_ID=chapter3-local-quic-go-rerun-20260630 \
PORT=4243 \
PAYLOAD_BYTES=1048576 \
harness/scripts/run-local-quic-go.sh
```

검증 결과:

| evidence | 결과 |
| --- | --- |
| run id | `chapter3-local-quic-go-rerun-20260630` |
| command exit | `0` |
| harness validation | `validation=ok` |
| client `ok` | `true` |
| server `ok` | `true` |
| before payload | 1 MiB, checksum matched |
| after payload | 1 MiB, checksum matched |
| validation-before-switch | `path not yet validated` |
| qlog client path frames | `path_challenge=2`, `path_response=2` |
| qlog server path frames | `path_challenge=2`, `path_response=2` |

Raw artifact는 `harness/results/chapter3-local-quic-go-rerun-20260630` 아래에 생성되었지만, `harness/results/`는 ignored artifact path라 commit하지 않는다.

## 3. 추가 구현체 Fresh Rerun

quic-go만 강하게 검수했다는 약점을 줄이기 위해 2026-06-30에 10개 구현체를 현재 HEAD 기준으로 다시 실행했고, quicly는 partial build/unit evidence를 추가로 확보했다.

| 구현체 | source commit | local command group | result | local artifact |
| --- | --- | --- | --- | --- |
| Cloudflare quiche | `c4c0b978461aa153399a90217d85bebd1800f84d` | `cargo test -p quiche --lib migration --features qlog`, sample client/server migration | `8 passed`, sample client exit `0` | `harness/results/impl-rerun-20260630T070249Z/logs/quiche-cargo-test-migration.log`, `harness/results/impl-rerun-20260630T070249Z/quiche-local-success` |
| picoquic | `d3a80307200d28c53a6470d257bdd0801fad7971` | `picoquic_ct` selected migration suite | `Tried 13 tests, 0 fails` | `harness/results/impl-rerun-20260630T070249Z/logs/picoquic-migration-tests.log` |
| s2n-quic | `0f5a4f8ae4163f1b84e72cd29ad110ad99d7efd1` | `cargo test -p s2n-quic-tests connection_migration` | `10 passed; 0 failed` | `harness/results/impl-rerun-20260630T070249Z/logs/s2n-quic-connection-migration-tests.log` |
| LiteSpeed LSQUIC | `f8ebaf838d2f4db836bda1182ee35b05d5191cee` | full CTest 79/79 plus selected `trapa`, `qlog`, `parse_packet_in`, `frame_reader`, `packet_out` tests; preferred-address app demo; NAT rebinding app demo | `100% tests passed, 0 tests failed out of 79`; selected 5/5 PASS; preferred-address demo `validation=ok`; NAT rebinding demo `validation=ok` | `harness/results/impl-rerun-20260630T070249Z/logs/lsquic-*.log`, `harness/results/lsquic-preferred-address-script-20260630T095500Z`, `harness/results/lsquic-nat-rebinding-demo-20260630T102751Z` |
| nginx QUIC | `072f6fdbac3323fab257280b7119224027b01315` | nginx HTTP/3 server runtime demo with quiche `--enable-active-migration --perform-migration` | `validation=ok`, response bytes `1048576`, server path seq:1 created/validated | `harness/results/nginx-quic-active-migration-20260630T104724Z` |
| MsQuic | `51d449b7d2deb553d6503591f72a8e62d1071054` | build `msquictest`, selected v4/v6 RebindPort/RebindAddr/PathValidation tests | `8 passed; 0 failed` | `harness/results/impl-rerun-20260630T070249Z/logs/msquic-rebind-pathvalidation-tests.log`, `harness/results/impl-rerun-20260630T070249Z/logs/msquic-rebind-pathvalidation-v6-tests.log` |
| ngtcp2 | `c24b12690c5bdf7ad2715ae427504e76bf5c6ffc` | selected `tests/main` migration/path-validation tests | `6 of 6 tests successful` | `harness/results/impl-rerun-20260630T070249Z/logs/ngtcp2-migration-tests.log` |
| aioquic | `6d36838d008c2202c337142fa07e8bf80e96bac8` | selected `unittest` path challenge/transport parameter tests | `Ran 9 tests ... OK` | `harness/results/impl-rerun-20260630T070249Z/logs/aioquic-migration-tests.log` |
| Quinn | `953b466747e667a9dfda0596b8051a0644f8333d` | `cargo test -p quinn-proto migration`, `cargo test -p quinn rebind` | `1 passed`, `1 passed` | `harness/results/impl-rerun-20260630T070249Z/logs/quinn-proto-migration-tests.log`, `harness/results/impl-rerun-20260630T070249Z/logs/quinn-rebind-tests.log` |
| Neqo | `3ba227d37f46a5684e984ead831b73344d9fec63` | `cargo test -p neqo-transport migration` | `53 passed; 0 failed` | `harness/results/impl-rerun-20260630T070249Z/logs/neqo-transport-migration-tests.log` |
| XQUIC | `96155cffbde7f062fe45ac3f6899f47e25709d30` | build `test_client`/`test_server`, manual NAT rebinding demo path 0 and path 1 | client exits `0`, rebinding evidence counts `2` and `1`, pass markers `2` and `2`; full `run_tests` build partial on macOS | `harness/results/impl-rerun-20260630T070249Z/logs/xquic-*.log`, `harness/results/impl-rerun-20260630T070249Z/xquic-nat-rebinding` |
| quicly | `ed83c7c7d545a01650651c9523466f561ec5d4bb` | build `test.t`/`cli`/`udpfw`, run `test.t`, attempt `t/e2e.t` | migration-related unit subtests `ok`; full `test.t` partial due unrelated `lossy`; e2e blocked by missing `Net::EmptyPort` | `harness/results/impl-rerun-20260630T070249Z/logs/quicly-*.log` |

상세 명령과 해석:

- [docs/results/implementation-rerun-results-20260630.md](../results/implementation-rerun-results-20260630.md)

## 4. qlog Validator Fix

fresh run 중 첫 validation은 실패했다.

```text
validation=fail
reason=missing qlog path validation evidence
```

실제 원인은 migration 실패가 아니었다. `.sqlog` 파일이 ignored artifact path 아래에 있어 `rg`가 기본 ignore rule로 qlog 파일을 스캔하지 않았다. `tools/scan_qlog_events.py`와 `grep -a`로 확인하면 path frames가 존재했다.

수정:

```text
rg --no-ignore --text -n "path_challenge|path_response" "$ARTIFACT_DIR/qlog"
```

수정한 파일:

- [harness/scripts/validate-quic-go-artifacts.sh](../../harness/scripts/validate-quic-go-artifacts.sh)
- [repro/quic-go-min-repro/scripts/run-local-happy-path.sh](../../repro/quic-go-min-repro/scripts/run-local-happy-path.sh)
- [repro/quic-go-min-repro/scripts/run-ec2-client.sh](../../repro/quic-go-min-repro/scripts/run-ec2-client.sh)
- [repro/quic-go-min-repro/scripts/run-h3-client.sh](../../repro/quic-go-min-repro/scripts/run-h3-client.sh)
- [repro/quic-go-min-repro/scripts/run-local-h3-midflight.sh](../../repro/quic-go-min-repro/scripts/run-local-h3-midflight.sh)

## 5. 외부 구현체 링크

| 구현체 | official/source link | Chapter 3에서의 역할 |
| --- | --- | --- |
| quic-go | [GitHub](https://github.com/quic-go/quic-go), [Connection Migration docs](https://quic-go.net/docs/quic/connection-migration/) | active migration positive control |
| Cloudflare quiche | [GitHub](https://github.com/cloudflare/quiche), [Connection API docs](https://docs.rs/quiche/latest/quiche/struct.Connection.html) | path event/qlog 교차검증 후보 |
| picoquic | [GitHub](https://github.com/private-octopus/picoquic) | NAT rebinding, migration failure, preferred address edge-case 기준선 |
| s2n-quic | [GitHub](https://github.com/aws/s2n-quic), [official docs](https://aws.github.io/s2n-quic/) | AWS/NLB 후보, migration tests |
| LiteSpeed LSQUIC | [GitHub](https://github.com/litespeedtech/lsquic), [official LSQUIC page](https://www.litespeedtech.com/open-source/quic-http3-library) | server-stack unit evidence, preferred-address app demo evidence, NAT rebinding app demo evidence |
| nginx QUIC | [GitHub](https://github.com/nginx/nginx), [HTTP/3 module docs](https://nginx.org/en/docs/http/ngx_http_v3_module.html) | web-server runtime evidence for active client migration handling |
| MsQuic | [GitHub](https://github.com/microsoft/msquic), [official docs](https://microsoft.github.io/msquic/), [deployment docs](https://microsoft.github.io/msquic/msquicdocs/docs/Deployment.html) | production-relevant NAT rebind/path-validation evidence with LB caveat |
| aioquic | [GitHub](https://github.com/aiortc/aioquic), [official docs](https://aioquic.readthedocs.io/) | Python readable passive/path-validation reference |
| ngtcp2 | [GitHub](https://github.com/ngtcp2/ngtcp2), [official site](https://nghttp2.org/ngtcp2/) | C library primitive comparison |
| Quinn | [GitHub](https://github.com/quinn-rs/quinn), [docs.rs](https://docs.rs/quinn/latest/quinn/) | Rust stack comparison |
| Neqo | [GitHub](https://github.com/mozilla/neqo) | Firefox-adjacent transport stack comparison |
| XQUIC | [GitHub](https://github.com/alibaba/xquic) | NAT rebinding client/server demo evidence |
| quicly | [GitHub](https://github.com/h2o/quicly) | partial path validation/path promotion primitive evidence |

구현체별 source trigger 위치는 Chapter 1 scanner table에 고정되어 있다.

- [tables/scanner-trigger-summary-20260630.md](tables/scanner-trigger-summary-20260630.md)

## 6. 기존 결과 문서와 현재 artifact 상태

| 항목 | 링크/상태 | 해석 |
| --- | --- | --- |
| local implementation summary | [docs/results/local-implementation-test-results.md](../results/local-implementation-test-results.md) | 8개 구현체 로컬 실행 요약 |
| implementation fresh rerun summary | [docs/results/implementation-rerun-results-20260630.md](../results/implementation-rerun-results-20260630.md) | 2026-06-30 현재 HEAD 기준 quiche/picoquic/s2n-quic/MsQuic/LSQUIC/ngtcp2/aioquic/Quinn/Neqo/XQUIC 재실행과 quicly partial 요약 |
| LSQUIC preferred-address app demo | [docs/results/lsquic-preferred-address-app-demo-20260630.md](../results/lsquic-preferred-address-app-demo-20260630.md) | LSQUIC example HTTP/3 client/server에서 preferred-address migration path와 app data on path 1 확인 |
| LSQUIC NAT rebinding app demo | [docs/results/lsquic-nat-rebinding-app-demo-20260630.md](../results/lsquic-nat-rebinding-app-demo-20260630.md) | LSQUIC example HTTP/3 client/server에서 local UDP proxy source-port rebinding, server new path recording, path validation 확인 |
| nginx QUIC active migration runtime demo | [docs/results/nginx-quic-active-migration-runtime-20260630.md](../results/nginx-quic-active-migration-runtime-20260630.md) | nginx HTTP/3 server에서 quiche active source-port migration, server path seq:1 validation, 1MiB response completion 확인 |
| quic-go minimum reproduction summary | [docs/results/quic-go-minimum-reproduction-results.md](../results/quic-go-minimum-reproduction-results.md) | quic-go active migration 최소 재현 요약 |
| quic-go fresh artifact | `harness/results/chapter3-local-quic-go-rerun-20260630` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음 |
| quiche fresh artifact | `harness/results/impl-rerun-20260630T070249Z/quiche-local-success` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음 |
| picoquic fresh artifact | `harness/results/impl-rerun-20260630T070249Z/logs/picoquic-migration-tests.log` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음 |
| s2n-quic fresh artifact | `harness/results/impl-rerun-20260630T070249Z/logs/s2n-quic-connection-migration-tests.log` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음 |
| LSQUIC fresh artifact | `harness/results/impl-rerun-20260630T070249Z/logs/lsquic-*.log`, `harness/results/impl-rerun-20260630T070249Z/results/lsquic-commit.txt` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음. full CTest 79/79와 selected CTest 5/5 PASS |
| LSQUIC preferred-address app demo artifact | `harness/results/lsquic-preferred-address-script-20260630T095500Z` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음. `validation=ok`, path 1 HTTP/3 STREAM evidence |
| LSQUIC NAT rebinding app demo artifact | `harness/results/lsquic-nat-rebinding-demo-20260630T102751Z` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음. `validation=ok`, `proxy_switched=true`, server `record new path ID 1`, path validation evidence |
| nginx QUIC runtime demo artifact | `harness/results/nginx-quic-active-migration-20260630T104724Z` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음. `validation=ok`, `GET /file-1M HTTP/3.0` 200, server path seq:1 created/validated |
| MsQuic fresh artifact | `harness/results/impl-rerun-20260630T070249Z/logs/msquic-*.log` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음 |
| ngtcp2 fresh artifact | `harness/results/impl-rerun-20260630T070249Z/logs/ngtcp2-migration-tests.log` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음 |
| aioquic fresh artifact | `harness/results/impl-rerun-20260630T070249Z/logs/aioquic-migration-tests.log` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음 |
| Quinn fresh artifact | `harness/results/impl-rerun-20260630T070249Z/logs/quinn-proto-migration-tests.log`, `harness/results/impl-rerun-20260630T070249Z/logs/quinn-rebind-tests.log` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음 |
| Neqo fresh artifact | `harness/results/impl-rerun-20260630T070249Z/logs/neqo-transport-migration-tests.log` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음 |
| XQUIC fresh artifact | `harness/results/impl-rerun-20260630T070249Z/logs/xquic-*.log`, `harness/results/impl-rerun-20260630T070249Z/xquic-nat-rebinding` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음. full `run_tests`는 macOS AppleClang `-Werror`로 partial |
| quicly partial artifact | `harness/results/impl-rerun-20260630T070249Z/logs/quicly-*.log` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음. full unit/e2e PASS가 아니라 partial |

## 7. 재현 명령 묶음

현재 repo에서 즉시 재현 가능한 최소 명령:

```bash
RUN_ID=chapter3-local-quic-go-rerun-$(date -u +%Y%m%dT%H%M%SZ) \
PORT=4243 \
PAYLOAD_BYTES=1048576 \
harness/scripts/run-local-quic-go.sh
```

qlog만 별도 요약:

```bash
python3 tools/scan_qlog_events.py harness/results/<RUN_ID>/qlog
```

artifact validation만 재실행:

```bash
harness/scripts/validate-quic-go-artifacts.sh harness/results/<RUN_ID>
```

LSQUIC preferred-address app demo:

```bash
RUN_ID=lsquic-preferred-address-$(date -u +%Y%m%dT%H%M%SZ) \
harness/scripts/run-lsquic-preferred-address-demo.sh
```

LSQUIC NAT rebinding app demo:

```bash
RUN_ID=lsquic-nat-rebinding-$(date -u +%Y%m%dT%H%M%SZ) \
harness/scripts/run-lsquic-nat-rebinding-demo.sh
```

nginx QUIC active migration runtime demo:

```bash
RUN_ID=nginx-quic-active-migration-$(date -u +%Y%m%dT%H%M%SZ) \
harness/scripts/run-nginx-quic-active-migration-demo.sh
```

외부 구현체 재현 명령은 [implementation-rerun-results-20260630.md](../results/implementation-rerun-results-20260630.md)의 구현체별 command block을 따른다.

## 8. 검수 체크리스트

| 항목 | 판정 | 근거 |
| --- | --- | --- |
| 현재 repo에서 최소 positive control이 재실행되는가? | PASS | `chapter3-local-quic-go-rerun-20260630` |
| quic-go 외 구현체도 fresh rerun을 확보했는가? | PASS | quiche, picoquic, s2n-quic, MsQuic, LSQUIC, nginx QUIC, ngtcp2, aioquic, Quinn, Neqo, XQUIC NAT rebinding demo |
| LSQUIC app-level demo를 확보했는가? | PASS | preferred-address demo `validation=ok`, NAT rebinding demo `validation=ok`, path validation evidence |
| nginx server runtime demo를 확보했는가? | PASS | active migration runtime demo `validation=ok`, server path seq:1 created/validated |
| partial evidence를 분리했는가? | PASS | quicly는 `fresh_build_partial_20260630`으로 분리 |
| qlog path validation false negative를 제거했는가? | PASS | validator와 qlog-producing scripts에 `--no-ignore --text` 적용 |
| 외부 구현체 링크가 있는가? | PASS | 11개 구현체 official/source/docs link 포함 |
| raw artifact 한계를 명시했는가? | PASS | raw logs는 ignored path에 보존하고 공개 문서에는 commit/command/result를 남김 |
| browser handover claim과 분리했는가? | PASS | 이 챕터는 implementation positive control로만 해석 |
