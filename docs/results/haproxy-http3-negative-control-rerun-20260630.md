# HAProxy HTTP/3 Negative Control Rerun

작성일: `2026-06-30`

## 1. 목적

이 실험의 목적은 HAProxy HTTP/3 endpoint가 일반 HTTP/3 request는 처리하지만, active Connection Migration support의 증거가 되지는 않는다는 negative-control을 재현 가능한 runner로 고정하는 것이다.

기존 `haproxy-http3-negative-control-results-20260623.md`는 수동 실험 결과였다. 이번 보강에서는 `harness/scripts/run-haproxy-http3-negative-control.sh`를 추가해 같은 반례를 fresh artifact로 다시 만든다.

## 2. 실행 환경

| 항목 | 값 |
| --- | --- |
| HAProxy binary | `/opt/homebrew/bin/haproxy` |
| HAProxy version | `3.4.0-64a335366` |
| HAProxy build | `USE_QUIC=1`, feature `+QUIC` |
| TLS library | OpenSSL `3.6.2` |
| HAProxy source clone | `/private/tmp/quic-cm-scan-repos/haproxy` |
| HAProxy source commit | `b68be6d0a2816c71137c53d2c958be9c93bef3ea` |
| HAProxy source date | `2026-06-29T16:04:57+02:00` |
| HAProxy source subject | `BUG/MINOR: hq-interop: support transcoding of absolute URI` |
| client | `/private/tmp/quic-cm-impl-rerun-20260630/quiche/target/debug/quiche-client` |
| curl | `/opt/homebrew/opt/curl/bin/curl`, HTTP/3 capable |
| origin | Python `http.server` on loopback |
| artifact root | `harness/results/haproxy-http3-negative-control-20260630T110201Z` |

## 3. 재현 명령

현재 repo에서 다음 명령으로 재현한다.

```bash
harness/scripts/run-haproxy-http3-negative-control.sh
```

스크립트가 하는 일:

| 단계 | 설명 |
| --- | --- |
| 1 | self-signed certificate와 simple origin HTML 생성 |
| 2 | Python HTTP/1.1 origin server 실행 |
| 3 | HAProxy `bind quic4@127.0.0.1:<port> ssl crt ... alpn h3` frontend 실행 |
| 4 | curl `--http3-only` baseline으로 HTTP/3 endpoint 확인 |
| 5 | quiche no-migration baseline으로 quiche/HAProxy ordinary H3 interop 확인 |
| 6 | quiche `--enable-active-migration --perform-migration`으로 active migration 시도 |
| 7 | client final path state와 qlog path frame을 negative-control 조건으로 검증 |

## 4. 최신 실행 결과

```text
run_id=haproxy-http3-negative-control-20260630T110201Z
curl_exit=0
curl_http3_count=2
curl_body_count=1
quiche_baseline_exit=0
quiche_baseline_body_count=1
quiche_baseline_response_count=1
quiche_baseline_valid_active_count=1
quiche_migration_exit=0
quiche_migration_failed_log_count=1
quiche_migration_failed_inactive_count=1
quiche_migration_original_active_count=1
qlog_path_challenge_count=3
qlog_path_response_count=0
validation=ok_negative_control
```

## 5. 핵심 evidence

| evidence | 결과 | 해석 |
| --- | --- | --- |
| curl HTTP/3 baseline | `curl_exit=0`, `using HTTP/3`, `HTTP/3 200` | HAProxy endpoint가 HTTP/3 request를 처리 |
| quiche no-migration baseline | `1/1 response(s) received`, `validation_state=Validated active=true` | quiche와 HAProxy가 ordinary H3 request에서는 interop |
| migration path failure | `Path (...) failed validation` | active migrated path validation 실패 |
| final path state | original path `Validated active=true`, migrated path `Failed active=false` | connection은 original path에 남고 migrated path는 실패 |
| qlog path challenge | `path_challenge=3` | client가 migrated path probe를 보냄 |
| qlog path response | `path_response=0` | migrated path probe에 대한 response가 관찰되지 않음 |

대표 로그:

```text
curl: using HTTP/3
curl: < HTTP/3 200
quiche baseline: 1/1 response(s) received
quiche migration: Path (0.0.0.0:<new>, 127.0.0.1:<haproxy>) failed validation
quiche migration: validation_state=Validated active=true, validation_state=Failed active=false
qlog: frame_type=path_challenge
qlog: no path_response
```

## 6. 해석

안전하게 쓸 수 있는 주장:

> In the HAProxy local negative-control rerun, ordinary HTTP/3 requests succeeded through HAProxy, but a quiche active source-port migration attempt failed path validation. The client qlog contains three `path_challenge` frames and no `path_response`, and the final client path summary marks the migrated path as `validation_state=Failed active=false`.

한국어 표현:

> HAProxy는 HTTP/3 proxy endpoint로는 동작하지만, 이번 fresh negative-control에서는 active Connection Migration을 유지하지 못했다. curl과 quiche no-migration request는 성공했지만, quiche active migration 시도는 새 path validation 실패로 끝났고 qlog에는 `path_challenge`만 3회, `path_response`는 0회였다.

피해야 할 과장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| HAProxy에는 migration 관련 코드가 전혀 없다 | source에는 handler/primitive가 있으므로 부정확하다 |
| 모든 미래 HAProxy 버전에서 CM은 불가능하다 | tested build와 current docs/source 기준 claim으로 제한해야 한다 |
| quiche migration command exit `0`이면 CM 성공이다 | request completion과 migrated path validation은 다르다. final path state가 `Failed active=false`다 |
| HTTP/3 endpoint success가 CM support다 | 이 실험의 핵심 반례와 충돌한다 |

## 7. 논문에서의 위치

이 결과는 Chapter 4 deployment boundary의 negative control이다.

| 비교 대상 | 결과 |
| --- | --- |
| nginx QUIC server runtime demo | active client migration을 server-side에서 처리하고 1MiB HTTP/3 response 완료 |
| HAProxy HTTP/3 proxy negative-control | ordinary H3는 PASS지만 active migrated path validation FAIL |

따라서 논문에서는 다음 문장으로 제한해서 쓸 수 있다.

> HTTP/3 support alone is insufficient evidence of QUIC Connection Migration support; proxy termination and endpoint migration policy must be evaluated separately.
