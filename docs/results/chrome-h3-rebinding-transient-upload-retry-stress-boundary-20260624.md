# Chrome H3 Local Rebinding Transient Upload Retry Stress Boundary

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped for very long bounded windows after proxy switch and the browser upload page is allowed one application-level retry. The goal is to find the point where one retry no longer recovers the upload task. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `6` |
| status counts | `{'FAIL': 3, 'PASS': 3}` |
| status by drop window | `{'12000ms': {'PASS': 3}, '15000ms': {'FAIL': 3}}` |
| classification counts | `{'browser_h3_request_failed': 3, 'nat_rebinding_multiple_quic_sessions': 3}` |
| application complete | `3/6` |
| proxy switched | `6/6` |
| total dropped A-side server packets | `362` |
| total dropped B-side server packets | `216` |

## Runs

| profile | workload | retry | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-upload-1m-drop-ab-12000ms | upload | 1x/1000ms | 12000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 19984 | - | 3 | 3 | 6/3 | 66/33 | 11827 | 68/1065 | 33/417 | 1048576 |
| rep01-upload-1m-drop-ab-15000ms | upload | 1x/1000ms | 15000ms | FAIL | `browser_h3_request_failed` | false | - | 15939 | 2 | 3 | 6/3 | 64/39 | 13528 | 65/93 | 33/0 | 0 |
| rep02-upload-1m-drop-ab-12000ms | upload | 1x/1000ms | 12000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 19983 | - | 3 | 3 | 6/3 | 59/33 | 11831 | 69/1045 | 33/423 | 1048576 |
| rep02-upload-1m-drop-ab-15000ms | upload | 1x/1000ms | 15000ms | FAIL | `browser_h3_request_failed` | false | - | 15936 | 2 | 3 | 6/3 | 63/39 | 13525 | 65/93 | 29/0 | 0 |
| rep03-upload-1m-drop-ab-12000ms | upload | 1x/1000ms | 12000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 19978 | - | 3 | 3 | 6/3 | 52/33 | 11829 | 70/1040 | 29/397 | 1048576 |
| rep03-upload-1m-drop-ab-15000ms | upload | 1x/1000ms | 15000ms | FAIL | `browser_h3_request_failed` | false | - | 15943 | 2 | 3 | 6/3 | 58/39 | 13532 | 67/95 | 34/0 | 0 |

## Interpretation Boundary

Use this stress boundary as the failure-side counterpart to the retry recovery controls. The 12000ms rows completed after retry, but the 15000ms rows failed before a second `/upload-sink` request reached the server.

Key interpretation:

- 12000ms retry upload passed 3/3 with DOM completion around 20.0s.
- 15000ms retry upload failed 3/3 with DOM error around 15.94s.
- 15000ms failure rows still had qlog H3/path evidence and Chrome target QUIC session count 3, but application completion was false and upload bytes were 0.
- One retry is therefore not a guarantee. In this local 1MiB Chrome forced-H3 upload workload, the observed one-retry recovery boundary lies between 12000ms and 15000ms.
