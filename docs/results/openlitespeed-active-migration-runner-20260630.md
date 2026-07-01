# OpenLiteSpeed Active Migration Runner

작성일: `2026-06-30`

## 1. 목적

이 문서는 OpenLiteSpeed production-like HTTP/3 Connection Migration runtime demo를 실행하기 위한 재현 runner를 추가한 결과다.

중요한 경계:

> 이 문서는 OpenLiteSpeed Connection Migration 성공 결과가 아니다. 현재 단계의 결론은 “Linux/EC2에서 실행할 수 있는 runtime demo packet을 준비했고, 현재 macOS 로컬 실행은 OpenLiteSpeed binary 부재로 blocked됨”이다.

## 2. 추가한 runner

```bash
harness/scripts/run-openlitespeed-active-migration-demo.sh
```

runner가 수행하는 일:

| 단계 | 내용 | 산출물 |
| --- | --- | --- |
| prerequisite gate | `lshttpd` 또는 `openlitespeed` binary, quiche client, OpenSSL, Linux `/dev/shm` 확인 | `result.env`의 `validation=blocked`와 `blocked_reason` |
| minimal server root 생성 | `LSWS_HOME`/`LSHTTPD_HOME`용 임시 server root, `httpd_config.conf`, vhost config, mime file, cert, 1MiB payload 생성 | `server-root/` |
| config test | `lshttpd -t` 실행 | `logs/config-test.stdout`, `logs/config-test.stderr` |
| runtime baseline | `lshttpd -d` foreground 실행 | `logs/lshttpd.stdout`, `logs/lshttpd.stderr`, server logs |
| active migration client | quiche `--enable-active-migration --perform-migration`로 `GET /file-1M` 요청 | `client/response.bin`, `logs/client.stderr` |
| validation | response size, access log, server/client path evidence 집계 | `result.env`, `logs/migration-grep.log` |

## 3. 실행 명령

현재 로컬에서는 실행 조건 확인만 수행했다.

```bash
RUN_ID=openlitespeed-active-migration-local-blocked-20260630 \
  harness/scripts/run-openlitespeed-active-migration-demo.sh
```

Linux/EC2에서 실제 실행할 때는 다음 값만 맞추면 된다.

```bash
LSHTTPD_BIN=/usr/local/lsws/bin/lshttpd \
QUICHE_CLIENT=/path/to/quiche-client \
OPENLITESPEED_DIR=/path/to/openlitespeed-source \
RUN_ID=openlitespeed-active-migration-linux-YYYYMMDD \
  harness/scripts/run-openlitespeed-active-migration-demo.sh
```

config test만 먼저 확인하려면 다음처럼 실행한다.

```bash
CONFIG_TEST_ONLY=1 \
LSHTTPD_BIN=/usr/local/lsws/bin/lshttpd \
QUICHE_CLIENT=/path/to/quiche-client \
  harness/scripts/run-openlitespeed-active-migration-demo.sh
```

## 4. 현재 로컬 결과

최신 로컬 blocked artifact:

```text
harness/results/openlitespeed-active-migration-local-blocked-20260630
```

결과 요약:

```text
run_id=openlitespeed-active-migration-local-blocked-20260630
validation=blocked
blocked_reason=missing-openlitespeed-binary
openlitespeed_dir=/private/tmp/quic-cm-scan-repos/openlitespeed
lshttpd_bin=
openlitespeed_bin=
quiche_client=/private/tmp/quic-cm-impl-rerun-20260630/quiche/target/debug/quiche-client
openssl_bin=/opt/local/bin/openssl
system_name=Darwin
system_machine=arm64
require_linux=1
```

해석:

| 항목 | 결과 | 의미 |
| --- | --- | --- |
| OpenLiteSpeed source | 있음 | source feasibility audit와 runner config generation 가능 |
| quiche client | 있음 | active migration client는 준비됨 |
| OpenSSL | 있음 | self-signed cert 생성 가능 |
| OpenLiteSpeed runtime binary | 없음 | local runtime demo blocked |
| OS | Darwin arm64 | runner 기본값은 Linux runtime만 허용 |
| `/dev/shm` | 없음 | OpenLiteSpeed QUIC shared-memory path와 맞지 않음 |

## 5. PASS 기준

runner는 다음 조건이 모두 맞아야 `validation=ok`로 판정한다.

| evidence | 조건 |
| --- | --- |
| config test | `lshttpd -t` exit `0` |
| application completion | quiche client exit `0`, response bytes `1048576` |
| HTTP/3 access evidence | server access log에 `/file-1M` request 존재 |
| server path evidence | server log에 `PATH_CHALLENGE`와 `PATH_RESPONSE` 계열 로그 존재 |
| client path evidence | quiche client log에 path validation 또는 migrated active path evidence 존재 |

다음은 실패 또는 blocked로 분리한다.

| 판정 | 의미 |
| --- | --- |
| `blocked` | prerequisite이 없어 runtime claim을 만들 수 없음 |
| `config_test_only` | server config syntax/readiness만 확인함 |
| `failed_client_exit` | active migration client가 실패함 |
| `failed_response_size` | application response continuity가 깨짐 |
| `failed_missing_access_log` | HTTP/3 request completion evidence가 없음 |
| `failed_missing_server_path_frames` | server-side path validation evidence가 부족함 |
| `failed_missing_client_validation` | client-side migrated path validation evidence가 부족함 |

## 6. Claim boundary

쓸 수 있는 주장:

> The repository now contains a reproducible OpenLiteSpeed runtime demo packet that can distinguish prerequisite blockage, configuration readiness, ordinary HTTP/3 request completion, and active migration evidence on a Linux/EC2 host.

현재 쓰면 안 되는 주장:

| 금지 claim | 이유 |
| --- | --- |
| OpenLiteSpeed에서 active migration이 성공했다 | 현재 로컬에서는 binary 부재로 runtime을 실행하지 못함 |
| OpenLiteSpeed에서 active migration이 실패했다 | active migration 시도 자체가 실행되지 않음 |
| LSQUIC example demo가 OpenLiteSpeed production behavior를 대체한다 | runner는 이 차이를 검증하기 위해 추가된 후속 packet임 |
| macOS blocked 결과가 Linux production behavior를 대표한다 | 현재 결과는 readiness/blockage evidence임 |

## 7. 다음 단계

| 우선순위 | 작업 | 필요한 입력 |
| ---: | --- | --- |
| 1 | Linux/EC2에 OpenLiteSpeed binary 또는 build 결과 준비 | `LSHTTPD_BIN` |
| 2 | quiche client binary 준비 | `QUICHE_CLIENT` |
| 3 | runner `CONFIG_TEST_ONLY=1` 실행 | config syntax/readiness |
| 4 | runner full mode 실행 | ordinary H3 + active migration evidence |
| 5 | `result.env`와 `migration-grep.log`를 보고서에 반영 | PASS/FAIL/blocked claim 분리 |

## 8. 참고 링크

| source | 링크 | 사용 목적 |
| --- | --- | --- |
| OpenLiteSpeed source | [litespeedtech/openlitespeed](https://github.com/litespeedtech/openlitespeed) | `LSWS_HOME`, `quicEnable`, `quicShmDir`, listener/vhost config 근거 |
| OpenLiteSpeed docs | [OpenLiteSpeed documentation](https://openlitespeed.org/kb/) | 설치/운영 경로의 공식 문서 entry point |
| LiteSpeed QUIC/HTTP3 docs | [QUIC.cloud / HTTP/3 setup reference](https://docs.litespeedtech.com/lsws/cp/cpanel/quic-http3/) | HTTP/3/QUIC가 HTTPS/UDP/listener 설정과 연결된다는 운영 참고 |
