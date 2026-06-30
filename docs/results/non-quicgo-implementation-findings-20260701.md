# Non-quic-go Implementation Findings

Generated: `2026-06-30`

This public-safe report answers the narrow question: what did we find outside quic-go? It uses `data/implementation-survey.csv` as the source of truth and intentionally separates implementation maturity from browser, CDN, LB, and application-continuity claims.

## Summary

| field | value |
| --- | --- |
| survey rows excluding quic-go | `17` |
| claim class counts | `{'strong_cross_implementation_positive': 8, 'server_or_app_runtime_positive': 2, 'focused_or_partial_positive': 2, 'source_or_readiness_only': 2, 'negative_control': 1, 'managed_or_deployment_pending': 2}` |
| evidence status counts | `{'fresh_app_demo_20260630': 1, 'fresh_focused_e2e_20260630': 1, 'fresh_negative_control_20260630': 1, 'fresh_rebind_demo_20260630': 1, 'fresh_rerun_20260630': 8, 'fresh_runtime_20260630': 1, 'partial_deferred': 2, 'source_and_local_browser_baseline': 1, 'source_inspected': 1}` |
| active migration API yes | `7` |
| passive migration yes | `13` |
| tests yes | `13` |
| interpretation | Non-quic-go evidence is broad enough to reject an implementation-absence explanation, but each stack has a different claim boundary. |

## Professor-facing Answer

We used quic-go as the deepest controllable positive control, then added non-quic-go evidence as cross-implementation maturity, server/app demos, readiness blockers, and negative controls.

## Safe Boundary

- Safe claim: quic-go is not the only implementation with CM evidence; multiple non-quic-go stacks expose tests, runtime demos, path validation, or policy hooks.
- Unsafe claim: All non-quic-go implementations provide equal active migration behavior, browser continuity, or production deployment success.

## Implementation Table

| priority | name | claim class | evidence status | level | active API | passive | tests | risk note | next action |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | Cloudflare quiche | `strong_cross_implementation_positive` | `fresh_rerun_20260630` | `L4` | `yes` | `yes` | `yes` | Library/sample evidence is strong, but Cloudflare managed edge behavior is a separate deployment claim. | Use as cross-implementation client/server migration evidence |
| 3 | AWS s2n-quic | `strong_cross_implementation_positive` | `fresh_rerun_20260630` | `L4_AWS_L5_candidate` | `likely` | `yes` | `yes` | Library tests are positive; live AWS NLB forwarding and active source migration remain separate phases. | Custom AWS NLB CID provider proof restored and rerun; live AWS NLB+s2n target test remains follow-up |
| 4 | ngtcp2 | `strong_cross_implementation_positive` | `fresh_rerun_20260630` | `L4` | `yes` | `yes` | `yes` | Use as implementation maturity evidence, not as browser or managed-deployment proof. | Use as C library primitive/path-validation comparison |
| 5 | LiteSpeed lsquic | `server_or_app_runtime_positive` | `fresh_app_demo_20260630` | `L4_L5_candidate` | `yes` | `yes` | `yes` | Example app demos are positive; OpenLiteSpeed production-like deployment is still follow-up. | Use as preferred-address and NAT-rebinding app-level positive control; OpenLiteSpeed production-like demo remains follow-up |
| 6 | MsQuic | `strong_cross_implementation_positive` | `fresh_rerun_20260630` | `L4_L5_caveat` | `policy_constrained` | `yes` | `yes` | NAT rebind/path validation tests are positive; API audit shows constrained local-address control, while QUIC-aware load balancing remains a deployment boundary. | Use as production-relevant NAT rebinding/path-validation evidence; API audit shows constrained local-address control rather than quic-go-style AddPath/Probe/Switch |
| 7 | Quinn | `strong_cross_implementation_positive` | `fresh_rerun_20260630` | `L3_L4` | `partial` | `yes` | `yes` | Use as implementation maturity evidence, not as browser or managed-deployment proof. | Use as Rust migration/rebind comparison |
| 8 | Neqo | `strong_cross_implementation_positive` | `fresh_rerun_20260630` | `L3_L4` | `yes` | `yes` | `yes` | Use as implementation maturity evidence, not as browser or managed-deployment proof. | Use as Firefox-adjacent broad migration test evidence |
| 9 | XQUIC | `focused_or_partial_positive` | `fresh_rebind_demo_20260630` | `L3_L4_partial` | `unclear` | `yes` | `yes` | NAT rebinding demo passed; full test suite needs Linux or compiler-flag follow-up. | Use as NAT rebinding demo evidence; retry full run_tests on Linux because macOS AppleClang Werror blocks QPACK unit build |
| 10 | Chromium Chrome Cronet | `source_or_readiness_only` | `source_and_local_browser_baseline` | `L4_client_runtime_policy_dependent` | `yes` | `policy_dependent` | `yes` | Policy hooks and NetLog exist, but browser handover success requires runtime rows. | Run Android/Cronet active interface handover; compare Chrome policy with Cronet network-change migration defaults |
| 11 | AWS CloudFront | `managed_or_deployment_pending` | `partial_deferred` | `L5_edge` | `n/a` | `n/a` | `managed` | Viewer-edge continuity is not end-to-end origin Connection Migration. | Design viewer-edge experiment and clarify non-end-to-end interpretation |
| 12 | AWS NLB plus s2n-quic | `managed_or_deployment_pending` | `partial_deferred` | `L5_deployment_candidate` | `likely` | `yes` | `local_provider_proof` | Local CID provider proof exists, but live target forwarding and active migration are pending. | s2n custom CID local provider proof PASS; next run live AWS NLB target A/B forwarding and migration continuity |
| 13 | mvfst | `source_or_readiness_only` | `source_inspected` | `L5_candidate` | `yes` | `yes` | `yes` | Focused source/test map is strong, but local build/test execution is blocked by toolchain/disk gates. | Use source audit plus focused migration target map as large-scale implementation maturity evidence; Linux/Buck/getdeps build test remains follow-up |
| 14 | picoquic | `strong_cross_implementation_positive` | `fresh_rerun_20260630` | `L4_L5` | `yes` | `yes` | `yes` | Use as implementation maturity evidence, not as browser or managed-deployment proof. | Use as edge-case maturity and preferred-address comparison |
| 15 | nginx QUIC | `server_or_app_runtime_positive` | `fresh_runtime_20260630` | `L4_server_runtime` | `no` | `yes` | `runtime_demo` | Server runtime evidence is positive; Linux quic_bpf and browser handover are separate claims. | Use as server-side runtime active-client-migration positive control; browser handover, Linux quic_bpf, and production deployment remain follow-up |
| 16 | quicly | `focused_or_partial_positive` | `fresh_focused_e2e_20260630` | `L3_L4_focused_e2e` | `internal` | `yes` | `yes` | Focused path-migration e2e is positive; full e2e still has unrelated host-specific failures. | Use as focused e2e path-migration evidence; full e2e still fails unrelated slow-start subtest on this host |
| 17 | aioquic | `strong_cross_implementation_positive` | `fresh_rerun_20260630` | `L2_L3` | `no` | `partial` | `yes` | Readable passive/path-validation reference; not a primary active-migration API candidate. | Use as readable passive path-validation reference, not primary experiment |
| 18 | HAProxy QUIC | `negative_control` | `fresh_negative_control_20260630` | `L1_L2` | `no` | `partial` | `runtime_negative_control` | HTTP/3 proxy success is a negative control for active migration support. | Use fresh local negative control as evidence that HTTP/3 proxy support does not imply active CM support |

## Interpretation

1. quic-go remains the deepest controllable AddPath/Probe/Switch positive control.
2. Non-quic-go results are not empty: quiche, picoquic, s2n-quic, LSQUIC, nginx QUIC, MsQuic, ngtcp2, Quinn, Neqo, XQUIC, quicly, and aioquic all contribute different evidence levels.
3. HAProxy is valuable because it is a negative control: ordinary HTTP/3 availability does not imply active Connection Migration support.
4. Chromium/Cronet, CloudFront, AWS NLB+s2n, and mvfst should be reported as policy/deployment/readiness boundaries until their runtime gates open.
