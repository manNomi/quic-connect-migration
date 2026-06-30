# nginx QUIC / HAProxy Connection Migration Boundary

작성일: `2026-06-30`

## 1. 목적

이 문서는 iPhone 연결 없이 보강할 수 있는 연구 공백 중 하나인 proxy/server 계층의 Connection Migration boundary를 정리한다.

핵심 질문은 다음이다.

> HTTP/3 endpoint가 동작한다는 사실만으로 QUIC Connection Migration이 지원된다고 볼 수 있는가?

현재 근거 기준의 답은 `no`다. nginx QUIC은 source inspection에 더해 local runtime demo에서 quiche client의 active source-port migration을 처리했다. 반면 HAProxy는 공식 문서와 로컬 negative-control 결과상 HTTP/3 proxy support와 active Connection Migration support를 분리해서 보아야 한다.

## 2. 검사 대상과 버전

| 대상 | 역할 | 기준 commit / version | 검수 범위 |
| --- | --- | --- | --- |
| nginx QUIC | web server | `072f6fdbac3323fab257280b7119224027b01315`, runtime run `nginx-quic-active-migration-20260630T104724Z` | official docs + source inspection + runtime demo |
| HAProxy QUIC | reverse proxy / H3 frontend | source `ff6bb343f4a9c8dc38b2917ab1dd70785314b625`, local negative control `HAProxy 3.4.0-64a335366` | official docs + source inspection + existing local negative-control |

검수 명령:

```bash
git -C /private/tmp/quic-cm-scan-repos/nginx rev-parse HEAD
git -C /private/tmp/quic-cm-scan-repos/haproxy fetch origin
git -C /private/tmp/quic-cm-scan-repos/haproxy rev-parse origin/master

rg -n "migration|migrat|PATH_CHALLENGE|PATH_RESPONSE|disable_active_migration|preferred_address|rebinding" \
  /private/tmp/quic-cm-scan-repos/nginx/src/event/quic \
  /private/tmp/quic-cm-scan-repos/nginx/src/http/v3

rg -n "connection migration|disable_active_migration|PATH_CHALLENGE|PATH_RESPONSE|path validation|migrat|rebinding" \
  /private/tmp/quic-cm-scan-repos/haproxy/doc \
  /private/tmp/quic-cm-scan-repos/haproxy/src

harness/scripts/run-nginx-quic-active-migration-demo.sh
```

## 3. nginx QUIC 결과

nginx 공식 HTTP/3 문서는 `quic_bpf` directive가 QUIC packet routing을 활성화하고, 이것이 QUIC connection migration 지원을 가능하게 한다고 설명한다.

확인한 공식/소스 근거:

| 근거 | 위치 | 의미 |
| --- | --- | --- |
| HTTP/3 module docs | [nginx ngx_http_v3_module](https://nginx.org/en/docs/http/ngx_http_v3_module.html) | nginx가 HTTP/3/QUIC module을 제공하고 `quic_bpf`를 문서화 |
| `quic_bpf` docs | [directive docs](https://nginx.org/en/docs/http/ngx_http_v3_module.html#quic_bpf) | Linux eBPF 기반 packet routing과 migration support 연결 |
| source migration file | [ngx_event_quic_migration.c](https://github.com/nginx/nginx/blob/072f6fdbac3323fab257280b7119224027b01315/src/event/quic/ngx_event_quic_migration.c) | PATH_CHALLENGE/RESPONSE, new path, NAT rebinding, path switch 처리 |
| HTTP/3 server conf | [ngx_http_v3_module.c](https://github.com/nginx/nginx/blob/072f6fdbac3323fab257280b7119224027b01315/src/http/v3/ngx_http_v3_module.c#L189-L195) | server config에서 `disable_active_migration` 기본값이 unset/0로 시작 |
| transport parameter handling | [ngx_event_quic_transport.c](https://github.com/nginx/nginx/blob/072f6fdbac3323fab257280b7119224027b01315/src/event/quic/ngx_event_quic_transport.c#L1630-L1636) | peer의 `disable_active_migration` transport parameter parse |

소스에서 확인한 migration 흐름:

| 소스 흐름 | 확인 내용 | 해석 |
| --- | --- | --- |
| `ngx_quic_handle_path_challenge_frame` | PATH_CHALLENGE 수신 시 같은 path로 PATH_RESPONSE 전송 | peer path validation에 응답 가능 |
| `ngx_quic_handle_path_response_frame` | PATH_RESPONSE가 pending challenge와 일치하면 path validation 성공 처리 | path validation state machine 존재 |
| new path handling | unknown path packet을 probe path로 등록하고 client id 필요성을 검사 | tuple change를 별도 path로 모델링 |
| NAT rebinding branch | 이전에 본 DCID로 새 path에서 packet이 오면 NAT rebinding으로 표시 | passive migration/NAT rebinding handling 근거 |
| `ngx_quic_handle_migration` | non-probing packet이 non-active path로 오면 active path switch 및 validation 수행 | server-side passive migration handling 근거 |
| validation failure handling | active path validation 실패 시 last validated backup path로 복귀 | failure control path 존재 |

런타임 demo 결과:

| 항목 | 결과 |
| --- | --- |
| run id | `nginx-quic-active-migration-20260630T104724Z` |
| nginx build | `nginx/1.31.3`, `--with-http_v3_module`, `--with-debug` |
| client | quiche `--enable-active-migration --perform-migration` |
| workload | `GET /file-1M`, 1MiB HTTP/3 response |
| response bytes | `1048576` |
| access log | `"GET /file-1M HTTP/3.0" 200 1048576` |
| server new path | `quic path seq:1 created` |
| path validation | server/client `PATH_CHALLENGE`/`PATH_RESPONSE`, `successfully validated` |
| client final state | old path `active=false`, new path `active=true` |
| validation | `validation=ok` |

판정:

> nginx QUIC은 server-side passive migration 또는 NAT rebinding 처리 근거가 소스에 명확하고, local runtime demo에서도 quiche client의 active source-port migration을 HTTP/3 workload 중 처리했다. 다만 browser handover, Linux `quic_bpf` routing, production nginx deployment까지 검증한 것은 아니므로, 논문에서는 `server-side runtime positive control`로 제한해서 분류해야 한다.

## 4. HAProxy 결과

HAProxy 공식 configuration 문서는 HTTP/3가 QUIC 위에 구현되어 있고 QUIC이 connection migration support를 제공하지만, HAProxy는 현재 이를 지원하지 않는다고 설명한다.

확인한 공식/소스 근거:

| 근거 | 위치 | 의미 |
| --- | --- | --- |
| official configuration docs | [HAProxy configuration manual](https://docs.haproxy.org/3.2/configuration.html) | HTTP/3/QUIC 설명에서 HAProxy의 connection migration 미지원 문구 확인 |
| current source doc line | [haproxy doc/configuration.txt](https://github.com/haproxy/haproxy/blob/ff6bb343f4a9c8dc38b2917ab1dd70785314b625/doc/configuration.txt#L269-L273) | current master 문서에도 같은 boundary 존재 |
| migration handler | [src/quic_conn.c](https://github.com/haproxy/haproxy/blob/ff6bb343f4a9c8dc38b2917ab1dd70785314b625/src/quic_conn.c#L1401-L1458) | client-initiated migration detection/handler source exists |
| server transport parameter default | [src/quic_tp.c](https://github.com/haproxy/haproxy/blob/ff6bb343f4a9c8dc38b2917ab1dd70785314b625/src/quic_tp.c#L110-L113) | server side default에서 `disable_active_migration` set |
| transport parameter encode | [src/quic_tp.c](https://github.com/haproxy/haproxy/blob/ff6bb343f4a9c8dc38b2917ab1dd70785314b625/src/quic_tp.c#L625-L628) | `disable_active_migration` transport parameter encode path |
| local negative control | [haproxy-http3-negative-control-results-20260623.md](haproxy-http3-negative-control-results-20260623.md) | ordinary H3 PASS, quiche active migration FAIL |

로컬 negative-control 요약:

| 항목 | 결과 |
| --- | --- |
| HAProxy H3 endpoint | curl `--http3-only` PASS, `HTTP/3 200` |
| quiche no-migration request | PASS, response received |
| quiche `--perform-migration` | FAIL as expected |
| qlog | `PATH_CHALLENGE` 3회, `PATH_RESPONSE` 0회 |
| client path state | new path `validation_state=Failed active=false` |

판정:

> HAProxy는 HTTP/3 proxy endpoint로 동작할 수 있지만, tested build에서는 quiche active migration 시도가 path validation failure로 끝났다. current source에는 migration handler와 counters가 보이므로 "소스에 관련 코드가 전혀 없다"고 말하면 안 된다. 안전한 결론은 "공식 문서와 local negative-control 기준으로 HAProxy HTTP/3 support는 active Connection Migration support의 증거가 아니다"이다.

## 5. nginx와 HAProxy 비교

| 항목 | nginx QUIC | HAProxy QUIC |
| --- | --- | --- |
| 계층 | origin/web server | reverse proxy / H3 frontend |
| HTTP/3 support | yes | yes |
| official docs에서 CM 관련 문구 | `quic_bpf`가 migration support와 연결됨 | HAProxy는 현재 connection migration을 지원하지 않는다고 설명 |
| PATH_CHALLENGE/RESPONSE frame handling | yes | yes, frame primitive exists |
| server-side passive migration source flow | yes, `ngx_event_quic_migration.c` | partial/limited, handler exists but docs and local negative-control constrain claim |
| active client migration local result | quiche client active migration runtime demo PASS | negative-control FAIL |
| 논문 분류 | server-side runtime positive control | proxy negative control |

## 6. 논문에서 사용할 수 있는 문장

안전한 문장:

> HTTP/3 support alone is not sufficient evidence of QUIC Connection Migration support. In our HAProxy negative-control setup, ordinary HTTP/3 requests succeeded, while an active migration attempt failed path validation. Conversely, nginx source and official documentation show server-side mechanisms for passive migration and path validation, and our local runtime demo confirms that nginx can handle a quiche active source-port migration during a 1MiB HTTP/3 response. This does not imply browser or production deployment success.

한국어 표현:

> HTTP/3 지원은 Connection Migration 지원의 충분조건이 아니다. HAProxy negative-control에서는 일반 HTTP/3 요청은 성공했지만 active migration 시도는 path validation 실패로 끝났다. 반면 nginx QUIC은 소스와 공식 문서에서 server-side passive migration 및 path validation 처리 근거가 확인됐고, local runtime demo에서도 quiche client의 active source-port migration 중 1MiB HTTP/3 응답을 완료했다. 다만 이는 브라우저 또는 production deployment 성공을 의미하지 않는다.

피해야 할 문장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| nginx에서 브라우저 handover가 성공했다 | 이번 검수는 quiche sample client 기반 local runtime demo이며 browser handover가 아니다. |
| HAProxy 소스에는 migration 관련 구현이 없다 | handler/counter/frame primitive는 존재한다. |
| HAProxy는 모든 버전에서 영원히 CM을 지원하지 않는다 | current docs와 tested build에 대한 claim으로 제한해야 한다. |
| HTTP/3 proxy가 있으면 end-to-end CM도 된다 | proxy termination은 viewer-proxy와 proxy-origin continuity를 분리한다. |

## 7. 연구 기여

이 appendix는 Chapter 2와 Chapter 4의 claim boundary를 강화한다.

1. 구현체 수준에서 CM primitive가 넓게 존재한다는 Chapter 1 결론과 모순되지 않는다.
2. HTTP/3 availability와 CM availability를 분리해야 한다는 Chapter 2 friction claim을 강화한다.
3. proxy/CDN/LB deployment에서 end-to-end CM을 별도로 검증해야 한다는 Chapter 4 설계를 뒷받침한다.

후속 작업은 HAProxy 최신 빌드 negative-control 재실행, Linux `quic_bpf`가 있는 nginx deployment test, 또는 OpenLiteSpeed production-like demo다. 모두 iPhone 없이 가능하지만, browser handover claim과는 분리해야 한다.
