# Chrome H3 Local Rebinding Transient Return-Path Sweep

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped only for a bounded window after proxy switch. The goal is to separate permanent return-path loss from transient outage tolerance. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `10` |
| status counts | `{'FAIL': 4, 'PASS': 6}` |
| status by drop window | `{'250ms': {'PASS': 2}, '1500ms': {'PASS': 2}, '3000ms': {'PASS': 2}, '6000ms': {'FAIL': 2}, '9000ms': {'FAIL': 2}}` |
| classification counts | `{'browser_application_task_failed': 4, 'nat_rebinding_path_validation_without_observed_tuple_change': 6}` |
| application complete | `6/10` |
| proxy switched | `10/10` |
| total dropped A-side server packets | `664` |
| total dropped B-side server packets | `63` |

## Runs

| profile | workload | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| downlink-1m-drop-ab-250ms | downlink | 250ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 8062 | - | 2 | 1 | 4/3 | 15/2 | 248 | 37/116 | 212/614 | - |
| upload-1m-drop-ab-250ms | upload | 250ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 7551 | - | 2 | 1 | 4/3 | 35/2 | 228 | 68/855 | 95/281 | 1048576 |
| downlink-1m-drop-ab-1500ms | downlink | 1500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10470 | - | 2 | 1 | 2/1 | 80/1 | 1002 | 38/115 | 131/785 | - |
| upload-1m-drop-ab-1500ms | upload | 1500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 7542 | - | 2 | 2 | 5/4 | 51/4 | 1424 | 72/855 | 58/354 | 1048576 |
| downlink-1m-drop-ab-3000ms | downlink | 3000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10136 | - | 2 | 1 | 7/4 | 98/6 | 2081 | 37/130 | 166/755 | - |
| upload-1m-drop-ab-3000ms | upload | 3000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 9327 | - | 2 | 1 | 6/4 | 59/5 | 2919 | 65/865 | 51/313 | 1048576 |
| downlink-1m-drop-ab-6000ms | downlink | 6000ms | FAIL | `browser_application_task_failed` | false | - | 6928 | 2 | 1 | 7/3 | 105/7 | 5271 | 37/32 | 112/0 | - |
| upload-1m-drop-ab-6000ms | upload | 6000ms | FAIL | `browser_application_task_failed` | false | - | 6921 | 2 | 2 | 6/3 | 58/6 | 4768 | 68/89 | 38/14 | 0 |
| downlink-1m-drop-ab-9000ms | downlink | 9000ms | FAIL | `browser_application_task_failed` | false | - | 6923 | 2 | 1 | 7/3 | 109/7 | 5064 | 39/31 | 103/0 | - |
| upload-1m-drop-ab-9000ms | upload | 9000ms | FAIL | `browser_application_task_failed` | false | - | 11124 | 2 | 2 | 6/3 | 54/23 | 8417 | 68/197 | 32/111 | 0 |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.
