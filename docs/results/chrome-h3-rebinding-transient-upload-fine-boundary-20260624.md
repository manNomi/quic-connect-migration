# Chrome H3 Local Rebinding Transient Upload Fine Boundary

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding upload runs where both A-side and B-side server-to-client packets are dropped for fine-grained 4600ms, 4750ms, 4900ms, and 5000ms windows after proxy switch. The goal is to refine the upload-specific transition zone observed in the broader boundary repetition. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `12` |
| status counts | `{'FAIL': 8, 'PASS': 4}` |
| status by drop window | `{'4600ms': {'PASS': 3}, '4750ms': {'FAIL': 2, 'PASS': 1}, '4900ms': {'FAIL': 3}, '5000ms': {'FAIL': 3}}` |
| classification counts | `{'browser_application_task_failed': 8, 'nat_rebinding_path_validation_without_observed_tuple_change': 4}` |
| application complete | `4/12` |
| proxy switched | `12/12` |
| total dropped A-side server packets | `688` |
| total dropped B-side server packets | `72` |

## Runs

| profile | workload | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-upload-1m-drop-ab-4600ms | upload | 4600ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10218 | - | 2 | 1 | 7/4 | 48/6 | 3641 | 71/849 | 44/341 | 1048576 |
| rep01-upload-1m-drop-ab-4750ms | upload | 4750ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 11261 | - | 2 | 1 | 7/4 | 54/6 | 3949 | 68/853 | 43/327 | 1048576 |
| rep01-upload-1m-drop-ab-4900ms | upload | 4900ms | FAIL | `browser_application_task_failed` | false | - | 6922 | 2 | 2 | 6/3 | 64/6 | 4753 | 68/92 | 33/14 | 0 |
| rep01-upload-1m-drop-ab-5000ms | upload | 5000ms | FAIL | `browser_application_task_failed` | false | - | 6920 | 2 | 2 | 6/3 | 60/6 | 4636 | 65/89 | 32/14 | 0 |
| rep02-upload-1m-drop-ab-4600ms | upload | 4600ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10230 | - | 2 | 1 | 7/4 | 52/6 | 3668 | 66/852 | 33/297 | 1048576 |
| rep02-upload-1m-drop-ab-4750ms | upload | 4750ms | FAIL | `browser_application_task_failed` | false | - | 6917 | 2 | 2 | 6/3 | 57/6 | 4720 | 69/77 | 37/14 | 0 |
| rep02-upload-1m-drop-ab-4900ms | upload | 4900ms | FAIL | `browser_application_task_failed` | false | - | 6922 | 2 | 2 | 6/3 | 64/6 | 4692 | 68/91 | 34/14 | 0 |
| rep02-upload-1m-drop-ab-5000ms | upload | 5000ms | FAIL | `browser_application_task_failed` | false | - | 6918 | 2 | 2 | 6/3 | 52/6 | 4614 | 66/91 | 28/14 | 0 |
| rep03-upload-1m-drop-ab-4600ms | upload | 4600ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10215 | - | 2 | 1 | 7/4 | 55/6 | 3646 | 69/852 | 44/307 | 1048576 |
| rep03-upload-1m-drop-ab-4750ms | upload | 4750ms | FAIL | `browser_application_task_failed` | false | - | 6921 | 2 | 2 | 6/3 | 65/6 | 4681 | 66/85 | 39/9 | 0 |
| rep03-upload-1m-drop-ab-4900ms | upload | 4900ms | FAIL | `browser_application_task_failed` | false | - | 6919 | 2 | 2 | 6/3 | 56/6 | 4810 | 65/97 | 25/14 | 0 |
| rep03-upload-1m-drop-ab-5000ms | upload | 5000ms | FAIL | `browser_application_task_failed` | false | - | 6917 | 2 | 2 | 6/3 | 61/6 | 4754 | 68/89 | 35/14 | 0 |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.

Observed local boundary: max PASS window `4750ms`; min later FAIL window `4900ms`.
