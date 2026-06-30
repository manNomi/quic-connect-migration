# Local Implementation Test Results

작성일: 2026-06-22  
범위: AWS CLI/EC2 없이 로컬 머신에서 실행 가능한 QUIC 구현체별 Connection Migration 관련 테스트와 샘플을 검수한다.

> 2026-06-30 업데이트: 이 문서는 2026-06-22 당시의 로컬 실행 기록이다. quic-go 편중을 줄이기 위해 quiche, picoquic, s2n-quic, ngtcp2, aioquic을 현재 HEAD 기준으로 다시 실행한 최신 요약은 [implementation-rerun-results-20260630.md](implementation-rerun-results-20260630.md)를 기준으로 본다.

## 1. 결론

로컬에서 실제 테스트까지 실행한 구현체는 다음 8개다.

| 구현체 | 로컬 결과 | 확인한 Connection Migration 범위 | 해석 |
| --- | --- | --- | --- |
| quic-go | PASS | custom client/server active migration, `AddPath -> Probe -> Switch`, qlog | 직접 실험 baseline으로 적합 |
| Cloudflare quiche | PASS | library migration tests, sample client/server active migration, `PathEvent`, qlog | path event 교차 검증에 적합 |
| picoquic | PASS | NAT rebinding, active migration, failed migration, false migration, preferred address tests | edge-case 기준선으로 가장 풍부 |
| s2n-quic | PASS | IP/port rebinding, blocked migration, zero-length CID, path challenge/response | AWS/NLB 검증 후보로 유지 |
| aioquic | PASS | passive path challenge/response, transport parameter parsing | active public API 실험보다는 보조군 |
| ngtcp2 | PASS | client migration API, path validation, disable active migration, frame encode | C library primitive 비교군 |
| Quinn | PASS | proto migration, UDP socket rebind receive path | Rust application stack 비교군 |
| Neqo | PASS | rebind, graceful/immediate migration, preferred address, disabled migration, PMTUD/ECN migration | browser-adjacent Firefox 계열 비교군 |

핵심 판단:

> Connection Migration은 주요 구현체에 아예 없는 기술이 아니다. 다만 구현체별로 active API 노출, 관찰성, preferred address, deployment/LB 적합성, browser integration 수준이 크게 다르다.

## 2. 로컬 환경 변경

이번 로컬 테스트 과정에서 다음 도구 또는 의존성을 사용했다.

| 항목 | 상태 |
| --- | --- |
| Go | `go1.26.4 darwin/arm64` |
| Rust | `rustc 1.91.0`, s2n-quic은 repository toolchain으로 `1.88.0` 사용 |
| CMake/Ninja/pkg-config | Homebrew로 설치됨 |
| OpenSSL | `/opt/homebrew/opt/openssl@3` |
| NSS | Neqo 빌드를 위해 Homebrew `nss`를 `3.114 -> 3.125`로 업그레이드 |

NSS 업그레이드 로그:

- `experiments/brew-upgrade-nss.log`

## 3. 구현체별 실행 결과

### 3.1 quic-go

검증 버전:

- source commit: `9b0474c9b9971dd2ee8cdce0fba9ebf2574e193a`
- Go module: `github.com/quic-go/quic-go v0.60.1-0.20260622040909-9b0474c9b997`

실행 내용:

- custom local direct-origin reproduction 구현
- client UDP socket A로 연결
- stream payload 전송
- UDP socket B 추가
- `AddPath -> Probe -> Switch`
- migration 후 stream payload 전송
- server가 같은 accepted QUIC connection에서 before/after payload 수신
- qlog에서 `path_challenge`, `path_response` 확인

결과:

- `go test ./...`: PASS
- local happy path: PASS
- client result `ok: true`
- server result `ok: true`
- `Switch()` before `Probe()` 시 `path not yet validated` 확인

주요 artifact:

- `experiments/quic-go-minimum-reproduction-results.md`
- `experiments/quic-go-min-repro/artifacts/results/client.json`
- `experiments/quic-go-min-repro/artifacts/results/server.json`
- `experiments/quic-go-min-repro/artifacts/qlog/*.sqlog`

논문용 해석:

- quic-go는 active migration을 실험자가 직접 제어하기 좋다.
- AWS/Android 이전에 transport-level continuity를 고정하는 baseline으로 적합하다.

### 3.2 Cloudflare quiche

검증 버전:

- source commit: `839b23d0edcc98aa1cf90c2cf0797b8cc56d4f15`

실행 내용:

```bash
cargo test -p quiche --lib migration --features qlog -- --nocapture
cargo build -p quiche_apps --bins --features qlog
```

추가로 sample server/client를 실행했다.

```bash
./target/debug/quiche-server --listen 127.0.0.1:4443 --enable-active-migration --no-retry
./target/debug/quiche-client --no-verify --enable-active-migration --perform-migration https://127.0.0.1:4443/
```

결과:

- library migration tests: 8 passed
- sample client/server local migration: PASS
- client log에서 새 local port path validated 확인
- server log에서 `Seen new path`, `Path ... validated`, `Connection migrated` 확인
- qlog에서 `path_challenge`, `path_response` 확인

주요 artifact:

- `experiments/quiche-local/artifacts/logs/client.log`
- `experiments/quiche-local/artifacts/logs/server.log`
- `experiments/quiche-local/artifacts/qlog/*.sqlog`

논문용 해석:

- quiche는 `PathEvent`와 qlog 기반 관찰성이 좋아 quic-go 결과의 cross-check에 적합하다.
- preferred address encode/decode는 TODO로 확인되어 preferred-address maturity는 낮게 분리해야 한다.

### 3.3 picoquic

검증 버전:

- source commit: `09d29cc5bb3f47ad2f3f5ef7732dfe7b80f6d473`

실행 내용:

```bash
cmake -S . -B build-local -G Ninja -DPICOQUIC_FETCH_PTLS=Y -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build-local --target picoquic_ct -j 8
./build-local/picoquic_ct -S /tmp/quic-cm-audit-repos/picoquic -n -r nat_rebinding nat_rebinding_loss nat_rebinding_zero nat_rebinding_fast migration migration_with_loss migration_fail preferred_address preferred_address_zero false_migration migration_disabled probe_api sockloop_migration
```

결과:

- 13 tests executed
- 0 fails
- NAT rebinding/loss/zero/fast rebinding, active migration, migration failure, preferred address, false migration, disabled migration, probe API를 확인

주요 artifact:

- `experiments/picoquic-local-test.log`

논문용 해석:

- picoquic은 production deployment 대표라기보다 CM edge-case maturity를 보여주는 기준선으로 적합하다.

### 3.4 s2n-quic

검증 버전:

- source commit: `547e973da525aef637a7cc1db2f1733ce42be929`

실행 내용:

```bash
cargo test -p s2n-quic-tests connection_migration -- --nocapture
```

결과:

- 10 passed
- IP rebind, port rebind, IP+port rebind, before-handshake rebinding, blocked port, zero-length CID client migration 포함
- log에서 `PathChallenge`, `PathResponse`, `path_challenge_updated: Validated` 확인

주요 artifact:

- `experiments/s2n-quic-local/connection-migration-tests.log`

논문용 해석:

- s2n-quic은 migration primitive와 event/validator 계층이 테스트되어 있다.
- 다음 질문은 AWS NLB의 8-byte Server ID와 custom CID provider를 어떻게 맞출 수 있는지다.

### 3.5 aioquic

검증 버전:

- source commit: `6d36838d008c2202c337142fa07e8bf80e96bac8`

실행 내용:

```bash
python3 -m venv .venv
CFLAGS=-I/opt/homebrew/opt/openssl@3/include LDFLAGS=-L/opt/homebrew/opt/openssl@3/lib .venv/bin/python -m pip install -e .
.venv/bin/python -m unittest \
  tests.test_connection.QuicConnectionTest.test_handle_path_challenge_frame \
  tests.test_connection.QuicConnectionTest.test_handle_path_challenge_response_on_different_path \
  tests.test_connection.QuicConnectionTest.test_local_path_challenges_are_bounded \
  tests.test_connection.QuicConnectionTest.test_remote_path_challenges_are_bounded \
  tests.test_connection.QuicConnectionTest.test_handle_path_response_frame_bad \
  tests.test_packet.ParamsTest.test_params_disable_active_migration
```

결과:

- 6 tests passed
- passive path update, PATH_CHALLENGE/PATH_RESPONSE, challenge bound, bad PATH_RESPONSE, `disable_active_migration` transport parameter parsing 확인

주요 artifact:

- `experiments/aioquic-install.log`
- `experiments/aioquic-local-migration-tests.log`

논문용 해석:

- aioquic은 passive migration primitive 확인에는 좋다.
- 실험자가 active migration을 직접 제어하는 public API는 quic-go/quiche보다 약하므로 보조군으로 둔다.

### 3.6 ngtcp2

검증 버전:

- source commit: `40f7ec64c70528afb16553e023af4d1c3d3183cf`

실행 내용:

```bash
git submodule update --init --recursive tests/munit
cmake -S . -B build-local-libtest -G Ninja -DENABLE_LIB_ONLY=ON -DENABLE_OPENSSL=OFF -DENABLE_SHARED_LIB=OFF -DENABLE_STATIC_LIB=ON -DBUILD_TESTING=ON
cmake --build build-local-libtest --target main -j 8
./build-local-libtest/tests/main \
  /conn/test_ngtcp2_conn_client_connection_migration \
  /conn/test_ngtcp2_conn_recv_path_challenge \
  /conn/test_ngtcp2_conn_disable_active_migration \
  /conn/test_ngtcp2_conn_path_validation \
  /pkt/test_ngtcp2_pkt_encode_path_challenge_frame \
  /pkt/test_ngtcp2_pkt_encode_path_response_frame
```

결과:

- 6 of 6 tests successful
- client connection migration, receive path challenge, disable active migration, path validation, PATH_CHALLENGE/PATH_RESPONSE frame encode 확인

주요 artifact:

- `experiments/ngtcp2-configure.log`
- `experiments/ngtcp2-build.log`
- `experiments/ngtcp2-local-migration-tests.log`

논문용 해석:

- ngtcp2는 C library primitive와 API 근거가 선명하다.
- HTTP/3 application stack 실험보다는 library-level maturity 비교군으로 적합하다.

### 3.7 Quinn

검증 버전:

- source commit: `76020ba4abd89716e4bf6e365169d5728983cef9`

실행 내용:

```bash
cargo test -p quinn-proto migration -- --nocapture
cargo test -p quinn rebind -- --nocapture
```

결과:

- `quinn-proto` migration test: 1 passed
- `quinn` rebind receive test: 1 passed
- log에서 migration initiated, PATH_CHALLENGE, PATH_RESPONSE, new path validated 확인

주요 artifact:

- `experiments/quinn-local-migration-tests.log`
- `experiments/quinn-local-rebind-tests.log`

논문용 해석:

- Quinn은 Rust application stack에서 migration default/disable 정책과 socket rebind 경로를 비교하기 좋다.

### 3.8 Neqo

검증 버전:

- source commit: `694edf6184a69b457a49e35bc0eebcfc0c2ce6e0`

사전 이슈:

- 첫 빌드 실패 원인: `nss-rs has NSS version requirement >=3.121, found 3.114`
- 해결: Homebrew `nss 3.125`로 업그레이드

실행 내용:

```bash
cargo test -p neqo-transport migration -- --nocapture
```

결과:

- 52 passed
- rebind port/address, zero-length CID, immediate migration, graceful migration, migration failure, preferred address, disabled migration, retire-prior-to migration, ECN migration, PMTUD migration 포함

주요 artifact:

- `experiments/neqo-local-migration-tests.log`
- `experiments/brew-upgrade-nss.log`

논문용 해석:

- Neqo는 Firefox 계열/browser-adjacent 구현체로서 migration 테스트 폭이 넓다.
- Android Chrome 실험 전에 “브라우저 인접 구현체도 transport 테스트는 성숙하다”는 비교 근거로 쓸 수 있다.

## 4. 아직 로컬 실행하지 않은 주요 대상

이번 단계에서 소스 검수는 했지만 실제 로컬 테스트 실행까지 가지 않은 대상은 다음과 같다.

| 대상 | 이유 | 다음 처리 |
| --- | --- | --- |
| Chromium QUICHE | Chromium 전체 빌드/브라우저 NetLog 검증 축이라 로컬 단위 테스트보다 비용이 큼 | Android/Chrome 실험 단계에서 NetLog와 feature flag로 검증 |
| MsQuic | production 중요도는 높지만 별도 CMake/test 환경 검토 필요 | 다음 로컬 테스트 후보 |
| mvfst | Folly/Fizz/Wangle 등 C++ 의존성이 커서 별도 빌드 계획 필요 | static audit + 필요 시 Docker/CI 기반 테스트 |
| lsquic | BoringSSL/OpenSSL 및 example interop 설정 필요 | optional 비교군 |
| XQUIC | CMake 의존성과 test target 파악 필요 | optional 비교군 |
| quicly | C library primitive 비교군이나 우선순위 낮음 | ngtcp2 이후 optional |
| nginx/HAProxy | 서버/proxy 배포 계층 검증 대상 | CM 지원/미지원 반례로 문서화, 이후 실제 HTTP/3 proxy test |

## 5. 연구 방향에 대한 업데이트

이번 로컬 테스트 이후 연구 질문은 더 선명해졌다.

기존 질문:

> Connection Migration은 왜 안 쓰이는가?

수정된 질문:

> Connection Migration primitive는 여러 구현체에서 구현 및 테스트되어 있지만, 왜 실제 HTTP/3 배포와 브라우저 웹 애플리케이션에서는 end-to-end 기능으로 잘 드러나지 않는가?

이 질문은 다음 하위 질문으로 나눌 수 있다.

1. 구현체는 active/passive migration, path validation, preferred address, disable migration을 어디까지 지원하는가?
2. 구현체가 제공하는 API와 관찰성은 실험자가 migration 성공/실패를 분류할 만큼 충분한가?
3. LB/CDN/proxy 환경에서 CID 기반 routing과 path change가 end-to-end로 유지되는가?
4. 브라우저와 OS network switch policy가 transport-level CM을 실제 HTTP/3 요청에 노출하는가?
5. transport connection이 유지되어도 web application task continuity가 유지되는가?

## 6. 바로 다음 단계

AWS를 미루는 조건에서 다음 로컬 단계는 둘 중 하나다.

1. `MsQuic` 로컬 migration/path validation 테스트 실행
2. 이번 8개 구현체 결과를 논문용 maturity table로 환원

추천은 2번을 먼저 하는 것이다. 이유는 이미 로컬 PASS 근거가 충분히 쌓였고, 이제 교수님께 보여줄 수 있는 “구현체 maturity evidence table”이 필요하기 때문이다.
