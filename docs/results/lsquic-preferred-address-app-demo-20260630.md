# LSQUIC Preferred Address App Demo

작성일: `2026-06-30`

## 1. 목적

이 실험의 목적은 LiteSpeed LSQUIC을 단순 full CTest evidence에서 한 단계 더 올려, 실제 LSQUIC `http_client`/`http_server` workload에서 Connection Migration 관련 path transition이 관찰되는지 확인하는 것이다.

주의할 점은 이 실험이 NAT rebinding demo가 아니라는 것이다. LSQUIC의 client migration 경로는 서버가 `preferred_address` transport parameter를 제공할 때 client가 preferred address로 migration을 시작하는 형태다. 따라서 이 결과는 `preferred_address` 기반 app-level positive control로 해석한다.

## 2. 실행 환경

| 항목 | 값 |
| --- | --- |
| source repo | `/private/tmp/quic-cm-scan-repos/lsquic` |
| source commit | `f8ebaf838d2f4db836bda1182ee35b05d5191cee` |
| build dir | `/private/tmp/quic-cm-scan-repos/lsquic/build-local` |
| server binary | `build-local/bin/http_server` |
| client binary | `build-local/bin/http_client` |
| workload | `GET /file-1M`, response discarded by client with `-K` |
| artifact root | `harness/results/lsquic-preferred-address-script-20260630T095500Z` |

## 3. 재현 명령

현재 repo에서 다음 명령으로 재현한다.

```bash
RUN_ID=lsquic-preferred-address-$(date -u +%Y%m%dT%H%M%SZ) \
harness/scripts/run-lsquic-preferred-address-demo.sh
```

필요한 기본 조건:

| 조건 | 설명 |
| --- | --- |
| LSQUIC clone | 기본값은 `/private/tmp/quic-cm-scan-repos/lsquic` |
| LSQUIC build | 기본값은 `$LSQUIC_DIR/build-local` |
| OpenSSL CLI | self-signed test certificate 생성용 |
| `rg` | artifact evidence count용 |

다른 clone/build 위치를 쓰려면 다음 환경 변수를 지정한다.

```bash
LSQUIC_DIR=/path/to/lsquic \
LSQUIC_BUILD_DIR=/path/to/lsquic/build-local \
harness/scripts/run-lsquic-preferred-address-demo.sh
```

## 4. 실험 절차

스크립트가 수행하는 단계는 다음과 같다.

| 단계 | 설명 |
| --- | --- |
| 1 | ignored artifact directory 아래에 self-signed certificate 생성 |
| 2 | 사용 가능한 UDP 포트 2개 선택 |
| 3 | `http_server`를 initial port와 preferred port 두 곳에 bind |
| 4 | server option으로 `-o preferred_v4=127.0.0.1:<preferred_port>` 설정 |
| 5 | `http_client`가 initial port로 접속해 `GET /file-1M` 요청 |
| 6 | client가 server transport parameter의 preferred address를 받고 path 1 migration 시작 |
| 7 | logs에서 preferred address, PATH_CHALLENGE/PATH_RESPONSE, path 1 STREAM 전송, exit status 확인 |

## 5. 최신 실행 결과

최신 재현 실행:

```text
run_id=lsquic-preferred-address-script-20260630T095500Z
initial_port=56879
preferred_port=59603
payload_path=/file-1M
client_exit=0
server_exit=0
client_schedule_migration_count=1
client_tx_path1_count=13
server_tx_path1_count=568
server_tx_stream_path1_count=565
client_path_challenge_count=13
client_path_response_count=12
server_path_challenge_count=12
server_path_response_count=12
preferred_address_tp_count=2
max_client_read_off=1048835
validation=ok
```

## 6. 핵심 evidence

| evidence | 결과 | 해석 |
| --- | --- | --- |
| client/server exit | `client_exit=0`, `server_exit=0` | workload가 실패하지 않고 종료 |
| preferred address TP | `preferred_address_tp_count=2` | client/server logs에서 preferred address가 확인됨 |
| migration scheduling | `client_schedule_migration_count=1` | client가 path 1 migration을 시작 |
| path validation | `PATH_CHALLENGE`/`PATH_RESPONSE` 양방향 로그 존재 | QUIC path validation primitive가 실행됨 |
| migrated path traffic | `client_tx_path1_count=13`, `server_tx_path1_count=568` | path 1에서 packet 송수신 |
| app data on migrated path | `server_tx_stream_path1_count=565` | HTTP/3 STREAM data가 migrated path 1에서 전송됨 |
| response progress | `max_client_read_off=1048835` | 1MiB class response를 client가 읽음 |

대표 로그:

```text
client: peer transport parameters ... IPv4 preferred address: 127.0.0.1:<preferred_port>
client: Schedule migration to path 1: will send PATH_CHALLENGE
client: TX packet #... SHORT (PATH_CHALLENGE) ... path: 1
server: record path 1: (127.0.0.1:<preferred_port> - 127.0.0.1:<client_port>)
server: scheduled return path challenge on path 1
server: TX packet #... SHORT (STREAM) ... path: 1
```

## 7. 해석

이 결과로 LSQUIC은 `source inspection + full CTest`보다 강한 위치가 된다.

안전하게 쓸 수 있는 주장:

> LSQUIC's example HTTP/3 client/server can complete a 1MiB-class HTTP/3 workload while using the QUIC preferred-address migration path. Logs show the advertised preferred address, client migration scheduling to path 1, PATH_CHALLENGE/PATH_RESPONSE exchange, and HTTP/3 STREAM frames sent on the migrated path.

한국어 표현:

> LSQUIC은 full unit suite뿐 아니라 example HTTP/3 client/server에서도 preferred-address 기반 migration path를 재현할 수 있었다. client는 서버가 광고한 preferred address를 받은 뒤 path 1 migration을 시작했고, PATH_CHALLENGE/PATH_RESPONSE 교환 후 HTTP/3 STREAM data가 path 1에서 전송됐다.

피해야 할 과장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| LSQUIC NAT rebinding demo가 통과했다 | 이번 실험은 NAT rebinding이 아니라 preferred-address migration이다 |
| OpenLiteSpeed production 환경에서도 동일하게 보장된다 | example binary local loopback 실험이지 production server 배포 검증이 아니다 |
| browser handover success를 증명한다 | LSQUIC example client/server 실험이지 Chrome/Safari runtime 검증이 아니다 |

## 8. 논문에서의 위치

이 결과는 Chapter 3 구현체 positive control을 보강한다. 특히 quic-go/quiche/XQUIC 외에 LSQUIC도 app-level workload와 path migration evidence를 함께 가진 구현체로 분류할 수 있다.

다만 후속 연구에서는 다음 두 갈래를 분리해야 한다.

| 후속 질문 | 이유 |
| --- | --- |
| LSQUIC/OpenLiteSpeed production-like HTTP/3 server에서도 같은 evidence가 나오는가? | example binary와 production server는 다름 |
| NAT rebinding path도 LSQUIC local app workload에서 재현 가능한가? | preferred_address migration과 NAT rebinding은 다른 path-change mechanism |
