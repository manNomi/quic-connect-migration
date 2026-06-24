# Chrome H3 Local Rebinding Transient Return-Path Sweep

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped only for a bounded window after proxy switch. The goal is to separate permanent return-path loss from transient outage tolerance. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `9` |
| status counts | `{'FAIL': 8, 'PASS': 1}` |
| status by drop window | `{'4000ms': {'FAIL': 2, 'PASS': 1}, '6000ms': {'FAIL': 3}, '9000ms': {'FAIL': 3}}` |
| classification counts | `{'browser_application_task_failed': 8, 'nat_rebinding_multiple_quic_sessions': 1}` |
| application complete | `1/9` |
| proxy switched | `9/9` |
| total dropped A-side server packets | `120` |
| total dropped B-side server packets | `150` |

## Runs

| profile | workload | retry | used | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-poll-1m-drop-ab-4000ms | poll | 0x/500ms |  | 4000ms | FAIL | `browser_application_task_failed` | false | - | - | 2 | 2 | 0/0 | 0/18 | 3864 | 16/11 | 37/0 | - |
| rep01-poll-1m-drop-ab-6000ms | poll | 0x/500ms |  | 6000ms | FAIL | `browser_application_task_failed` | false | - | - | 2 | 2 | 0/0 | 11/18 | 5273 | 12/11 | 20/0 | - |
| rep01-poll-1m-drop-ab-9000ms | poll | 0x/500ms |  | 9000ms | FAIL | `browser_application_task_failed` | false | - | - | 2 | 2 | 0/0 | 16/18 | 7654 | 12/11 | 19/0 | - |
| rep02-poll-1m-drop-ab-4000ms | poll | 0x/500ms |  | 4000ms | FAIL | `browser_application_task_failed` | false | - | - | 2 | 2 | 0/0 | 0/18 | 3868 | 15/11 | 37/0 | - |
| rep02-poll-1m-drop-ab-6000ms | poll | 0x/500ms |  | 6000ms | FAIL | `browser_application_task_failed` | false | - | - | 2 | 2 | 0/0 | 14/18 | 5707 | 12/11 | 21/0 | - |
| rep02-poll-1m-drop-ab-9000ms | poll | 0x/500ms |  | 9000ms | FAIL | `browser_application_task_failed` | false | - | - | 2 | 2 | 0/0 | 16/18 | 7431 | 12/11 | 19/0 | - |
| rep03-poll-1m-drop-ab-4000ms | poll | 0x/500ms |  | 4000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | - | - | 7 | 2 | 7/4 | 33/6 | 3933 | 16/43 | 20/44 | - |
| rep03-poll-1m-drop-ab-6000ms | poll | 0x/500ms |  | 6000ms | FAIL | `browser_application_task_failed` | false | - | - | 2 | 2 | 0/0 | 14/18 | 5716 | 12/11 | 21/0 | - |
| rep03-poll-1m-drop-ab-9000ms | poll | 0x/500ms |  | 9000ms | FAIL | `browser_application_task_failed` | false | - | - | 2 | 2 | 0/0 | 16/18 | 7407 | 15/11 | 21/0 | - |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.

Observed local boundary: max PASS window `4000ms`; min later FAIL window `6000ms`.
