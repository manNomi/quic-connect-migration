# Non-iPhone Research Gap Plan

작성일: `2026-06-30`

이 문서는 현재 연구에서 아직 약한 부분을 iPhone 연결 없이 보강하기 위한 다음 실행 계획이다. 목표는 논문에서 “Connection Migration은 구현체 수준에서는 존재하지만, 실제 웹 작업 연속성으로 이어지려면 배포 경로와 runtime policy 검증이 필요하다”는 주장을 더 단단하게 만드는 것이다.

## 1. 현재까지 채워진 근거

| 영역 | 현재 상태 | 해석 |
| --- | --- | --- |
| 구현체 성숙도 survey | 18개 구현체/스택 정리 | CM은 구현체 수준에서 실재한다는 claim 가능 |
| fresh rerun/demo/negative-control | 13개 fresh rerun/demo/negative-control, 1개 partial build/test | quic-go 편중 약점과 proxy 반례 약점이 줄어듦 |
| LSQUIC | full CTest 79/79, selected CTest 5/5 PASS, preferred-address app demo `validation=ok`, NAT rebinding app demo `validation=ok` | source-only에서 server-stack unit evidence와 두 종류의 app-level path-transition evidence로 승격 |
| nginx QUIC | source audit + HTTP/3 runtime active-client-migration demo `validation=ok` | source-only에서 web-server runtime evidence로 승격 |
| HAProxy QUIC | HTTP/3 fresh negative-control `validation=ok_negative_control` | source/docs 반례에서 재현 가능한 proxy runtime 반례로 보강 |
| XQUIC | local client/server NAT rebinding demo PASS | NAT rebinding path가 실제 demo에서 동작함 |
| quicly | migration-related unit subtest OK, full/e2e partial | partial evidence로 분리해 과장 방지 |
| Chrome local controls | local forced-H3/rebinding/retry matrix 존재 | browser success claim은 아직 제한적 |

## 2. 아직 약한 부분

| 공백 | 왜 중요한가 | iPhone 없이 가능한가 |
| --- | --- | --- |
| LSQUIC OpenLiteSpeed production-like migration demo | preferred-address와 NAT rebinding example app demo는 확보했지만 production-like OpenLiteSpeed 경로는 아직 없음 | 가능 |
| mvfst fresh build/test or focused source audit | 대규모 deployment 구현체인데 아직 source inspection 중심 | 가능하나 빌드 비용 큼 |
| nginx QUIC production/Linux `quic_bpf` | nginx local runtime은 확보됐지만 production packet routing은 아직 약함 | 가능 |
| AWS NLB + s2n-quic CID routing 검증 | 교수님 decision의 AWS 구축 검수와 직접 연결 | 가능 |
| Chrome desktop public-origin simulation | iPhone 없이 browser/runtime policy의 한계를 보강 | 가능 |
| sanitized evidence bundle | raw log가 ignored path에 있어 심사/보고 시 재현 근거가 약해질 수 있음 | 가능 |

## 3. 우선순위 제안

### P1. LSQUIC app-level local demo

목표:

> LSQUIC이 unit suite만 통과하는 것이 아니라, HTTP/3 server/client workload에서 path change 또는 NAT rebinding을 관찰할 수 있는지 확인한다.

상태:

> 완료. `harness/scripts/run-lsquic-preferred-address-demo.sh`로 LSQUIC example `http_client`/`http_server` preferred-address migration demo를 재현했고, 최신 run `lsquic-preferred-address-script-20260630T095500Z`에서 `validation=ok`, `server_tx_stream_path1_count=565`, `max_client_read_off=1048835`를 확보했다. 이어서 `harness/scripts/run-lsquic-nat-rebinding-demo.sh`로 local UDP proxy NAT rebinding demo를 재현했고, 최신 run `lsquic-nat-rebinding-demo-20260630T102751Z`에서 `validation=ok`, `proxy_switched=true`, `server_record_new_path_count=1`, `server_path_validated_count=3`을 확보했다.

실행 방향:

1. 완료: LSQUIC repo의 `http_client`, `http_server` 실행 확인
2. 완료: server preferred address를 두 번째 UDP port로 광고해 path 1 migration 유도
3. 완료: preferred address, PATH_CHALLENGE/PATH_RESPONSE, path 1 STREAM, request completion 확인
4. 완료: local UDP proxy로 NAT rebinding path 재현
5. 남음: OpenLiteSpeed production-like 환경에서 path transition 재현

판정:

| 결과 | 해석 |
| --- | --- |
| request completes with path validation evidence | 완료: LSQUIC preferred-address 및 NAT-rebinding app-level positive control 확보 |
| request completes but path evidence 없음 | 단순 HTTP/3 success로만 분리 |
| path validation exists but request fails | transport/application continuity gap 근거 |
| setup cost too high | appendix candidate로 보류 |

### P2. AWS NLB + s2n-quic without iPhone

목표:

> mobile handover가 아니라도, AWS NLB passthrough에서 CID-aware routing과 QUIC path continuity 조건을 검증한다.

상태:

> 부분 완료. `experiments/s2n-quic-nlb-cid-provider` proof crate를 복원했고, `docs/results/s2n-quic-nlb-cid-provider-rerun-20260630.md`에 `cargo test` 3개 PASS와 local s2n-quic echo proof PASS를 정리했다. AWS live NLB target A/B forwarding은 아직 후속이다.

2026-06-30 추가 확인:

> `./harness/scripts/aws-preflight.sh` 실행 결과 현재 local AWS credential은 `invalid_client_token`으로 분류됐다. 따라서 live AWS NLB 재실행은 credential refresh 이후 진행한다.

실행 방향:

1. 완료: s2n-quic custom CID provider local proof 복원 및 rerun
2. 후속: EC2 server에서 s2n-quic 또는 quic-go HTTP/3 origin 구동
3. 후속: NLB `QUIC` 또는 `TCP_QUIC` target group 구성
4. 후속: desktop client에서 local source port rebinding 또는 multi-path client로 path change 유도
5. 후속: NLB가 같은 backend로 보냈는지 server log/qlog로 확인

핵심 질문:

| 질문 | 필요한 근거 |
| --- | --- |
| NLB가 QUIC CID를 보고 routing하는가? | target consistency, CID/server-id 설정 |
| tuple change 뒤 같은 backend로 가는가? | server instance id, qlog path validation |
| application payload가 이어지는가? | before/after payload checksum 또는 HTTP response completion |

### P3. nginx QUIC / HAProxy negative control

목표:

> HTTP/3을 지원한다는 사실과 Connection Migration을 지원한다는 사실은 다르다는 반례를 명확히 만든다.

상태:

> 완료. `docs/results/nginx-haproxy-quic-cm-boundary-20260630.md`에 nginx QUIC source/official-doc 기반 server-side passive migration evidence와 HAProxy official-doc/source/local negative-control evidence를 분리해 정리했다. 추가로 `harness/scripts/run-nginx-quic-active-migration-demo.sh`와 `docs/results/nginx-quic-active-migration-runtime-20260630.md`를 추가해 nginx HTTP/3 server runtime demo를 확보했다. 최신 nginx run `nginx-quic-active-migration-20260630T104724Z`는 `validation=ok`, `client_response_bytes=1048576`, `server_path_seq1_created_count=1`, `server_path_seq1_validated_count=2`, server/client PATH_CHALLENGE/PATH_RESPONSE evidence를 기록했다. 이어서 `harness/scripts/run-haproxy-http3-negative-control.sh`와 `docs/results/haproxy-http3-negative-control-rerun-20260630.md`를 추가해 HAProxy fresh negative-control도 확보했다. 최신 HAProxy run `haproxy-http3-negative-control-20260630T110201Z`는 ordinary H3 baseline PASS, quiche no-migration PASS, active migration path validation FAIL, qlog `path_challenge=3`, `path_response=0`을 기록했다.

실행 방향:

1. 완료: nginx QUIC source에서 server-side passive migration handling과 한계 정리
2. 완료: HAProxy 공식 문서/소스에서 migration unsupported 또는 제한 근거 고정
3. 완료: 기존 local proxy negative-control에서 ordinary H3 PASS, active migration FAIL, client qlog `PATH_RESPONSE=0` 확인
4. 완료: nginx HTTP/3 runtime demo에서 quiche active source-port migration, server path seq:1 validation, 1MiB response completion 확인
5. 완료: HAProxy fresh negative-control runner로 ordinary H3 PASS와 active migration FAIL 재현
6. 남음: Linux `quic_bpf` 기반 packet routing 또는 production-like nginx deployment 검증

논문 기여:

> HTTP/3 availability is not sufficient evidence of QUIC Connection Migration support.

### P4. mvfst focused maturity audit

목표:

> mvfst를 full build까지 못 하더라도, path manager, migration tests, qlog/stats 근거를 source-linked appendix로 정리한다.

상태:

> 완료. `docs/results/mvfst-cm-source-audit-20260630.md`에 `QuicPathManager`, client active probe/migration flow, server passive migration state machine, qlog/stat hook, migration-specific test files를 source-linked appendix로 정리했다.

실행 방향:

1. 완료: migration/path manager 관련 파일과 test 목록 고정
2. 완료: build/test는 이번 턴에서 실행하지 않고 dependency/build cost caveat로 분리
3. 완료: fresh PASS가 아니라 source-audited evidence로 분류

### P5. Chrome desktop public-origin simulation

목표:

> iPhone 없이 Chrome desktop에서 public-origin, forced-H3, local route/proxy change가 browser-visible continuity로 이어지는지 검증한다.

실행 방향:

1. 기존 Chrome local forced-H3 matrix 재사용
2. public origin 또는 local HTTPS origin에서 upload/download/range/media workload 반복
3. NetLog에서 QUIC session 수, path validation event, retry 여부 분류

주의:

> retry로 완료된 작업은 single-session CM 성공으로 쓰지 않는다.

## 4. 다음 실행 순서

| 순서 | 작업 | 이유 |
| ---: | --- | --- |
| 1 | nginx/HAProxy negative-control source+doc appendix + nginx runtime demo | 완료. HTTP/3 support와 CM support의 경계를 강화했고 nginx server runtime positive control 확보 |
| 2 | OpenLiteSpeed production-like demo | LSQUIC example binary와 production-like server 경계 확인 |
| 3 | AWS NLB + s2n-quic desktop/client path-change 설계 | 교수님 decision의 AWS 검증과 직접 연결. 현재 credential refresh 필요 |
| 4 | Linux nginx `quic_bpf` 또는 production-like nginx deployment test | nginx local runtime evidence를 deployment 쪽으로 확장 |
| 5 | sanitized evidence bundle 생성 | 보고/논문 제출용 재현성 강화 |

## 5. 바로 다음 턴의 권장 작업

다음 턴에서는 OpenLiteSpeed production-like demo를 우선 진행하는 것이 좋다. AWS credential이 refresh되면 live NLB+s2n target forwarding으로 넘어간다. nginx/HAProxy boundary appendix, nginx runtime demo, HAProxy fresh negative-control, LSQUIC preferred-address/NAT-rebinding app demo는 확보됐다.
