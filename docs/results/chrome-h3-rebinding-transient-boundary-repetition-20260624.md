# Chrome H3 Local Rebinding Transient Boundary Repetition

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped for repeated 4000ms, 4500ms, and 5000ms windows after proxy switch. The goal is to test whether the observed 4-5s local outage boundary is stable or workload-sensitive. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `18` |
| status counts | `{'FAIL': 3, 'PASS': 15}` |
| status by drop window | `{'4000ms': {'PASS': 6}, '4500ms': {'PASS': 6}, '5000ms': {'FAIL': 3, 'PASS': 3}}` |
| classification counts | `{'browser_application_task_failed': 3, 'nat_rebinding_path_validation_without_observed_tuple_change': 15}` |
| application complete | `15/18` |
| proxy switched | `18/18` |
| total dropped A-side server packets | `1395` |
| total dropped B-side server packets | `105` |

## Runs

| profile | workload | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-downlink-1m-drop-ab-4000ms | downlink | 4000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 11834 | - | 2 | 2 | 7/4 | 100/6 | 3780 | 45/135 | 193/756 | - |
| rep01-upload-1m-drop-ab-4000ms | upload | 4000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10224 | - | 2 | 2 | 7/4 | 48/6 | 3652 | 73/853 | 63/307 | 1048576 |
| rep01-downlink-1m-drop-ab-4500ms | downlink | 4500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 12091 | - | 2 | 1 | 7/4 | 97/6 | 4042 | 38/133 | 163/753 | - |
| rep01-upload-1m-drop-ab-4500ms | upload | 4500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10366 | - | 2 | 1 | 7/4 | 53/6 | 3803 | 65/854 | 30/339 | 1048576 |
| rep01-downlink-1m-drop-ab-5000ms | downlink | 5000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 12095 | - | 2 | 1 | 7/4 | 98/6 | 4045 | 37/125 | 165/754 | - |
| rep01-upload-1m-drop-ab-5000ms | upload | 5000ms | FAIL | `browser_application_task_failed` | false | - | 6922 | 2 | 2 | 6/3 | 64/6 | 4739 | 68/89 | 37/14 | 0 |
| rep02-downlink-1m-drop-ab-4000ms | downlink | 4000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 11245 | - | 2 | 1 | 7/4 | 103/6 | 3113 | 37/122 | 114/763 | - |
| rep02-upload-1m-drop-ab-4000ms | upload | 4000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10272 | - | 2 | 1 | 7/4 | 57/6 | 3702 | 67/853 | 34/303 | 1048576 |
| rep02-downlink-1m-drop-ab-4500ms | downlink | 4500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 12179 | - | 2 | 1 | 8/4 | 106/7 | 4124 | 37/128 | 147/778 | - |
| rep02-upload-1m-drop-ab-4500ms | upload | 4500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10302 | - | 2 | 1 | 7/4 | 58/6 | 3730 | 68/854 | 33/293 | 1048576 |
| rep02-downlink-1m-drop-ab-5000ms | downlink | 5000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 13882 | - | 2 | 1 | 2/1 | 70/1 | 2779 | 39/109 | 124/773 | - |
| rep02-upload-1m-drop-ab-5000ms | upload | 5000ms | FAIL | `browser_application_task_failed` | false | - | 6922 | 2 | 2 | 6/3 | 65/6 | 4713 | 65/89 | 22/14 | 0 |
| rep03-downlink-1m-drop-ab-4000ms | downlink | 4000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 11119 | - | 2 | 1 | 7/4 | 102/6 | 3067 | 37/128 | 114/757 | - |
| rep03-upload-1m-drop-ab-4000ms | upload | 4000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10295 | - | 2 | 1 | 7/4 | 57/6 | 3727 | 65/856 | 32/307 | 1048576 |
| rep03-downlink-1m-drop-ab-4500ms | downlink | 4500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 12333 | - | 2 | 1 | 8/4 | 100/7 | 4282 | 38/136 | 151/756 | - |
| rep03-upload-1m-drop-ab-4500ms | upload | 4500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10352 | - | 2 | 1 | 7/4 | 53/6 | 3786 | 68/852 | 29/287 | 1048576 |
| rep03-downlink-1m-drop-ab-5000ms | downlink | 5000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 12062 | - | 2 | 1 | 7/4 | 100/6 | 4009 | 39/128 | 169/755 | - |
| rep03-upload-1m-drop-ab-5000ms | upload | 5000ms | FAIL | `browser_application_task_failed` | false | - | 6921 | 2 | 2 | 6/3 | 64/6 | 4625 | 67/91 | 34/14 | 0 |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.

Observed local boundary: PASS and FAIL windows overlap or are non-monotonic; inspect per-row evidence before drawing a threshold.
