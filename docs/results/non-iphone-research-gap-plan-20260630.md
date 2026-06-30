# Non-iPhone Research Gap Plan

작성일: `2026-06-30`

이 문서는 현재 연구에서 아직 약한 부분을 iPhone 연결 없이 보강하기 위한 다음 실행 계획이다. 목표는 논문에서 “Connection Migration은 구현체 수준에서는 존재하지만, 실제 웹 작업 연속성으로 이어지려면 배포 경로와 runtime policy 검증이 필요하다”는 주장을 더 단단하게 만드는 것이다.

## 1. 현재까지 채워진 근거

| 영역 | 현재 상태 | 해석 |
| --- | --- | --- |
| 구현체 성숙도 survey | 18개 구현체/스택 정리 | CM은 구현체 수준에서 실재한다는 claim 가능 |
| fresh rerun/demo | 11개 fresh rerun/demo, 1개 partial build/test | quic-go 편중 약점이 줄어듦 |
| LSQUIC | full CTest 79/79, selected CTest 5/5 PASS, preferred-address app demo `validation=ok` | source-only에서 server-stack unit evidence와 preferred-address app-level evidence로 승격 |
| XQUIC | local client/server NAT rebinding demo PASS | NAT rebinding path가 실제 demo에서 동작함 |
| quicly | migration-related unit subtest OK, full/e2e partial | partial evidence로 분리해 과장 방지 |
| Chrome local controls | local forced-H3/rebinding/retry matrix 존재 | browser success claim은 아직 제한적 |

## 2. 아직 약한 부분

| 공백 | 왜 중요한가 | iPhone 없이 가능한가 |
| --- | --- | --- |
| LSQUIC NAT rebinding/OpenLiteSpeed app-level migration demo | preferred-address app demo는 확보했지만 NAT rebinding과 production-like OpenLiteSpeed 경로는 아직 없음 | 가능 |
| mvfst fresh build/test or focused source audit | 대규모 deployment 구현체인데 아직 source inspection 중심 | 가능하나 빌드 비용 큼 |
| nginx QUIC / HAProxy negative-control 정리 | HTTP/3 지원과 CM 지원이 다르다는 반례를 강화 | 가능 |
| AWS NLB + s2n-quic CID routing 검증 | 교수님 decision의 AWS 구축 검수와 직접 연결 | 가능 |
| Chrome desktop public-origin simulation | iPhone 없이 browser/runtime policy의 한계를 보강 | 가능 |
| sanitized evidence bundle | raw log가 ignored path에 있어 심사/보고 시 재현 근거가 약해질 수 있음 | 가능 |

## 3. 우선순위 제안

### P1. LSQUIC app-level local demo

목표:

> LSQUIC이 unit suite만 통과하는 것이 아니라, HTTP/3 server/client workload에서 path change 또는 NAT rebinding을 관찰할 수 있는지 확인한다.

상태:

> 완료. `harness/scripts/run-lsquic-preferred-address-demo.sh`로 LSQUIC example `http_client`/`http_server` preferred-address migration demo를 재현했고, 최신 run `lsquic-preferred-address-script-20260630T095500Z`에서 `validation=ok`, `server_tx_stream_path1_count=565`, `max_client_read_off=1048835`를 확보했다.

실행 방향:

1. 완료: LSQUIC repo의 `http_client`, `http_server` 실행 확인
2. 완료: server preferred address를 두 번째 UDP port로 광고해 path 1 migration 유도
3. 완료: preferred address, PATH_CHALLENGE/PATH_RESPONSE, path 1 STREAM, request completion 확인
4. 남음: local UDP proxy 또는 OpenLiteSpeed 환경에서 NAT rebinding path 재현

판정:

| 결과 | 해석 |
| --- | --- |
| request completes with path validation evidence | 완료: LSQUIC preferred-address app-level positive control 확보 |
| request completes but path evidence 없음 | 단순 HTTP/3 success로만 분리 |
| path validation exists but request fails | transport/application continuity gap 근거 |
| setup cost too high | appendix candidate로 보류 |

### P2. AWS NLB + s2n-quic without iPhone

목표:

> mobile handover가 아니라도, AWS NLB passthrough에서 CID-aware routing과 QUIC path continuity 조건을 검증한다.

실행 방향:

1. EC2 server에서 s2n-quic 또는 quic-go HTTP/3 origin 구동
2. NLB UDP/TCP_UDP listener 구성
3. desktop client에서 local source port rebinding 또는 multi-path client로 path change 유도
4. NLB가 같은 backend로 보냈는지 server log/qlog로 확인

핵심 질문:

| 질문 | 필요한 근거 |
| --- | --- |
| NLB가 QUIC CID를 보고 routing하는가? | target consistency, CID/server-id 설정 |
| tuple change 뒤 같은 backend로 가는가? | server instance id, qlog path validation |
| application payload가 이어지는가? | before/after payload checksum 또는 HTTP response completion |

### P3. nginx QUIC / HAProxy negative control

목표:

> HTTP/3을 지원한다는 사실과 Connection Migration을 지원한다는 사실은 다르다는 반례를 명확히 만든다.

실행 방향:

1. nginx QUIC source에서 server-side passive migration handling과 한계 정리
2. HAProxy 공식 문서/소스에서 migration unsupported 또는 제한 근거 고정
3. 가능하면 local proxy path에서 migration attempt가 실패하거나 새 connection으로 분리되는 로그 확보

논문 기여:

> HTTP/3 availability is not sufficient evidence of QUIC Connection Migration support.

### P4. mvfst focused maturity audit

목표:

> mvfst를 full build까지 못 하더라도, path manager, migration tests, qlog/stats 근거를 source-linked appendix로 정리한다.

실행 방향:

1. migration/path manager 관련 파일과 test 목록 고정
2. build 가능성 빠른 점검
3. 실패하면 dependency caveat와 source evidence를 분리

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
| 1 | nginx/HAProxy negative-control source+doc appendix | 빠르게 논문 claim boundary를 강화할 수 있음 |
| 2 | LSQUIC NAT rebinding 또는 OpenLiteSpeed production-like demo | preferred-address app demo 다음의 LSQUIC 남은 공백 |
| 3 | AWS NLB + s2n-quic desktop/client path-change 설계 | 교수님 decision의 AWS 검증과 직접 연결 |
| 4 | mvfst focused audit | 대규모 구현체 coverage를 보강 |
| 5 | sanitized evidence bundle 생성 | 보고/논문 제출용 재현성 강화 |

## 5. 바로 다음 턴의 권장 작업

다음 턴에서는 nginx/HAProxy negative-control source+doc appendix를 먼저 진행하는 것이 좋다. LSQUIC preferred-address app demo는 이미 확보했으므로, 이제는 HTTP/3 지원이 CM 지원을 의미하지 않는다는 반례를 강화해 논문 claim boundary를 더 단단하게 만들 차례다.
