# Chapter 1 상세 조사: QUIC Connection Migration 구현체 성숙도는 어떻게 검수했는가

작성일: `2026-06-30`

이 문서는 `Chapter 1. Connection Migration 성숙도 조사`가 어떤 절차로 수행되었는지 설명한다. 목적은 교수님께 “왜 이런 구현체를 골랐는가”, “무슨 근거로 L4/L5 같은 판정을 했는가”, “실제로 테스트를 돌렸는가”, “어떤 한계가 있는가”를 답할 수 있게 만드는 것이다.

공개 안전성: 이 문서는 AWS 계정, 인스턴스 ID, 공인 IP, hostname, SSH target, credential, 로컬 네트워크 주소를 포함하지 않는다.

## 1. Chapter 1의 원래 질문

초기 질문은 다음이었다.

> QUIC Connection Migration은 실제 구현체에 구현되어 있는가?

이 질문을 먼저 둔 이유는 교수님 피드백 때문이다. 애초에 구현체들이 CM을 구현하지 않았다면 “왜 CM이 실제 웹에서 덜 쓰이는가”라는 질문은 성립하기 어렵다. 그래서 연구의 첫 단계는 성능 측정이나 Chrome 실험이 아니라, 주요 QUIC 구현체의 기능 존재 여부와 성숙도를 확인하는 것이었다.

## 2. 조사 대상은 어떻게 뽑았는가

### 2.1 1차 후보군

1차 후보는 QUIC WG의 구현체 목록에서 시작했다.

- QUIC WG archived wiki: `https://github.com/quicwg/base-drafts/wiki/Implementations`
- QUIC WG newer implementation list: `https://github.com/quicwg/quicwg.github.io/blob/main/implementations.md`

QUIC WG wiki는 2025-06-09 기준 archived 상태라고 명시되어 있어, 이후에는 `quicwg.github.io`의 `implementations.md`를 더 나은 seed source로 보았다. 다만 두 문서 모두 “known implementations” 목록이지 Connection Migration 지원 여부를 직접 판정해주는 표는 아니다. 따라서 이 목록은 출발점으로만 사용했다.

### 2.2 최종 조사 대상 18개

최종 조사표는 `data/implementation-survey.csv`에 만들었다. 조사 대상은 다음 18개다.

| 우선순위 | 구현체/스택 | 선택 이유 |
| ---: | --- | --- |
| 1 | quic-go | active migration API가 명확하고 custom 실험 작성이 쉬움 |
| 2 | Cloudflare quiche | Cloudflare 생태계, PathEvent/qlog 관찰성이 좋음 |
| 3 | AWS s2n-quic | AWS/NLB/CID-aware routing 연구와 연결성이 높음 |
| 4 | ngtcp2 | C 기반 RFC QUIC 구현체와 nghttp3 생태계 |
| 5 | LiteSpeed lsquic | LiteSpeed/OpenLiteSpeed HTTP/3 deployment와 연결 |
| 6 | MsQuic | Microsoft ecosystem 및 production deployment relevance |
| 7 | Quinn | Rust async QUIC stack 비교군 |
| 8 | Neqo | Mozilla/Firefox 계열 browser-adjacent QUIC stack |
| 9 | XQUIC | Alibaba cross-platform QUIC/HTTP/3 stack |
| 10 | Chromium/Cronet | Chrome/Android browser runtime policy의 핵심 |
| 11 | AWS CloudFront | managed edge HTTP/3와 edge-level continuity 해석 |
| 12 | AWS NLB + s2n-quic | CID-aware data plane/deployment candidate |
| 13 | mvfst | Meta scale transport, large-scale deployment candidate |
| 14 | picoquic | research/interop 성격, migration edge-case test가 풍부함 |
| 15 | nginx QUIC | server-side passive migration/web server deployment |
| 16 | quicly | H2O 계열 C implementation 비교군 |
| 17 | aioquic | Python prototype/reference, passive validation 확인에 적합 |
| 18 | HAProxy QUIC | HTTP/3 proxy가 CM을 의미하지 않는 반례로 중요 |

Apple QUIC stack은 처음 후보에는 있었지만, 비공개 구현체라 source/test 기반 maturity audit이 어렵기 때문에 최종 matrix에서는 제외했다.

## 3. 조사 범위와 제외 범위

### 3.1 포함한 것

Chapter 1에서는 다음을 확인했다.

| 항목 | 본 이유 |
| --- | --- |
| RFC primitive | `PATH_CHALLENGE`, `PATH_RESPONSE`, CID, transport parameter가 있는지 |
| passive migration | NAT rebinding, peer address change, remote tuple change를 처리하는지 |
| active migration API | client가 새 path를 추가/probe/switch할 수 있는지 |
| migration policy | `disable_active_migration`, migration disabled, runtime option이 있는지 |
| preferred address | server preferred address 관련 구현이 있는지 |
| CID/load balancing | CID generator, QUIC-LB, Server ID, LB-aware routing 근거가 있는지 |
| observability | qlog, PathEvent, NetLog, tracing, event callback이 있는지 |
| tests | migration/rebinding/path validation 관련 unit/integration test가 있는지 |
| local reproducibility | 실제 빌드/테스트/샘플 실행으로 PASS를 확인할 수 있는지 |

### 3.2 제외한 것

Chapter 1에서 일부러 제외한 것도 있다.

| 제외 항목 | 이유 |
| --- | --- |
| 실제 Chrome Wi-Fi/cellular handover 성공 여부 | Chapter 5 이후 브라우저 실험 범위 |
| CDN/LB end-to-end continuity | Chapter 4 배포 경로 실험 범위 |
| 웹 앱 upload/download/streaming task continuity | Chapter 8 이후 workload 실험 범위 |
| 성능 수치 비교 | Chapter 1은 기능 성숙도 audit이지 benchmark가 아님 |
| private/closed implementation 내부 검증 | source/test 접근이 없으면 성숙도 판정 근거가 약함 |

## 4. 성숙도 판정 기준

Chapter 1에서는 구현체를 L0-L5로 나눴다.

| Level | 의미 | 논문에서의 해석 |
| --- | --- | --- |
| L0 | CM 관련 근거 없음 | CM 구현체 후보로 쓰기 어려움 |
| L1 | `PATH_CHALLENGE`, `PATH_RESPONSE`, CID, transport parameter 일부 확인 | RFC primitive 일부만 확인 |
| L2 | NAT rebinding 또는 peer address change 처리 가능 | passive migration 계층 근거 |
| L3 | client active migration API 또는 명확한 내부 API 존재 | active migration 실험 후보 |
| L4 | test, qlog, event, failure handling 등 검증 가능성 존재 | 구현체 maturity 근거로 사용 가능 |
| L5 | LB/CDN/cloud/production 배포 근거까지 존재 | deployment discussion 또는 positive control 후보 |

중요한 점은 L4와 L5의 차이다. L4는 구현체 자체의 기능과 테스트가 있다는 뜻이고, L5는 운영/배포 경로까지 연결되는 근거가 있다는 뜻이다. 따라서 library가 L4라고 해서 자동으로 production browser CM이 된다는 뜻은 아니다.

## 5. 1차 evidence scanner

### 5.1 scanner를 만든 이유

구현체가 18개라서 모든 repository를 처음부터 수동으로 읽으면 누락과 편향이 생긴다. 그래서 `tools/scan_implementation_evidence.py`를 만들었다. 이 도구는 clone된 구현체 repo에서 CM 관련 키워드를 찾아 category별 evidence 후보를 표로 만든다.

주의: scanner는 maturity level을 자동 판정하지 않는다. scanner는 “읽어야 할 파일과 줄”을 찾는 도구이고, 최종 판정은 사람이 source/test를 읽고 수행했다.

### 5.2 scanner가 보는 category

| category | 찾는 근거 |
| --- | --- |
| `path_validation` | `PATH_CHALLENGE`, `PATH_RESPONSE`, path validation, `ErrPathNotValidated` |
| `active_migration_api` | `AddPath`, `Probe`, `Switch`, `probe_path`, `migrate_source`, `perform_migration` |
| `passive_rebinding` | NAT rebinding, peer address, remote address, tuple change |
| `disable_migration_policy` | `disable_active_migration`, migration disabled |
| `preferred_address` | preferred address 관련 코드/문서 |
| `cid_and_load_balancing` | Connection ID generator, QUIC-LB, Server ID, load balancing |
| `observability` | qlog, PathEvent, NetLog, tracing, path event |
| `tests` | migration/rebinding/path 관련 test |

### 5.3 scanner 실행 방식

재현 예시는 다음과 같다.

```bash
cd /Users/manwook-han/Desktop/lab
git clone https://github.com/quic-go/quic-go.git
git clone https://github.com/cloudflare/quiche.git
git clone https://github.com/aws/s2n-quic.git

cd /Users/manwook-han/Desktop/lab/quic-connect-migration
python3 tools/scan_implementation_evidence.py \
  ../quic-go ../quiche ../s2n-quic \
  --format markdown
```

scanner output은 다음 질문을 하기 위한 1차 자료로 사용했다.

1. path validation primitive가 실제 코드에 있는가?
2. active migration API가 public API인지, internal API인지, test-only인지?
3. passive NAT rebinding 처리가 있는가?
4. qlog/PathEvent/NetLog 등 관찰성이 있는가?
5. migration 관련 test가 있는가?
6. CID/load balancing과 연결할 수 있는가?

## 6. 수동 source/test audit

scanner 이후에는 각 구현체별로 source, test, official docs, sample command를 수동으로 읽었다. 수동 판정에서 특히 중요하게 본 것은 다음이다.

| 판정 질문 | 이유 |
| --- | --- |
| primitive가 실제 state machine과 연결되는가? | 단순 frame encode/decode만으로 active migration을 말할 수 없음 |
| active migration API가 실제 application에서 호출 가능한가? | internal/test-only API면 실험 재현성이 낮음 |
| path validation 실패를 구분하는가? | 실패 처리 없이 성공만 있으면 maturity가 약함 |
| qlog/event/log가 남는가? | 논문에서는 성공 주장보다 evidence가 중요함 |
| HTTP/3 layer와 연결되는가? | QUIC transport 성공이 H3 task continuity와 같지 않음 |
| deployment path를 고려하는가? | LB/CDN/proxy에서는 CID-aware routing이 중요함 |

## 7. 실제 로컬 실행 검수

Chapter 1에서 가장 강한 근거는 실제 로컬 테스트를 돌린 구현체들이다. 초기 local test는 8개 구현체였고, 2026-06-30 fresh rerun에서 MsQuic, XQUIC, LiteSpeed LSQUIC, quicly, nginx QUIC, HAProxy negative-control까지 보강해 총 14개 구현체/스택의 local test/demo/partial/negative-control artifact를 확보했다.

### 7.1 로컬 실행 대상

| 구현체 | 실행한 검수 | 결과 | 의미 |
| --- | --- | --- | --- |
| quic-go | custom active migration reproduction, `AddPath -> Probe -> Switch` | PASS | 직접 실험 baseline |
| Cloudflare quiche | migration tests, sample client/server active migration | PASS | PathEvent/qlog lifecycle 검증 |
| picoquic | NAT rebinding, migration, failure, preferred address 등 13개 test | PASS | edge-case maturity 기준선 |
| s2n-quic | connection_migration test | PASS | AWS/NLB 후보 근거 |
| aioquic | path challenge/response unit tests | PASS | passive validation reference |
| ngtcp2 | client migration/path validation/disable migration tests | PASS | C library primitive 비교군 |
| Quinn | migration/rebind tests | PASS | Rust stack 비교군 |
| Neqo | migration test suite | PASS | Mozilla/browser-adjacent 비교군 |
| MsQuic | NAT rebind/path-validation selected gtests, IPv4/IPv6 | PASS | production-relevant library evidence |
| XQUIC | loopback client/server NAT rebinding demo | PASS demo, full suite partial | NAT rebinding implementation evidence |
| LiteSpeed LSQUIC | full CTest 79/79, selected primitive tests, preferred-address 및 NAT-rebinding HTTP/3 app demo | PASS | server-stack unit and app-level path-transition evidence |
| nginx QUIC | HTTP/3 server runtime demo, quiche active migration, server path seq:1 validation | PASS | web server runtime path-validation evidence |
| HAProxy QUIC | HTTP/3 proxy baseline PASS, quiche active migration path validation FAIL | PASS_NEGATIVE_CONTROL | HTTP/3 proxy support가 active CM support가 아님을 보이는 반례 |
| quicly | build `test.t`/`cli`/`udpfw`, migration-related unit evidence | PARTIAL | path validation/path promotion primitive evidence |

### 7.2 로컬 환경

`docs/results/local-implementation-test-results.md` 기준 환경은 다음이었다.

| 항목 | 값 |
| --- | --- |
| OS | macOS darwin/arm64 |
| Go | `go1.26.4` |
| Rust | `rustc 1.91.0`, s2n-quic은 repo toolchain 사용 |
| C/C++ build tools | CMake, Ninja, pkg-config |
| OpenSSL | Homebrew OpenSSL |
| NSS | Neqo 빌드를 위해 NSS 업그레이드 |

### 7.3 PASS로 인정한 기준

단순히 test command가 0으로 끝난 것만 PASS로 보지 않았다. 가능한 경우 다음 증거를 함께 확인했다.

| 증거 | 예시 |
| --- | --- |
| path validation frame | qlog 또는 log의 PATH_CHALLENGE/PATH_RESPONSE |
| path switch 또는 rebind | source port/local path 변경, path validated event |
| application payload | before/after payload 또는 HTTP/3 request/response 완료 |
| negative behavior | `Switch()` before `Probe()` 실패, migration disabled, failed migration |
| observability | qlog, PathEvent, logs, trace |

## 8. 대표 구현체별 상세 방식

### 8.1 quic-go

quic-go는 Chapter 1에서 가장 중요한 positive control이다.

확인 흐름:

```text
client UDP socket A로 QUIC 연결
-> before payload 전송
-> UDP socket B 생성
-> conn.AddPath(transport B)
-> path.Switch() before Probe 실패 확인
-> path.Probe() 성공
-> path.Switch() 성공
-> after payload 전송
-> server가 같은 QUIC connection에서 before/after payload 수신
```

판정 근거:

- `Switch()` before `Probe()`가 `path not yet validated`를 반환했다.
- qlog에서 `path_challenge`, `path_response`가 기록됐다.
- migration 이후 payload가 socket B local address로 전송된 것이 관찰됐다.
- client/server result가 모두 `ok: true`였다.

결론:

> quic-go는 active migration을 실험자가 직접 제어하기 좋아, 이후 AWS direct origin과 browser testbed의 transport positive control로 쓰기 적합하다.

### 8.2 Cloudflare quiche

quiche는 path lifecycle을 관찰하기 좋은 구현체로 보았다.

실행 방식:

```bash
cargo test -p quiche --lib migration --features qlog -- --nocapture
cargo build -p quiche_apps --bins --features qlog
./target/debug/quiche-server --listen 127.0.0.1:4443 --enable-active-migration --no-retry
./target/debug/quiche-client --no-verify --enable-active-migration --perform-migration https://127.0.0.1:4443/
```

판정 근거:

- library migration tests 8개가 pass했다.
- server log에 `Seen new path`, path validated, connection migrated 계열 이벤트가 있었다.
- qlog에서 `PATH_CHALLENGE` / `PATH_RESPONSE`가 확인됐다.
- migration 이후 HTTP/3 request/response가 완료됐다.

결론:

> quiche는 “migration lifecycle이 어떤 이벤트와 frame sequence로 보이는가”를 설명하는 observability baseline으로 적합하다.

### 8.3 picoquic

picoquic은 production web deployment 대표라기보다 edge-case maturity 검수에 강했다.

실행 방식:

```bash
./build-local/picoquic_ct -S /tmp/quic-cm-audit-repos/picoquic -n -r \
  nat_rebinding nat_rebinding_loss nat_rebinding_zero nat_rebinding_fast \
  migration migration_with_loss migration_fail preferred_address \
  preferred_address_zero false_migration migration_disabled probe_api \
  sockloop_migration
```

판정 근거:

- 13개 migration/rebinding 관련 test가 실행됐다.
- NAT rebinding, active migration, failed migration, false migration, preferred address, disabled migration을 모두 포함했다.
- 0 fail이었다.

결론:

> picoquic은 CM edge-case test 폭이 넓어 maturity 기준선으로 유용하다.

### 8.4 s2n-quic

s2n-quic은 AWS/NLB 실험과 연결하기 위해 중요했다.

실행 방식:

```bash
cargo test -p s2n-quic-tests connection_migration -- --nocapture
```

판정 근거:

- 10개 test pass.
- IP rebind, port rebind, IP+port rebind, before-handshake rebinding, blocked port, zero-length CID client migration 포함.
- log에서 `PathChallenge`, `PathResponse`, `path_challenge_updated: Validated` 확인.

결론:

> s2n-quic은 migration primitive와 validator/event 계층이 있어 AWS deployment discussion의 후보로 유지했다.

### 8.5 ngtcp2

ngtcp2는 C library primitive 비교군으로 확인했다.

확인 항목:

- client connection migration
- receive path challenge
- disable active migration
- path validation
- PATH_CHALLENGE/PATH_RESPONSE frame encode

결론:

> ngtcp2는 HTTP/3 application testbed보다는 RFC primitive와 C implementation maturity 비교군으로 적합하다.

### 8.6 Quinn, Neqo, aioquic

| 구현체 | 확인 방식 | 결론 |
| --- | --- | --- |
| Quinn | `quinn-proto` migration test, `quinn` rebind test | Rust application stack 비교군 |
| Neqo | `neqo-transport migration` test suite | Mozilla/browser-adjacent 구현체로 테스트 폭이 넓음 |
| aioquic | path challenge/response unit tests | active migration 주력보다는 passive validation reference |

## 9. Source-only 또는 deferred 대상은 어떻게 처리했는가

모든 구현체를 빌드하지는 않았다. 빌드 비용이나 목적 차이 때문에 source/docs 기반으로만 판정한 대상도 있다.

| 대상 | 처리 방식 | 이유 |
| --- | --- | --- |
| Chromium/Cronet | source/API/docs + Chrome baseline | 전체 Chromium 빌드보다 browser NetLog 실험이 더 중요 |
| MsQuic | fresh selected gtest로 승격 | production 중요도가 높고 NAT rebind/path-validation v4/v6 selected tests가 통과함 |
| mvfst | source/docs audit | Folly/Fizz 등 의존성이 커서 source maturity evidence로 유지 |
| LiteSpeed LSQUIC | fresh full CTest와 preferred-address/NAT-rebinding app demo로 승격 | 서버 스택 단위 테스트와 example HTTP/3 app-level positive control은 통과했지만 OpenLiteSpeed demo는 후속 필요 |
| XQUIC | fresh NAT rebinding demo로 승격 | client/server NAT rebinding demo는 통과했지만 full suite는 macOS build caveat가 있음 |
| nginx QUIC | fresh runtime demo로 승격 | server-side source 근거에 더해 quiche client active migration 중 HTTP/3 1MiB response와 path validation을 확인 |
| quicly | fresh build/unit partial로 승격 | migration-related subtest는 확인됐지만 full unit/e2e PASS가 아님 |
| HAProxy QUIC | fresh negative-control로 승격 | HTTP/3 proxy baseline은 PASS지만 quiche active migration은 migrated path validation 실패 |
| AWS CloudFront | managed edge analysis | end-to-end CM이 아니라 edge-level continuity로 해석해야 함 |
| AWS NLB + s2n-quic | deployment candidate | Chapter 4의 CID-aware routing 실험으로 연결 |

## 10. 조사 결과의 수치 요약

`data/implementation-survey.csv` 기준 요약은 다음이다.

| 항목 | 결과 |
| --- | --- |
| 총 조사 대상 | 18 |
| local test/demo/partial build/negative-control까지 실행한 구현체 | 14 |
| 2026-06-30 fresh rerun/demo/negative-control artifact 확보 | 13 |
| fresh app-level/runtime demo artifact 확보 | 3 |
| fresh negative-control artifact 확보 | 1 |
| fresh partial build/test artifact 확보 | 1 |
| source inspected only | 1 |
| source + local browser baseline | 1 |
| partial/deferred | 2 |
| active migration API `yes` | 8 |
| passive migration `yes` | 14 |
| tests `yes` | 14 |
| high AWS suitability | 5 |

Level 분포:

| level | count |
| --- | ---: |
| L1_L2 | 1 |
| L2_L3 | 1 |
| L3_L4 | 2 |
| L3_L4_partial | 2 |
| L4 | 3 |
| L4_AWS_L5_candidate | 1 |
| L4_L5 | 1 |
| L4_L5_candidate | 1 |
| L4_L5_caveat | 1 |
| L4_client_runtime_policy_dependent | 1 |
| L4_server_runtime | 1 |
| L5_candidate | 1 |
| L5_deployment_candidate | 1 |
| L5_edge | 1 |

## 11. 판정표는 어떻게 만들어졌는가

최종적으로 다음 방식으로 `current_level`을 정했다.

| 관찰된 근거 | 가능한 판정 |
| --- | --- |
| frame encode/decode와 transport parameter만 있음 | L1-L2 |
| NAT rebinding/peer address change 처리 있음 | L2-L3 |
| active migration API 또는 internal API 있음 | L3-L4 |
| migration tests + qlog/event/log + failure handling 있음 | L4 |
| production/cloud/LB/CDN deployment evidence까지 있음 | L5 후보 |

구체적인 판정 방식:

1. QUIC WG 목록에서 후보를 잡는다.
2. `implementation-survey.csv`에 category, usage reason, evidence fields를 만든다.
3. scanner로 각 repo의 path/migration/rebinding/log/test 후보 파일을 찾는다.
4. source/test를 사람이 읽어 false positive를 제거한다.
5. 빌드 가능한 구현체는 local test를 실행한다.
6. PASS artifact와 qlog/log/test output을 남긴다.
7. L0-L5 rubric으로 level을 부여한다.
8. 이후 Chapter 2에서 friction matrix와 연결한다.

## 12. 이 조사로 알게 된 것

### 12.1 강하게 말할 수 있는 것

1. CM은 구현체 수준에서 존재하는 기능이다.
2. 주요 구현체 다수는 path validation, NAT rebinding, active/passive migration, qlog/event/test 중 일부 이상을 갖고 있다.
3. 적어도 quic-go, quiche, picoquic, s2n-quic, ngtcp2, Quinn, Neqo, aioquic은 로컬에서 migration/path validation 관련 test 또는 reproduction을 실행해 근거를 확보했다.
4. 구현체 maturity와 production/browser availability는 다른 문제다.

### 12.2 말하면 안 되는 것

1. “18개 구현체가 모두 production-ready CM을 지원한다.”
2. “HTTP/3를 지원하면 CM도 지원한다.”
3. “library test PASS는 Chrome/Safari handover 성공을 의미한다.”
4. “CDN edge HTTP/3 continuity는 origin까지의 end-to-end CM이다.”
5. “scanner match가 곧 기능 지원이다.”

## 13. 한계

| 한계 | 의미 |
| --- | --- |
| 시점 한계 | 구현체는 계속 바뀌므로 2026-06-30 기준 최신 상태와 다를 수 있다. |
| scanner 한계 | keyword 기반이므로 false positive/false negative 가능성이 있다. |
| local test 한계 | loopback/local test는 mobile handover나 public network를 대표하지 않는다. |
| source-only 한계 | 빌드하지 않은 구현체는 runtime behavior까지 확인하지 못했다. nginx는 runtime demo로 보강됐지만 mvfst 등은 여전히 source audit로 분리된다. |
| production 한계 | L4 library maturity는 L5 deployment maturity와 다르다. |
| browser 한계 | Chromium/Cronet source policy는 실제 Chrome browser CM success와 다르다. |

## 14. Chapter 1이 Chapter 2로 이어진 이유

Chapter 1의 결론은 “CM은 없는 기술이 아니다”였다. 그렇다면 다음 질문은 자연스럽게 바뀐다.

> 구현체에는 CM primitive와 test가 있는데, 왜 실제 웹 브라우저와 배포 환경에서는 user-visible continuity로 잘 드러나지 않는가?

이 질문 때문에 Chapter 2에서 runtime policy, HTTP/3 discovery, path-change proof, session attribution, CID-aware routing, CDN/proxy termination, application recovery 같은 friction layer를 분석했다.

## 15. 관련 산출물

| 산출물 | 역할 |
| --- | --- |
| `data/implementation-survey.csv` | 18개 구현체별 survey table |
| `tools/scan_implementation_evidence.py` | repo keyword evidence scanner |
| `docs/reproducibility-guide-ko.md` | scanner와 구현체 테스트 재현 절차 |
| `docs/results/local-implementation-test-results.md` | 초기 8개 구현체 local test 결과 |
| `docs/results/implementation-rerun-results-20260630.md` | 2026-06-30 fresh rerun/demo/partial 결과 |
| `docs/results/lsquic-preferred-address-app-demo-20260630.md` | LSQUIC preferred-address HTTP/3 app demo 결과 |
| `docs/results/quic-go-minimum-reproduction-results.md` | quic-go active migration positive control |
| `docs/results/quiche-path-event-timeline-20260623.md` | quiche path-event timeline |
| `docs/results/cm-operational-friction-matrix-20260624.md` | Chapter 2로 이어지는 friction matrix |
| `docs/results/chaptered-research-synthesis-20260629.md` | 전체 챕터 흐름 |

## 16. 교수님께 설명할 때의 짧은 버전

Chapter 1에서는 QUIC WG 구현체 목록을 seed로 삼아, 실제 연구와 배포에 영향이 큰 18개 구현체/스택을 골랐다. 각 구현체에 대해 path validation, NAT rebinding, active migration API, migration policy, preferred address, CID/LB, qlog/event, test 존재 여부를 CSV로 정리했다. 이후 keyword scanner로 1차 evidence file을 찾고, source/test를 수동으로 읽어 false positive를 제거했다. 2026-06-30 기준 14개 구현체/스택은 실제 local test/demo/partial build/negative-control까지 실행했다. 결과적으로 CM은 구현체 수준에서 존재하고 여러 구현체가 L3-L4 이상의 성숙도를 보였지만, 이것이 곧 브라우저나 CDN에서 end-to-end CM이 작동한다는 뜻은 아니므로 Chapter 2에서 deployment/runtime friction을 분석하게 되었다.
