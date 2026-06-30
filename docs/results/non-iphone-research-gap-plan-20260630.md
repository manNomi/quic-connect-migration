# Non-iPhone Research Gap Plan

작성일: `2026-06-30`

이 문서는 현재 연구에서 아직 약한 부분을 iPhone 연결 없이 보강하기 위한 다음 실행 계획이다. 목표는 논문에서 “Connection Migration은 구현체 수준에서는 존재하지만, 실제 웹 작업 연속성으로 이어지려면 배포 경로와 runtime policy 검증이 필요하다”는 주장을 더 단단하게 만드는 것이다.

## 1. 현재까지 채워진 근거

| 영역 | 현재 상태 | 해석 |
| --- | --- | --- |
| 구현체 성숙도 survey | 18개 구현체/스택 정리 | CM은 구현체 수준에서 실재한다는 claim 가능 |
| fresh rerun/demo/negative-control | 13개 fresh rerun/demo/negative-control, 1개 partial build/test | quic-go 편중 약점과 proxy 반례 약점이 줄어듦 |
| LSQUIC | full CTest 79/79, selected CTest 5/5 PASS, preferred-address app demo `validation=ok`, NAT rebinding app demo `validation=ok` | source-only에서 server-stack unit evidence와 두 종류의 app-level path-transition evidence로 승격 |
| OpenLiteSpeed | source feasibility audit + runtime preflight + Linux/EC2 runtime runner 추가, local blocked result `missing-openlitespeed-binary` | follow-up target은 타당하고 실행 packet은 준비됐지만 현재 macOS local runtime gate는 닫힘 |
| nginx QUIC | source audit + HTTP/3 runtime active-client-migration demo `validation=ok` | source-only에서 web-server runtime evidence로 승격 |
| HAProxy QUIC | HTTP/3 fresh negative-control `validation=ok_negative_control` | source/docs 반례에서 재현 가능한 proxy runtime 반례로 보강 |
| XQUIC | local client/server NAT rebinding demo PASS | NAT rebinding path가 실제 demo에서 동작함 |
| quicly | migration-related unit subtest OK, focused e2e `path-migration` PASS, full e2e `slow-start` caveat | full e2e PASS가 아니라 focused migration evidence로 분리해 과장 방지 |
| mvfst | source audit + focused migration test readiness map | production-scale 구현체의 실행 후보 test target과 현재 blocker를 고정 |
| Chrome local controls | local forced-H3/rebinding/retry matrix 존재 | browser success claim은 아직 제한적 |

## 2. 아직 약한 부분

| 공백 | 왜 중요한가 | iPhone 없이 가능한가 |
| --- | --- | --- |
| LSQUIC OpenLiteSpeed production-like migration demo | preferred-address와 NAT rebinding example app demo는 확보했지만 production-like OpenLiteSpeed 경로는 아직 없음 | 가능 |
| mvfst fresh build/test or focused source audit | 대규모 deployment 구현체인데 아직 source inspection 중심 | 가능하나 빌드 비용 큼 |
| nginx QUIC production/Linux `quic_bpf` | nginx local runtime은 확보됐지만 production packet routing은 아직 약함 | 가능 |
| AWS NLB + s2n-quic CID routing 검증 | 교수님 decision의 AWS 구축 검수와 직접 연결. dedicated runner는 준비됐고 live 실행은 AWS identity 갱신 필요 | 가능 |
| Chrome desktop public-origin simulation | iPhone 없이 browser/runtime policy의 한계를 보강 | 가능 |
| sanitized evidence bundle | raw log가 ignored path에 있어 심사/보고 시 재현 근거가 약해질 수 있음 | 완료 |

## 3. 우선순위 제안

### P1. LSQUIC app-level local demo

목표:

> LSQUIC이 unit suite만 통과하는 것이 아니라, HTTP/3 server/client workload에서 path change 또는 NAT rebinding을 관찰할 수 있는지 확인한다.

상태:

> 완료. `harness/scripts/run-lsquic-preferred-address-demo.sh`로 LSQUIC example `http_client`/`http_server` preferred-address migration demo를 재현했고, 최신 run `lsquic-preferred-address-script-20260630T095500Z`에서 `validation=ok`, `server_tx_stream_path1_count=565`, `max_client_read_off=1048835`를 확보했다. 이어서 `harness/scripts/run-lsquic-nat-rebinding-demo.sh`로 local UDP proxy NAT rebinding demo를 재현했고, 최신 run `lsquic-nat-rebinding-demo-20260630T102751Z`에서 `validation=ok`, `proxy_switched=true`, `server_record_new_path_count=1`, `server_path_validated_count=3`을 확보했다.

2026-06-30 추가 확인:

> `docs/results/openlitespeed-quic-cm-source-feasibility-20260630.md`에 OpenLiteSpeed source feasibility audit를 추가했다. OpenLiteSpeed `f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379`는 `LSQUIC_SERVER_MODE`, `quicEnable 1`, `lsquic_engine_new(LSENG_HTTP_SERVER, &api)`, SCID lifecycle callback, CID/PID shared-memory mapping을 갖고 있고, `LSQUICCOMMIT`이 현재 검수한 LSQUIC `f8ebaf838d2f4db836bda1182ee35b05d5191cee`와 일치한다. 이어서 `harness/scripts/openlitespeed-runtime-preflight.sh`를 추가해 실행했고, 최신 run `openlitespeed-runtime-preflight-20260630T120037Z`는 `runtime_ready=no`, `submodule_ready=no`, `binary_ready=no`, `linux_recommended_ready=no`, `dev_shm_ready=no`, `disk_ready=no`, `disk_free_gib=19.58`로 판정했다. 추가로 OpenLiteSpeed build 여유를 확보할 수 있는지 cleanup dry-run을 실행했고, `docs/results/artifact-cleanup-dry-run-20260630-openlitespeed-preflight.md` 기준 review-unreferenced 후보 전체를 지워도 `27.7GiB`까지만 올라가 `30GiB` 목표에 `2.3GiB` 부족하다. 마지막으로 `harness/scripts/run-openlitespeed-active-migration-demo.sh`를 추가해 Linux/EC2 runtime demo packet을 준비했고, 현재 로컬 실행은 `openlitespeed-active-migration-local-blocked-20260630`에서 `validation=blocked`, `blocked_reason=missing-openlitespeed-binary`로 고정했다. 따라서 runtime build/demo는 Linux/EC2 환경을 우선하거나, referenced raw artifact archive 정책을 정한 뒤 진행한다.

실행 방향:

1. 완료: LSQUIC repo의 `http_client`, `http_server` 실행 확인
2. 완료: server preferred address를 두 번째 UDP port로 광고해 path 1 migration 유도
3. 완료: preferred address, PATH_CHALLENGE/PATH_RESPONSE, path 1 STREAM, request completion 확인
4. 완료: local UDP proxy로 NAT rebinding path 재현
5. 완료: OpenLiteSpeed source feasibility audit로 production-like follow-up target 타당성 확인
6. 완료: OpenLiteSpeed runtime preflight로 현재 local blocker를 기계적으로 고정
7. 완료: OpenLiteSpeed build 전 cleanup dry-run으로 안전 후보만으로는 30GiB 목표 미달 확인
8. 완료: OpenLiteSpeed Linux/EC2 active-migration runtime runner 추가 및 local blocked result 고정
9. 남음: OpenLiteSpeed production-like runtime 환경에서 path transition 재현

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

> 부분 완료. `experiments/s2n-quic-nlb-cid-provider` proof crate를 복원했고, `docs/results/s2n-quic-nlb-cid-provider-rerun-20260630.md`에 `cargo test` 3개 PASS와 local s2n-quic echo proof PASS를 정리했다. 추가로 `harness/scripts/check-s2n-nlb-live-readiness.sh`와 `docs/results/s2n-nlb-live-readiness-20260630.md`를 추가해 live AWS NLB+s2n 실험 전제 조건을 fail-closed로 고정했다. 이번 보강에서 `harness/scripts/run-aws-s2n-nlb-live-data-plane.sh`, `nlb_live_server`, `nlb_live_client`, `generate_localhost_cert`를 추가해 dedicated live runner까지 준비했다. AWS live NLB target A/B forwarding은 현재 credential 때문에 아직 후속이다.

2026-06-30 추가 확인:

> `./harness/scripts/aws-preflight.sh` 실행 결과 현재 local AWS credential은 `invalid_client_token`으로 분류됐다. 이후 `RUN_ID=s2n-nlb-live-readiness-after-runner-proof-20260630 harness/scripts/check-s2n-nlb-live-readiness.sh`를 실행했고, 결과는 `aws_identity_ok=no`, `aws_identity_classification=invalid_client_token`, `local_proof_status=PASS`, `local_proof_echo_matches=yes`, `existing_quic_go_nlb_runner_ready=yes`, `s2n_live_nlb_runner_ready=yes`, `can_run_live_s2n_nlb_now=no`, `blocked_reason=aws_identity_invalid_client_token`이었다. 또한 `RUN_ID=aws-s2n-nlb-live-local-blocked-20260630 harness/scripts/run-aws-s2n-nlb-live-data-plane.sh`는 `crate_ready=yes`, `server_binary_source_ready=yes`, `client_binary_source_ready=yes`, `validation=blocked`, `blocked_reason=aws_identity_invalid_client_token`으로 AWS resource 생성 전에 닫혔다. 따라서 live AWS NLB 재실행은 credential refresh 이후 진행한다.

2026-06-30 live binary smoke:

> 새 `nlb_live_server`와 `nlb_live_client`는 AWS 없이 loopback에서 `payload_bytes=2048`, `echo_matches=true`, server `received_bytes=2048`, `echoed_bytes=2048`로 PASS했다. 이 smoke는 NLB routing proof가 아니라 dedicated live runner에 들어가는 s2n binary들이 같은 TLS/CID-provider 전제로 동작한다는 검증이다.

2026-06-30 active migration API audit:

> `tools/audit_s2n_active_migration_feasibility.py`를 추가해 s2n-quic `0f5a4f8ae4163f1b84e72cd29ad110ad99d7efd1` checkout을 source-linked 방식으로 감사했다. focused `connection_migration` test는 현재 host에서 `10 passed; 0 failed; 90 filtered out`로 재확인됐다. 그러나 `quic/s2n-quic/src/provider.rs`의 `path_migration` provider는 `pub(crate)`이고, provider 주석도 현재 public 기능이 아님을 명시한다. `s2n-quic-qns` interop client도 `ConnectionMigration => false`와 active migration TODO를 남긴다. 따라서 s2n-quic은 migration/rebinding machinery와 active-path observability가 있는 구현체로 분류하되, AWS NLB live runner에서 quic-go처럼 public `AddPath -> Probe -> Switch` 흐름을 직접 트리거할 수 있다고 주장하지 않는다.

실행 방향:

1. 완료: s2n-quic custom CID provider local proof 복원 및 rerun
2. 완료: live AWS NLB+s2n readiness gate 추가 및 현재 blocker 고정
3. 완료: dedicated s2n live NLB data-plane runner 구현
4. 완료: live server/client source와 local binary smoke 검증
5. 완료: s2n active migration API audit로 public app trigger boundary 고정
6. 후속: credential refresh 후 EC2 server에서 s2n-quic target A/B 구동
7. 후속: NLB `QUIC` 또는 `TCP_QUIC` target group 구성
8. 후속: NLB forwarding echo에서 target A/B 중 하나만 PASS하는지 확인
9. 후속: public API가 생기거나 lower-level IO/proxy variant를 설계한 뒤 active path-change 유도
10. 후속: NLB가 같은 backend로 보냈는지 server log/qlog/event로 확인

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

> 완료. `docs/results/nginx-haproxy-quic-cm-boundary-20260630.md`에 nginx QUIC source/official-doc 기반 server-side passive migration evidence와 HAProxy official-doc/source/local negative-control evidence를 분리해 정리했다. 추가로 `harness/scripts/run-nginx-quic-active-migration-demo.sh`와 `docs/results/nginx-quic-active-migration-runtime-20260630.md`를 추가해 nginx HTTP/3 server runtime demo를 확보했다. 최신 nginx run `nginx-quic-active-migration-20260630T104724Z`는 `validation=ok`, `client_response_bytes=1048576`, `server_path_seq1_created_count=1`, `server_path_seq1_validated_count=2`, server/client PATH_CHALLENGE/PATH_RESPONSE evidence를 기록했다. 이어서 `harness/scripts/run-haproxy-http3-negative-control.sh`와 `docs/results/haproxy-http3-negative-control-rerun-20260630.md`를 추가해 HAProxy fresh negative-control도 확보했다. 최신 HAProxy run `haproxy-http3-negative-control-20260630T110201Z`는 ordinary H3 baseline PASS, quiche no-migration PASS, active migration path validation FAIL, qlog `path_challenge=3`, `path_response=0`을 기록했다. 마지막으로 `harness/scripts/check-nginx-quic-bpf-readiness.sh`와 `docs/results/nginx-quic-bpf-readiness-20260630.md`를 추가해 Linux `quic_bpf` deployment claim을 local runtime claim과 분리했고, 현재 macOS local run은 `can_run_linux_quic_bpf_now=no`, `blocked_reason=linux_required`로 닫혔다.

실행 방향:

1. 완료: nginx QUIC source에서 server-side passive migration handling과 한계 정리
2. 완료: HAProxy 공식 문서/소스에서 migration unsupported 또는 제한 근거 고정
3. 완료: 기존 local proxy negative-control에서 ordinary H3 PASS, active migration FAIL, client qlog `PATH_RESPONSE=0` 확인
4. 완료: nginx HTTP/3 runtime demo에서 quiche active source-port migration, server path seq:1 validation, 1MiB response completion 확인
5. 완료: HAProxy fresh negative-control runner로 ordinary H3 PASS와 active migration FAIL 재현
6. 완료: Linux `quic_bpf` readiness gate로 현재 local blocker와 claim boundary 고정
7. 남음: Linux `quic_bpf` 기반 packet routing 또는 production-like nginx deployment 검증

논문 기여:

> HTTP/3 availability is not sufficient evidence of QUIC Connection Migration support.

### P4. mvfst focused maturity audit

목표:

> mvfst를 full build까지 못 하더라도, path manager, migration tests, qlog/stats 근거를 source-linked appendix로 정리한다.

상태:

> 완료. `docs/results/mvfst-cm-source-audit-20260630.md`에 `QuicPathManager`, client active probe/migration flow, server passive migration state machine, qlog/stat hook, migration-specific test files를 source-linked appendix로 정리했다. 추가로 `tools/check_mvfst_migration_test_readiness.py`와 `docs/results/mvfst-migration-test-readiness-20260630.md`를 추가해 latest remote HEAD `d9d65a3ab3e6ffba785d6605afe6f05b8db015ec` 기준 focused test target map을 고정했다. 결과는 총 106개 test case, high-value migration/path case 78개, BUCK target 3개 확인이다. 현재 로컬 실행은 `disk_below_threshold`, `buck2_missing`, `focused_files_not_directly_exposed_by_current_cmake` 때문에 `validation=blocked`다.

실행 방향:

1. 완료: migration/path manager 관련 파일과 test 목록 고정
2. 완료: build/test는 이번 턴에서 실행하지 않고 dependency/build cost caveat로 분리
3. 완료: fresh PASS가 아니라 source-audited evidence로 분류
4. 완료: focused migration test target readiness runner 추가
5. 완료: latest remote HEAD 기준 source/BUCK target 존재와 현재 local blocker 고정
6. 남음: Linux/Buck 또는 충분한 disk의 getdeps 환경에서 target 실행

### P5. Chrome desktop public-origin simulation

목표:

> iPhone 없이 Chrome desktop에서 public-origin, forced-H3, local route/proxy change가 browser-visible continuity로 이어지는지 검증한다.

실행 방향:

1. 기존 Chrome local forced-H3 matrix 재사용
2. public origin 또는 local HTTPS origin에서 upload/download/range/media workload 반복
3. NetLog에서 QUIC session 수, path validation event, retry 여부 분류

주의:

> retry로 완료된 작업은 single-session CM 성공으로 쓰지 않는다.

### P6. quicly focused e2e path-migration

목표:

> quicly를 단순 partial build/unit evidence로만 남기지 않고, Connection Migration과 직접 관련된 e2e subtest를 분리해 실행 가능한 근거로 고정한다.

상태:

> 완료. `harness/scripts/run-quicly-e2e-path-migration-check.sh`를 추가했고, 최신 run `quicly-e2e-path-migration-local-20260630`에서 `validation=ok_path_migration`, `path_subtest_ok=yes`, `cid_seq_check_ok=yes`를 확보했다. full `t/e2e.t`는 `prove_exit=1`, `slow_start_failed=yes`라 전체 PASS로 주장하지 않는다.

실행 방향:

1. 완료: local CPAN install로 `Net::EmptyPort` dependency 충족
2. 완료: full `t/e2e.t` 실행
3. 완료: `path-migration` subtest와 CID seq 1 first path probe check 분리 추출
4. 완료: unrelated `slow-start` failure와 migration evidence를 분리 보고
5. 남음: Linux 또는 upstream-compatible timing 환경에서 full `t/e2e.t` clean PASS 여부 확인

### P7. Sanitized evidence bundle

목표:

> raw qlog, keylog, pcap, NetLog, private host, credential을 커밋하지 않으면서도, 각 연구 claim이 어떤 공개 문서와 runner/tool에 의해 지지되는지 추적 가능한 bundle을 만든다.

상태:

> 완료. `tools/build_sanitized_evidence_bundle.py`와 `tools/test_build_sanitized_evidence_bundle.py`를 추가했고, `docs/results/sanitized-evidence-bundle-20260630.md` 및 `data/sanitized-evidence-bundle-20260630.json`을 생성했다. 현재 bundle은 18개 evidence item을 포함하고, 각 항목마다 `supports`, `do_not_claim`, `next_gap`을 기록한다.

해석:

> 이 bundle은 raw artifact archive가 아니라 evidence-to-claim map이다. 따라서 논문/보고서에서 어떤 문장을 쓸 수 있고 어떤 문장을 피해야 하는지 빠르게 확인하는 안전장치로 쓴다.

## 4. 다음 실행 순서

| 순서 | 작업 | 이유 |
| ---: | --- | --- |
| 1 | nginx/HAProxy negative-control source+doc appendix + nginx runtime demo | 완료. HTTP/3 support와 CM support의 경계를 강화했고 nginx server runtime positive control 확보 |
| 2 | OpenLiteSpeed production-like runtime demo | source feasibility/preflight/cleanup dry-run/runtime runner는 완료. 현재는 Linux/EC2 환경 또는 referenced raw artifact archive 정책이 필요 |
| 3 | AWS NLB + s2n-quic desktop/client path-change 설계 | readiness gate와 dedicated live runner 완료. 현재 credential refresh 후 live forwarding echo와 active path-change variant 필요 |
| 4 | Linux nginx `quic_bpf` 또는 production-like nginx deployment test | readiness gate 완료. Linux/eBPF host에서 packet-routing runtime 검증 필요 |
| 5 | quicly focused e2e path-migration | 완료. path-migration subtest는 PASS, full e2e caveat는 유지 |
| 6 | sanitized evidence bundle 생성 | 완료. 18개 evidence item에 대해 supports/do-not-claim/next-gap boundary를 public-safe로 고정 |

## 5. 바로 다음 턴의 권장 작업

다음 턴에서는 AWS credential이 refresh되면 s2n live NLB runner를 실제로 실행해 target A/B forwarding echo를 먼저 확인한다. 그 다음 active path-change variant를 설계한다. AWS를 바로 쓰기 어렵다면 Linux/EC2 환경을 먼저 확보하거나, referenced raw artifact를 archive해도 되는지 결정한 뒤 OpenLiteSpeed production-like runtime demo를 진행하는 것이 좋다. nginx/HAProxy boundary appendix, nginx runtime demo, HAProxy fresh negative-control, LSQUIC preferred-address/NAT-rebinding app demo, OpenLiteSpeed source feasibility audit, OpenLiteSpeed runtime preflight, cleanup dry-run, OpenLiteSpeed runtime runner, s2n NLB live readiness gate, s2n dedicated live runner, nginx `quic_bpf` readiness gate, quicly focused e2e path-migration check, sanitized evidence-to-claim bundle은 확보됐다.
