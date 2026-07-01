# MsQuic Migration API Boundary Audit

Generated: `2026-07-01`

This public-safe audit narrows the remaining MsQuic question from the non-quic-go execution-depth audit: MsQuic clearly has migration/rebinding support, but the claim boundary differs from the quic-go active AddPath/Probe/Switch positive control.

## Summary

| field | value |
| --- | --- |
| implementation | `MsQuic` |
| source commit | `51d449b7d2deb553d6503591f72a8e62d1071054` |
| local clone observed | `True` |
| local clone commit | `51d449b7d2deb553d6503591f72a8e62d1071054` |
| local clone matches audit commit | `yes` |
| migration enabled default | `TRUE` |
| load balancing default | `QUIC_LOAD_BALANCING_DISABLED` |
| NAT rebinding tests present | `yes` |
| peer address changed event present | `yes` |
| local address param present | `yes` |
| quic-go-style AddPath/Probe/Switch API | `not_established_by_public_header_scan` |
| interpretation | MsQuic is mature for client migration/NAT rebinding and QUIC-aware LB deployments, but its public control surface differs from quic-go's direct AddPath/Probe/Switch experiment API. |

## Conclusion

| claim axis | result |
| --- | --- |
| migration support | `implemented_and_tested_for_client_migration_rebinding` |
| active API boundary | `policy_constrained_local_address_control_not_quic_go_style_addpath_probe_switch` |
| deployment boundary | `requires_no_load_balancer_or_cooperative_quic_aware_load_balancer` |
| observability | `public_address_changed_events_and_internal_logs_available` |
| paper use | Use MsQuic as production-relevant selected rebind/path-validation runtime-test and deployment-boundary evidence, not as the deepest controllable active-migration positive control. |

## Evidence Table

| id | source | topic | observation | implication |
| --- | --- | --- | --- | --- |
| `load-balancing-mode-enum` | [src/inc/msquic.h:90-96](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/inc/msquic.h#L90) | `QUIC_LOAD_BALANCING_MODE` | Public API defines disabled, server-id-by-IP, and fixed-server-id load balancing modes. | MsQuic has explicit CID/load-balancing support, but it is deployment configuration rather than per-connection migration proof. |
| `migration-setting-public-api` | [src/inc/msquic.h:789-843](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/inc/msquic.h#L789) | `QUIC_SETTINGS.MigrationEnabled` | The public settings struct exposes a MigrationEnabled bit. | Client migration support is a first-class setting in the public API surface. |
| `default-migration-enabled` | [src/core/quicdef.h:441-448](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/core/quicdef.h#L441) | `QUIC_DEFAULT_MIGRATION_ENABLED` | Migration defaults to TRUE while load balancing defaults to disabled. | The implementation is not missing migration support, but production LB routing is not enabled by default. |
| `settings-doc-migration-lb-boundary` | [docs/Settings.md:51-55](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/docs/Settings.md#L51) | `Settings documentation` | Docs list load balancing as disabled by default and client migration as enabled by default, requiring a cooperative load balancer or no load balancer. | A paper claim must separate endpoint support from QUIC-aware deployment routing. |
| `deployment-doc-lb-configuration` | [docs/Deployment.md:90-105](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/docs/Deployment.md#L90) | `Deployment load balancing modes` | Docs state load-balancing encoding is not enabled by default and describe modes 1 and 2. | Managed or multi-server deployment evidence requires explicit LoadBalancingMode configuration and routing validation. |
| `local-address-connection-param` | [src/inc/msquic.h:1035-1039](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/inc/msquic.h#L1035) | `QUIC_PARAM_CONN_LOCAL_ADDRESS` | The connection parameter table exposes local and remote address parameters. | Applications can influence local address binding, but this is not the same shape as quic-go AddPath/Probe/Switch. |
| `settings-doc-local-address-limits` | [docs/Settings.md:180-186](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/docs/Settings.md#L180) | `QUIC_PARAM_CONN_LOCAL_ADDRESS docs` | Docs say local address is client-only and must be set before start or after handshake confirmation. | There is a controlled local-address hook, but it has state and endpoint limits that must be respected in experiments. |
| `local-address-set-state-check` | [src/core/connection.c:6380-6405](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/core/connection.c#L6380) | `Set QUIC_PARAM_CONN_LOCAL_ADDRESS` | The setter rejects server use and rejects use between start and handshake confirmation. | MsQuic exposes a policy-constrained address-setting API rather than a generic active-path switch primitive. |
| `peer-address-changed-event-api` | [src/inc/msquic.h:1344-1394](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/inc/msquic.h#L1344) | `QUIC_CONNECTION_EVENT_PEER_ADDRESS_CHANGED` | The public connection event enum includes local and peer address changed notifications. | MsQuic has application-visible observability for tuple change events. |
| `peer-address-changed-implementation` | [src/core/connection.c:5561-5568](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/core/connection.c#L5561) | `Indicate peer address changed` | Core connection code emits the peer-address-changed event when the remote path changes. | Passive rebinding/migration can be observed at the application callback layer. |
| `nat-port-rebind-test` | [src/test/lib/HandshakeTest.cpp:685-735](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/test/lib/HandshakeTest.cpp#L685) | `QuicTestNatPortRebind` | The test changes the observed client port and waits for the server-side peer address change event. | There is concrete NAT port rebinding test coverage. |
| `nat-address-rebind-test` | [src/test/lib/HandshakeTest.cpp:739-790](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/test/lib/HandshakeTest.cpp#L739) | `QuicTestNatAddrRebind` | The test changes the observed client address and waits for the peer address change event. | There is concrete NAT address rebinding test coverage. |

## Reporting Boundary

- Safe claim: MsQuic exposes migration settings, address-change events, constrained local-address control, NAT rebinding tests, and a companion selected v4/v6 rebind/path-validation runtime-test PASS artifact.
- Unsafe claim: MsQuic has the same direct application-triggered active migration API shape as quic-go or proves managed-LB continuity without a QUIC-aware routing experiment.
- Next non-iPhone gate: Use the companion selected runtime-test packet for MsQuic implementation evidence; build a small payload-continuity harness or live QUIC-aware LB row only if reviewers require it.

## Paper Interpretation

1. MsQuic weakens an `implementation absence` explanation because client migration is enabled by default and NAT rebind tests exist.
2. MsQuic strengthens the `deployment friction` explanation because load-balancing support requires explicit mode selection and cooperative routing.
3. MsQuic now has a companion selected rebind/path-validation runtime-test packet, but payload continuity and managed-LB claims remain separate gates.
