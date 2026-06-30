# Paper Claim Support Matrix

Generated: `2026-06-30`

This matrix is public-safe. It translates the current measured corpus into claim-level wording guidance so the paper can separate supported results from tempting overclaims.

## Summary

| field | value |
| --- | --- |
| claims | `9` |
| support levels | `{'negative_control_supported': 1, 'not_supported_yet': 2, 'supported_local_control': 4, 'supported_scoped': 2}` |

## Claim Guidance

| claim id | support | scope | computed evidence | safe paper wording | do not claim |
| --- | --- | --- | --- | --- | --- |
| `implementation-maturity-is-real-but-heterogeneous` | `supported_scoped` | implementation survey | 18 implementations surveyed; active_migration_api=yes for 8; passive_migration=yes for 14; tests=yes for 14; L4/L5-like levels in 10; top examples: quic-go, Cloudflare quiche, AWS s2n-quic, ngtcp2, LiteSpeed lsquic | QUIC connection migration is not merely a paper feature: surveyed implementations expose path validation, migration or rebinding primitives, tests, and observability at different maturity levels. | Do not claim every HTTP/3 implementation exposes production-ready browser/mobile CM. |
| `controlled-quic-http3-cm-can-preserve-workloads` | `supported_scoped` | quic-go direct origin and AWS NLB controlled experiments | 11 PASS rows with path validation, tuple change, and application success; tiers=['AWS NLB TCP_QUIC :443 passthrough', 'local direct origin', 'local direct origin replication']; task classes=5 | In controlled quic-go direct-origin and AWS NLB passthrough settings, explicit QUIC path migration preserved HTTP/3 request continuity and 1MiB mid-flight upload/download completion. | Do not generalize this result to unmanaged browsers, CDNs, or all load balancers. |
| `http3-support-alone-is-insufficient` | `negative_control_supported` | negative controls across proxy, browser discovery, and outage cases | 60 negative-control rows; proxy-path-validation=2; browser-alt-svc-h3-not-observed=2; browser-multiple-quic-sessions-no-network-change=1; return-path-loss-application-continuity=1; transient-return-path-outage-threshold=6 | HTTP/3 availability and isolated transport artifacts are insufficient evidence of user-visible connection migration; negative controls show failure at proxy path validation, browser policy, session attribution, and return-path continuity. | Do not use Alt-Svc discovery, tuple change, or a qlog PATH event alone as browser CM success. |
| `browser-local-h3-is-ready-but-final-handover-is-pending` | `not_supported_yet` | Chrome/Safari/Android final browser handover protocol | final protocol complete=False; requirements=3/6 | The repository has browser H3 baselines and final handover harnesses, but the final browser/mobile active path-change protocol is not complete yet. | Do not claim Chrome, Safari, or Android Wi-Fi/LTE handover CM success from the current corpus. |
| `workload-direction-changes-continuity-boundary` | `supported_local_control` | Chrome forced-H3 local UDP rebinding transient outage controls | downlink stable-through=-, first all-fail=6000ms, mixed=5000ms 5/6, 5500ms 4/6; upload stable-through=4600ms, first all-fail=4900ms, mixed=4750ms 3/6 | Local outage tolerance is workload-sensitive: downlink and upload enter mixed/failure regions at different outage windows, so continuity must be measured per workload rather than with one global threshold. | Do not convert the local UDP rebinding boundary into a public network handover threshold. |
| `application-retry-shifts-upload-boundary-with-session-cost` | `supported_local_control` | Chrome forced-H3 local upload retry controls | 0 retry stable-through=4600ms, first all-fail=4900ms, max Chrome sessions=2; 1 retry stable-through=12000ms, first all-fail=15000ms, max Chrome sessions=3; 2 retry stable-through=18000ms, first all-fail=21000ms, max Chrome sessions=4 | Application-level upload retry shifted the local completion boundary to longer outage windows, but it increased completion latency and Chrome QUIC session churn; this is task recovery, not single-session browser CM. | Do not describe retry-based completion as proof that the original browser QUIC session migrated. |
| `downlink-retry-effect-is-not-just-waiting` | `supported_local_control` | Chrome forced-H3 local downlink wait-only versus retry controls | wait-only 6000/9000ms PASS=0/6; retry-enabled 6000/9000ms PASS=6/6; retry classification=nat_rebinding_multiple_quic_sessions=2; nat_rebinding_path_validation_without_observed_tuple_change=1; nat_rebinding_multiple_quic_sessions=1; nat_rebinding_path_validation_without_observed_tuple_change=2 | Downlink retry-enabled completion cannot be explained by longer waiting alone: wait-only controls failed at the same 6000ms/9000ms windows where retry-enabled rows completed. | Do not collapse retransmission-only completion and application retry completion into one mechanism. |
| `polling-dashboard-continuity-has-own-boundary` | `supported_local_control` | Chrome forced-H3 local polling/dashboard controls | 250-3000ms PASS=9/9; mixed=4000ms 1/6; all-fail=6000ms, 9000ms; max Chrome sessions=3 | Dashboard-like polling has a separate transition zone: short local outages completed, 4000ms was mixed, and longer windows repeatedly failed; passing rows still need session attribution. | Do not treat polling completion via multiple sessions as single-session browser CM. |
| `publication-ready-browser-cm-claim-remains-blocked` | `not_supported_yet` | paper-level browser CM claim | final protocol complete=False; requirements=3/6 | The current publishable contribution should be framed as a maturity, evidence-chain, and workload-continuity study with controlled implementation/deployment positives and browser handover blockers. | Do not write the final abstract as if real browser/mobile connection migration success has been demonstrated. |

## Next Proof Needed

| claim id | next proof |
| --- | --- |
| `implementation-maturity-is-real-but-heterogeneous` | Tie each selected implementation to a runnable reproduction or source-level citation before final paper submission. |
| `controlled-quic-http3-cm-can-preserve-workloads` | Repeat with at least one non-quic-go server stack or cite why quic-go is the primary experimental implementation. |
| `http3-support-alone-is-insufficient` | Keep the evidence chain gate in the final protocol and report each artifact class separately. |
| `browser-local-h3-is-ready-but-final-handover-is-pending` | chrome-downlink-noheartbeat-active-cm: 0/3; chrome-downlink-heartbeat-active-cm: 0/3; p1-safari-or-android-feasibility: 0/1 |
| `workload-direction-changes-continuity-boundary` | Run the same downlink/upload workload pair on the controlled public active-path protocol. |
| `application-retry-shifts-upload-boundary-with-session-cost` | Measure the same recovery policy under real active path change and compare manual-refresh requirement. |
| `downlink-retry-effect-is-not-just-waiting` | Add public active-path downlink rows with retry counters and browser session attribution. |
| `polling-dashboard-continuity-has-own-boundary` | Run controlled public polling/no-change and active-path rows before using it as a browser handover result. |
| `publication-ready-browser-cm-claim-remains-blocked` | chrome-downlink-noheartbeat-active-cm: 0/3; chrome-downlink-heartbeat-active-cm: 0/3; p1-safari-or-android-feasibility: 0/1 |

## Interpretation

- Positive implementation and controlled deployment claims are supported within their stated scope.
- Browser/mobile active handover remains pending until the final protocol rows are completed.
- Application-level recovery results are useful paper evidence only when reported separately from single-session browser CM.
