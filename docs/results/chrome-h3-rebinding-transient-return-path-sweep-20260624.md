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
| total dropped B-side server packets | `66` |

## Runs

| profile | workload | drop window | status | classification | app complete | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| downlink-1m-drop-ab-250ms | downlink | 250ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 2 | 1 | 4/3 | 4/2 | 169 | 39/113 | 214/597 | - |
| upload-1m-drop-ab-250ms | upload | 250ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 2 | 1 | 4/3 | 37/2 | 237 | 67/855 | 79/298 | 1048576 |
| downlink-1m-drop-ab-1500ms | downlink | 1500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 2 | 1 | 6/4 | 96/5 | 1445 | 37/129 | 212/598 | - |
| upload-1m-drop-ab-1500ms | upload | 1500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 2 | 1 | 5/4 | 53/4 | 1428 | 68/853 | 34/327 | 1048576 |
| downlink-1m-drop-ab-3000ms | downlink | 3000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 2 | 1 | 7/4 | 93/6 | 2091 | 38/134 | 152/757 | - |
| upload-1m-drop-ab-3000ms | upload | 3000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 2 | 1 | 6/4 | 59/5 | 2860 | 70/854 | 44/355 | 1048576 |
| downlink-1m-drop-ab-6000ms | downlink | 6000ms | FAIL | `browser_application_task_failed` | false | 2 | 1 | 7/3 | 103/7 | 5899 | 38/31 | 114/0 | - |
| upload-1m-drop-ab-6000ms | upload | 6000ms | FAIL | `browser_application_task_failed` | false | 2 | 2 | 6/3 | 63/6 | 4729 | 65/89 | 30/14 | 0 |
| downlink-1m-drop-ab-9000ms | downlink | 9000ms | FAIL | `browser_application_task_failed` | false | 2 | 1 | 6/3 | 102/6 | 5002 | 38/32 | 113/0 | - |
| upload-1m-drop-ab-9000ms | upload | 9000ms | FAIL | `browser_application_task_failed` | false | 2 | 2 | 6/3 | 54/23 | 8420 | 65/171 | 28/112 | 0 |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.
