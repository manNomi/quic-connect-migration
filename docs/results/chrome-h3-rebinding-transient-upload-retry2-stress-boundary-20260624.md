# Chrome H3 Local Rebinding Upload Retry2 Stress Boundary

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped for bounded windows after proxy switch and the upload page may retry twice with a fresh request body stream. The goal is to locate the failure side after the 15000ms retry2 recovery control. These rows are local recovery controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `6` |
| status counts | `{'FAIL': 3, 'PASS': 3}` |
| status by drop window | `{'18000ms': {'PASS': 3}, '21000ms': {'FAIL': 3}}` |
| classification counts | `{'browser_application_task_failed': 3, 'nat_rebinding_multiple_quic_sessions': 3}` |
| application complete | `3/6` |
| proxy switched | `6/6` |
| total dropped A-side server packets | `367` |
| total dropped B-side server packets | `315` |

## Runs

| profile | workload | retry | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-upload-1m-drop-ab-18000ms | upload | 2x/1000ms | 18000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 28196 | - | 3 | 4 | 6/3 | 57/51 | 17446 | 69/1630 | 34/941 | 1048576 |
| rep01-upload-1m-drop-ab-21000ms | upload | 2x/1000ms | 21000ms | FAIL | `browser_application_task_failed` | false | - | 20950 | 2 | 4 | 6/3 | 56/54 | 18560 | 65/99 | 33/0 | 0 |
| rep02-upload-1m-drop-ab-18000ms | upload | 2x/1000ms | 18000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 28199 | - | 3 | 4 | 6/3 | 67/51 | 17448 | 69/1619 | 29/996 | 1048576 |
| rep02-upload-1m-drop-ab-21000ms | upload | 2x/1000ms | 21000ms | FAIL | `browser_application_task_failed` | false | - | 20955 | 2 | 4 | 6/3 | 62/54 | 18566 | 65/99 | 28/0 | 0 |
| rep03-upload-1m-drop-ab-18000ms | upload | 2x/1000ms | 18000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 28197 | - | 3 | 4 | 6/3 | 65/51 | 17443 | 68/1623 | 30/956 | 1048576 |
| rep03-upload-1m-drop-ab-21000ms | upload | 2x/1000ms | 21000ms | FAIL | `browser_application_task_failed` | false | - | 20950 | 2 | 4 | 6/3 | 60/54 | 18561 | 66/101 | 29/0 | 0 |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage when application-level retry is allowed. A PASS row means the browser task eventually completed in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success or single-session browser connection migration. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.

Observed local boundary: with two retries and 1000ms retry delay, 18000ms upload passed 3/3 and 21000ms upload failed 3/3. PASS rows completed around 28.2s and were classified as `nat_rebinding_multiple_quic_sessions` with four Chrome target QUIC sessions. FAIL rows errored at 20950-20955ms, retained qlog H3/path evidence and four Chrome target QUIC sessions, but only one `/upload-sink` reached the server and upload bytes remained zero. The local retry2 recovery boundary is therefore between 18s and 21s for this 1MiB upload workload.
