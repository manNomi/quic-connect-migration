# Chrome H3 Local Rebinding Return-Path Drop Controls

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding controls that selectively drop server-to-client packets after proxy switch. B-only drop tests whether the old return path can still carry the task; A+B drop is the stronger expected-failure return-path-loss control. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `4` |
| expected status counts | `{'FAIL': 2, 'PASS': 2}` |
| actual status counts | `{'FAIL': 2, 'PASS': 2}` |
| classification counts | `{'browser_application_task_failed': 2, 'nat_rebinding_path_probe_without_validation': 2}` |
| application complete | `2/4` |
| proxy switched | `4/4` |
| B-side drop enabled | `4/4` |
| total dropped A-side server packets | `157` |
| total dropped B-side server packets | `49` |

## Runs

| profile | workload | expected | actual | classification | app complete | server requests | Chrome QUIC sessions | qlog PATH C/R | drop A/B | client packets A/B | server packets A/B | dropped A/B packets | upload bytes |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | ---: |
| downlink-1m-drop-b-only | downlink | PASS | PASS | `nat_rebinding_path_probe_without_validation` | true | 2 | 1 | 9/0 | false/true | 39/131 | 796/0 | 0/9 | - |
| upload-1m-drop-b-only | upload | PASS | PASS | `nat_rebinding_path_probe_without_validation` | true | 2 | 1 | 9/0 | false/true | 67/847 | 398/0 | 0/9 | 1048576 |
| downlink-1m-drop-a-and-b | downlink | FAIL | FAIL | `browser_application_task_failed` | false | 2 | 1 | 7/3 | true/true | 36/32 | 112/0 | 103/7 | - |
| upload-1m-drop-a-and-b | upload | FAIL | FAIL | `browser_application_task_failed` | false | 2 | 2 | 6/3 | true/true | 66/88 | 35/0 | 54/24 | 0 |

## Interpretation Boundary

The B-only rows show that dropping only new-path server packets is not necessarily a failure because the old return path can still deliver application data. The A+B rows are the stronger failure boundary: once both old and new return paths are unavailable after switch, browser application completion should fail. This distinction prevents overclaiming path-validation or packet-drop evidence as application continuity.
