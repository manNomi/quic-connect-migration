# Chrome H3 Local Rebinding Downlink Fine Boundary

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding downlink runs where both A-side and B-side server-to-client packets are dropped for bounded windows after proxy switch. The goal is to refine the downlink side of the workload-sensitive transition zone around 5-6s. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `9` |
| status counts | `{'FAIL': 5, 'PASS': 4}` |
| status by drop window | `{'5000ms': {'FAIL': 1, 'PASS': 2}, '5500ms': {'FAIL': 1, 'PASS': 2}, '6000ms': {'FAIL': 3}}` |
| classification counts | `{'browser_application_task_failed': 5, 'nat_rebinding_path_validation_without_observed_tuple_change': 4}` |
| application complete | `4/9` |
| proxy switched | `9/9` |
| total dropped A-side server packets | `894` |
| total dropped B-side server packets | `48` |

## Runs

| profile | workload | retry | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-downlink-1m-drop-ab-5000ms | downlink | 0x/500ms | 5000ms | FAIL | `browser_application_task_failed` | false | - | 6922 | 2 | 1 | 6/3 | 102/6 | 4969 | 39/31 | 115/0 | - |
| rep01-downlink-1m-drop-ab-5500ms | downlink | 0x/500ms | 5500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 13840 | - | 2 | 1 | 2/1 | 75/1 | 2765 | 38/105 | 126/786 | - |
| rep01-downlink-1m-drop-ab-6000ms | downlink | 0x/500ms | 6000ms | FAIL | `browser_application_task_failed` | false | - | 6924 | 2 | 1 | 7/3 | 105/7 | 5092 | 38/32 | 114/0 | - |
| rep02-downlink-1m-drop-ab-5000ms | downlink | 0x/500ms | 5000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 13411 | - | 2 | 1 | 7/4 | 104/6 | 4376 | 37/125 | 111/766 | - |
| rep02-downlink-1m-drop-ab-5500ms | downlink | 0x/500ms | 5500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 14114 | - | 2 | 1 | 2/1 | 83/1 | 2857 | 39/115 | 136/783 | - |
| rep02-downlink-1m-drop-ab-6000ms | downlink | 0x/500ms | 6000ms | FAIL | `browser_application_task_failed` | false | - | 6923 | 2 | 1 | 7/3 | 106/7 | 5170 | 36/33 | 113/0 | - |
| rep03-downlink-1m-drop-ab-5000ms | downlink | 0x/500ms | 5000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 12276 | - | 2 | 1 | 8/4 | 106/7 | 4219 | 37/132 | 156/768 | - |
| rep03-downlink-1m-drop-ab-5500ms | downlink | 0x/500ms | 5500ms | FAIL | `browser_application_task_failed` | false | - | 6923 | 2 | 1 | 6/3 | 106/6 | 5020 | 39/27 | 95/0 | - |
| rep03-downlink-1m-drop-ab-6000ms | downlink | 0x/500ms | 6000ms | FAIL | `browser_application_task_failed` | false | - | 6927 | 2 | 1 | 7/3 | 107/7 | 5257 | 37/28 | 96/0 | - |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.

Observed local boundary: 5000ms and 5500ms were mixed at 2/3 PASS each, while 6000ms failed 3/3. The downlink transition is therefore not a clean monotonic threshold in this harness. PASS rows completed at 12276-14114ms with one Chrome target QUIC session and qlog H3/path evidence. FAIL rows errored at 6922-6927ms, also with qlog H3/path evidence, showing again that transport evidence does not guarantee DOM-level task completion.
