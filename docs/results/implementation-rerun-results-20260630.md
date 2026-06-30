# Implementation Rerun Results

작성일: `2026-06-30`

## 1. 왜 quic-go만 먼저 강하게 검수했는가

Chapter 3의 1차 목적은 모든 구현체를 동일 깊이로 평가하는 것이 아니라, 이후 browser/public handover 실험을 해석하기 위한 transport positive control을 먼저 확보하는 것이었다.

quic-go를 먼저 고른 이유는 다음과 같다.

| 이유 | 설명 |
| --- | --- |
| active migration API가 명확함 | `AddPath -> Probe -> Switch` 흐름을 실험자가 직접 트리거할 수 있다. |
| HTTP/3 harness와 연결이 쉬움 | 같은 repo 안에서 local, EC2, browser workload까지 확장하기 쉬웠다. |
| qlog와 payload continuity를 함께 확인 가능 | `PATH_CHALLENGE`, `PATH_RESPONSE`, remote tuple 변화, before/after payload checksum을 한 번에 묶을 수 있었다. |
| 이후 실험의 기준점 필요 | browser 실패를 "CM 자체가 구현되지 않아서"라고 오해하지 않게 하는 최소 positive control이 필요했다. |

다만 이 선택은 Chapter 3의 한계도 만든다. quic-go만 fresh artifact가 있으면 "다른 구현체는 직접 검수하지 않은 것 아닌가?"라는 질문이 남는다. 그래서 2026-06-30에 주요 구현체를 현재 HEAD 기준으로 다시 실행해 cross-implementation evidence를 보강했다.

## 2. Fresh Rerun 요약

실행 위치:

| 항목 | 값 |
| --- | --- |
| clone/build workspace | `/private/tmp/quic-cm-impl-rerun-20260630` |
| local artifact root | `harness/results/impl-rerun-20260630T070249Z` |
| artifact policy | raw log는 ignored path에 보존하고, 공개 repo에는 요약 문서와 재현 명령을 남긴다. |

결과 요약:

| 구현체 | source commit | 실행 범위 | 결과 | claim strength |
| --- | --- | --- | --- | --- |
| quic-go | repo harness 기준 | active migration, `AddPath -> Probe -> Switch`, qlog, payload continuity | PASS | strong local positive control |
| Cloudflare quiche | `c4c0b978461aa153399a90217d85bebd1800f84d` | library migration tests, sample client/server migration, qlog | PASS | strong implementation positive control |
| picoquic | `d3a80307200d28c53a6470d257bdd0801fad7971` | NAT rebinding, migration, loss, failure, preferred address, disabled migration | PASS | broad edge-case maturity evidence |
| s2n-quic | `0f5a4f8ae4163f1b84e72cd29ad110ad99d7efd1` | `connection_migration` test suite, PathChallenge/PathResponse/event evidence | PASS | AWS-relevant library evidence |
| ngtcp2 | `c24b12690c5bdf7ad2715ae427504e76bf5c6ffc` | C library migration/path-validation/frame tests | PASS | primitive/API evidence |
| aioquic | `6d36838d008c2202c337142fa07e8bf80e96bac8` | PATH_CHALLENGE/PATH_RESPONSE and transport parameter tests | PASS | passive/path-validation reference |
| Quinn | `953b466747e667a9dfda0596b8051a0644f8333d` | `quinn-proto` migration, `quinn` endpoint rebind | PASS | Rust stack migration/rebind evidence |
| Neqo | `3ba227d37f46a5684e984ead831b73344d9fec63` | `neqo-transport` migration suite | PASS | Firefox-adjacent broad migration evidence |

## 3. 구현체별 실행 상세

### 3.1 Cloudflare quiche

Source:

- [cloudflare/quiche](https://github.com/cloudflare/quiche)

Commands:

```bash
cargo test -p quiche --lib migration --features qlog -- --nocapture
cargo build -p quiche_apps --bins --features qlog
RUST_LOG=info ./target/debug/quiche-server --cert apps/src/bin/cert.crt --key apps/src/bin/cert.key --root apps/src/bin/root --enable-active-migration --no-retry
RUST_LOG=info ./target/debug/quiche-client --no-verify --enable-active-migration --perform-migration https://localhost:<port>/
```

Evidence:

| 항목 | 결과 |
| --- | --- |
| library tests | `8 passed; 0 failed` |
| sample client exit | `0` |
| server log | `Seen new path`, `Path ... is now validated`, `Connection migrated` |
| qlog | `path_challenge`, `path_response` 확인 |
| local log | `harness/results/impl-rerun-20260630T070249Z/logs/quiche-cargo-test-migration.log` |
| sample artifact | `harness/results/impl-rerun-20260630T070249Z/quiche-local-success` |

Interpretation:

quiche는 quic-go 외에 실제 sample client/server에서 migration event와 qlog를 함께 확인한 두 번째 강한 positive control이다. 다만 browser나 CDN 성공을 의미하지는 않는다.

### 3.2 picoquic

Source:

- [private-octopus/picoquic](https://github.com/private-octopus/picoquic)

Commands:

```bash
cmake -S . -B build-local -G Ninja -DPICOQUIC_FETCH_PTLS=Y -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build-local --target picoquic_ct -j 4
./build-local/picoquic_ct -S <picoquic-source> -n -r \
  nat_rebinding nat_rebinding_loss nat_rebinding_zero nat_rebinding_fast \
  migration migration_with_loss migration_fail preferred_address preferred_address_zero \
  false_migration migration_disabled probe_api sockloop_migration
```

Evidence:

| 항목 | 결과 |
| --- | --- |
| selected tests | 13 |
| failures | 0 |
| covered cases | NAT rebinding, loss, zero CID, fast rebinding, migration failure, preferred address, disabled migration |
| local log | `harness/results/impl-rerun-20260630T070249Z/logs/picoquic-migration-tests.log` |

Interpretation:

picoquic은 단일 happy path보다 edge case coverage가 강하다. 논문에서는 "CM primitive가 여러 failure/control case와 함께 테스트되고 있다"는 성숙도 근거로 쓰는 것이 안전하다.

### 3.3 s2n-quic

Source:

- [aws/s2n-quic](https://github.com/aws/s2n-quic)
- [s2n-quic docs](https://aws.github.io/s2n-quic/)

Command:

```bash
cargo test -p s2n-quic-tests connection_migration -- --nocapture
```

Evidence:

| 항목 | 결과 |
| --- | --- |
| test result | `10 passed; 0 failed` |
| event evidence | `PathChallenge`, `PathResponse`, `path_challenge_updated: Validated`, `active_path_updated` |
| local log | `harness/results/impl-rerun-20260630T070249Z/logs/s2n-quic-connection-migration-tests.log` |

Interpretation:

s2n-quic은 AWS 연구 흐름과 연결성이 높다. 이 결과는 s2n-quic library가 migration/path validation primitive를 테스트한다는 근거지만, AWS NLB나 CloudFront 같은 managed path에서 end-to-end CM이 보장된다는 뜻은 아니다.

### 3.4 ngtcp2

Source:

- [ngtcp2/ngtcp2](https://github.com/ngtcp2/ngtcp2)
- [ngtcp2 official site](https://nghttp2.org/ngtcp2/)

Commands:

```bash
cmake -S . -B build-tests -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_TESTING=ON -DENABLE_LIB_ONLY=OFF
cmake --build build-tests --target main -j 4
./build-tests/tests/main \
  /conn/test_ngtcp2_conn_client_connection_migration \
  /conn/test_ngtcp2_conn_recv_path_challenge \
  /conn/test_ngtcp2_conn_disable_active_migration \
  /conn/test_ngtcp2_conn_path_validation \
  /pkt/test_ngtcp2_pkt_encode_path_challenge_frame \
  /pkt/test_ngtcp2_pkt_encode_path_response_frame
```

Evidence:

| 항목 | 결과 |
| --- | --- |
| selected tests | 6 |
| failures | 0 |
| covered cases | client connection migration, recv path challenge, disable active migration, path validation, frame encode |
| local log | `harness/results/impl-rerun-20260630T070249Z/logs/ngtcp2-migration-tests.log` |

Interpretation:

ngtcp2는 C library-level primitive 비교군으로 적합하다. 직접 웹 애플리케이션 continuity를 말하기보다는 RFC primitive 구현 성숙도 근거로 사용하는 편이 안전하다.

### 3.5 aioquic

Source:

- [aiortc/aioquic](https://github.com/aiortc/aioquic)
- [aioquic docs](https://aioquic.readthedocs.io/)

Commands:

```bash
python3 -m venv .venv
CFLAGS=-I/opt/homebrew/opt/openssl@3/include LDFLAGS=-L/opt/homebrew/opt/openssl@3/lib .venv/bin/python -m pip install -e .
.venv/bin/python -m unittest \
  tests.test_connection.QuicConnectionTest.test_handle_path_challenge_frame \
  tests.test_connection.QuicConnectionTest.test_handle_path_challenge_response_on_different_path \
  tests.test_connection.QuicConnectionTest.test_local_path_challenges_are_bounded \
  tests.test_connection.QuicConnectionTest.test_remote_path_challenges_are_bounded \
  tests.test_connection.QuicConnectionTest.test_handle_path_response_frame_bad \
  tests.test_packet.ParamsTest.test_params_disable_active_migration \
  tests.test_packet.ParamsTest.test_params_preferred_address \
  tests.test_packet.ParamsTest.test_preferred_address_ipv4_only \
  tests.test_packet.ParamsTest.test_preferred_address_ipv6_only
```

Evidence:

| 항목 | 결과 |
| --- | --- |
| selected tests | 9 |
| failures | 0 |
| covered cases | PATH_CHALLENGE/PATH_RESPONSE, challenge bounds, bad response, disable active migration, preferred address |
| local log | `harness/results/impl-rerun-20260630T070249Z/logs/aioquic-migration-tests.log` |

Interpretation:

aioquic은 readable Python implementation이라 path-validation behavior를 설명하기 좋다. 하지만 active migration public API 실험 후보로는 quic-go/quiche보다 약하므로 보조 근거로 분리한다.

### 3.6 Quinn

Source:

- [quinn-rs/quinn](https://github.com/quinn-rs/quinn)
- [Quinn docs.rs](https://docs.rs/quinn/latest/quinn/)

Commands:

```bash
cargo test -p quinn-proto migration -- --nocapture
cargo test -p quinn rebind -- --nocapture
```

Evidence:

| 항목 | 결과 |
| --- | --- |
| `quinn-proto` migration test | `1 passed; 0 failed` |
| `quinn` rebind test | `1 passed; 0 failed` |
| event evidence | `migration initiated`, `PATH_CHALLENGE`, `PATH_RESPONSE`, `new path validated` |
| local logs | `harness/results/impl-rerun-20260630T070249Z/logs/quinn-proto-migration-tests.log`, `harness/results/impl-rerun-20260630T070249Z/logs/quinn-rebind-tests.log` |

Interpretation:

Quinn은 Rust application stack 관점에서 migration and endpoint rebind behavior를 확인하는 비교군이다. quic-go처럼 현재 repo의 custom application payload harness까지 연결한 것은 아니지만, path validation event와 rebind receive path가 fresh rerun으로 확인되었다.

### 3.7 Neqo

Source:

- [mozilla/neqo](https://github.com/mozilla/neqo)

Command:

```bash
cargo test -p neqo-transport migration -- --nocapture
```

Evidence:

| 항목 | 결과 |
| --- | --- |
| selected tests | 53 |
| failures | 0 |
| covered cases | rebind port/address, zero-length CID, immediate/graceful migration, migration failure, preferred address, disabled migration, retire-prior-to, ECN migration, PMTUD migration |
| local log | `harness/results/impl-rerun-20260630T070249Z/logs/neqo-transport-migration-tests.log` |

Interpretation:

Neqo는 Firefox-adjacent transport stack으로서 migration test breadth가 가장 넓은 편에 속한다. 논문에서는 browser product behavior가 아니라 browser-adjacent implementation maturity evidence로 사용하는 것이 안전하다.

## 4. 논문에서 사용할 결론

안전한 결론:

> Connection Migration is not merely a paper feature. Fresh local reruns across quic-go, quiche, picoquic, s2n-quic, ngtcp2, aioquic, Quinn, and Neqo show that path validation and migration-related primitives are implemented and tested in multiple QUIC stacks. However, implementation-level maturity does not imply browser-level or managed-deployment continuity.

한국어 표현:

> QUIC Connection Migration은 구현되지 않은 기술이 아니다. 주요 구현체들은 path validation, NAT rebinding, active/passive migration, preferred address, disable-active-migration 같은 primitive를 테스트하고 있다. 다만 이러한 transport-level 성숙도는 Chrome/Safari/Android 브라우저 또는 CDN/LB 환경에서 웹 작업 연속성이 보장된다는 뜻은 아니다.

## 5. 남은 한계

| 한계 | 이유 | 후속 보강 |
| --- | --- | --- |
| raw logs는 ignored path | 로그가 크고 local address/path가 섞여 있어 공개 repo에는 요약만 둔다. | 제출 전 sanitized evidence bundle 생성 |
| 동일 깊이의 app-level 테스트는 아님 | quic-go/quiche는 sample client/server, 나머지는 library tests 중심이다. | 후보 1-2개를 골라 동일 workload harness로 재실험 |
| production-scale stack fresh rerun 미반영 | MsQuic, mvfst, lsquic, XQUIC은 빌드/운영 cost가 더 크다. | 필요 시 별도 chapter 또는 appendix로 분리 |
| browser CM claim은 별도 검증 필요 | browser policy, OS route, certificate, Alt-Svc, NetLog attribution이 개입한다. | Chapter 7 이후 controlled public browser handover 실험으로 분리 |
