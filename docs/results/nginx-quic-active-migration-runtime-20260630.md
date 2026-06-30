# nginx QUIC Active Migration Runtime Demo

작성일: `2026-06-30`

## 1. 목적

이 실험의 목적은 nginx QUIC을 source-only evidence에서 runtime evidence로 한 단계 올리는 것이다. 기존 `nginx-haproxy-quic-cm-boundary-20260630.md`는 nginx source와 공식 문서에서 server-side passive migration/path validation 흐름을 확인했지만, 실제 HTTP/3 request 중 active client migration이 처리되는지는 재현하지 않았다.

이번 실험은 nginx HTTP/3 server를 loopback에서 실행하고, Cloudflare quiche sample client가 `--enable-active-migration --perform-migration`으로 source port migration을 수행하게 만든다. workload는 `GET /file-1M` 1MiB HTTP/3 download다.

## 2. 실행 환경

| 항목 | 값 |
| --- | --- |
| nginx source | `/private/tmp/quic-cm-scan-repos/nginx` |
| nginx commit | `072f6fdbac3323fab257280b7119224027b01315` |
| nginx commit date | `2026-06-29T20:22:32+01:00` |
| nginx commit subject | `Revert "HTTP/2: fixed overlapping memcpy in CONTINUATION frames"` |
| nginx version | `nginx/1.31.3` |
| build flags | `--with-http_ssl_module --with-http_v3_module --with-debug` |
| TLS library | `OpenSSL 3.3.1 4 Jun 2024` |
| client | `/private/tmp/quic-cm-impl-rerun-20260630/quiche/target/debug/quiche-client` |
| workload | `GET /file-1M`, 1MiB response |
| artifact root | `harness/results/nginx-quic-active-migration-20260630T104724Z` |

## 3. 재현 명령

현재 repo에서 다음 명령으로 재현한다.

```bash
harness/scripts/run-nginx-quic-active-migration-demo.sh
```

기본 경로가 다른 경우:

```bash
NGINX_DIR=/path/to/nginx \
NGINX_BUILD_DIR=/path/to/nginx/build-quic-runtime \
QUICHE_CLIENT=/path/to/quiche-client \
harness/scripts/run-nginx-quic-active-migration-demo.sh
```

스크립트가 하는 일:

| 단계 | 설명 |
| --- | --- |
| 1 | nginx source commit/version 정보를 artifact에 기록 |
| 2 | nginx binary가 없으면 `--with-http_v3_module --with-debug`로 빌드 |
| 3 | self-signed certificate와 1MiB payload 생성 |
| 4 | `listen 127.0.0.1:<port> quic; http3 on; quic_retry off;` nginx config 생성 |
| 5 | nginx config test 후 foreground server 실행 |
| 6 | quiche client가 HTTP/3 request 중 active migration 수행 |
| 7 | response size, access log, nginx debug log, client path log를 검증 |

## 4. 최신 실행 결과

```text
run_id=nginx-quic-active-migration-20260630T104724Z
client_exit=0
payload_bytes=1048576
client_response_bytes=1048576
access_get_file_count=1
server_path_seq1_created_count=1
server_path_seq1_validated_count=2
server_path_challenge_rx_count=1
server_path_response_tx_count=1
server_path_challenge_tx_count=2
server_path_response_rx_count=2
server_disable_active_migration_zero_count=1
client_path_validated_count=1
client_active_true_count=1
client_active_false_count=1
validation=ok
```

## 5. 핵심 evidence

| evidence | 결과 | 해석 |
| --- | --- | --- |
| HTTP/3 workload | access log `"GET /file-1M HTTP/3.0" 200 1048576` | nginx가 HTTP/3 request를 처리하고 1MiB body를 반환 |
| client response | `client_response_bytes=1048576` | application response body가 완전히 수신됨 |
| peer policy | `quic tp disable active migration: 0` | quiche client가 active migration을 금지하지 않음 |
| new path | `quic path seq:1 created addr:127.0.0.1:<port>` | nginx가 migrated source port를 새 path로 모델링 |
| client challenge response | server log `frame rx PATH_CHALLENGE`, `frame tx PATH_RESPONSE` | nginx가 client의 path validation probe에 응답 |
| server challenge response | server log `frame tx PATH_CHALLENGE`, `frame rx PATH_RESPONSE` | nginx도 새 path를 검증 |
| server validation | `quic path seq:1 ... successfully validated`, `is validated` | server-side path validation 완료 |
| client validation | `Path (...) is now validated` | quiche client도 새 path validation 완료 |
| final path state | old path `active=false`, new path `active=true` | client final summary에서 migrated path가 active |

대표 로그:

```text
access: "GET /file-1M HTTP/3.0" 200 1048576
client: Path (0.0.0.0:<new>, 127.0.0.1:<server>) is now validated
client: local_addr=0.0.0.0:<old> ... active=false, local_addr=0.0.0.0:<new> ... active=true
server: quic tp disable active migration: 0
server: quic path seq:1 created addr:127.0.0.1:<new>
server: quic frame rx app:5 PATH_CHALLENGE ...
server: quic frame tx app:1 PATH_RESPONSE ...
server: quic frame tx app:2 PATH_CHALLENGE ...
server: quic frame rx app:7 PATH_RESPONSE ...
server: quic path seq:1 addr:127.0.0.1:<new> successfully validated while handling frames
```

## 6. 해석

안전하게 쓸 수 있는 주장:

> nginx built with `--with-http_v3_module` accepted a quiche active source-port migration during a 1MiB HTTP/3 download on loopback. Server logs show path seq:1 creation, PATH_CHALLENGE/PATH_RESPONSE exchange, successful path validation, and continued response delivery on the validated path.

한국어 표현:

> nginx QUIC은 source-only 근거에 머물지 않고, loopback HTTP/3 runtime demo에서 quiche client의 active source-port migration을 처리했다. nginx debug log에는 새 path 생성, PATH_CHALLENGE/PATH_RESPONSE 교환, path validation 성공이 남았고, client는 1MiB 응답을 완전히 수신했다.

피해야 할 과장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| nginx에서 브라우저 Wi-Fi/LTE handover가 성공했다 | 이번 실험은 quiche sample client loopback 실험이지 Chrome/Safari/Android 실험이 아니다 |
| nginx가 client active migration API를 제공한다 | nginx는 server이며, active migration trigger는 quiche client가 수행했다 |
| production nginx deployment에서 그대로 보장된다 | local loopback, self-signed cert, 단일 server process 실험이다 |
| Linux `quic_bpf` deployment까지 검증했다 | macOS loopback runtime demo이며 eBPF packet routing 검증은 아니다 |

## 7. 논문에서의 위치

이 결과는 Chapter 1과 Chapter 3의 구현체 성숙도 근거를 보강한다.

| 이전 분류 | 보강 후 분류 |
| --- | --- |
| nginx QUIC: source-inspected server-side passive migration evidence | nginx QUIC: server-side runtime active-client-migration positive control |

다만 Chapter 4의 HAProxy negative-control과 함께 해석해야 한다. nginx runtime success는 "서버 구현체가 active client migration을 처리할 수 있다"는 근거이고, HAProxy negative-control은 "HTTP/3 endpoint/proxy support만으로 CM support를 추론할 수 없다"는 반례다.
