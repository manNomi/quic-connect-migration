# Non-quic-go Execution Depth Audit

Generated: `2026-07-01`

This public-safe audit explains why quic-go has the deepest controlled run while other implementations are still useful evidence. It is generated from `data/implementation-survey.csv` plus the latest AWS s2n readiness artifact when present.

## Summary

| field | value |
| --- | --- |
| survey rows excluding quic-go | `17` |
| depth counts | `{'local_test_suite_rerun': 6, 'local_runtime_or_app_demo': 4, 'focused_partial_runtime': 2, 'client_policy_source_plus_local_baseline': 1, 'source_test_map_only': 1, 'managed_or_external_deployment_gate': 2, 'negative_control_runtime': 1}` |
| evidence strength counts | `{'deployment_gate_pending': 2, 'focused_positive_but_not_full_stack': 2, 'negative_control': 1, 'policy_dependent_client_evidence': 1, 'source_level_active_and_passive_evidence': 1, 'strong_implementation_or_runtime_evidence': 6, 'strong_runtime_or_app_evidence': 4}` |
| remaining deepening candidates | `['XQUIC', 'Chromium Chrome Cronet', 'AWS CloudFront', 'AWS NLB plus s2n-quic', 'mvfst', 'quicly']` |
| interpretation | quic-go is the deepest controllable positive control, but non-quic-go evidence is broad enough to show that CM is implemented across multiple stacks at different depths. |

## Current AWS Gate

| field | value |
| --- | --- |
| input exists | `True` |
| aws identity ok | `no` |
| aws identity classification | `invalid_client_token` |
| local s2n proof | `PASS` |
| local proof echo matches | `yes_from_pass` |
| s2n live runner ready | `yes` |
| can run live s2n NLB now | `no` |
| blocked reason | `aws_identity_invalid_client_token` |

## Professor-facing Answer

quic-go was used for the deepest controlled migration run because it exposes the cleanest AddPath/Probe/Switch-style control path; other implementations were still verified, but many are better used as maturity, runtime, deployment-readiness, or negative-control evidence.

## Implementation Depth Table

| priority | implementation | depth class | strength | level | active API | passive | tests | why not quic-go depth | next non-iPhone gate |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | Cloudflare quiche | `local_test_suite_rerun` | `strong_implementation_or_runtime_evidence` | `L4` | `yes` | `yes` | `yes` | Local migration tests and sample evidence are strong, but the target question for Cloudflare's managed edge is a separate deployment-layer claim. | Keep as cross-implementation evidence; only promote Cloudflare managed edge after a separate public edge experiment. |
| 3 | AWS s2n-quic | `local_test_suite_rerun` | `strong_implementation_or_runtime_evidence` | `L4_AWS_L5_candidate` | `likely` | `yes` | `yes` | Library tests and the local AWS-NLB-compatible CID proof are positive, but live forwarding still depends on the AWS identity gate. | Refresh AWS credentials, rerun the s2n NLB readiness gate, then run forwarding echo before any path-change variant. |
| 4 | ngtcp2 | `local_runtime_or_app_demo` | `strong_runtime_or_app_evidence` | `L4_runtime_example` | `yes` | `yes` | `yes` | The library exposes migration/path-validation primitives, and the official osslclient/osslserver example now provides a local HTTP/3 runtime migration positive row; it still is not a browser or managed-deployment proof. | Use the ngtcp2 runtime packet as a second C-library positive control; repeat on a clean host only if reviewers require independent replication. |
| 5 | LiteSpeed lsquic | `local_runtime_or_app_demo` | `strong_runtime_or_app_evidence` | `L4_L5_candidate` | `yes` | `yes` | `yes` | Runtime demos reached app-level evidence, but production-like OpenLiteSpeed deployment needs a Linux/EC2 follow-up. | Run the OpenLiteSpeed or LSQUIC production-like demo on Linux/EC2. |
| 6 | MsQuic | `local_test_suite_rerun` | `strong_implementation_or_runtime_evidence` | `L4_L5_caveat` | `policy_constrained` | `yes` | `yes` | Selected NAT rebinding and path-validation tests passed, and the focused API audit shows constrained local-address control plus a QUIC-aware LB boundary rather than quic-go-style AddPath/Probe/Switch control. | Optional: build a small MsQuic runtime harness that changes QUIC_PARAM_CONN_LOCAL_ADDRESS after handshake confirmation and verifies peer-address-change plus payload continuity. |
| 7 | Quinn | `local_runtime_or_app_demo` | `strong_runtime_or_app_evidence` | `L4_runtime_rebind` | `partial` | `yes` | `yes` | Rust test evidence plus the endpoint-rebind runtime packet are useful for maturity comparison, but the active migration surface remains endpoint-wide rebind rather than quic-go's per-connection AddPath/Probe/Switch API. | Use the Quinn rebind runtime packet as Rust-stack endpoint-rebind evidence; add a custom HTTP/3 workload only if reviewers require application-layer Rust evidence. |
| 8 | Neqo | `local_test_suite_rerun` | `strong_implementation_or_runtime_evidence` | `L3_L4` | `yes` | `yes` | `yes` | Mozilla-adjacent tests and the Firefox/Neqo boundary audit provide broad migration maturity evidence, but this did not become a Firefox browser runtime proof without Firefox/Necko controlled handover rows. | Use the Firefox/Neqo browser-boundary audit now; run Firefox/Necko controlled rows only when browser-runtime evidence becomes reviewer-critical. |
| 9 | XQUIC | `focused_partial_runtime` | `focused_positive_but_not_full_stack` | `L3_L4_partial` | `unclear` | `yes` | `yes` | The NAT rebinding demo passed, and a fail-closed Linux full-suite replay runner is now packaged; the current macOS build path still hits unrelated AppleClang Werror toolchain friction. | Run harness/scripts/run-xquic-full-suite-linux.sh on Linux and accept only validation=ok with zero failed unit/case markers. |
| 10 | Chromium Chrome Cronet | `client_policy_source_plus_local_baseline` | `policy_dependent_client_evidence` | `L4_client_policy_boundary_audit` | `yes` | `policy_dependent` | `yes` | Source policy hooks, tests, NetLog migration events, and Cronet default-disable evidence exist, but actual browser handover behavior is runtime-policy dependent and must be proven with browser rows. | Use the policy-boundary audit now; run Android/Cronet or desktop Chrome active network-change rows when a non-iPhone secondary path is available. |
| 11 | AWS CloudFront | `managed_or_external_deployment_gate` | `deployment_gate_pending` | `L5_edge_boundary_audit` | `n/a` | `n/a` | `managed` | CloudFront official docs support viewer-edge HTTP/3 Connection Migration, but CloudFront cannot be treated as end-to-end origin Connection Migration without separate origin evidence. | Use the CDN edge boundary audit now; run a viewer-edge continuity experiment only if the paper needs managed-edge runtime evidence. |
| 12 | AWS NLB plus s2n-quic | `managed_or_external_deployment_gate` | `deployment_gate_pending` | `L5_deployment_candidate` | `likely` | `yes` | `local_provider_proof` | The local custom CID provider proof exists, but live target forwarding and path-change continuity are blocked until AWS identity opens. | Use the packaged live runner after AWS identity is valid; start with forwarding echo. |
| 13 | mvfst | `source_test_map_only` | `source_level_active_and_passive_evidence` | `L5_candidate` | `yes` | `yes` | `yes` | Source/test coverage is strong and a focused Linux runner is now packaged, but local build/test execution is still gated by Buck/getdeps/disk/toolchain cost. | Run harness/scripts/run-mvfst-focused-migration-tests-linux.sh on a Linux builder with buck2 and enough disk; accept only validation=ok for all three focused targets. |
| 14 | picoquic | `local_test_suite_rerun` | `strong_implementation_or_runtime_evidence` | `L4_L5` | `yes` | `yes` | `yes` | The test suite is rich and positive, but it is used here as an edge-case maturity comparison rather than the primary browser/deployment harness. | Use as edge-case appendix evidence; no immediate deeper run is required unless reviewers ask for another active API baseline. |
| 15 | nginx QUIC | `local_runtime_or_app_demo` | `strong_runtime_or_app_evidence` | `L4_server_runtime` | `no` | `yes` | `runtime_demo` | The server runtime demo is positive, but nginx is server-side only; Linux quic_bpf and browser handover are separate deployment claims. | Run the Linux quic_bpf runner on EC2 or another Linux host with the required privileges. |
| 16 | quicly | `focused_partial_runtime` | `focused_positive_but_not_full_stack` | `L3_L4_focused_e2e_full_gate` | `internal` | `yes` | `yes` | The focused path-migration e2e subtest passed and a fail-closed Linux full-e2e runner is packaged, while the current study still lacks a clean full t/e2e.t PASS artifact. | Run harness/scripts/run-quicly-full-e2e-linux.sh on Linux and accept full-e2e promotion only when validation=ok_full_e2e. |
| 17 | aioquic | `local_test_suite_rerun` | `strong_implementation_or_runtime_evidence` | `L2_L3` | `no` | `partial` | `yes` | The Python implementation is a readable passive/path-validation reference, not the strongest active-migration API candidate. | Keep as readable reference evidence unless a Python passive rebind demonstration is needed. |
| 18 | HAProxy QUIC | `negative_control_runtime` | `negative_control` | `L1_L2` | `no` | `partial` | `runtime_negative_control` | This is intentionally a negative control showing that HTTP/3 proxy availability does not imply active Connection Migration support. | Keep version-scoped negative control paired with HTTP/3 proxy support evidence. |

## Reporting Boundary

- Safe claim: The non-quic-go corpus contains implementation, runtime, source, readiness, and negative-control evidence with explicit depth limits.
- Unsafe claim: The non-quic-go corpus proves equal active migration control, browser handover, or managed deployment continuity across all stacks.

## Interpretation

1. The result is not `only quic-go has Connection Migration`; the result is `quic-go is the cleanest controllable positive control`.
2. Library/test-suite positives should be used to reject an implementation-absence explanation.
3. Browser, CDN, LB, and server production claims require their own runtime gates because they add policy, routing, observability, and deployment constraints.
4. The next non-iPhone experimental upgrade is still AWS NLB+s2n forwarding echo once credentials are valid; until then, this audit prevents overclaiming.
