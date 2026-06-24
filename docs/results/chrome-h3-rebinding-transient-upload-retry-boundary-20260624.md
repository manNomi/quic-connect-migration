# Chrome H3 Local Rebinding Transient Upload Retry Boundary

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped for a bounded window after proxy switch and the browser upload page is allowed one application-level retry. The goal is to test whether a failed upload boundary can recover at the application layer, while still separating that recovery from single-session browser connection migration. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `6` |
| status counts | `{'PASS': 6}` |
| status by drop window | `{'4900ms': {'PASS': 3}, '5000ms': {'PASS': 3}}` |
| classification counts | `{'nat_rebinding_multiple_quic_sessions': 6}` |
| application complete | `6/6` |
| proxy switched | `6/6` |
| total dropped A-side server packets | `342` |
| total dropped B-side server packets | `36` |

## Runs

| profile | workload | retry | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-upload-1m-drop-ab-4900ms | upload | 1x/1000ms | 4900ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 15470 | - | 3 | 2 | 6/3 | 61/6 | 4647 | 71/991 | 42/322 | 1048576 |
| rep01-upload-1m-drop-ab-5000ms | upload | 1x/1000ms | 5000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 15466 | - | 3 | 2 | 6/3 | 59/6 | 4919 | 68/988 | 27/328 | 1048576 |
| rep02-upload-1m-drop-ab-4900ms | upload | 1x/1000ms | 4900ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 15476 | - | 3 | 2 | 6/3 | 56/6 | 4842 | 65/986 | 25/357 | 1048576 |
| rep02-upload-1m-drop-ab-5000ms | upload | 1x/1000ms | 5000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 15468 | - | 3 | 2 | 6/3 | 49/6 | 4645 | 69/988 | 41/316 | 1048576 |
| rep03-upload-1m-drop-ab-4900ms | upload | 1x/1000ms | 4900ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 15475 | - | 3 | 2 | 6/3 | 60/6 | 4655 | 65/992 | 29/350 | 1048576 |
| rep03-upload-1m-drop-ab-5000ms | upload | 1x/1000ms | 5000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 15463 | - | 3 | 2 | 6/3 | 57/6 | 4636 | 70/991 | 40/345 | 1048576 |

## Interpretation Boundary

Use this retry boundary as an application-recovery control, not as a CM success proof. A PASS row means the upload task completed after a fresh `/upload-sink` attempt. In all six rows Chrome reported two target QUIC sessions, so the observed recovery is reconnect/multiple-session behavior rather than single-session browser connection migration.

Comparison against the no-retry upload fine boundary:

| condition | 4900ms upload | 5000ms upload | interpretation |
| --- | ---: | ---: | --- |
| no retry | 0/3 PASS | 0/3 PASS | repeated DOM upload failure despite qlog H3/path evidence |
| one retry after 1000ms | 3/3 PASS | 3/3 PASS | task completion recovered, but with `nat_rebinding_multiple_quic_sessions` |

This strengthens the paper framing: transport/path evidence, browser session continuity, and application task completion must be reported as separate layers.
