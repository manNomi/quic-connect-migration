# Chapter 9 Scanner Trigger Map

작성일: `2026-06-30`

이 표는 Chapter 9 byte-range download and retry recovery에서 어떤 scanner/classifier가 어떤 evidence를 읽는지 line-level로 정리한다.

## 1. Range Workload Implementation

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [h3server/main.go#L572-L605](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L572-L605) | `/browser-range-download` query params | range HTML workload 생성 | browser-side range task |
| [h3server/main.go#L606-L653](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L606-L653) | `/range-download`, HTTP `Range` header | partial/full response, `Accept-Ranges`, `Content-Range` | byte-range transfer |
| [h3server/main.go#L957-L974](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L957-L974) | JS range fetch loop, retry budget | `rangeCompletedBytes`, `rangeRetriesUsed`, `rangeComplete`, `rangeError` | application outcome artifact |

## 2. Runner And Trigger Path

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [run-aws-controlled-public-chrome-trial.sh#L49-L82](../../../harness/scripts/run-aws-controlled-public-chrome-trial.sh#L49-L82) | trial id, mode, variant, target URL shape | public trial envelope | remote server and local browser pairing |
| [run-aws-controlled-public-chrome-trial.sh#L83-L101](../../../harness/scripts/run-aws-controlled-public-chrome-trial.sh#L83-L101) | network-change vs no-change mode | runner selection and active trigger variables | active/no-change 분리 |
| [run-aws-controlled-public-chrome-trial.sh#L172-L201](../../../harness/scripts/run-aws-controlled-public-chrome-trial.sh#L172-L201) | active network-change env | Chrome network-change runner and Wi-Fi restore | active handover execution |
| [run-aws-controlled-public-chrome-trial.sh#L238-L245](../../../harness/scripts/run-aws-controlled-public-chrome-trial.sh#L238-L245) | local browser artifact and copied server artifact | classifier summary regeneration | server/browser artifact join |
| [run-aws-controlled-public-chrome-trial.sh#L256-L259](../../../harness/scripts/run-aws-controlled-public-chrome-trial.sh#L256-L259) | trial id and artifact dir | validation markdown | reportable validation artifact |
| [run-controlled-public-h3-network-change.sh#L160-L225](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L160-L225) | page-ready expression | waits until range progress before command | trigger tied to workload bytes |
| [run-controlled-public-h3-network-change.sh#L226-L246](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L226-L246) | command-before/after path snapshots | `client-path-change-summary.json` | path-change proof |
| [run-controlled-public-h3-network-change.sh#L360-L370](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L360-L370) | classifier args | network-change summary JSON | final classification |

## 3. Application Outcome Parsing

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [classify_controlled_public_h3_baseline.py#L94-L103](../../../tools/classify_controlled_public_h3_baseline.py#L94-L103) | CDP `body_dataset`, error keys | terminal error keys | DOM failure source |
| [classify_controlled_public_h3_baseline.py#L123-L126](../../../tools/classify_controlled_public_h3_baseline.py#L123-L126) | keys starting with `range`, `rangeComplete` | workload `range`, complete/success booleans | range task success criterion |
| [test_classify_controlled_public_h3_baseline.py#L98-L112](../../../tools/test_classify_controlled_public_h3_baseline.py#L98-L112) | synthetic `rangeComplete` and `rangeError` datasets | success/failure regression tests | parser behavior locked |

## 4. Network-Change Classifier Guards

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [classify_controlled_public_h3_network_change.py#L16-L31](../../../tools/classify_controlled_public_h3_network_change.py#L16-L31) | target workload list includes `browser-range-download`, `range-download` | target H3 workload filter | bootstrap noise exclusion |
| [classify_controlled_public_h3_network_change.py#L71-L84](../../../tools/classify_controlled_public_h3_network_change.py#L71-L84) | server requests filtered to target H3 workloads | target H3 remote addr count | range tuple evidence |
| [classify_controlled_public_h3_network_change.py#L129-L136](../../../tools/classify_controlled_public_h3_network_change.py#L129-L136) | `application.success is False`, qlog path validation | application failure classifications | failed range task not CM success |
| [classify_controlled_public_h3_network_change.py#L140-L151](../../../tools/classify_controlled_public_h3_network_change.py#L140-L151) | tuple count, qlog path validation, session count, application success | `possible_connection_migration` or negative controls | tuple-only overclaim guard |

## 5. Result Row And Validation Guards

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [draft_final_handover_result_row.py#L97-L115](../../../tools/draft_final_handover_result_row.py#L97-L115) | application workload and request workloads | workload inference | range-specific row |
| [draft_final_handover_result_row.py#L118-L131](../../../tools/draft_final_handover_result_row.py#L118-L131) | workload `range` | `GET /browser-range-download plus byte-range GET /range-download` | task label |
| [draft_final_handover_result_row.py#L162-L183](../../../tools/draft_final_handover_result_row.py#L162-L183) | phase/browser/workload | byte-range migration trigger text | trigger label |
| [test_draft_final_handover_result_row.py#L109-L126](../../../tools/test_draft_final_handover_result_row.py#L109-L126) | synthetic range summary | asserts task and trigger | row behavior locked |
| [validate_final_handover_trial_artifact.py#L33-L53](../../../tools/validate_final_handover_trial_artifact.py#L33-L53) | status, application success, notes | warnings | tuple-only and failed rows are flagged |

## 6. Local Range Control Summarizer

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [summarize_chrome_rebinding_range_matrix.py#L18-L42](../../../tools/summarize_chrome_rebinding_range_matrix.py#L18-L42) | CSV fields | range bytes/retry/session/qlog output schema | local control comparability |
| [summarize_chrome_rebinding_range_matrix.py#L77-L89](../../../tools/summarize_chrome_rebinding_range_matrix.py#L77-L89) | range completion and retries | human-readable note | retry recovery interpretation |
| [summarize_chrome_rebinding_range_matrix.py#L92-L128](../../../tools/summarize_chrome_rebinding_range_matrix.py#L92-L128) | local artifact DOM/qlog/proxy summary | row extraction | local public comparison support |

## 7. False-Positive Guards

| guard | 코드 근거 | 방지하는 오해 |
| --- | --- | --- |
| Range DOM success is application-only | [classify_controlled_public_h3_baseline.py#L123-L126](../../../tools/classify_controlled_public_h3_baseline.py#L123-L126) | `rangeComplete`를 transport CM으로 해석하는 것 |
| tuple-only negative control | [classify_controlled_public_h3_network_change.py#L144-L145](../../../tools/classify_controlled_public_h3_network_change.py#L144-L145) | remote tuple count 2를 CM success로 과장하는 것 |
| task success without migration evidence | [classify_controlled_public_h3_network_change.py#L148-L149](../../../tools/classify_controlled_public_h3_network_change.py#L148-L149) | app success를 migration proof로 쓰는 것 |
| validation warning | [validate_final_handover_trial_artifact.py#L37-L46](../../../tools/validate_final_handover_trial_artifact.py#L37-L46) | negative control을 final protocol result로 집계하는 것 |
| range row regression test | [test_draft_final_handover_result_row.py#L109-L126](../../../tools/test_draft_final_handover_result_row.py#L109-L126) | generic downlink task로 잘못 라벨링하는 것 |
