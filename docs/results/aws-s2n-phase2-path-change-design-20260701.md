# AWS s2n Phase-2 Path-Change Design

Generated: `2026-06-30`

This public-safe design fixes the next AWS NLB + s2n-quic experiment sequence after the live forwarding echo. It does not include credentials, account IDs, hostnames, IP addresses, key material, qlogs, keylogs, pcaps, or NetLogs.

## Summary

| field | value |
| --- | --- |
| public active trigger API found | `false` |
| migration tests present | `true` |
| active path events present | `true` |
| path migration provider public | `false` |
| live runner safety ok | `true` |
| AWS gate open | `false` |
| current open gates | `[]` |
| recommended first step | `phase1_forwarding_echo_prerequisite` |
| preferred phase-2 design | `phase2_nat_rebinding_proxy` |
| decision | Run live forwarding echo first when AWS opens; because s2n lacks a current public AddPath/Probe/Switch API, use NAT-rebinding proxy as the preferred phase-2 path-change design. |

## Claim Boundary

- Safe claim: The current design separates AWS forwarding, NAT-rebinding style path change, implementation-level test-IO rebind evidence, and future public active API work.
- Unsafe claim: The current upstream s2n public API already supports application-triggered active migration through AWS NLB.
- Paper use: Use this as the methods plan for the AWS follow-up, not as a result row.

## Design Options

| rank | id | label | type | prerequisite | mechanism | evidence required | claim if success | do not claim | feasibility | next action |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `phase1_forwarding_echo_prerequisite` | Live forwarding echo prerequisite | `prerequisite` | AWS identity ok and live runner safety audit ok. | Run the existing AWS NLB+s2n live runner without path-change injection. | - validation=ok<br>- client_echo_matches=true<br>- server_success_count=1<br>- successful_target present<br>- cleanup_status recorded | AWS NLB can forward a deterministic s2n-quic echo workload to exactly one CID-routed target in this setup. | Active migration or path-change continuity. | `blocked_until_aws_identity_ok` | Refresh AWS credentials, then run `harness/scripts/run-aws-s2n-nlb-live-data-plane.sh` with default cleanup. |
| 1 | `phase2_nat_rebinding_proxy` | NAT-rebinding proxy path-change | `preferred_phase2` | Phase-1 forwarding echo passes; NLB endpoint, server IDs, and cleanup are validated. | Insert a UDP rebinding proxy between the s2n client and the NLB endpoint so the server/NLB observes a source tuple change while the application workload continues. | - client echo or stream continuity<br>- proxy upstream A/B packet counters<br>- server observed remote tuple count >= 2 or active-path update event<br>- same successful target before/after rebind<br>- PATH_CHALLENGE/PATH_RESPONSE or s2n active-path event when available<br>- CID Server ID remains routable | AWS NLB+s2n can tolerate a controlled NAT-rebinding style path change for the tested echo/stream workload. | Application-triggered active migration API support or browser handover. | `best_next_design_without_s2n_public_active_api` | Run the packaged live-runner variant with PATH_CHANGE_MODE=rebinding_proxy after forwarding echo is stable, then inspect client/proxy/server evidence. |
| 2 | `phase2_linux_network_namespace_rebind` | Linux namespace/SNAT client path-change | `deployment_like_variant` | Linux/EC2 client host with permission to create namespaces, veth, routes, or NAT rules. | Run the s2n client on a Linux host and change the egress source tuple using namespace/routing/SNAT controls during a longer stream workload. | - client path-change command log<br>- before/after local route or SNAT state<br>- server tuple change<br>- same target after path change<br>- workload completion<br>- s2n event/qlog evidence if enabled | The AWS NLB+s2n setup survives a host-level Linux client path-change trigger under the tested conditions. | Mobile Wi-Fi/cellular handover or public browser continuity. | `requires_linux_client_host` | Use only after forwarding echo and proxy rebinding design are stable, or when a Linux EC2 client host is easier than local desktop path-change. |
| 3 | `phase2_s2n_test_io_rebind` | s2n test-IO rebind adaptation | `implementation_variant` | Access to s2n-quic test IO hooks or a forked test harness. | Adapt the s2n test-suite socket rebind mechanism into a controlled local or lab runner to reproduce the library's tested rebind path outside the public app API. | - socket.rebind-style trigger<br>- ActivePathUpdated event<br>- workload completion<br>- negative-control blocked-port row | s2n-quic's lower-level rebind machinery works in a reproduced lab harness. | Public application API support, AWS NLB deployment success, or browser behavior. | `useful_but_lower_paper_value` | Keep as fallback if AWS remains blocked and implementation-depth appendix becomes necessary. |
| 4 | `phase2_public_api_wait_or_patch` | Wait for or patch public active API | `long_term` | Upstream public path migration provider or an explicit research fork. | Expose a quic-go-like application trigger in s2n-quic, then perform AddPath/Probe/Switch-like migration through AWS NLB. | - public API call trace<br>- path probe before switch<br>- validated new path<br>- payload continuity<br>- same target through NLB | A modified or future s2n-quic API can perform application-triggered active migration through CID-aware NLB routing. | Current upstream public API behavior. | `not_current_upstream` | Do not block the paper on this; mention as future improvement direction unless a fork is approved. |

## Recommended Sequence

1. Keep live AWS execution blocked until `aws_identity_ok=yes`.
2. Run the existing live forwarding echo and inspect `validation=ok`, `client_echo_matches=true`, and `server_success_count=1`.
3. Run the packaged NAT-rebinding proxy variant only after forwarding echo is stable.
4. Treat proxy or namespace path-change evidence as passive/NAT-rebinding continuity unless a current public s2n active migration API is introduced.
5. Keep a future public API/fork path as future work rather than the next paper-critical blocker.
