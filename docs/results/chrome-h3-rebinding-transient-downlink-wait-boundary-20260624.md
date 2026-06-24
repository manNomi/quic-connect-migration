# Chrome H3 Local Rebinding Transient Return-Path Sweep

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped only for a bounded window after proxy switch. The goal is to separate permanent return-path loss from transient outage tolerance. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `6` |
| status counts | `{'FAIL': 6}` |
| status by drop window | `{'6000ms': {'FAIL': 3}, '9000ms': {'FAIL': 3}}` |
| classification counts | `{'browser_application_task_failed': 6}` |
| application complete | `0/6` |
| proxy switched | `6/6` |
| total dropped A-side server packets | `621` |
| total dropped B-side server packets | `41` |

## Runs

| profile | workload | retry | used | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-downlink-1m-drop-ab-6000ms | downlink | 0x/500ms |  | 6000ms | FAIL | `browser_application_task_failed` | false | - | 6931 | 2 | 1 | 7/3 | 104/7 | 5886 | 38/31 | 116/0 | - |
| rep01-downlink-1m-drop-ab-9000ms | downlink | 0x/500ms |  | 9000ms | FAIL | `browser_application_task_failed` | false | - | 6923 | 2 | 1 | 7/3 | 103/7 | 5128 | 39/31 | 115/0 | - |
| rep02-downlink-1m-drop-ab-6000ms | downlink | 0x/500ms |  | 6000ms | FAIL | `browser_application_task_failed` | false | - | 6927 | 2 | 1 | 7/3 | 103/7 | 5088 | 38/32 | 114/0 | - |
| rep02-downlink-1m-drop-ab-9000ms | downlink | 0x/500ms |  | 9000ms | FAIL | `browser_application_task_failed` | false | - | 6924 | 2 | 1 | 7/3 | 106/7 | 5845 | 36/32 | 114/0 | - |
| rep03-downlink-1m-drop-ab-6000ms | downlink | 0x/500ms |  | 6000ms | FAIL | `browser_application_task_failed` | false | - | 6926 | 2 | 1 | 6/3 | 102/6 | 4928 | 39/31 | 115/0 | - |
| rep03-downlink-1m-drop-ab-9000ms | downlink | 0x/500ms |  | 9000ms | FAIL | `browser_application_task_failed` | false | - | 6935 | 2 | 1 | 7/3 | 103/7 | 6370 | 39/31 | 115/0 | - |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.

Observed local boundary: inconclusive because the sweep does not contain both PASS and FAIL windows.
