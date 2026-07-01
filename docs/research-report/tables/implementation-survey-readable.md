# Chapter 1 표: QUIC 구현체별 Connection Migration 성숙도 조사

작성일: `2026-06-30`

원본 CSV: `data/implementation-survey.csv`

이 문서는 원본 CSV를 연구 보고용으로 읽기 쉽게 재구성한 표다. 원본 CSV는 기계적으로 처리하기 좋지만 가로로 너무 길기 때문에, 여기서는 지원 여부와 연구상 해석이 잘 보이도록 컬럼을 줄였다.

## 표기법

| 표기 | 의미 |
| --- | --- |
| `O` | 명확한 근거 있음 |
| `X` | 근거 없거나 지원하지 않음 |
| `△` | 부분 지원 또는 제한적 근거 |
| `△ likely` | 가능성이 높지만 추가 검증 필요 |
| `?` | 불확실함 |
| `? check` | API/문서 추가 확인 필요 |
| `? test` | test 존재 여부 추가 확인 필요 |
| `-` | 해당 없음 |
| `policy` | 구현체 primitive보다 runtime policy 영향을 받음 |
| `internal` | public API가 아니라 내부 API 성격 |
| `managed` | managed service 성격이라 일반 구현체 test와 다름 |
| `fresh_app_demo_20260630` | fresh build/test에 더해 app-level demo evidence 확보 |
| `fresh_runtime_20260630` | fresh runtime demo evidence 확보 |
| `fresh_runtime_20260701` | 2026-07-01 fresh runtime demo/packet evidence 확보 |
| `fresh_negative_control_20260630` | fresh negative-control runtime evidence 확보 |
| `source_policy_audit_20260701` | source-level client policy boundary audit 확보 |
| `source_edge_boundary_audit_20260701` | CDN/edge source-level claim boundary audit 확보 |

## 요약 숫자

| 항목 | 값 |
| --- | ---: |
| 총 조사 대상 | 18 |
| local test/demo까지 실행한 구현체 | 14 |
| 2026-06-30 fresh rerun/demo/negative-control/focused-e2e artifact 확보 | 14 |
| fresh app-level/runtime demo artifact 확보 | 5 |
| fresh negative-control artifact 확보 | 1 |
| fresh focused e2e/full-gate artifact 확보 | 1 |
| fresh partial build/test artifact 확보 | 0 |
| source inspected only | 1 |
| source/client policy audit | 1 |
| partial/deferred | 2 |
| active migration API `yes` | 8 |
| passive migration `yes` | 14 |
| tests `yes` | 14 |
| AWS suitability `high` | 5 |

## 구현체별 보고용 표

| # | 구현체/스택 | 분류 | RFC | Passive | Active API | 관찰성 | Tests | 배포/LB | 판정 | 증거 | 다음 액션 |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | quic-go | library/server | O | O | O | `qlog` | O | `manual` | `L4` | `fresh_rerun_20260630` | Maintain as strong AddPath/Probe/Switch positive control |
| 2 | Cloudflare quiche | library/server | O | O | O | `qlog/logs` | O | `library_yes_cloud_unclear` | `L4` | `fresh_rerun_20260630` | Use as cross-implementation client/server migration evidence |
| 3 | AWS s2n-quic | library/server | O | O | △ likely | `events_qlog_likely` | O | `yes_with_custom_cid` | `L4_AWS_L5_candidate` | `fresh_rerun_20260630` | Custom AWS NLB CID provider proof restored and rerun; live AWS NLB+s2n target test remains follow-up |
| 4 | ngtcp2 | library/tooling | O | O | O | `qlog/logs` | O | `manual` | `L4_runtime_example` | `fresh_runtime_20260701` | Use as C library primitive/path-validation comparison plus official osslclient/osslserver local HTTP/3 runtime positive control |
| 5 | LiteSpeed lsquic | server | O | O | O | `logs` | O | `likely` | `L4_L5_candidate` | `fresh_app_demo_20260630` | Use as preferred-address and NAT-rebinding app-level positive control; OpenLiteSpeed production-like demo remains follow-up |
| 6 | MsQuic | library/server | O | O | policy | `ETW/logs` | O | `yes_with_QUIC_aware_LB` | `L4_selected_runtime_tests` | `fresh_runtime_20260701` | Use as selected v4/v6 NAT rebind/path-validation runtime-test positive control; live QUIC-aware LB and app payload continuity remain follow-up |
| 7 | Quinn | library/server | O | O | △ | `tracing/qlog` | O | `manual` | `L4_runtime_rebind` | `fresh_runtime_20260701` | Use as Rust endpoint-rebind runtime positive control; HTTP/3/browser/deployment rows remain follow-up |
| 8 | Neqo | library/server | O | O | O | `qlog/events` | O | `manual` | `L3_L4` | `fresh_rerun_20260630` | Use as Firefox-adjacent transport maturity evidence; Firefox browser runtime proof remains a separate gate |
| 9 | XQUIC | library/server | O | O | ? | `logs` | O | `manual` | `L3_L4_partial` | `fresh_rebind_demo_20260630` | Use as NAT rebinding demo evidence; Linux full-suite replay runner is packaged in harness/scripts/run-xquic-full-suite-linux.sh because macOS AppleClang Werror blocks QPACK unit build |
| 10 | Chromium Chrome Cronet | client | O | policy | O | `NetLog` | O | `n/a` | `L4_client_policy_boundary_audit` | `source_policy_audit_20260701` | Use Chromium/Cronet policy-boundary audit as high-usage client evidence; runtime Chrome/Cronet handover still requires active network-change rows |
| 11 | AWS CloudFront | managed edge | - | - | - | `limited` | managed | `yes` | `L5_edge_boundary_audit` | `source_edge_boundary_audit_20260701` | Use CDN edge boundary audit for viewer-edge versus origin-end-to-end separation; live viewer-edge experiment remains follow-up |
| 12 | AWS NLB plus s2n-quic | lb_plus_server | O | O | △ likely | `qlog_likely` | s2n local provider proof | `yes` | `L5_deployment_candidate` | `partial_deferred` | s2n custom CID local provider proof PASS; next run live AWS NLB target A/B forwarding and migration continuity |
| 13 | mvfst | library/server | O | O | O | `qlog_stats` | O | `complex_manual` | `L5_candidate` | `source_inspected` | Use source audit plus packaged focused Linux runner as large-scale implementation maturity evidence; Buck/getdeps execution remains follow-up |
| 14 | picoquic | library/tooling | O | O | O | `callbacks_logs` | O | `manual` | `L4_L5` | `fresh_rerun_20260630` | Use as edge-case maturity and preferred-address comparison |
| 15 | nginx QUIC | server | O | O | X | `logs` | runtime demo | `server_deploy` | `L4_server_runtime` | `fresh_runtime_20260630` | Use as server-side runtime active-client-migration positive control; browser handover, Linux quic_bpf, and production deployment remain follow-up |
| 16 | quicly | library/server | O | O | internal | `stats_logs` | O | `manual` | `L3_L4_focused_e2e_full_gate` | `fresh_focused_e2e_full_gate_20260701` | Use as focused e2e path-migration evidence plus packaged Linux full-e2e runner; full `t/e2e.t` PASS still requires `validation=ok_full_e2e` |
| 17 | aioquic | library/tooling | O | △ | X | `logs_tests` | O | `manual` | `L2_L3` | `fresh_rerun_20260630` | Use as readable passive path-validation reference, not primary experiment |
| 18 | HAProxy QUIC | proxy | △ | △ | X | `stats` | runtime negative control | `deployment_constraint` | `L1_L2` | `fresh_negative_control_20260630` | Use fresh local negative control as evidence that HTTP/3 proxy support does not imply active CM support |

## 보고용 해석

### 1. 상위 positive-control 후보

| 후보 | 이유 |
| --- | --- |
| quic-go | active migration API가 명확하고 qlog evidence 확보가 쉬움 |
| Cloudflare quiche | PathEvent/log/qlog로 migration lifecycle 설명에 좋음 |
| picoquic | migration edge-case test가 풍부함 |
| s2n-quic | AWS/NLB/CID-aware deployment 연구와 연결성이 좋음 |
| LiteSpeed lsquic | full CTest 79/79와 preferred-address/NAT-rebinding HTTP/3 app demo 근거를 확보함 |
| nginx QUIC | quiche client active migration 중 1MiB HTTP/3 response, server path seq:1 validation evidence 확보 |
| Quinn | endpoint-wide `Endpoint::rebind` runtime runner에서 stream receive, proto migration, PATH_CHALLENGE/PATH_RESPONSE, new path validation evidence를 확보함 |
| MsQuic | dedicated fail-closed packet에서 production-relevant NAT rebind/path validation gtest가 v4/v6에서 통과함 |
| XQUIC | NAT rebinding demo가 실제 client/server로 통과했고 full suite는 Linux replay runner로 재실행 가능 |
| quicly | full e2e 전체는 `slow-start` 실패로 PASS가 아니지만 `path-migration` e2e subtest와 CID seq 1 first path probe check는 통과했고, Linux full-e2e fail-closed runner/audit가 추가됨 |

### 2. production/deployment 논의 후보

| 후보 | 이유 |
| --- | --- |
| MsQuic | selected v4/v6 rebind/path-validation packet은 PASS, API boundary audit에서 constrained local-address control과 QUIC-aware LB deployment boundary를 확인함 |
| LiteSpeed lsquic | preferred-address와 NAT-rebinding app-level positive control까지 확보했으며 OpenLiteSpeed/서버 배포 논의에 연결 가능 |
| mvfst | 대규모 deployment 후보이며 source audit appendix, focused readiness map, Linux runner에서 path manager/client/server migration test 구조 및 BUCK target을 고정함. build/test cost가 큼 |
| nginx QUIC | 실제 web server deployment와 연결 가능하며 local runtime demo에서 server-side path creation/validation evidence를 확보함. browser/production deployment는 후속 |
| AWS NLB + s2n-quic | s2n custom CID local provider proof가 PASS했고, live AWS NLB target A/B forwarding 실험으로 이어짐 |
| AWS CloudFront | end-to-end CM이 아니라 edge-level continuity로 해석해야 함 |

### 3. 주의해야 할 대상

| 대상 | 주의점 |
| --- | --- |
| Chromium/Cronet | runtime policy와 browser behavior가 중요하며 source 근거만으로 Chrome handover success를 말할 수 없음 |
| HAProxy QUIC | HTTP/3 proxy 지원이 active CM 지원을 의미하지 않는 반례. fresh negative-control에서 ordinary H3 PASS, migrated path validation FAIL |
| aioquic | passive validation reference로 좋지만 active migration 주력 후보는 아님 |
| nginx QUIC | server-side runtime evidence는 있으나 client active migration API나 browser handover evidence는 아님 |

## 이 표에서 바로 말할 수 있는 결론

1. 조사 대상 18개 중 다수가 RFC primitive와 passive migration 근거를 갖고 있다.
2. active migration API가 명확한 구현체는 더 적지만, quic-go/quiche/picoquic/Neqo 등에서 실험 후보가 확인됐고 MsQuic은 selected v4/v6 runtime-test packet과 API boundary audit, LSQUIC은 preferred-address 및 NAT-rebinding app demo, nginx는 server-side runtime demo, Quinn은 endpoint-wide rebind runtime 근거가 보강됐다. Neqo는 Firefox-adjacent maturity evidence로 쓰되 Firefox browser runtime handover와 분리한다. quicly는 full e2e caveat를 유지하되 focused `path-migration` e2e evidence와 Linux full-e2e gate를 확보했다.
3. qlog, PathEvent, NetLog, tracing 등 관찰성이 구현체별로 다르다.
4. HTTP/3 지원과 Connection Migration 지원은 같은 말이 아니다.
5. L4 library maturity는 browser 또는 CDN deployment maturity와 다르다.

## 원본으로 돌아가서 볼 파일

| 원본 | 확인할 내용 |
| --- | --- |
| `data/implementation-survey.csv` | 전체 원본 CSV |
| `docs/results/local-implementation-test-results.md` | local test 실행 결과 |
| `docs/results/chapter1-implementation-maturity-methodology-20260630.md` | 상세 방법론 |
| `tools/scan_implementation_evidence.py` | evidence scanner |
