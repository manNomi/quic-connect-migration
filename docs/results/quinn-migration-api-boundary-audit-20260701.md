# Quinn Migration API Boundary Audit

Generated: `2026-06-30`

This public-safe audit narrows Quinn's role in the implementation survey. It explains why Quinn is strong Rust-stack migration/rebind evidence while still not being the same positive-control shape as quic-go.

## Summary

| field | value |
| --- | --- |
| implementation | `Quinn` |
| source repository | [https://github.com/quinn-rs/quinn](https://github.com/quinn-rs/quinn) |
| source commit | `953b466747e667a9dfda0596b8051a0644f8333d` |
| local clone observed | `True` |
| local clone commit | `953b466747e667a9dfda0596b8051a0644f8333d` |
| local clone matches audit commit | `yes` |
| evidence items | `20` |
| server migration default | `enabled` |
| endpoint rebind api | `present_endpoint_wide` |
| passive client migration | `implemented_and_tested` |
| active local address control | `endpoint_rebind_plus_internal_local_address_changed_hook` |
| preferred address | `implemented_with_config_and_tests` |
| path validation | `PATH_CHALLENGE_RESPONSE_state_and_stats` |
| fresh local tests | `quinn-proto migration 1 passed; quinn rebind 1 passed` |
| quic go style addpath probe switch | `not_established` |
| browser or http3 runtime row | `absent` |

## Conclusion

| claim axis | result |
| --- | --- |
| implementation status | `mature_for_server_allowed_client_migration_and_endpoint_rebind` |
| api boundary | `endpoint_wide_socket_rebind_not_per_connection_addpath_probe_switch` |
| paper use | `Use Quinn as Rust-stack migration/rebind maturity evidence and optional runtime-follow-up target, not as browser/deployment continuity proof.` |

## Evidence Table

| id | source | topic | observation | implication |
| --- | --- | --- | --- | --- |
| `server-migration-default` | [quinn-proto/src/config/mod.rs:215](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/config/mod.rs#L215) | `ServerConfig migration policy` | ServerConfig documents client migration/NAT rebinding support and the default constructor sets migration to true. | Quinn is not missing server-side support for client address changes; this weakens a pure implementation-absence explanation. |
| `server-migration-setter` | [quinn-proto/src/config/mod.rs:288](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/config/mod.rs#L288) | `Public server migration knob` | ServerConfig exposes a migration(value) setter that controls whether clients may migrate to new addresses. | Migration is an explicit endpoint policy, so experiments must record whether the server permits it. |
| `connection-remote-address-doc` | [quinn/src/connection.rs:542](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn/src/connection.rs#L542) | `Application-visible peer address` | Connection::remote_address documents that clients may change addresses when ServerConfig::migration is true. | Applications can observe the peer address boundary, but this is not by itself a full workload-continuity proof. |
| `endpoint-rebind-api` | [quinn/src/endpoint.rs:265](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn/src/endpoint.rs#L265) | `Endpoint socket rebind API` | Endpoint::rebind switches the endpoint to a new UDP socket and delegates to rebind_abstract. | Quinn exposes a runtime mechanism that can trigger local-address change handling for all active connections. |
| `endpoint-rebind-scope` | [quinn/src/endpoint.rs:273](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn/src/endpoint.rs#L273) | `Endpoint-wide rebind scope` | rebind_abstract updates the endpoint address live, affecting all active connections, and warns that unreachable connections may be lost. | The public control surface is endpoint-wide socket rebind, not a per-connection AddPath/Probe/Switch API. |
| `abandoned-socket-during-active-migration` | [quinn/src/endpoint.rs:502](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn/src/endpoint.rs#L502) | `Active migration receive path` | Endpoint state keeps an abandoned_socket during active migration until the first packet arrives on the new socket. | The implementation accounts for in-flight traffic around endpoint rebind, but this remains a library/runtime behavior claim. |
| `migration-forbidden-drop` | [quinn-proto/src/connection/mod.rs:1103](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/connection/mod.rs#L1103) | `Remote migration policy enforcement` | A datagram from a new remote address is dropped when the side does not allow remote migration. | Quinn enforces the disable/allow migration boundary, so experiments must avoid assuming every tuple change is accepted. |
| `server-migration-handler` | [quinn-proto/src/connection/mod.rs:3080](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/connection/mod.rs#L3080) | `Server-side migration detection` | When a non-probing data packet arrives from a new remote address on a server connection, Quinn calls migrate and updates the remote CID. | Quinn has server-side passive/client-migration machinery with linkability-conscious CID handling. |
| `migrate-path-validation-state` | [quinn-proto/src/connection/mod.rs:3100](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/connection/mod.rs#L3100) | `New path setup` | migrate creates a new PathData, distinguishes NAT-rebinding-like same-IP moves, queues PATH_CHALLENGE, and arms a path-validation timer. | The implementation models new-path validation rather than blindly accepting the new tuple. |
| `local-address-changed-hook` | [quinn-proto/src/connection/mod.rs:3141](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/connection/mod.rs#L3141) | `Local address change hook` | local_address_changed updates the remote CID and sends a ping after a local address change. | Active local-address migration exists internally through endpoint rebind, but it differs from quic-go's explicit path probe/switch control. |
| `path-challenge-transmit` | [quinn-proto/src/connection/mod.rs:3268](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/connection/mod.rs#L3268) | `PATH_CHALLENGE transmission` | Outgoing data-space packets on an unvalidated path include PATH_CHALLENGE and update frame statistics. | Quinn has observable path-validation frame accounting for migration/rebinding evidence. |
| `path-response-transmit` | [quinn-proto/src/connection/mod.rs:3283](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/connection/mod.rs#L3283) | `PATH_RESPONSE transmission` | Queued path responses are emitted on the relevant path and counted in frame statistics. | Responder-side path validation is implemented, not merely recognized in the frame parser. |
| `preferred-address-config` | [quinn-proto/src/config/mod.rs:297](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/config/mod.rs#L297) | `Preferred address configuration` | ServerConfig exposes preferred IPv4 and IPv6 address setters, and the docs say clients switch if reachable. | Quinn supports the preferred-address migration mode separately from generic rebinding. |
| `preferred-address-cid-receive` | [quinn-proto/src/connection/mod.rs:3519](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/connection/mod.rs#L3519) | `Preferred-address CID handling` | When a preferred address is received, Quinn inserts the preferred-address connection ID as sequence 1. | Preferred-address support has concrete CID state handling, not just transport-parameter parsing. |
| `path-frame-stats` | [quinn-proto/src/connection/stats.rs:117](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/connection/stats.rs#L117) | `Frame-level observability` | FrameStats includes NEW_CONNECTION_ID, PATH_CHALLENGE, PATH_RESPONSE, and RETIRE_CONNECTION_ID fields. | Quinn exposes useful in-process counters for migration/path-validation tests. |
| `proto-migration-test` | [quinn-proto/src/tests/mod.rs:1351](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/tests/mod.rs#L1351) | `Focused migration test` | The migration test changes the client address, sends data, observes the server remote address update, and checks immediate ACK behavior. | There is focused protocol-level test coverage for client migration/rebinding behavior. |
| `mtud-after-migration-test` | [quinn-proto/src/tests/mod.rs:2455](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/tests/mod.rs#L2455) | `Post-migration path property test` | The MTUD migration test changes the client port, observes the server remote address update, and verifies MTU behavior on the new path. | Quinn tests post-migration path characteristics, not only tuple recognition. |
| `preferred-address-test` | [quinn-proto/src/tests/mod.rs:3590](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn-proto/src/tests/mod.rs#L3590) | `Preferred-address test` | The preferred_address test ensures a connection can be made when the server advertises a preferred address. | Preferred-address behavior has a test hook, but the test is not a full production/browser workload. |
| `runtime-rebind-receive-test` | [quinn/src/tests.rs:691](https://github.com/quinn-rs/quinn/blob/953b466747e667a9dfda0596b8051a0644f8333d/quinn/src/tests.rs#L691) | `Runtime endpoint rebind test` | The rebind_recv Tokio test connects client/server endpoints, rebinds the client UDP socket, and receives a server unidirectional stream. | There is runtime-level evidence that endpoint rebind can preserve a simple Quinn stream workload. |
| `local-rerun-summary` | [docs/results/implementation-rerun-results-20260630.md:337](https://github.com/manNomi/quic-connect-migration/blob/docs/quinn-neqo-rerun-20260630/docs/results/implementation-rerun-results-20260630.md#L337) | `Fresh local rerun` | The study records cargo test -p quinn-proto migration and cargo test -p quinn rebind as passing at the audited commit. | The current corpus has local test execution evidence, but not a custom HTTP/3 or browser deployment row for Quinn. |

## Reporting Boundary

- Safe claim: Quinn exposes server migration policy, endpoint-wide socket rebind, preferred-address support, path-validation machinery, frame stats, and fresh local migration/rebind tests.
- Unsafe claim: Quinn currently provides the same per-connection AddPath/Probe/Switch control shape as quic-go or proves HTTP/3 browser/deployment workload continuity in this study.
- Next non-iPhone gap: If reviewers require a Rust runtime row, build a small Quinn echo/HTTP workload harness that calls Endpoint::rebind mid-stream and records frame stats, peer address change, and payload continuity.

## Paper Interpretation

1. Quinn weakens an implementation-absence explanation because migration policy, rebind, preferred address, and path validation are present and tested.
2. Quinn strengthens the API-shape explanation because the public runtime trigger is endpoint-wide socket rebind, not quic-go-style per-connection path control.
3. Quinn should stay in the non-quic-go maturity section unless a dedicated Quinn echo/HTTP runtime harness is added.
