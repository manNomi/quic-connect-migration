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
| Chrome local controls | local forced-H3/rebinding/retry matrix + fresh media/range/upload local refresh 존재 | browser success claim은 아직 제한적이지만 workload별 local artifact 해석 근거는 보강됨 |

## 2. 아직 약한 부분

| 공백 | 왜 중요한가 | iPhone 없이 가능한가 |
| --- | --- | --- |
| LSQUIC OpenLiteSpeed production-like migration demo | preferred-address와 NAT rebinding example app demo는 확보했지만 production-like OpenLiteSpeed 경로는 아직 없음 | 가능 |
| mvfst fresh build/test or focused source audit | 대규모 deployment 구현체인데 아직 source inspection 중심 | 가능하나 빌드 비용 큼 |
| nginx QUIC production/Linux `quic_bpf` | nginx local runtime은 확보됐지만 production packet routing은 아직 약함 | 가능 |
| AWS NLB + s2n-quic CID routing 검증 | 교수님 decision의 AWS 구축 검수와 직접 연결. dedicated runner는 준비됐고 live 실행은 AWS identity 갱신 필요 | 가능 |
| Chrome desktop public-origin simulation | iPhone 없이 browser/runtime policy의 한계를 보강 | 가능 |
| Safari desktop WebDriver/session readiness | cross-browser feasibility 후보지만 Chrome NetLog와 관찰성이 다르고 WebDriver session gate가 별도 존재 | 가능 |
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

> 완료. `docs/results/nginx-haproxy-quic-cm-boundary-20260630.md`에 nginx QUIC source/official-doc 기반 server-side passive migration evidence와 HAProxy official-doc/source/local negative-control evidence를 분리해 정리했다. 추가로 `harness/scripts/run-nginx-quic-active-migration-demo.sh`와 `docs/results/nginx-quic-active-migration-runtime-20260630.md`를 추가해 nginx HTTP/3 server runtime demo를 확보했다. 최신 nginx run `nginx-quic-active-migration-20260630T104724Z`는 `validation=ok`, `client_response_bytes=1048576`, `server_path_seq1_created_count=1`, `server_path_seq1_validated_count=2`, server/client PATH_CHALLENGE/PATH_RESPONSE evidence를 기록했다. 이어서 `harness/scripts/run-haproxy-http3-negative-control.sh`와 `docs/results/haproxy-http3-negative-control-rerun-20260630.md`를 추가해 HAProxy fresh negative-control도 확보했다. 최신 HAProxy run `haproxy-http3-negative-control-20260630T110201Z`는 ordinary H3 baseline PASS, quiche no-migration PASS, active migration path validation FAIL, qlog `path_challenge=3`, `path_response=0`을 기록했다. 마지막으로 `harness/scripts/check-nginx-quic-bpf-readiness.sh`와 `docs/results/nginx-quic-bpf-readiness-20260630.md`를 추가해 Linux `quic_bpf` deployment claim을 local runtime claim과 분리했고, `harness/scripts/run-nginx-quic-bpf-linux-demo.sh`와 `docs/results/nginx-quic-bpf-linux-runner-20260630.md`를 추가해 Linux/root/`/sys/fs/bpf` gate가 열리면 `quic_bpf on;`과 `listen ... reuseport`로 같은 active migration workload를 실행할 수 있게 했다. 현재 macOS local run은 `validation=blocked`, `blocked_reason=linux_required`로 닫혔다.

실행 방향:

1. 완료: nginx QUIC source에서 server-side passive migration handling과 한계 정리
2. 완료: HAProxy 공식 문서/소스에서 migration unsupported 또는 제한 근거 고정
3. 완료: 기존 local proxy negative-control에서 ordinary H3 PASS, active migration FAIL, client qlog `PATH_RESPONSE=0` 확인
4. 완료: nginx HTTP/3 runtime demo에서 quiche active source-port migration, server path seq:1 validation, 1MiB response completion 확인
5. 완료: HAProxy fresh negative-control runner로 ordinary H3 PASS와 active migration FAIL 재현
6. 완료: Linux `quic_bpf` readiness gate로 현재 local blocker와 claim boundary 고정
7. 완료: Linux `quic_bpf` active migration runner 추가 및 macOS local blocked artifact 고정
8. 남음: Linux `quic_bpf` 기반 packet routing 또는 production-like nginx deployment 검증

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

상태:

> 부분 완료. public-origin handover는 controlled origin/AWS 또는 별도 public config가 필요하므로 아직 main claim으로 열지 않았다. 대신 `docs/results/chrome-desktop-noniphone-media-local-refresh-20260630.md`로 fresh local Chrome forced-H3 media control을 재실행했다. 최신 run `chrome-desktop-noniphone-media-drop3000-retry0-20260630`은 `PASS`, `nat_rebinding_possible_session_continuity`, browser application complete `true`, Chrome target QUIC session `1`, server remote tuple `2`, qlog PATH_CHALLENGE/PATH_RESPONSE `1/1`, NetLog target PATH_CHALLENGE/PATH_RESPONSE `1/1`, proxy packet rebinding `true`를 기록했다. 이는 local browser artifact 해석 근거이지 public Wi-Fi/LTE handover 성공 근거는 아니다.

2026-06-30 range 추가 확인:

> `docs/results/chrome-desktop-noniphone-range-local-refresh-20260630.md`로 fresh local Chrome forced-H3 byte-range control 2회를 추가했다. `chrome-desktop-noniphone-range-drop3000-retry0-20260630`과 `chrome-desktop-noniphone-range-slow-drop3000-retry0-20260630`은 모두 `PASS`, `nat_rebinding_possible_session_continuity`, range complete `true`, retry used `0`, Chrome target QUIC session `1`, server remote tuple `2`, qlog PATH_CHALLENGE/PATH_RESPONSE `1/1`이었다. slow row는 server packets A/B가 `170/683`으로 B 경로에 집중되어, local path transition evidence로는 강하지만 real public handover evidence는 아니다.

2026-06-30 upload 추가 확인:

> `docs/results/chrome-desktop-noniphone-upload-local-refresh-20260630.md`로 fresh local Chrome forced-H3 upload control을 추가했다. `chrome-desktop-noniphone-upload-drop3000-retry0-20260630`은 `PASS`, `nat_rebinding_path_validation_without_observed_tuple_change`, upload complete `true`, retry used `0`, upload bytes `131072`, Chrome target QUIC session `1`, qlog/NetLog PATH_CHALLENGE/PATH_RESPONSE `1/1`, proxy packet A/B `29/110`이었다. server request-level remote tuple은 `1`개로 유지되어 upload에서는 request log만으로 packet-level rebinding을 판단하면 안 된다는 기존 2026-06-24 결과를 fresh row로 재확인했다.

2026-07-01 music-like 추가 확인:

> `docs/results/chrome-desktop-noniphone-musiclike-local-refresh-20260701.md`로 fresh local Chrome forced-H3 music-like segment control 2개 row를 추가했다. 6000ms A+B return-path outage에서 retry0 row는 `FAIL`, `browser_h3_request_failed`, media complete `false`, completed segment `1/8`, Chrome target QUIC session `2`였다. 같은 조건에서 retry1 row는 `PASS`, `nat_rebinding_multiple_quic_sessions`, media complete `true`, completed segment `8/8`, Chrome target QUIC session `3`이었다. 따라서 음악형 streaming completion은 retry/reconnect 기반 작업 회복으로 해석해야 하며, single-session browser CM 성공으로 쓰면 안 된다.

2026-07-01 buffered-media 추가 확인:

> `docs/results/chrome-desktop-noniphone-buffered-media-local-refresh-20260701.md`로 fresh local Chrome forced-H3 buffered-media control 2개 row를 추가했다. 6000ms A+B return-path outage에서 low-buffer `1/1` row와 high-buffer `4/6` row는 모두 playback complete였지만, low-buffer는 rebuffer `6`, high-buffer는 rebuffer `1`이었다. 두 row 모두 Chrome target QUIC session `3`, qlog PATH_CHALLENGE/PATH_RESPONSE `6/3`이어서, 동영상형 workload는 completion뿐 아니라 rebuffer/startup/session churn을 함께 보고해야 한다.

2026-07-01 workload continuity/QoE synthesis:

> `docs/results/noniphone-workload-qoe-continuity-synthesis-20260701.md`로 iPhone 없이 수집된 local Chrome/quic-go workload CSV 8개를 32개 normalized row로 묶었다. 이 synthesis는 range/download와 upload가 local single-session path-validation evidence 측면에서 더 선명하고, buffered video와 music-like segment는 completion을 QoE 비용, retry/reconnect, Chrome session churn과 반드시 분리해야 함을 보여준다. 따라서 public origin이 준비되면 range/upload를 먼저 실행하고, streaming은 rebuffer/startup/retry/session count를 함께 수집하는 순서가 더 방어 가능하다.

2026-07-01 public workload trial packet:

> `docs/results/noniphone-public-workload-trial-packet-20260701.md`로 non-iPhone controlled-public Chrome workload 실행 순서를 고정했다. packet은 H3 baseline, range no-change, range active 3회, upload no-change, upload active 3회, buffered low/high active, music-like retry0/retry1 active 순서이며, active row의 strong CM acceptance는 application completion, client active path change, target H3 tuple change, qlog PATH_CHALLENGE/PATH_RESPONSE, Chrome target QUIC session `1`개를 모두 요구한다. 이는 현재 성공 근거가 아니라 public origin과 desktop path-change gate가 열렸을 때 실행할 protocol이다.

2026-07-01 controlled public origin workload deploy packet:

> `docs/results/controlled-public-origin-workload-deploy-packet-20260701.md`로 public H3 origin 준비 절차를 새 workload packet과 연결했다. packet은 WebPKI certificate, TCP/UDP 443, Alt-Svc `h3`, quic-go H3 server baseline, `CONTROLLED_PUBLIC_BASELINE_SUMMARY`, non-iPhone public workload packet 실행 순서를 하나의 run plan으로 묶는다. 이는 public origin이 현재 준비됐다는 근거가 아니라, origin gate가 열렸을 때 range/upload/media trial로 바로 넘어가기 위한 deployment protocol이다.

2026-07-01 non-iPhone desktop path-change readiness:

> `docs/results/noniphone-desktop-path-change-readiness-20260701.md`로 iPhone을 제외한 desktop active path-change gate를 별도 점검했다. 현재 호스트는 active IPv4 interface가 `en0` 하나뿐이라 non-iPhone secondary desktop path가 없고, `macos_wifi_to_iphone_usb_latent_failover`와 `android_wifi_to_cellular_cutover` 후보는 이번 desktop gate에서 제외했다. 따라서 public workload active row를 세려면 먼저 Ethernet, USB LAN, Thunderbolt Ethernet 같은 non-iPhone secondary path를 연결/활성화한 뒤 `client_active_path_changed` snapshot gate를 통과해야 한다.

2026-07-01 controlled-public bridge synthesis:

> `docs/results/controlled-public-chrome-bridge-synthesis-20260701.md`로 tracked controlled-public Chrome validation 문서 18개를 통합했다. no-change baseline 6개는 모두 H3 application baseline으로 확인됐지만, active network-change 12개 중 strong controlled-public CM success row는 `0`개였다. active row 중 2개는 application task가 성공했지만 qlog path validation이 없어서 `tuple_changed_without_path_validation` 또는 negative-control로만 쓸 수 있다. 따라서 이 corpus는 Chrome public-origin CM 성공 근거가 아니라 deployment/browser bridge gap과 negative-control 근거다.

2026-06-30 user-provided public origin readiness:

> 사용자가 제안한 public HTTPS origin 후보를 `tools/check_public_origin_readiness.py`로 redacted 검사했다. 결과는 HTTPS reachability `true`, final status `HTTP/2 200`, `h3 Alt-Svc=false`였다. 따라서 이 후보는 그대로 controlled-public H3 workload target이 아니며, 해당 도메인을 쓰려면 WebPKI TLS, HTTP/3 listener, `Alt-Svc: h3`, workload endpoint를 우리가 통제하도록 설정해야 한다. 결과는 `docs/results/user-provided-public-origin-readiness-20260630.md`와 `data/user-provided-public-origin-readiness-20260630.json`에 기록했다.

실행 방향:

1. 완료: 기존 Chrome local forced-H3 matrix 재사용
2. 완료: local HTTPS origin에서 media workload fresh control 실행
3. 완료: local HTTPS origin에서 byte-range workload fresh control 실행
4. 완료: local HTTPS origin에서 upload workload fresh control 실행
5. 완료: NetLog에서 QUIC session 수, path validation event, retry 여부 분류
6. 남음: controlled public origin에서 page-ready media/upload/range handover 실행

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

> 완료. `tools/build_sanitized_evidence_bundle.py`와 `tools/test_build_sanitized_evidence_bundle.py`를 추가했고, `docs/results/sanitized-evidence-bundle-20260630.md` 및 `data/sanitized-evidence-bundle-20260630.json`을 생성했다. 현재 bundle은 35개 evidence item을 포함하고, 각 항목마다 `supports`, `do_not_claim`, `next_gap`을 기록한다.

해석:

> 이 bundle은 raw artifact archive가 아니라 evidence-to-claim map이다. 따라서 논문/보고서에서 어떤 문장을 쓸 수 있고 어떤 문장을 피해야 하는지 빠르게 확인하는 안전장치로 쓴다.

### P8. Safari desktop WebDriver/session readiness

목표:

> Safari를 Chrome과 같은 등급의 browser CM evidence로 다루지 않되, cross-browser feasibility 후보로 실행 가능한 gate를 정확히 분리한다.

상태:

> 부분 완료. `tools/check_browser_cm_observability.py`에 `--safari-session-smoke` 옵션을 추가해 `safaridriver --version`과 실제 WebDriver session creation을 분리했다. fresh run 기준 Safari `26.2`, `safaridriver exit=0`, packet capture tooling, `rvictl`은 준비되어 있지만, session creation은 Safari Settings의 `Allow remote automation` 미활성화로 실패했다. 따라서 Safari controlled-public baseline/network-change trial은 현재 host에서 바로 실행할 수 없다.

실행 방향:

1. 완료: Safari/safaridriver binary readiness 확인
2. 완료: 실제 WebDriver session creation smoke 추가
3. 완료: 현재 blocker를 `Allow remote automation` 설정으로 좁힘
4. 남음: Safari 설정에서 remote automation 활성화 후 session smoke 재실행
5. 남음: controlled public Safari baseline 실행
6. 남음: Safari network-change feasibility 실행

주의:

> Safari WebDriver session이 열려도 Chrome NetLog-equivalent가 없으므로 Safari 결과는 server/qlog/client-path 중심 `PASS_FEASIBILITY`로만 해석한다.

### P9. Non-iPhone next research decision brief

목표:

> 현재 확보된 evidence bundle과 readiness blocker를 기준으로, iPhone 없이 다음에 진행할 연구 트랙을 우선순위화한다.

상태:

> 완료. `tools/build_non_iphone_next_research_decision.py`와 regression test를 추가했고, `docs/results/non-iphone-next-research-decision-20260630.md` 및 `data/non-iphone-next-research-decision-20260630.json`을 생성했다. 이 decision brief는 6개 후보 트랙을 비교한다: AWS NLB+s2n live forwarding, Chrome controlled-public media/range/upload, nginx `quic_bpf` Linux, OpenLiteSpeed production-like runtime, Safari desktop baseline, mvfst focused tests. Chrome 트랙은 user-provided public origin readiness 결과를 반영해, 현재 후보 origin이 H3-ready가 아니라는 blocker를 포함한다.

해석:

> 구현체 성숙도 조사는 더 늘리는 것보다, 이제 deployment/browser bridge를 열어야 논문 기여가 커진다. 현재 1순위는 AWS credential refresh 후 AWS NLB+s2n live forwarding echo이고, 2순위는 controlled public Chrome media/range/upload trial이다. Safari는 `Allow remote automation`을 켠 뒤 cross-browser `PASS_FEASIBILITY` 보강으로 진행하는 것이 적절하다.

### P10. 2026-07-01 non-iPhone gate rerun

목표:

> 다음 실험을 시작하기 전에 AWS, Safari, user-provided public origin 중 하나라도 열렸는지 재검사한다.

상태:

> 완료. `tools/build_non_iphone_gate_rerun_report.py`와 regression test를 추가했고, `docs/results/non-iphone-gate-rerun-20260701.md` 및 `data/non-iphone-gate-rerun-20260701.json`을 생성했다. 재검사 결과 open gate는 없었다. AWS NLB+s2n은 `aws_identity_invalid_client_token`, Safari WebDriver session은 `allow_remote_automation_disabled`, user-provided public origin은 `h3 Alt-Svc=false`로 남았다. `safaridriver --enable`도 비대화식 실행에서는 password/authorization prompt 때문에 성공하지 못했다.

해석:

> 현재 상태에서 바로 새 live/browser 실험을 시작하면 실패가 예상된다. 연구적으로는 “구현체 성숙도는 충분히 보강됐고, 다음 논문 기여는 외부 gate를 하나 열어 deployment/browser bridge를 실험하는 것”이라는 결론이 더 강해졌다.

### P11. 2026-07-01 non-iPhone claim readiness dashboard

목표:

> 현재 evidence bundle, non-iPhone gate rerun, desktop path readiness, controlled-public Chrome bridge synthesis, workload QoE synthesis를 묶어서 논문에서 허용 가능한 claim과 아직 막아야 하는 claim을 분리한다.

상태:

> 완료. `tools/build_noniphone_claim_readiness_dashboard.py`와 regression test를 추가했고, `docs/results/noniphone-claim-readiness-dashboard-20260701.md` 및 `data/noniphone-claim-readiness-dashboard-20260701.json`을 생성했다. 대시보드는 8개 claim을 분류한다: implementation maturity, deployment/routing boundary, local Chrome workload controls, controlled-public Chrome CM, AWS NLB+s2n live claim, Safari cross-browser feasibility, streaming/QoE framing, paper scope decision.

해석:

> 현재 corpus는 conservative maturity/gap report에는 충분하다. 즉 “CM primitive는 여러 구현체에 존재하지만, public browser CM success와 live AWS+s2n success는 아직 gate-blocked”라고 말할 수 있다. 반대로 Chrome public-origin single-session CM 성공, Safari handover 성공, live AWS NLB+s2n 성공은 아직 주장하면 안 된다.

### P12. 2026-07-01 professor decision packet

목표:

> claim readiness dashboard를 교수님 미팅에서 바로 사용할 수 있는 decision packet으로 압축한다. 특히 현재 논문 scope를 maturity/gap analysis로 확정할지, positive public/browser/AWS result를 위해 외부 gate를 더 열지, Safari를 appendix로 제한할지를 분리한다.

상태:

> 완료. `tools/build_noniphone_professor_decision_packet.py`와 regression test를 추가했고, `docs/results/noniphone-professor-decision-packet-20260701.md` 및 `data/noniphone-professor-decision-packet-20260701.json`을 생성했다. 이 packet은 한 문장 결론, 현재 판정, 교수님께 받을 decision 4개, 현재 말해도 되는 claim, 아직 말하면 안 되는 claim, 교수님께 물어볼 질문, 금지 문장을 포함한다.

해석:

> 다음 논의에서는 “현재 근거로 conservative maturity/gap paper로 scope를 잡을지”가 1순위 decision이다. 교수님이 positive result를 요구하면 AWS credential을 열어 NLB+s2n live forwarding부터 갈지, public H3 origin과 non-iPhone secondary desktop path를 열어 Chrome controlled-public workload부터 갈지를 정하면 된다. Safari는 main result보다는 feasibility appendix로 보는 것이 방어 가능하다.

### P13. 2026-07-01 reviewer risk and validity audit

목표:

> 교수님 decision packet을 논문 리뷰어 관점으로 한 번 더 압축한다. 특히 guarantee overclaim, local rebinding external validity, public positive result 부재, AWS+s2n scope 혼동, streaming QoE confound, mobile/unstable terminology ambiguity 같은 공격 지점을 미리 식별한다.

상태:

> 완료. `tools/build_noniphone_reviewer_risk_audit.py`와 regression test를 추가했고, `docs/results/noniphone-reviewer-risk-audit-20260701.md` 및 `data/noniphone-reviewer-risk-audit-20260701.json`을 생성했다. audit은 9개 reviewer risk를 포함하고, `guarantee_overclaim`과 `public_positive_absence`를 critical risk로 분류한다.

해석:

> 현재 논문은 critical overclaim을 피하면 conservative maturity/gap analysis로 방어 가능하다. 반대로 Chrome public CM 성공, live AWS+s2n 성공, Safari handover 성공을 main claim에 넣으면 현재 evidence로는 리뷰어 공격을 막기 어렵다. Introduction/abstract에서는 "guarantee" 대신 evaluate/assess/classify 표현을 써야 하고, local rebinding은 public handover proof가 아니라 controlled probe로 표시해야 한다.

### P14. 2026-07-01 paper wording guard

목표:

> reviewer risk audit을 실제 논문 문장 규칙으로 바꾼다. abstract, introduction, method, results, limitations, artifact policy에서 피해야 할 문장과 대신 사용할 한국어/영어 문장을 정리한다.

상태:

> 완료. `tools/build_noniphone_paper_wording_guard.py`와 regression test를 추가했고, `docs/results/noniphone-paper-wording-guard-20260701.md` 및 `data/noniphone-paper-wording-guard-20260701.json`을 생성했다. guard는 9개 bilingual wording rule을 포함하며, `guarantee`, `validated`, `works`, public Chrome success, live AWS success, streaming zero-impact continuity 같은 표현을 피하도록 고정한다.

해석:

> 논문 초록과 서론에서는 "HTTP/3 Connection Migration이 작업 연속성을 보장한다"가 아니라 "QUIC/HTTP/3 migration primitive, deployment routing, browser behavior, workload design이 application-level continuity에 만드는 경계를 평가한다"라고 써야 한다. 결과 섹션에서는 local Chrome rebinding control, AWS readiness, streaming QoE를 각각 분리해 쓰고, 한계 섹션에는 public Chrome strong CM success와 Safari handover가 아직 없다는 점을 명시한다.

### P15. 2026-07-01 paper section scaffold

목표:

> 지금까지 만든 evidence bundle과 wording guard를 실제 논문 구조로 배치한다. abstract, introduction, method, results, limitations에 어떤 claim/evidence/금지 문장을 넣을지 고정한다.

상태:

> 완료. `tools/build_noniphone_paper_section_scaffold.py`와 regression test를 추가했고, `docs/results/noniphone-paper-section-scaffold-20260701.md` 및 `data/noniphone-paper-section-scaffold-20260701.json`을 생성했다. scaffold는 9개 section row를 포함하며, missing evidence ID와 missing wording section이 없도록 검증한다.

해석:

> 논문 작성 순서는 이제 보수적으로 정리됐다. 초록/서론은 boundary framing, 방법은 evidence level과 strong-CM acceptance, 결과는 implementation/deployment/browser workload/streaming QoE를 분리, 한계는 public Chrome/live AWS/Safari gap을 명시하는 구조가 가장 방어 가능하다.

## 4. 다음 실행 순서

| 순서 | 작업 | 이유 |
| ---: | --- | --- |
| 1 | nginx/HAProxy negative-control source+doc appendix + nginx runtime demo | 완료. HTTP/3 support와 CM support의 경계를 강화했고 nginx server runtime positive control 확보 |
| 2 | OpenLiteSpeed production-like runtime demo | source feasibility/preflight/cleanup dry-run/runtime runner는 완료. 현재는 Linux/EC2 환경 또는 referenced raw artifact archive 정책이 필요 |
| 3 | AWS NLB + s2n-quic desktop/client path-change 설계 | readiness gate와 dedicated live runner 완료. 현재 credential refresh 후 live forwarding echo와 active path-change variant 필요 |
| 4 | Linux nginx `quic_bpf` 또는 production-like nginx deployment test | readiness gate 완료. Linux/eBPF host에서 packet-routing runtime 검증 필요 |
| 5 | quicly focused e2e path-migration | 완료. path-migration subtest는 PASS, full e2e caveat는 유지 |
| 6 | sanitized evidence bundle 생성 | 완료. evidence item에 대해 supports/do-not-claim/next-gap boundary를 public-safe로 고정 |
| 7 | Chrome desktop upload local refresh | 완료. media/range에 이어 upload fresh local control까지 추가해 streaming/large-transfer workload 비교 근거를 보강 |
| 8 | Safari WebDriver session readiness | 완료. binary readiness와 session creation readiness를 분리했고 현재 host의 Safari blocker를 `Allow remote automation`으로 좁힘 |
| 9 | non-iPhone next research decision brief | 완료. AWS NLB+s2n live forwarding을 1순위, Chrome controlled-public workload를 2순위, Safari feasibility를 설정 의존 보강으로 정리 |
| 10 | 2026-07-01 non-iPhone gate rerun | 완료. AWS/Safari/public-origin 세 gate 모두 아직 닫혀 있음을 public-safe report로 고정 |
| 11 | Chrome desktop music-like local refresh | 완료. 6000ms outage에서 retry0 실패와 retry1 multiple-session 회복을 fresh row로 재확인 |
| 12 | non-iPhone claim readiness dashboard | 완료. 허용 가능한 논문 claim과 금지해야 할 public/browser/AWS claim을 evidence ID 기준으로 분리 |
| 13 | non-iPhone professor decision packet | 완료. 교수님께 받을 scope/positive-result/Safari appendix decision을 한국어 보고용 packet으로 압축 |
| 14 | non-iPhone reviewer risk audit | 완료. 리뷰어 공격 지점과 방어 가능한 wording, 남은 evidence gap을 validity audit으로 정리 |
| 15 | non-iPhone paper wording guard | 완료. 논문 abstract/introduction/method/results/limitations에 넣을 safe bilingual wording과 금지 문장을 정리 |
| 16 | non-iPhone paper section scaffold | 완료. 현재 evidence를 abstract/introduction/method/results/limitations에 배치하는 논문 구조 scaffold 생성 |

## 5. 바로 다음 턴의 권장 작업

다음 턴에서는 AWS credential이 refresh되면 s2n live NLB runner를 실제로 실행해 target A/B forwarding echo를 먼저 확인한다. 그 다음 active path-change variant를 설계한다. AWS를 바로 쓰기 어렵다면 controlled public Chrome origin을 준비해 media/range/upload/page-ready music-like trial로 넘어간다. Safari를 진행하려면 먼저 macOS Safari Settings에서 `Allow remote automation`을 켠 뒤 `--safari-session-smoke`를 다시 통과시켜야 한다. nginx/HAProxy boundary appendix, nginx runtime demo, HAProxy fresh negative-control, LSQUIC preferred-address/NAT-rebinding app demo, OpenLiteSpeed source feasibility audit, OpenLiteSpeed runtime preflight, cleanup dry-run, OpenLiteSpeed runtime runner, s2n NLB live readiness gate, s2n dedicated live runner, nginx `quic_bpf` readiness gate, quicly focused e2e path-migration check, Chrome desktop media/range/upload/music-like local refresh, Safari session readiness split, user-provided public-origin readiness, sanitized evidence-to-claim bundle, non-iPhone next research decision brief, 2026-07-01 gate rerun report, non-iPhone claim readiness dashboard, non-iPhone professor decision packet, non-iPhone reviewer risk audit, non-iPhone paper wording guard, non-iPhone paper section scaffold는 확보됐다.
