# Chrome H3 Local UDP Rebinding Upload Summary

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 streaming upload repetitions through a UDP rebinding proxy. It is a local NAT-rebinding control, not a public Wi-Fi/LTE handover result.

## Aggregate

| field | value |
| --- | --- |
| runs | `3` |
| status counts | `{'PASS': 3}` |
| classification counts | `{'nat_rebinding_path_validation_without_observed_tuple_change': 3}` |
| upload request counts | `{'1': 3}` |
| packet rebinding observed counts | `{'true': 3}` |

## Runs

| run | status | classification | remote tuples | Chrome QUIC sessions | upload sink requests | upload bytes | qlog PATH_CHALLENGE/PATH_RESPONSE | proxy client packets A/B | packet rebind |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| upload-r1 | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1 | 262144 | 1/1 | 87/159 | true |
| upload-r2 | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1 | 262144 | 1/1 | 89/161 | true |
| upload-r3 | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1 | 262144 | 1/1 | 90/161 | true |

## Interpretation Boundary

Use these rows as a client-sending local control. Each run records client packets forwarded through both proxy upstream sockets, while the request-level server tuple remains stable. This strengthens the evidence boundary: request logs alone may miss packet-level rebinding, so qlog, proxy packet logs, and browser NetLog remain required. These rows do not complete the final controlled-public browser handover protocol.
