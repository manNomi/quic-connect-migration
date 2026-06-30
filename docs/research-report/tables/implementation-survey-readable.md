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

## 요약 숫자

| 항목 | 값 |
| --- | ---: |
| 총 조사 대상 | 18 |
| local test까지 실행한 구현체 | 8 |
| 2026-06-30 fresh rerun artifact 확보 | 8 |
| source inspected | 15 |
| source + local browser baseline | 1 |
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
| 3 | AWS s2n-quic | library/server | O | O | △ likely | `events_qlog_likely` | O | `yes_with_custom_cid` | `L4_AWS_L5_candidate` | `fresh_rerun_20260630` | Verify custom CID generator and NLB 8-byte Server ID compatibility |
| 4 | ngtcp2 | library/tooling | O | O | O | `qlog/logs` | O | `manual` | `L4` | `fresh_rerun_20260630` | Use as C library primitive/path-validation comparison |
| 5 | LiteSpeed lsquic | server | O | O | O | `logs` | O | `likely` | `L4_L5_candidate` | `source_inspected` | Check OpenLiteSpeed/lsquic instrumentation and setup cost |
| 6 | MsQuic | library/server | O | O | ? check | `ETW/logs` | O | `yes_with_QUIC_aware_LB` | `L4_L5_caveat` | `source_inspected` | Confirm active migration sample/API and LB assumptions |
| 7 | Quinn | library/server | O | O | △ | `tracing/qlog` | O | `manual` | `L3_L4` | `fresh_rerun_20260630` | Use as Rust migration/rebind comparison |
| 8 | Neqo | library/server | O | O | O | `qlog/events` | O | `manual` | `L3_L4` | `fresh_rerun_20260630` | Use as Firefox-adjacent broad migration test evidence |
| 9 | XQUIC | library/server | O | O | ? | `logs` | O | `manual` | `L2_L4` | `source_inspected` | Assess docs language/build feasibility |
| 10 | Chromium Chrome Cronet | client | O | policy | O | `NetLog` | O | `n/a` | `L4_client_runtime_policy_dependent` | `source_and_local_browser_baseline` | Run Android/Cronet active interface handover; compare Chrome policy with Cronet network-change migration defaults |
| 11 | AWS CloudFront | managed edge | - | - | - | `limited` | managed | `yes` | `L5_edge` | `partial_deferred` | Design viewer-edge experiment and clarify non-end-to-end interpretation |
| 12 | AWS NLB plus s2n-quic | lb_plus_server | O | O | △ likely | `qlog_likely` | ? s2n | `yes` | `L5_deployment_candidate` | `partial_deferred` | Start only after s2n-quic custom CID compatibility is verified |
| 13 | mvfst | library/server | O | O | O | `qlog_stats` | O | `complex_manual` | `L5_candidate` | `source_inspected` | Use as large-scale implementation maturity evidence; not first experiment |
| 14 | picoquic | library/tooling | O | O | O | `callbacks_logs` | O | `manual` | `L4_L5` | `fresh_rerun_20260630` | Use as edge-case maturity and preferred-address comparison |
| 15 | nginx QUIC | server | O | O | X | `logs` | ? test | `server_deploy` | `L3_L4` | `source_inspected` | Use as server-side passive migration and web-server deployment evidence |
| 16 | quicly | library/server | O | O | internal | `stats_logs` | O | `manual` | `L3_L4` | `source_inspected` | Use as RFC primitive and C implementation comparison |
| 17 | aioquic | library/tooling | O | △ | X | `logs_tests` | O | `manual` | `L2_L3` | `fresh_rerun_20260630` | Use as readable passive path-validation reference, not primary experiment |
| 18 | HAProxy QUIC | proxy | △ | △ | X | `stats` | ? | `deployment_constraint` | `L1_L2` | `source_inspected` | Use as evidence that HTTP/3 support does not imply Connection Migration support |

## 보고용 해석

### 1. 상위 positive-control 후보

| 후보 | 이유 |
| --- | --- |
| quic-go | active migration API가 명확하고 qlog evidence 확보가 쉬움 |
| Cloudflare quiche | PathEvent/log/qlog로 migration lifecycle 설명에 좋음 |
| picoquic | migration edge-case test가 풍부함 |
| s2n-quic | AWS/NLB/CID-aware deployment 연구와 연결성이 좋음 |

### 2. production/deployment 논의 후보

| 후보 | 이유 |
| --- | --- |
| MsQuic | production deployment relevance가 높지만 API/LB assumption 확인 필요 |
| mvfst | 대규모 deployment 후보이나 build/test cost가 큼 |
| lsquic/nginx QUIC | 실제 server deployment와 연결 가능 |
| AWS NLB + s2n-quic | CID-aware routing 실험으로 이어짐 |
| AWS CloudFront | end-to-end CM이 아니라 edge-level continuity로 해석해야 함 |

### 3. 주의해야 할 대상

| 대상 | 주의점 |
| --- | --- |
| Chromium/Cronet | runtime policy와 browser behavior가 중요하며 source 근거만으로 Chrome handover success를 말할 수 없음 |
| HAProxy QUIC | HTTP/3 proxy 지원이 CM 지원을 의미하지 않는 반례 |
| aioquic | passive validation reference로 좋지만 active migration 주력 후보는 아님 |
| nginx QUIC | server-side passive migration 근거는 있으나 client active migration API는 아님 |

## 이 표에서 바로 말할 수 있는 결론

1. 조사 대상 18개 중 다수가 RFC primitive와 passive migration 근거를 갖고 있다.
2. active migration API가 명확한 구현체는 더 적지만, quic-go/quiche/picoquic/Neqo 등에서 실험 후보가 확인됐다.
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
