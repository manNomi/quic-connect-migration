# Chapter 8 Scanner Trigger Map

작성일: `2026-06-30`

이 표는 Chapter 8 full-response downlink public handover에서 어떤 scanner/classifier가 어떤 evidence를 읽는지 line-level로 정리한다.

## 1. Active Network-Change Runner

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [run-controlled-public-h3-network-change.sh#L12-L17](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L12-L17) | `PUBLIC_ORIGIN_URL`, baseline summary, `NETWORK_CHANGE_CMD` | active public H3 run required inputs | active trial precondition |
| [run-controlled-public-h3-network-change.sh#L57-L70](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L57-L70) | prior controlled public baseline summary | blocks run unless baseline status is `PASS` | baseline 없는 handover claim 방지 |
| [run-controlled-public-h3-network-change.sh#L72-L77](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L72-L77) | public origin readiness check | `public-origin-readiness.json` | Alt-Svc/WebPKI/public origin precondition |
| [run-controlled-public-h3-network-change.sh#L152-L154](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L152-L154) | before snapshot | `client-path-before.json` | client path baseline |
| [run-controlled-public-h3-network-change.sh#L160-L225](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L160-L225) | page-ready expression file | waits before executing network-change command | trigger timing is tied to DOM progress |
| [run-controlled-public-h3-network-change.sh#L226-L246](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L226-L246) | command-before/after snapshots and `NETWORK_CHANGE_CMD` | `client-path-change-summary.json` | active path-change evidence |
| [run-controlled-public-h3-network-change.sh#L291-L319](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L291-L319) | CDP or dump-dom Chrome runner | NetLog and DOM dump | browser-side artifact |
| [run-controlled-public-h3-network-change.sh#L335-L343](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L335-L343) | final path snapshot | `client-path-eventual-change-summary.json` | delayed path-change evidence |
| [run-controlled-public-h3-network-change.sh#L360-L370](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh#L360-L370) | artifact dirs, URL, Chrome exit, expected requests | `controlled-public-h3-network-change-summary.json` | classifier is final judge |

## 2. Final Chrome Wrapper

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [final-chrome-network-change-run.sh#L36-L51](../../../harness/scripts/final-chrome-network-change-run.sh#L36-L51) | controlled public config and user override env | local config loaded without committing values | public-safe config handling |
| [final-chrome-network-change-run.sh#L130-L136](../../../harness/scripts/final-chrome-network-change-run.sh#L130-L136) | `--require-active-ready` | active config readiness check | missing network command blocks final run |
| [final-chrome-network-change-run.sh#L138-L146](../../../harness/scripts/final-chrome-network-change-run.sh#L138-L146) | baseline unlock checker | final-countable baseline precondition | baseline PASS required before active run |
| [final-chrome-network-change-run.sh#L154-L181](../../../harness/scripts/final-chrome-network-change-run.sh#L154-L181) | env passed into network-change runner | active run execution | reproducible trial envelope |
| [final-chrome-network-change-run.sh#L187-L203](../../../harness/scripts/final-chrome-network-change-run.sh#L187-L203) | bundle checker and validator | postcheck reports | negative-control vs final-countable separation |

## 3. Client Path Snapshot Evidence

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [capture_network_path_snapshot.py#L142-L164](../../../tools/capture_network_path_snapshot.py#L142-L164) | URL, DNS resolution, `ifconfig`, default route, target route, optional public IP probe | JSON route/interface snapshot | client path state artifact |
| [compare_network_path_snapshots.py#L51-L77](../../../tools/compare_network_path_snapshots.py#L51-L77) | before/after default route, target route, gateway, public IP | boolean change fields | active path change criteria |
| [compare_network_path_snapshots.py#L79-L87](../../../tools/compare_network_path_snapshots.py#L79-L87) | missing/error/change booleans | `client_active_path_changed`, `interface_set_changed_without_route_change`, `no_client_path_change_observed` | path-change classification |

## 4. Chrome CDP And DOM Evidence

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [run_chrome_cdp_navigation.js#L163-L187](../../../tools/run_chrome_cdp_navigation.js#L163-L187) | Chrome args, `--enable-quic`, NetLog path, remote debugging port | controlled Chrome session | browser artifact capture |
| [run_chrome_cdp_navigation.js#L222-L263](../../../tools/run_chrome_cdp_navigation.js#L222-L263) | ready expression polling | ready JSON or timeout | page-ready network-change trigger |
| [run_chrome_cdp_navigation.js#L331-L351](../../../tools/run_chrome_cdp_navigation.js#L331-L351) | `Page.navigate`, optional ready expression | navigation and trigger synchronization | trigger after workload progress |
| [run_chrome_cdp_navigation.js#L355-L379](../../../tools/run_chrome_cdp_navigation.js#L355-L379) | DOM evaluation | `bodyDataset`, text, HTML dump | application outcome source |
| [run_chrome_cdp_navigation.js#L386-L403](../../../tools/run_chrome_cdp_navigation.js#L386-L403) | error/finally summary | CDP summary and DOM dump | failed navigation still leaves artifact |

## 5. Workload Implementation

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [h3server/main.go#L672-L710](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L672-L710) | `/browser-downlink` query params | browser HTML with stream/retry config | full-response workload page |
| [h3server/main.go#L741-L777](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L741-L777) | `/downlink-stream` query params | streaming octet response | actual downlink body |
| [h3server/main.go#L987-L1007](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L987-L1007) | browser fetch, reader loop, retry count, error handling | `downlinkBytes`, `downlinkComplete`, `downlinkError` dataset | application success/failure trigger |

## 6. Classifier And Registration Guards

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [classify_controlled_public_h3_network_change.py#L43-L68](../../../tools/classify_controlled_public_h3_network_change.py#L43-L68) | network-change JSON and client path summary JSON | command and path-change summary | active trigger evidence |
| [classify_controlled_public_h3_network_change.py#L71-L84](../../../tools/classify_controlled_public_h3_network_change.py#L71-L84) | server requests filtered to target H3 workloads | target H3 remote addr count | migration tuple evidence limited to target workload |
| [classify_controlled_public_h3_network_change.py#L87-L152](../../../tools/classify_controlled_public_h3_network_change.py#L87-L152) | server qlog, NetLog, client path, application outcome | PASS/PASS_NEGATIVE_CONTROL/FAIL classification | overclaim guard |
| [classify_controlled_public_h3_network_change.py#L168-L225](../../../tools/classify_controlled_public_h3_network_change.py#L168-L225) | server.json, qlog, NetLog, DOM dump, network-change JSON, path summaries | combined summary object | evidence chain materialization |
| [draft_final_handover_result_row.py#L255-L280](../../../tools/draft_final_handover_result_row.py#L255-L280) | summary JSON | CSV row fields, notes, application success, tuple/path validation booleans | row-level reproducibility |
| [validate_final_handover_trial_artifact.py#L20-L30](../../../tools/validate_final_handover_trial_artifact.py#L20-L30) | matched final requirements and status | claim strength | negative control stays record-only |
| [validate_final_handover_trial_artifact.py#L33-L53](../../../tools/validate_final_handover_trial_artifact.py#L33-L53) | status, application_success, notes | warnings | prevents CM success overclaim |
| [validate_final_handover_trial_artifact.py#L56-L84](../../../tools/validate_final_handover_trial_artifact.py#L56-L84) | artifact summary and requirements | validation payload | final-countable gate |

## 7. False-Positive Guards

| guard | 코드 근거 | 방지하는 오해 |
| --- | --- | --- |
| application failure demotion | [classify_controlled_public_h3_network_change.py#L129-L136](../../../tools/classify_controlled_public_h3_network_change.py#L129-L136) | DOM failure를 CM success로 처리하는 것 |
| no path validation demotion | [classify_controlled_public_h3_network_change.py#L144-L151](../../../tools/classify_controlled_public_h3_network_change.py#L144-L151) | tuple change or task success alone as migration proof |
| final protocol exclusion | [validate_final_handover_trial_artifact.py#L20-L30](../../../tools/validate_final_handover_trial_artifact.py#L20-L30) | negative-control row를 final success로 집계하는 것 |
| warning emission | [validate_final_handover_trial_artifact.py#L33-L53](../../../tools/validate_final_handover_trial_artifact.py#L33-L53) | `application_success=false`를 숨기는 것 |
| target workload tuple filter | [classify_controlled_public_h3_network_change.py#L71-L84](../../../tools/classify_controlled_public_h3_network_change.py#L71-L84) | bootstrap/heartbeat tuple을 target workload migration으로 착각하는 것 |
