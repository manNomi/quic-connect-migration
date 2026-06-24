# Chrome H3 Local Rebinding Upload Retry2 15000ms Recovery

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped for a 15000ms bounded window after proxy switch and the upload page may retry twice with a fresh request body stream. The goal is to check whether the one-retry 15000ms failure region can be recovered by a stronger application-level retry strategy. These rows are local recovery controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `3` |
| status counts | `{'PASS': 3}` |
| status by drop window | `{'15000ms': {'PASS': 3}}` |
| classification counts | `{'nat_rebinding_multiple_quic_sessions': 3}` |
| application complete | `3/3` |
| proxy switched | `3/3` |
| total dropped A-side server packets | `179` |
| total dropped B-side server packets | `117` |

## Runs

| profile | workload | retry | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-upload-1m-drop-ab-15000ms | upload | 2x/1000ms | 15000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 24503 | - | 3 | 4 | 6/3 | 56/39 | 13538 | 66/1031 | 37/374 | 1048576 |
| rep02-upload-1m-drop-ab-15000ms | upload | 2x/1000ms | 15000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 24484 | - | 3 | 4 | 6/3 | 59/39 | 13525 | 71/1033 | 42/347 | 1048576 |
| rep03-upload-1m-drop-ab-15000ms | upload | 2x/1000ms | 15000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 24492 | - | 3 | 4 | 6/3 | 64/39 | 13527 | 69/1033 | 30/363 | 1048576 |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage when application-level retry is allowed. A PASS row means the browser task eventually completed in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success or single-session browser connection migration. A FAIL row would mean transport artifacts can exist while DOM-level task completion still fails.

Observed local boundary: two retries recovered the 15000ms upload region that failed 3/3 with one retry. All three rows completed around 24.5s, delivered the final 1MiB body, and were classified as `nat_rebinding_multiple_quic_sessions` with four Chrome target QUIC sessions. The result is therefore evidence for application-level task recovery under a longer outage, not evidence for single-session browser CM.
