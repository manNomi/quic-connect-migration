# LSQUIC NAT Rebinding App Demo

작성일: `2026-06-30`

## 1. 목적

이 실험의 목적은 LiteSpeed LSQUIC example HTTP/3 client/server workload에서 NAT rebinding 형태의 peer address change가 application workload와 함께 처리되는지 확인하는 것이다.

이전 `lsquic-preferred-address-app-demo-20260630.md`는 server가 `preferred_address` transport parameter를 광고해 client가 의도적으로 path 1로 이동하는 실험이었다. 이번 실험은 별도다. client와 server 사이에 local UDP proxy를 두고, proxy가 server-facing UDP source port를 중간에 바꾸어 NAT rebinding과 유사한 상황을 만든다.

## 2. 실행 환경

| 항목 | 값 |
| --- | --- |
| source repo | `/private/tmp/quic-cm-scan-repos/lsquic` |
| source commit | `f8ebaf838d2f4db836bda1182ee35b05d5191cee` |
| source date | `2026-06-28T18:34:48-04:00` |
| source subject | `Release 4.8.2 (#663)` |
| build dir | `/private/tmp/quic-cm-scan-repos/lsquic/build-local` |
| server binary | `build-local/bin/http_server` |
| client binary | `build-local/bin/http_client` |
| workload | `GET /file-1M`, response discarded by client with `-K` |
| server option | `-o allow_migration=1` |
| local rebinding component | Python UDP proxy inside `harness/scripts/run-lsquic-nat-rebinding-demo.sh` |
| artifact root | `harness/results/lsquic-nat-rebinding-demo-20260630T102751Z` |

## 3. 재현 명령

현재 repo에서 다음 명령으로 재현한다.

```bash
harness/scripts/run-lsquic-nat-rebinding-demo.sh
```

필요한 기본 조건:

| 조건 | 설명 |
| --- | --- |
| LSQUIC clone | 기본값은 `/private/tmp/quic-cm-scan-repos/lsquic` |
| LSQUIC build | 기본값은 `$LSQUIC_DIR/build-local` |
| OpenSSL CLI | self-signed test certificate 생성용 |
| Python 3 | UDP rebinding proxy 실행용 |
| `rg` | artifact evidence count용 |

다른 clone/build 위치를 쓰려면 다음 환경 변수를 지정한다.

```bash
LSQUIC_DIR=/path/to/lsquic \
LSQUIC_BUILD_DIR=/path/to/lsquic/build-local \
harness/scripts/run-lsquic-nat-rebinding-demo.sh
```

## 4. 실험 구조

```text
LSQUIC http_client
  -> UDP proxy listen port
       -> upstream socket 0 -> LSQUIC http_server
       -> upstream socket 1 -> LSQUIC http_server
```

실험 절차:

| 단계 | 설명 |
| --- | --- |
| 1 | ignored artifact directory 아래에 self-signed certificate 생성 |
| 2 | `http_server`를 loopback UDP port에 bind하고 `allow_migration=1` 설정 |
| 3 | Python UDP proxy가 client-facing port와 server-facing upstream socket 2개를 생성 |
| 4 | `http_client`가 proxy port로 접속해 `GET /file-1M` 요청 |
| 5 | proxy가 일정 시간 뒤 server-facing socket을 upstream 0에서 upstream 1로 변경 |
| 6 | server는 같은 QUIC connection에서 새 peer path를 기록하고 PATH_CHALLENGE/PATH_RESPONSE로 검증 |
| 7 | client/server/proxy exit status와 path-change log를 확인 |

## 5. 최신 실행 결과

최신 재현 실행:

```text
run_id=lsquic-nat-rebinding-demo-20260630T102751Z
payload_path=/file-1M
server_rate=160000
switch_after_seconds=0.75
client_exit=0
server_exit=0
proxy_switched=true
proxy_c2s_packets=742
proxy_s2c_packets_upstream0=460
proxy_s2c_packets_upstream1=283
server_record_new_path_count=1
server_path_validated_count=3
server_path_challenge_count=8
server_path_response_count=4
client_path_challenge_count=4
client_path_response_count=8
validation=ok
```

## 6. 핵심 evidence

| evidence | 결과 | 해석 |
| --- | --- | --- |
| client/server exit | `client_exit=0`, `server_exit=0` | HTTP/3 workload가 실패하지 않고 종료 |
| proxy rebinding | `proxy_switched=true` | server-facing source port가 중간에 변경됨 |
| upstream response split | upstream 0 `460`, upstream 1 `283` packets | server가 rebinding 전후 경로 모두로 응답 |
| new path detection | `server_record_new_path_count=1` | LSQUIC server가 peer address change를 새 path로 기록 |
| path validation | server/client `PATH_CHALLENGE`/`PATH_RESPONSE` 존재 | QUIC path validation primitive가 실행됨 |
| path switch | server log에 `path validated: switching from path #0 to path #1` | server가 rebinding path를 검증 후 current path로 승격 |

대표 로그:

```text
proxy: upstream_rebind after_c2s_packets=457 old_upstream_port=<port0> new_upstream_port=<port1>
server: record new path ID 1
server: assigned new DCID ... to new path 1
server: generated 9-byte PATH_CHALLENGE frame for path 1
server: about to process QUIC_FRAME_PATH_RESPONSE frame
server: path validated: switching from path #0 to path #1
client: generated PATH_RESPONSE(...) frame
```

## 7. 해석

안전하게 쓸 수 있는 주장:

> LSQUIC's example HTTP/3 client/server completed a 1MiB-class workload through a local UDP proxy that changed its server-facing source port mid-connection. Server logs show new path recording, PATH_CHALLENGE/PATH_RESPONSE exchange, and path validation from path 0 to path 1.

한국어 표현:

> LSQUIC은 preferred-address뿐 아니라 NAT rebinding 형태의 peer address change도 local HTTP/3 app workload에서 처리했다. UDP proxy가 server-facing source port를 바꾼 뒤 server는 새 path를 기록했고, PATH_CHALLENGE/PATH_RESPONSE 교환 후 path 1을 검증된 경로로 승격했다.

피해야 할 과장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| OpenLiteSpeed production 환경에서도 동일하게 보장된다 | example binary local loopback 실험이지 production server 배포 검증이 아니다 |
| browser handover success를 증명한다 | LSQUIC example client/server 실험이지 Chrome/Safari runtime 검증이 아니다 |
| 모든 NAT rebinding 상황을 대표한다 | local UDP proxy가 source port 변경을 재현한 controlled positive control이다 |

## 8. 논문에서의 위치

이 결과는 Chapter 1/3의 구현체 성숙도 근거를 강화한다. LSQUIC은 이제 다음 세 가지 근거를 가진다.

| 근거 | 상태 |
| --- | --- |
| full CTest | 79/79 PASS |
| preferred-address app demo | PASS |
| NAT rebinding app demo | PASS |

따라서 LSQUIC은 `source-only`나 `unit-test only`가 아니라, controlled local application workload에서 두 종류의 path transition evidence를 가진 서버 구현체로 분류할 수 있다.
