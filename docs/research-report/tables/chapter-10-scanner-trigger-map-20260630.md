# Chapter 10 Scanner Trigger Map

작성일: `2026-06-30`

이 표는 Chapter 10 upload workload recovery에서 어떤 scanner/classifier가 어떤 evidence를 읽는지 line-level로 정리한다.

## 1. Upload Workload Implementation

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [h3server/main.go#L340-L360](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L340-L360) | `POST /upload-sink` body | received bytes and SHA-256 in JSON response | server-side upload receipt |
| [h3server/main.go#L711-L740](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L711-L740) | `/browser-upload` query params | browser upload HTML workload | upload task page |
| [h3server/main.go#L1010-L1030](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L1010-L1030) | JS `ReadableStream`, `fetch` POST, retry budget | `uploadBytes`, `uploadResponseBytes`, `uploadRetriesUsed`, `uploadComplete`, `uploadError` | application outcome artifact |

## 2. Public Runner And Trigger Path

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [run-aws-controlled-public-chrome-trial.sh#L49-L82](../../../harness/scripts/run-aws-controlled-public-chrome-trial.sh#L49-L82) | trial id, mode, variant, target URL shape | public trial envelope | remote server and local browser pairing |
| [run-aws-controlled-public-chrome-trial.sh#L83-L101](../../../harness/scripts/run-aws-controlled-public-chrome-trial.sh#L83-L101) | network-change vs no-change mode | runner selection and active trigger variables | active/no-change 분리 |
| [run-aws-controlled-public-chrome-trial.sh#L172-L201](../../../harness/scripts/run-aws-controlled-public-chrome-trial.sh#L172-L201) | active network-change env | Chrome network-change runner and Wi-Fi restore | active handover execution |
| [run-aws-controlled-public-chrome-trial.sh#L238-L245](../../../harness/scripts/run-aws-controlled-public-chrome-trial.sh#L238-L245) | local browser artifact and copied server artifact | classifier summary regeneration | server/browser artifact join |
| [run-aws-controlled-public-chrome-trial.sh#L256-L259](../../../harness/scripts/run-aws-controlled-public-chrome-trial.sh#L256-L259) | trial id and artifact dir | validation markdown | reportable validation artifact |
| [run-controlled-public-h3-network-change.sh#L160-L225](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L160-L225) | page-ready expression | waits until upload progress before command | trigger tied to workload bytes |
| [run-controlled-public-h3-network-change.sh#L360-L370](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L360-L370) | classifier args | network-change summary JSON | final classification |

## 3. Application Outcome Parsing

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [classify_controlled_public_h3_baseline.py#L94-L103](../../../tools/classify_controlled_public_h3_baseline.py#L94-L103) | CDP `body_dataset`, error keys | terminal error keys | DOM failure source |
| [classify_controlled_public_h3_baseline.py#L111-L114](../../../tools/classify_controlled_public_h3_baseline.py#L111-L114) | keys starting with `upload`, `uploadComplete` | workload `upload`, complete/success booleans | upload task success criterion |
| [classify_chrome_h3_artifacts.py#L193-L205](../../../tools/classify_chrome_h3_artifacts.py#L193-L205) | local DOM dump | upload complete and status 200 check | local control success criterion |
| [classify_chrome_h3_artifacts.py#L226-L236](../../../tools/classify_chrome_h3_artifacts.py#L226-L236) | workload prefix | upload timing field extraction | latency/error timing |

## 4. Network-Change Classifier Guards

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [classify_controlled_public_h3_network_change.py#L16-L31](../../../tools/classify_controlled_public_h3_network_change.py#L16-L31) | target workload list includes `browser-upload`, `upload-sink`, `upload` | target H3 workload filter | bootstrap noise exclusion |
| [classify_controlled_public_h3_network_change.py#L71-L84](../../../tools/classify_controlled_public_h3_network_change.py#L71-L84) | server requests filtered to target H3 workloads | target H3 remote addr count | upload tuple evidence |
| [classify_controlled_public_h3_network_change.py#L129-L136](../../../tools/classify_controlled_public_h3_network_change.py#L129-L136) | `application.success is False`, qlog path validation | application failure classifications | failed upload task not CM success |
| [classify_controlled_public_h3_network_change.py#L140-L151](../../../tools/classify_controlled_public_h3_network_change.py#L140-L151) | tuple count, qlog path validation, session count, application success | `possible_connection_migration` or negative controls | retry success and tuple-only overclaim guard |

## 5. Local Upload Summarizer

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [summarize_chrome_rebinding_upload_matrix.py#L16-L39](../../../tools/summarize_chrome_rebinding_upload_matrix.py#L16-L39) | CSV fields | upload bytes/session/qlog/proxy output schema | local control comparability |
| [summarize_chrome_rebinding_upload_matrix.py#L59-L78](../../../tools/summarize_chrome_rebinding_upload_matrix.py#L59-L78) | target NetLog source ids | PATH_CHALLENGE/PATH_RESPONSE counts | browser-side path frame evidence |
| [summarize_chrome_rebinding_upload_matrix.py#L81-L106](../../../tools/summarize_chrome_rebinding_upload_matrix.py#L81-L106) | proxy JSONL `client_to_server` events | A/B packet counts and bytes | packet rebinding evidence |
| [summarize_chrome_rebinding_upload_matrix.py#L109-L150](../../../tools/summarize_chrome_rebinding_upload_matrix.py#L109-L150) | server upload-sink records and summary JSON | upload request count/bytes, qlog counts, packet rebind | upload evidence row |
| [test_summarize_chrome_rebinding_upload_matrix.py#L76-L102](../../../tools/test_summarize_chrome_rebinding_upload_matrix.py#L76-L102) | synthetic upload artifact | asserts upload bytes, packet rebind, NetLog path validation | summarizer behavior locked |

## 6. Result Row Guards

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [draft_final_handover_result_row.py#L97-L115](../../../tools/draft_final_handover_result_row.py#L97-L115) | application workload and request workloads | workload inference | upload-specific row |
| [draft_final_handover_result_row.py#L118-L124](../../../tools/draft_final_handover_result_row.py#L118-L124) | workload `upload` | `POST upload workload with application retry policy` | task label |
| [draft_final_handover_result_row.py#L162-L183](../../../tools/draft_final_handover_result_row.py#L162-L183) | phase/browser/workload | upload migration trigger text | trigger label |

## 7. False-Positive Guards

| guard | 코드 근거 | 방지하는 오해 |
| --- | --- | --- |
| Upload DOM success is application-only | [classify_controlled_public_h3_baseline.py#L111-L114](../../../tools/classify_controlled_public_h3_baseline.py#L111-L114) | `uploadComplete`를 transport CM으로 해석하는 것 |
| tuple-only negative control | [classify_controlled_public_h3_network_change.py#L144-L145](../../../tools/classify_controlled_public_h3_network_change.py#L144-L145) | remote tuple count 2를 CM success로 과장하는 것 |
| app success without migration evidence | [classify_controlled_public_h3_network_change.py#L148-L149](../../../tools/classify_controlled_public_h3_network_change.py#L148-L149) | upload retry success를 migration proof로 쓰는 것 |
| local proxy boundary | [summarize_chrome_rebinding_upload_matrix.py#L161-L200](../../../tools/summarize_chrome_rebinding_upload_matrix.py#L161-L200) | local NAT rebinding control을 public handover로 혼동하는 것 |
