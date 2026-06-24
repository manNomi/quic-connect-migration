# Chrome H3 Local Rebinding Transient Upload Retry Long Outage

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped for longer bounded windows after proxy switch and the browser upload page is allowed one application-level retry. The goal is to test whether retry recovery still completes the user-visible upload after outage windows that failed in the no-retry transient sweep. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `6` |
| status counts | `{'PASS': 6}` |
| status by drop window | `{'6000ms': {'PASS': 3}, '9000ms': {'PASS': 3}}` |
| classification counts | `{'nat_rebinding_multiple_quic_sessions': 6}` |
| application complete | `6/6` |
| proxy switched | `6/6` |
| total dropped A-side server packets | `385` |
| total dropped B-side server packets | `88` |

## Runs

| profile | workload | retry | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-upload-1m-drop-ab-6000ms | upload | 1x/1000ms | 6000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 15465 | - | 3 | 2 | 7/3 | 61/7 | 5346 | 68/1014 | 21/348 | 1048576 |
| rep01-upload-1m-drop-ab-9000ms | upload | 1x/1000ms | 9000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 19671 | - | 3 | 3 | 6/3 | 72/23 | 8635 | 73/1094 | 46/452 | 1048576 |
| rep02-upload-1m-drop-ab-6000ms | upload | 1x/1000ms | 6000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 15469 | - | 3 | 2 | 6/3 | 58/6 | 4644 | 70/990 | 38/331 | 1048576 |
| rep02-upload-1m-drop-ab-9000ms | upload | 1x/1000ms | 9000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 19674 | - | 3 | 2 | 6/3 | 56/23 | 8417 | 71/1098 | 40/408 | 1048576 |
| rep03-upload-1m-drop-ab-6000ms | upload | 1x/1000ms | 6000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 15469 | - | 3 | 3 | 6/3 | 69/6 | 5314 | 73/988 | 45/371 | 1048576 |
| rep03-upload-1m-drop-ab-9000ms | upload | 1x/1000ms | 9000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 19679 | - | 3 | 3 | 6/3 | 69/23 | 8914 | 74/1096 | 50/474 | 1048576 |

## Interpretation Boundary

Use this long-outage retry boundary as an application-recovery control. A PASS row means the page completed the upload after a fresh `/upload-sink` attempt, not that the original browser QUIC session migrated successfully.

Key interpretation:

- 6000ms retry upload passed 3/3 with DOM completion around 15.5s.
- 9000ms retry upload passed 3/3 with DOM completion around 19.7s.
- Chrome target QUIC session count ranged from 2 to 3 across the six rows.
- Longer outage therefore increased task completion latency and reinforced the split between application recovery and browser session continuity.

This result should be cited as retry/reconnect recovery evidence, not as browser CM success evidence.
