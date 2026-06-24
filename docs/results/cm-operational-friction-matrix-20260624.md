# CM Operational Friction Matrix

Generated: `2026-06-24`

This matrix turns the question "why is connection migration not widely used?" into layer-specific, evidence-linked friction points. It is public-safe and does not print private origin settings, commands, qlogs, pcaps, NetLogs, or credentials.

## Summary

| field | value |
| --- | --- |
| rubric | `data/cm-operational-friction-rubric.csv` |
| experiment corpus | `data/experiment-results.csv` |
| literature tracker | `data/literature-review-tracker.csv` |
| friction rows | `13` |
| layer counts | `{'adoption': 1, 'application': 1, 'browser': 2, 'cdn': 1, 'implementation': 1, 'load-balancer': 1, 'methods': 1, 'middlebox': 1, 'network': 1, 'performance': 1, 'proxy': 1, 'security': 1}` |
| paper-use counts | `{'cautious explanatory support': 2, 'related-work support only': 1, 'source-backed explanation with repo evidence': 10}` |

## Matrix

| id | layer | friction | repo evidence | literature evidence | paper use | next proof |
| --- | --- | --- | --- | --- | --- | --- |
| `implementation-policy` | implementation | CM primitives exist, but support is implementation- and policy-specific | 38 (PASS=20;PASS_FEASIBILITY=4;PASS_NEGATIVE_CONTROL=14) | 19 (A=16;B=3) | source-backed explanation with repo evidence | Runtime browser and mobile-client migration trials with policy artifacts. |
| `application-h3-discovery` | browser | HTTP/3 application use must be proven before CM can be tested | 17 (PASS=7;PASS_NEGATIVE_CONTROL=10) | 3 (A=2;B=1) | source-backed explanation with repo evidence | Controlled public WebPKI origin baseline with server H3 request log and qlog. |
| `active-path-proof` | network | The trigger may not change the active client path | 3 (PASS_NEGATIVE_CONTROL=3) | 7 (A=5;B=2) | source-backed explanation with repo evidence | Before/after client path snapshot showing active route or public IP change. |
| `session-attribution` | browser | Tuple changes can be replacement sessions rather than CM | 4 (PASS=1;PASS_NEGATIVE_CONTROL=3) | 7 (A=6;B=1) | source-backed explanation with repo evidence | NetLog/qlog/server evidence that target workload stayed on the migrated session. |
| `cid-load-balancing` | load-balancer | Load balancers need CID-aware routing across tuple changes | 8 (PASS=5;PASS_FEASIBILITY=1;PASS_NEGATIVE_CONTROL=2) | 3 (A=2;B=1) | source-backed explanation with repo evidence | Repeat with controlled public HTTP/3 browser workload through the same CID-aware path. |
| `proxy-termination` | proxy | HTTP/3 proxy support does not imply CM support | 1 (PASS_NEGATIVE_CONTROL=1) | 11 (A=2;B=7;C=2) | source-backed explanation with repo evidence | Add one positive QUIC-aware proxy or tunneling baseline if the paper needs proxy scope. |
| `cdn-edge-scope` | cdn | CDN HTTP/3 CM can be edge-level rather than end-to-end | 9 (PASS=5;PASS_NEGATIVE_CONTROL=4) | 4 (A=3;B=1) | source-backed explanation with repo evidence | Controlled edge test plus origin log separation if CDN scope is included. |
| `middlebox-manageability` | middlebox | Middleboxes and firewalls lose 5-tuple semantics | 22 (PASS=13;PASS_FEASIBILITY=3;PASS_NEGATIVE_CONTROL=6) | 8 (A=6;B=2) | cautious explanatory support | Optional Mininet or firewall reproduction only if the paper claims middlebox behavior directly. |
| `security-risk` | security | CM and preferred-address behavior can be operationally sensitive | 0 (-) | 9 (B=9) | related-work support only | Do not overclaim unless testing a specific security appliance or policy. |
| `silent-client-downlink` | application | Downlink-dominant workloads may not trigger timely migration recovery | 12 (PASS=6;PASS_FEASIBILITY=3;PASS_NEGATIVE_CONTROL=3) | 8 (A=3;B=2;Watch=3) | source-backed explanation with repo evidence | Controlled public active path-change trials with and without heartbeat. |
| `observability-gap` | methods | Browser and network artifacts are individually ambiguous | 35 (PASS=18;PASS_FEASIBILITY=3;PASS_NEGATIVE_CONTROL=14) | 12 (A=11;B=1) | source-backed explanation with repo evidence | Complete final browser handover rows with all required artifacts. |
| `measurement-gap` | adoption | HTTP/3 adoption does not equal CM adoption | 8 (PASS=4;PASS_NEGATIVE_CONTROL=4) | 8 (A=6;B=2) | source-backed explanation with repo evidence | Run controlled public browser handover protocol and compare with wild-scan framing. |
| `performance-risk` | performance | Successful migration can still impose stall, retransmission, or QoE cost | 15 (PASS=9;PASS_FEASIBILITY=3;PASS_NEGATIVE_CONTROL=3) | 6 (B=1;Watch=5) | cautious explanatory support | Measure recovery time, stall duration, and user-visible task success in final browser trials. |

## Paper Claim Boundary

The matrix supports a conservative claim: QUIC CM is not absent as a transport primitive, but production use is gated by runtime policy, endpoint discovery, path-change proof, session attribution, CID-aware routing, intermediary behavior, observability, and application-workload effects.

It does not support a final claim that Chrome/Safari/Android browser handover CM succeeds until the final browser handover protocol has countable rows.
