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

We then extended this into a transient return-path outage duration sweep. Both A-side and B-side server-to-client packet drops were bounded to 250 ms, 1500 ms, 3000 ms, 4000 ms, 5000 ms, 6000 ms, and 9000 ms after the proxy switch. For 1 MiB downlink and upload workloads, the 250 ms, 1500 ms, 3000 ms, and 4000 ms windows passed in all eight rows, while the 5000 ms, 6000 ms, and 9000 ms windows failed in all six rows. Successful rows reported DOM completion times between roughly 7.5 s and 11.3 s, while failed rows reported DOM error timing between roughly 6.9 s and 11.1 s. Since all rows still recorded proxy switch and qlog HTTP/3/path evidence, local browser workload continuity should be interpreted as a function of outage duration, retransmission opportunity, and browser task timing, not merely as the presence or absence of path frames. In this local 1 MiB Chrome forced-H3 workload, the observed boundary lies between 4 s and 5 s.

The boundary repetition shows that this boundary is not a single deterministic cut-off. We repeated 4000 ms, 4500 ms, and 5000 ms windows three times for both downlink and upload, yielding 18 rows. The 4000 ms and 4500 ms windows passed in all six rows each, while the 5000 ms window split by workload: downlink passed 3/3 and upload failed 3/3. Successful rows reported DOM completion between 10.2 s and 13.9 s; failed rows reported tightly clustered DOM error timing between 6.921 s and 6.922 s. Thus, around 5 s, the result should be framed as a workload-sensitive transition zone shaped by workload direction, browser task timing, and retransmission opportunity, not as a binary statement that connection migration works or does not work.

The downlink-only fine boundary further showed that this transition zone is not monotonic. The 5000 ms and 5500 ms windows each passed 2/3, while the 6000 ms window failed 3/3. Successful rows completed between 12.276 s and 14.114 s; failed rows errored between 6.922 s and 6.927 s. Every row still retained qlog HTTP/3/path evidence, so downlink also requires transport-level path evidence and DOM-level task completion to be reported separately.

We then refined the upload transition with upload-only repetitions at 4600 ms, 4750 ms, 4900 ms, and 5000 ms. The 4600 ms upload window passed 3/3, 4750 ms split with 1/3 pass, and 4900 ms plus 5000 ms failed 6/6. In this local 1 MiB upload workload, the stable completion region therefore extends to 4600 ms, the unstable transition begins at 4750 ms, and repeated failure starts at 4900 ms. All failed rows still retained qlog HTTP/3/path evidence, reinforcing that transport-level path evidence does not guarantee application-level upload continuity.

Finally, we ran an application-level retry control in the same 4900 ms and 5000 ms upload failure region. The browser upload page retried once with a fresh stream 1000 ms after the first `fetch()` failure. All six rows passed, each row produced two `/upload-sink` requests, and the final attempt delivered the 1 MiB body. However, all six rows reported two Chrome target QUIC sessions and were classified as `nat_rebinding_multiple_quic_sessions`. This is therefore not evidence that single-session browser connection migration succeeded. It shows that application-level retry can recover user-visible task completion while transport continuity and browser session continuity must still be reported separately.

We then extended the retry control to longer 6000 ms and 9000 ms outage windows. All six rows again passed. The 6000 ms rows completed around 15.5 s, while the 9000 ms rows completed around 19.7 s. Chrome target QUIC session counts ranged from two to three. Thus, retry can recover task completion even after longer local outages, but the recovery comes with higher completion latency and replacement/multiple-session behavior. Application-level recovery is therefore an additional evaluation axis, not a substitute for browser connection migration success.

The final retry stress boundary repeated 12000 ms and 15000 ms outage windows. The 12000 ms retry upload passed 3/3 with DOM completion around 20.0 s. In contrast, the 15000 ms retry upload failed 3/3 with DOM error timing around 15.94 s; the second `/upload-sink` request did not reach the server and received upload bytes were zero. The failure rows still retained qlog HTTP/3/path evidence and Chrome target QUIC session evidence. One retry is therefore not a guarantee: in this local 1 MiB upload workload, the observed one-retry recovery boundary lies between 12 s and 15 s.

To retest that failure region, we increased the application-level retry budget to two attempts under the same 15000 ms outage. All three repetitions passed and delivered the final 1 MiB body, but DOM completion moved to 24.484-24.503 s and all rows reported four Chrome target QUIC sessions. Increasing retry budget can therefore recover user-visible task completion under a longer outage, but the recovery comes with replacement/multiple-session behavior and substantial latency. This is not evidence that browser connection migration is mature enough by itself; it is evidence that application-level recovery must be designed and evaluated as a separate axis when browser CM does not preserve the task within one session.

We then searched for the failure side of the two-retry strategy by repeating 18000 ms and 21000 ms outage windows. The 18000 ms rows passed 3/3 with DOM completion between 28.196 s and 28.199 s. The 21000 ms rows failed 3/3 with DOM error timing between 20.950 s and 20.955 s. The failed rows still retained qlog HTTP/3/path evidence and four Chrome target QUIC sessions, but only one `/upload-sink` reached the server and received upload bytes remained zero. Thus, a larger retry budget moved the local failure boundary from 15 s to 18 s, but application task continuity still failed at 21 s.

Across the upload boundary controls, the latest all-pass window moved from 4600 ms without retry, to 12000 ms with one retry, and to 18000 ms with two retries. However, DOM completion at those latest all-pass windows also increased from about 10.2 s to 20.0 s and then 28.2 s, while Chrome target QUIC session count increased from one to three and then four. Application-level recovery therefore improves task completion, but it is not a maturity proof for browser connection migration by itself; recovery latency and session churn must be reported alongside success rate.

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
5. Service Worker recovery, application heartbeat, or upload retry improves real handover continuity.

These claims require follow-up experiments with a controlled public origin, an active secondary network path, Android/Safari observability, and packet capture.
