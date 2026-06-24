# Chrome H3 Local Rebinding Transient Return-Path Sweep

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped only for a bounded window after proxy switch. The goal is to separate permanent return-path loss from transient outage tolerance. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `14` |
| status counts | `{'FAIL': 6, 'PASS': 8}` |
| status by drop window | `{'250ms': {'PASS': 2}, '1500ms': {'PASS': 2}, '3000ms': {'PASS': 2}, '4000ms': {'PASS': 2}, '5000ms': {'FAIL': 2}, '6000ms': {'FAIL': 2}, '9000ms': {'FAIL': 2}}` |
| classification counts | `{'browser_application_task_failed': 6, 'nat_rebinding_path_validation_without_observed_tuple_change': 8}` |
| application complete | `8/14` |
| proxy switched | `14/14` |
| total dropped A-side server packets | `989` |
| total dropped B-side server packets | `91` |

## Runs

| profile | workload | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| downlink-1m-drop-ab-250ms | downlink | 250ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 8056 | - | 2 | 1 | 4/3 | 4/2 | 176 | 38/112 | 212/597 | - |
| upload-1m-drop-ab-250ms | upload | 250ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 7549 | - | 2 | 1 | 4/3 | 28/2 | 218 | 68/853 | 70/290 | 1048576 |
| downlink-1m-drop-ab-1500ms | downlink | 1500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 8804 | - | 2 | 1 | 6/4 | 93/5 | 1444 | 37/123 | 259/551 | - |
| upload-1m-drop-ab-1500ms | upload | 1500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 7545 | - | 2 | 1 | 5/4 | 51/4 | 1425 | 66/852 | 30/307 | 1048576 |
| downlink-1m-drop-ab-3000ms | downlink | 3000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10168 | - | 2 | 1 | 7/4 | 100/6 | 2114 | 38/132 | 167/755 | - |
| upload-1m-drop-ab-3000ms | upload | 3000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 9167 | - | 2 | 1 | 6/4 | 42/5 | 2848 | 68/852 | 40/327 | 1048576 |
| downlink-1m-drop-ab-4000ms | downlink | 4000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 11309 | - | 2 | 1 | 7/4 | 105/6 | 3136 | 37/121 | 106/773 | - |
| upload-1m-drop-ab-4000ms | upload | 4000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10206 | - | 2 | 1 | 7/4 | 57/6 | 3644 | 66/852 | 34/338 | 1048576 |
| downlink-1m-drop-ab-5000ms | downlink | 5000ms | FAIL | `browser_application_task_failed` | false | - | 6929 | 2 | 2 | 6/3 | 116/6 | 4928 | 42/34 | 129/0 | - |
| upload-1m-drop-ab-5000ms | upload | 5000ms | FAIL | `browser_application_task_failed` | false | - | 6920 | 2 | 2 | 6/3 | 65/6 | 4721 | 64/90 | 29/15 | 0 |
| downlink-1m-drop-ab-6000ms | downlink | 6000ms | FAIL | `browser_application_task_failed` | false | - | 6922 | 2 | 1 | 7/3 | 103/7 | 5121 | 37/32 | 112/0 | - |
| upload-1m-drop-ab-6000ms | upload | 6000ms | FAIL | `browser_application_task_failed` | false | - | 6918 | 2 | 2 | 6/3 | 59/6 | 4620 | 65/90 | 32/14 | 0 |
| downlink-1m-drop-ab-9000ms | downlink | 9000ms | FAIL | `browser_application_task_failed` | false | - | 6927 | 2 | 1 | 7/3 | 106/7 | 5258 | 39/32 | 115/0 | - |
| upload-1m-drop-ab-9000ms | upload | 9000ms | FAIL | `browser_application_task_failed` | false | - | 11122 | 2 | 3 | 6/3 | 60/23 | 8416 | 73/197 | 33/118 | 0 |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.

Observed local boundary: max PASS window `4000ms`; min later FAIL window `5000ms`.
