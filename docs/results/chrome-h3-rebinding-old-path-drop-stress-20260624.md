# Chrome H3 Local Rebinding Old-Path Drop Stress Summary

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding stress rows where the proxy switches client traffic to upstream B and drops any later server-to-client packets from upstream A. It is a local old-path-unavailable control, not a public browser handover result.

## Aggregate

| field | value |
| --- | --- |
| runs | `5` |
| status counts | `{'PASS': 5}` |
| workload counts | `{'downlink': 3, 'upload': 2}` |
| configured bytes counts | `{'1048576': 3, '4194304': 2}` |
| classification counts | `{'nat_rebinding_multiple_quic_sessions': 1, 'nat_rebinding_path_validation_without_observed_tuple_change': 4}` |
| proxy switched | `5/5` |
| old-path drop enabled | `5/5` |
| qlog path validation | `5/5` |
| NetLog target path validation | `5/5` |
| upload bytes received | `5242880` |
| downlink configured bytes | `6291456` |
| total dropped A-side server packets | `105` |
| total dropped A-side server bytes | `74279` |

## Runs

| profile | workload | heartbeat | bytes | duration ms | status | classification | remote tuples | Chrome QUIC sessions | qlog path | NetLog path | client packets A/B | server packets A/B | dropped A packets | upload bytes |
| --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: |
| downlink-1m-noheartbeat | downlink | noheartbeat | 1048576 | 8000 | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | true | true | 37/101 | 74/765 | 39 | - |
| downlink-1m-heartbeat | downlink | heartbeat | 1048576 | 8000 | PASS | `nat_rebinding_multiple_quic_sessions` | 2 | 2 | true | true | 37/78 | 101/450 | 12 | - |
| downlink-4m-noheartbeat | downlink | noheartbeat | 4194304 | 12000 | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | true | true | 68/332 | 299/2766 | 0 | - |
| upload-1m | upload | n/a | 1048576 | 8000 | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | true | true | 65/848 | 30/344 | 20 | 1048576 |
| upload-4m | upload | n/a | 4194304 | 12000 | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | true | true | 234/3340 | 85/1166 | 34 | 4194304 |

## Interpretation Boundary

These rows are stress controls for Chrome forced-H3 local NAT rebinding. Passing rows show application completion while the proxy removes the old return path after rebinding, but they still do not prove real Chrome/Safari/Android Wi-Fi-to-cellular handover. The final claim still requires a controlled public WebPKI origin, an actual client path change, and countable final browser handover trials.
