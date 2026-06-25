# Chrome H3 Local Rebinding Transient Return-Path Sweep

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped only for a bounded window after proxy switch. The goal is to separate permanent return-path loss from transient outage tolerance. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `3` |
| status counts | `{'FAIL': 3}` |
| status by drop window | `{'4000ms': {'FAIL': 3}}` |
| classification counts | `{'browser_application_task_failed': 3}` |
| application complete | `0/3` |
| proxy switched | `3/3` |
| total dropped A-side server packets | `37` |
| total dropped B-side server packets | `44` |

## Runs

| profile | workload | retry | used | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-poll-1m-drop-ab-4000ms | poll | 0x/500ms |  | 4000ms | FAIL | `browser_application_task_failed` | false | - | - | 3 | 3 | 6/3 | 35/6 | 3994 | 15/23 | 16/0 | - |
| rep02-poll-1m-drop-ab-4000ms | poll | 0x/500ms |  | 4000ms | FAIL | `browser_application_task_failed` | false | - | - | 2 | 2 | 0/0 | 1/19 | 3993 | 12/10 | 14/0 | - |
| rep03-poll-1m-drop-ab-4000ms | poll | 0x/500ms |  | 4000ms | FAIL | `browser_application_task_failed` | false | - | - | 2 | 2 | 0/0 | 1/19 | 3993 | 15/10 | 16/0 | - |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.

Observed local boundary: inconclusive because the sweep does not contain both PASS and FAIL windows.
