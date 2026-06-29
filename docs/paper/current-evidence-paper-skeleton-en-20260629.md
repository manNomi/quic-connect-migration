# Current-Evidence Paper Skeleton

Generated: `2026-06-29`

## Recommended Title

QUIC Connection Migration Maturity and Web Task Continuity: An Evidence-Chain and Workload-Sensitive Recovery Study

## Alternate Titles

- Evaluating HTTP/3/QUIC Connection Migration Maturity and Web Task Continuity under Wi-Fi-to-Cellular Failover
- Why QUIC Connection Migration Remains Hard To Observe On The Web: Implementation Maturity, Deployment Friction, and Workload Continuity

## Abstract Draft

QUIC Connection Migration is designed to preserve connection continuity when an endpoint's IP address or port changes. In HTTP/3 web applications, however, whether this transport feature becomes user-visible task continuity depends on implementation maturity, browser runtime policy, endpoint discovery, load-balancer routing, proxy/CDN termination, client path-change proof, and application recovery strategy. This study surveys QUIC CM maturity across implementations and deployment paths, and evaluates how Chrome HTTP/3 workloads such as upload, download, polling, and streaming respond to path disruption and application-level recovery. Current evidence shows that controlled QUIC implementations and deployments can reproduce path validation and tuple changes, but it does not yet prove Chrome single-session browser CM success. Large upload/download, Range resume, and media buffering results instead show that task continuity is shaped by retry, replacement sessions, buffering, and QoE tradeoffs. The paper therefore argues that HTTP/3 CM evaluation requires an evidence chain and workload semantics, not only a binary connection-continuity test.

## Contributions

1. A maturity survey of QUIC CM implementations across active/passive migration, API exposure, qlog/tracing, tests, and deployment suitability.
2. A browser CM evidence chain requiring application H3 use, client path change, server tuple change, qlog path validation, browser session continuity, and task completion.
3. A layered explanation for why CM is underused: runtime policy, endpoint discovery, session attribution, CID-aware routing, proxy/CDN termination, middleboxes, security risk, workload recovery, and observability.
4. A workload-continuity analysis showing that upload/download, Range resume, and media buffering expose different failure and recovery mechanisms.
5. A clear boundary for the current Mac+iPhone setup: the latent Wi-Fi-loss-to-iPhone-USB cellular failover trigger is ready, but final browser CM success remains pending until the controlled public origin is restored and final rows are completed.

## Current Key Results

- iPhone USB trigger: `latent_iphone_usb_failover_observed, en0 -> en8, 1321 ms`
- public origin blocker: `TCP connection_refused, AWS invalid_client_token`
- upload: retry0 failed 3/3; retry1 succeeded 3/3 after one failed first attempt
- download: timeout-only retry0 failed 3/3; timeout+retry1 succeeded 3/3; local Range 6000ms no-retry 1/3 PASS and retry2 3/3 PASS
- media segments/buffered playback: segment replication 3000ms/6000ms completed 3/3; buffered playback 3000ms completed 12/12 but low buffer had 14 rebuffer events while high buffer had ~15s startup delay and 0 rebuffer
- music-like buffered media: 6000ms no-retry failed 3/3 after first segment; retry1 completed 3/3 with all eight segments
- Chrome single-session browser CM: not-supported-yet

## Recommended Paper Structure

1. Introduction
2. Background
3. Implementation And Deployment Maturity
4. Evidence Chain Methodology
5. Workload Continuity Experiments
6. Why CM Is Underused
7. Discussion
8. Limitations And Future Work

## Candidate Tables And Figures

- Table 1: QUIC implementation CM maturity survey
- Table 2: Browser CM evidence chain rubric
- Table 3: Operational friction matrix
- Table 4: Workload sensitivity synthesis
- Figure 1: Transport CM vs application-level recovery boundary
- Figure 2: Browser final handover evidence chain
- Figure 3: Streaming buffer depth vs rebuffer/startup tradeoff

## Sentences To Avoid For Now

- Chrome successfully migrated the HTTP/3 connection during Wi-Fi-to-cellular failover.
- Servers that support HTTP/3 also support Connection Migration.
- The tuple changed, therefore CM succeeded.
- Streaming workload completion proves that CM works well.

## Remaining Experiment Gaps

- Fresh controlled public origin baseline.
- Three Chrome no-heartbeat active path-change rows.
- Three Chrome heartbeat active path-change rows.
- Public Range handover.
- Public buffered-media handover.
- One Safari or Android feasibility row.
