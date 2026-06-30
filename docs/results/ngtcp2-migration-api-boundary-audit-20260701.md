# ngtcp2 Migration API Boundary Audit

Generated: `2026-06-30`

This public-safe audit narrows ngtcp2's role in the implementation survey. It explains why ngtcp2 is strong C-library migration/path-validation evidence while still not being browser or managed-deployment continuity evidence.

## Summary

| field | value |
| --- | --- |
| implementation | `ngtcp2` |
| source repository | [https://github.com/ngtcp2/ngtcp2](https://github.com/ngtcp2/ngtcp2) |
| source commit | `c24b12690c5bdf7ad2715ae427504e76bf5c6ffc` |
| local clone observed | `True` |
| local clone commit | `c24b12690c5bdf7ad2715ae427504e76bf5c6ffc` |
| local clone matches audit commit | `yes` |
| evidence items | `26` |
| public client migration api | `present_immediate_and_validation_gated` |
| active api boundary | `direct_client_path_api_not_quic_go_addpath_probe_switch_shape` |
| passive rebinding | `server_path_validation_and_nat_rebinding_tests_present` |
| preferred address | `transport_parameter_and_policy_exception_present` |
| disable active migration policy | `implemented_and_tested` |
| path validation | `begin_result_callbacks_plus_PATH_CHALLENGE_RESPONSE` |
| observability | `qlog_transport_params_and_path_frames` |
| fresh local tests | `focused_ngtcp2_migration_path_validation_tests_passed_in_corpus` |
| browser or deployment runtime row | `absent` |

## Conclusion

| claim axis | result |
| --- | --- |
| implementation status | `mature_C_library_for_client_migration_path_validation_and_rebinding` |
| api boundary | `direct_ngtcp2_path_api_but_no_browser_or_managed_deployment_claim` |
| paper use | `Use ngtcp2 as source-linked C-library maturity evidence and optional second positive-control candidate, not as browser or cloud deployment continuity proof.` |

## Evidence Table

| id | source | topic | observation | implication |
| --- | --- | --- | --- | --- |
| `transport-param-disable-active-migration` | [lib/includes/ngtcp2/ngtcp2.h:1595](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/includes/ngtcp2/ngtcp2.h#L1595) | `Transport-parameter migration policy` | ngtcp2_transport_params exposes disable_active_migration and documents it as the local endpoint not supporting active connection migration. | ngtcp2 models the RFC migration policy boundary directly in its public transport-parameter surface. |
| `transport-param-preferred-address` | [lib/includes/ngtcp2/ngtcp2.h:1615](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/includes/ngtcp2/ngtcp2.h#L1615) | `Preferred-address transport parameter` | The public transport-parameter struct records whether a preferred_address is set. | Preferred-address migration is represented as a public protocol primitive, not only as an internal parser detail. |
| `public-path-object` | [lib/includes/ngtcp2/ngtcp2.h:2142](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/includes/ngtcp2/ngtcp2.h#L2142) | `Public network path representation` | ngtcp2_path represents the local and remote endpoints where a packet is sent and received. | Applications can pass explicit path objects to the connection APIs, which makes ngtcp2 a useful C-library comparison point. |
| `begin-path-validation-callback` | [lib/includes/ngtcp2/ngtcp2.h:3219](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/includes/ngtcp2/ngtcp2.h#L3219) | `Path-validation start callback` | ngtcp2_begin_path_validation notifies the application when validation starts and exposes the path plus fallback path. | Migration/path probing can be observed at the application callback boundary. |
| `path-validation-result-callback` | [lib/includes/ngtcp2/ngtcp2.h:3241](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/includes/ngtcp2/ngtcp2.h#L3241) | `Path-validation result callback` | ngtcp2_path_validation reports success or failure for a validated path and optional fallback path. | ngtcp2 gives applications a first-class completion signal for path validation. |
| `callback-table-path-validation` | [lib/includes/ngtcp2/ngtcp2.h:3800](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/includes/ngtcp2/ngtcp2.h#L3800) | `Callback table integration` | The public callback table includes an optional path_validation callback. | Path-validation observability is part of the regular application integration surface. |
| `callback-table-begin-path-validation` | [lib/includes/ngtcp2/ngtcp2.h:3945](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/includes/ngtcp2/ngtcp2.h#L3945) | `Callback table integration` | The public callback table includes begin_path_validation as a versioned callback. | Applications can observe both the start and the result of migration-related validation. |
| `testing-local-address-api` | [lib/includes/ngtcp2/ngtcp2.h:5912](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/includes/ngtcp2/ngtcp2.h#L5912) | `Local-address setter boundary` | ngtcp2_conn_set_local_addr changes the current path local endpoint address but is documented as testing-purpose only. | The setter is useful for tests and NAT-rebinding simulation, but it should not be reported as the general production active-migration API. |
| `public-immediate-migration-api` | [lib/includes/ngtcp2/ngtcp2.h:6013](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/includes/ngtcp2/ngtcp2.h#L6013) | `Immediate client migration API` | ngtcp2_conn_initiate_immediate_migration starts client connection migration to a given path and performs path validation without waiting for success. | ngtcp2 has a direct public client migration trigger, stronger than source-only or endpoint-wide-only evidence. |
| `public-validation-gated-migration-api` | [lib/includes/ngtcp2/ngtcp2.h:6039](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/includes/ngtcp2/ngtcp2.h#L6039) | `Validation-gated client migration API` | ngtcp2_conn_initiate_migration starts validation on a new path and migrates after successful validation. | The public API exposes a safer validation-gated migration mode distinct from immediate migration. |
| `implementation-path-validation-start` | [lib/ngtcp2_conn.c:323](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/ngtcp2_conn.c#L323) | `Begin-path-validation callback dispatch` | Connection code calls begin_path_validation with flags, the validation path, and the fallback path when present. | The public callback is wired into the migration/path-validation implementation. |
| `implementation-path-validation-result` | [lib/ngtcp2_conn.c:350](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/ngtcp2_conn.c#L350) | `Path-validation result dispatch` | Connection code calls path_validation with success, failure, or aborted results. | A test or runtime harness can observe validation outcomes without inferring from packet logs alone. |
| `path-challenge-transmit` | [lib/ngtcp2_conn.c:5172](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/ngtcp2_conn.c#L5172) | `PATH_CHALLENGE transmission` | conn_write_path_challenge constructs PATH_CHALLENGE frames for the path being validated and tracks probe entries. | ngtcp2 implements active validation traffic rather than simply accepting tuple changes. |
| `path-response-validation-switch` | [lib/ngtcp2_conn.c:6130](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/ngtcp2_conn.c#L6130) | `PATH_RESPONSE validation and path switch` | conn_recv_path_response validates the challenge data, updates the current DCID/path on success, resets path state, and reports success. | Successful validation can promote the new path and reset transport state, which is core migration behavior. |
| `disable-active-migration-enforcement` | [lib/ngtcp2_conn.c:10027](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/ngtcp2_conn.c#L10027) | `Disable-active-migration enforcement` | Server-side packet receive logic discards packets to a new local address when active migration is disabled unless the path matches preferred-address migration. | The implementation enforces policy and preferred-address exceptions, so experiments must record server transport parameters. |
| `immediate-migration-implementation` | [lib/ngtcp2_conn.c:13846](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/ngtcp2_conn.c#L13846) | `Immediate migration implementation` | ngtcp2_conn_initiate_immediate_migration stops PMTUD, retires the current DCID, installs a new path/DCID, resets congestion and ECN state, then begins validation. | Immediate migration is implemented as a real path/DCID transition with follow-up validation. |
| `validation-gated-migration-implementation` | [lib/ngtcp2_conn.c:13921](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/ngtcp2_conn.c#L13921) | `Validation-gated migration implementation` | ngtcp2_conn_initiate_migration creates a path-validation object for the new path, activates a DCID, and begins validation before switching. | ngtcp2 can model validation-first migration semantics directly. |
| `client-migration-test-registered` | [tests/ngtcp2_conn_test.c:86](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/tests/ngtcp2_conn_test.c#L86) | `Focused test registration` | The test suite registers test_ngtcp2_conn_client_connection_migration and related path challenge/disable-active-migration tests. | Migration behavior is first-class in the unit test suite rather than incidental parser coverage. |
| `client-migration-test` | [tests/ngtcp2_conn_test.c:10813](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/tests/ngtcp2_conn_test.c#L10813) | `Client connection migration test` | The client migration test exercises immediate migration, validation-gated migration, PATH_RESPONSE handling, current-path update, and path-history reuse. | The fresh local rerun covers both public migration APIs and validation behavior. |
| `disable-active-migration-test` | [tests/ngtcp2_conn_test.c:11169](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/tests/ngtcp2_conn_test.c#L11169) | `Disable-active-migration policy test` | The tests verify that PATH_CHALLENGE to a new local address is ignored when server disable_active_migration is set, while preferred-address migration is accepted. | Policy and preferred-address exceptions are covered by focused tests. |
| `nat-rebinding-path-validation-test` | [tests/ngtcp2_conn_test.c:14268](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/tests/ngtcp2_conn_test.c#L14268) | `NAT rebinding path-validation test` | A server-side NAT rebinding scenario starts path validation after the remote port changes and checks fallback-path state. | Passive rebinding and server-initiated validation are covered in addition to client active migration. |
| `example-client-active-versus-nat-rebinding` | [examples/client.cc:1347](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/examples/client.cc#L1347) | `Example client local-address change` | The example client distinguishes NAT rebinding simulation from active migration: NAT rebinding updates the local address, while the non-NAT path calls ngtcp2_conn_initiate_immediate_migration. | The sample application demonstrates the boundary between passive rebinding simulation and active client migration. |
| `example-client-cli-flags` | [examples/client.cc:2015](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/examples/client.cc#L2015) | `Example CLI migration trigger` | The example client documents --change-local-addr and --nat-rebinding, with NAT rebinding described as changing local address without starting path validation. | ngtcp2 ships runnable example controls that separate path-change modes for experiments. |
| `qlog-path-validation-frames` | [lib/ngtcp2_qlog.c:839](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/ngtcp2_qlog.c#L839) | `qlog frame observability` | qlog frame writing includes PATH_CHALLENGE and PATH_RESPONSE frame types. | Frame-level path-validation evidence can be captured in qlog when the application enables qlog_write. |
| `qlog-transport-params` | [lib/ngtcp2_qlog.c:946](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/lib/ngtcp2_qlog.c#L946) | `qlog transport-parameter observability` | qlog parameter output includes disable_active_migration and preferred_address when present. | Policy and preferred-address state can be recorded in qlog artifacts. |
| `local-rerun-summary` | [docs/results/implementation-rerun-results-20260630.md:279](https://github.com/manNomi/quic-connect-migration/blob/docs/quinn-neqo-rerun-20260630/docs/results/implementation-rerun-results-20260630.md#L279) | `Fresh local rerun` | The study reran ngtcp2 migration/path-validation focused tests, including client migration, path challenge receive, disable active migration, path validation, and PATH_CHALLENGE/PATH_RESPONSE frame encoding. | The repository has executed local test evidence for the audited source commit, but not a custom ngtcp2 HTTP/3 browser/deployment workload row. |

## Reporting Boundary

- Safe claim: ngtcp2 exposes public immediate and validation-gated client migration APIs, path-validation callbacks, disable-active-migration/preferred-address policy handling, qlog observability, example controls, and focused local test evidence.
- Unsafe claim: ngtcp2 currently proves Chrome/Safari/Android browser handover, managed-CDN/LB continuity, or application-level HTTP/3 workload continuity in this study.
- Next non-iPhone gap: If reviewers require a second C-library runtime positive control, build a small ngtcp2/nghttp3 echo or HTTP/3 harness that changes local address mid-stream and records qlog path validation plus payload continuity.

## Paper Interpretation

1. ngtcp2 weakens an implementation-absence explanation because active client migration, passive rebinding validation, preferred-address policy, and qlog evidence are present.
2. ngtcp2 strengthens the API-shape explanation because it exposes direct path-based APIs, but the current study still lacks a custom ngtcp2 HTTP/3 workload row.
3. ngtcp2 is the best next candidate if the paper needs a second C-library positive control beyond quic-go.
