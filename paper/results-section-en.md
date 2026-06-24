# Results

## RQ1. Do deployed QUIC implementations expose usable connection migration primitives?

Our implementation survey and local/EC2 positive controls show that QUIC connection migration is not merely a specification-level feature. In quic-go, active migration can be driven through the `AddPath -> Probe -> Switch` sequence. In both local direct-origin and EC2 direct-origin experiments, payload checksums remained valid across migration and qlog exposed path validation evidence, including `PATH_CHALLENGE` and `PATH_RESPONSE`.

Thus, the research question should not be framed as “connection migration is unused because it is not implemented.” A more defensible framing is that transport primitives exist, but browser policy, deployment routing, and application workloads determine whether those primitives translate into web task continuity.

## RQ2. Does the deployment path preserve migration continuity?

The AWS NLB experiments show that deployment routing directly affects migration maturity. With NLB `TCP_QUIC :443`, continuity was preserved when the QUIC-LB plaintext connection ID format matched the registered `QuicServerId`. In contrast, malformed connection IDs or mismatched Server IDs caused QUIC application payload failure even when target health checks remained green.

This means HTTP/3 support at a CDN or load balancer is insufficient evidence for end-to-end QUIC connection migration. CID routing, backend affinity, target protocol behavior, and qlog evidence must be evaluated together.

## RQ3. Can HTTP/3 application tasks complete after migration?

In the controlled quic-go client setting, HTTP/3 post-migration request continuity and mid-flight upload/download continuity were observed. In local direct-origin and AWS NLB `TCP_QUIC :443` conditions, 1 MiB upload and download workloads completed without manual retry, while qlog retained HTTP/3 frame and path validation evidence. In an additional local repetition set, three mid-flight upload cases and three mid-flight download cases all passed, with client migration trigger, probe/switch success, socket-B transition, and payload decode success confirmed in each case.

However, this result applies to a custom controlled client. It cannot be directly generalized to browser workloads, where HTTP/3 discovery, certificate trust, client policy, JavaScript timers, and page lifecycle behavior can alter the outcome.

## RQ4. Is Chrome browser HTTP/3 workload evidence sufficient?

With Chrome 149 headless and a forced local QUIC origin, single request, page-subresource sequence, polling, slow subresource, and downlink-dominant streaming workloads reached the quic-go HTTP/3 server. Server request logs, Chrome NetLog, and qlog jointly supported application HTTP/3 evidence.

In contrast, natural Alt-Svc local controls did not produce confirmed application HTTP/3 requests under self-signed or mkcert local origins. Some runs produced QUIC/H3 candidate evidence, but the application request still fell back or failed due to certificate validation or broken alternative service state. Public third-party endpoints produced discovery hints, but those hints were not sufficient to confirm application HTTP/3.

Therefore, browser migration experiments require a controlled public WebPKI origin and a passing application HTTP/3 baseline before any network-change result can be interpreted.

## RQ5. What evidence is required for a browser-level connection migration claim?

The Chrome CDP downlink/heartbeat controls provide the strongest caution for browser-level interpretation. In a no-change downlink workload without heartbeat, the server observed one remote tuple and Chrome reported one target QUIC session. In a no-change downlink workload with heartbeat, the server observed two remote tuples and Chrome reported two target QUIC sessions. In an inactive-interface-toggle control, the command exited successfully, but the client path snapshot reported `no_client_path_change_observed`, and qlog showed no path validation.

We also added a local UDP rebinding proxy experiment that changes the server-facing upstream socket from A to B for Chrome forced-H3 traffic. Across three no-heartbeat repetitions, the proxy packet log confirmed client packets on both upstream sockets, and both server qlog and the Chrome target NetLog source showed PATH_CHALLENGE/PATH_RESPONSE-family evidence at 1/1, but request-level remote tuple evidence remained single-valued. Across three heartbeat repetitions, packet rebinding, two server remote tuples, and qlog/NetLog target path validation were observed, but Chrome NetLog also reported two target QUIC sessions.

A client-sending streaming upload control reinforces the same evidence boundary. During three repetitions, a Chrome page uploaded 256 KiB through streaming `fetch()` while the proxy rebound its upstream socket. The proxy packet log confirmed A/B upstream forwarding in all three runs, all uploads completed, Chrome NetLog reported one target QUIC session, and both server qlog and Chrome target NetLog source path-validation frame evidence appeared. However, the request-level server remote tuple still remained single-valued.

We then ran a timing-sensitivity set with early `500ms` and late `5s` rebinding. Across eight downlink runs and four upload runs, all 12 application tasks completed, and every row recorded proxy packet rebinding, qlog path validation, and Chrome target NetLog path-validation frames. The packet distribution changed substantially: average upstream-B packet share was `0.618` for early downlink and `0.800` for early upload, but only `0.172` for late downlink and `0.181` for late upload. In downlink heartbeat runs, early rebinding produced two remote tuples and two target sessions, while late rebinding kept one request-level remote tuple but still produced two Chrome target sessions. Thus, heartbeat or recovery logic must be evaluated together with timing and browser session attribution.

Finally, we repeated an old-path-drop proxy control. After switching client traffic to upstream B, the proxy dropped server-to-client packets arriving on upstream A. Across seven downlink rows and four upload rows, all 11 tasks completed and all rows recorded qlog and Chrome target NetLog path-validation frames. The downlink rows did not receive A-side server packets after the switch, but the upload rows dropped 60 total A-side server packets and still completed a 256 KiB upload each time. The three repeated upload rows also kept one Chrome target QUIC session. In contrast, the three heartbeat downlink rows still produced multiple sessions, so heartbeat-based recovery or observability must be interpreted with session attribution even under old-path-drop conditions.

We then scaled the same old-path-drop control to 1 MiB and 4 MiB workloads. Across three downlink rows and two upload rows, all five stress tasks completed and all five rows recorded qlog and Chrome target NetLog path validation. The upload rows delivered 1 MiB and 4 MiB bodies to `/upload-sink`, for 5 MiB total received, while the stress rows dropped 105 A-side server packets and 74,279 bytes after the switch. No-heartbeat downlink and upload rows kept one Chrome target QUIC session, but the 1 MiB heartbeat downlink row still created two target sessions. Thus the stress condition preserves the same interpretation boundary: local NAT rebinding can complete application work under an old-path-unavailable control, but a browser handover claim still requires active client path-change evidence and browser session-continuity evidence.

Finally, we added return-path drop controls. When only B-side server-to-client packets were dropped, the 1 MiB downlink and upload rows both completed. The proxy dropped 18 total B-side server packets, but A-side server packets continued to carry the application data. In contrast, when both A-side and B-side server-to-client packets were dropped after the switch, the 1 MiB downlink and upload rows both failed with `browser_application_task_failed`. Both failure rows still had server requests, qlog HTTP/3/path-frame evidence, and Chrome QUIC session evidence, but DOM-level application completion was false. Thus, even when transport artifacts exist, web-task continuity can fail if return-path availability is lost, which justifies treating application completion as an independent final-protocol criterion.

We then extended this into a transient return-path outage duration sweep. Both A-side and B-side server-to-client packet drops were bounded to 250 ms, 1500 ms, 3000 ms, 6000 ms, and 9000 ms after the proxy switch. For 1 MiB downlink and upload workloads, the 250 ms, 1500 ms, and 3000 ms windows passed in all six rows, while the 6000 ms and 9000 ms windows failed in all four rows. Since all rows still recorded proxy switch and qlog HTTP/3/path evidence, local browser workload continuity should be interpreted as a function of outage duration, retransmission opportunity, and browser task timing, not merely as the presence or absence of path frames.

Thus, a source tuple change at the server, even with qlog path validation, is not sufficient evidence of browser connection migration; conversely, the absence of a request-level tuple change does not prove that packet-level rebinding or path validation did not occur. Packet forwarding logs, qlog path validation, request-level tuples, and Chrome NetLog session attribution are distinct evidence layers. Heartbeats or browser connection management can create multiple QUIC sessions without migration. The classifier therefore separates these cases as `multiple_quic_sessions_without_network_change`, `multiple_quic_sessions_without_client_path_change`, `nat_rebinding_path_validation_without_observed_tuple_change`, and `nat_rebinding_multiple_quic_sessions`.

For the follow-up main experiments, we prepared controlled-public network-change harnesses for Chrome, Safari, and Android Chrome. However, the browser observability matrix shows that only Chrome desktop currently provides NetLog-based session attribution in this harness. Safari and Android Chrome currently lack browser-internal QUIC session logs here, so their outcomes must be interpreted as server/qlog-centered `PASS_FEASIBILITY` evidence. Harness readiness is not itself a successful handover result.

## Overall Findings

The current results support the following claims.

1. QUIC connection migration primitives work in controlled implementations and selected deployment paths.
2. HTTP/3 application workloads can complete after migration in controlled clients.
3. LB/CDN/proxy paths can determine success or failure through CID routing and backend affinity.
4. Browser experiments require application HTTP/3 baseline, active client path change, qlog path validation, and browser session continuity evidence.
5. Tuple changes or NetLog mode events alone are not sufficient to claim connection migration success.

The current results do not yet support the following claims.

1. Chrome preserves HTTP/3 connection migration across a real Wi-Fi/LTE handover.
2. Safari preserves HTTP/3 connection migration across a real handover.
3. Android Chrome preserves HTTP/3 connection migration across a real Wi-Fi/LTE handover.
4. Managed CDN edge deployments preserve end-to-end QUIC connection migration.
5. Service Worker recovery or application heartbeat improves real handover continuity.

These claims require follow-up experiments with a controlled public origin, an active secondary network path, Android/Safari observability, and packet capture.
