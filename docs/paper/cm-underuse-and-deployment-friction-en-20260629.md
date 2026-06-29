# Why QUIC Connection Migration Is Underused

Generated: `2026-06-29`

## Core Answer

The current evidence does not support the simple answer that CM is unused because it is unimplemented. Major QUIC stacks expose path validation, NAT rebinding handling, active or passive migration primitives, qlog/tracing, and tests. The harder problem is that those transport primitives must align with browser runtime policy, HTTP/3 endpoint discovery, real client path change, load-balancer routing, proxy/CDN termination, middlebox operations, and application recovery before users see continuity.

The paper should therefore use this framing:

> QUIC CM is implemented unevenly and deployed conservatively because transport support is only one layer. Browser policy, endpoint discovery, routing, observability, workload semantics, and operational risk decide whether CM becomes visible application continuity.

## Implementation Maturity Summary

| metric | value |
| --- | --- |
| surveyed implementations | 18 |
| active migration API = yes | 8 |
| passive migration = yes | 14 |
| tests = yes | 14 |
| level distribution | L1_L2=1; L2_L3=1; L2_L4=1; L3_L4=4; L4=3; L4_AWS_L5_candidate=1; L4_L5=1; L4_L5_candidate=1; L4_L5_caveat=1; L4_client_runtime_policy_dependent=1; L5_candidate=1; L5_deployment_candidate=1; L5_edge=1 |

## Layered Friction

| layer | friction | why it blocks or discourages CM | repo evidence rows | literature matches | paper use |
| --- | --- | --- | --- | --- | --- |
| implementation | CM primitives exist, but support is implementation- and policy-specific | A QUIC stack can expose migration primitives while browsers, application APIs, or default policies still suppress runtime migration. | 61 | 19 | source-backed explanation with repo evidence |
| browser | HTTP/3 application use must be proven before CM can be tested | A browser cannot demonstrate HTTP/3 CM if the target application request never used HTTP/3; Alt-Svc and DNS ALPN hints are not enough. | 17 | 3 | source-backed explanation with repo evidence |
| network | The trigger may not change the active client path | Interface toggles or scripted commands can complete successfully while the route/interface/public IP used for the QUIC path does not change. | 3 | 7 | source-backed explanation with repo evidence |
| browser | Tuple changes can be replacement sessions rather than CM | Browser workloads may open another QUIC session even without a real network change, so server tuple change alone is insufficient. | 4 | 7 | source-backed explanation with repo evidence |
| load-balancer | Load balancers need CID-aware routing across tuple changes | Traditional 5-tuple routing can send migrated packets to the wrong backend; QUIC-aware routing needs routable CIDs or shared connection state. | 8 | 3 | source-backed explanation with repo evidence |
| proxy | HTTP/3 proxy support does not imply CM support | A proxy may terminate QUIC, fail path validation, or create a new upstream connection, breaking end-to-end CM semantics. | 1 | 11 | source-backed explanation with repo evidence |
| cdn | CDN HTTP/3 CM can be edge-level rather than end-to-end | Managed CDNs often terminate viewer QUIC at the edge; viewer-edge continuity should not be described as origin-end-to-end CM. | 9 | 4 | source-backed explanation with repo evidence |
| middlebox | Middleboxes and firewalls lose 5-tuple semantics | Connection migration changes IP/port while keeping QUIC state, stressing NAT, firewalls, rate limiters, Kubernetes conntrack, and operational monitoring. | 26 | 8 | cautious explanatory support |
| security | CM and preferred-address behavior can be operationally sensitive | Migration can be repurposed for IP masking, censorship circumvention, exfiltration, or state-table abuse, making operators cautious. | 0 | 9 | related-work support only |
| application | Downlink-dominant workloads may not trigger timely migration recovery | If the client has no post-change data to send, path validation or failure detection can be delayed; application heartbeats or retries may recover the task while still hiding transport/session failure. | 27 | 8 | source-backed explanation with repo evidence |
| methods | Browser and network artifacts are individually ambiguous | NetLog hints, tuple changes, qlog frames, and route snapshots each miss part of the story; publishable CM evidence needs a combined chain. | 55 | 12 | source-backed explanation with repo evidence |
| adoption | HTTP/3 adoption does not equal CM adoption | Internet-wide studies find uneven CM support among HTTP/3-capable servers; provider configuration dominates observed support. | 13 | 8 | source-backed explanation with repo evidence |
| performance | Successful migration can still impose stall, retransmission, or QoE cost | Even when migration works, handover latency and retransmission behavior can affect real-time media and task continuity. | 25 | 6 | cautious explanatory support |

## Paper-Level Conclusion

1. CM exists in the standard and in mature implementations.
2. HTTP/3 support is not equivalent to CM support.
3. Browser evidence requires application H3 use, client path change, tuple change, qlog path validation, session continuity, and task completion in the same row.
4. Load balancers, CDNs, and proxies may not preserve end-to-end CM semantics.
5. Many web workloads hide missing transport CM through retry, Range resume, buffering, reconnect, or replacement sessions.
6. Long-lived upload/download tasks expose missing transport continuity more directly as task failure.

## Link To Current Evidence

The repository mirrors these frictions. quic-go, quiche, and AWS NLB controls show transport/deployment feasibility. HAProxy, browser Alt-Svc, inactive interface toggles, multiple-session rows, return-path outage controls, and public iPhone USB rows show why HTTP/3 or tuple change alone is insufficient. Upload, download, Range, and media results show that application-level recovery and workload semantics dominate task continuity.

## Remaining Evidence Needed

- Fresh Chrome H3 baseline after controlled public origin recovery.
- Three Chrome no-heartbeat active path-change rows.
- Three Chrome heartbeat active path-change rows.
- One Safari or Android feasibility row.
- Public Range and buffered-media handover rows.
