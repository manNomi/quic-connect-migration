# s2n-quic Active Migration API Feasibility Audit

Generated: `2026-06-30`

This document is public-safe. It records relative source paths and claim boundaries, not raw test logs.

## Summary

| field | value |
| --- | --- |
| source commit | `0f5a4f8ae4163f1b84e72cd29ad110ad99d7efd1` |
| public active trigger API found | `False` |
| migration tests present | `True` |
| active path events present | `True` |
| path migration provider public | `False` |
| qns active migration testcase supported | `False` |

## Public Trigger Candidate Counts

| candidate | count |
| --- | ---: |
| `AddPath` | `0` |
| `Probe_call` | `0` |
| `Switch_call` | `0` |
| `migrate_connection` | `0` |
| `migrate_source` | `0` |
| `start_path_probe` | `0` |
| `perform_migration` | `0` |

## Evidence

| id | source | line | snippet | meaning |
| --- | --- | ---: | --- | --- |
| `path_migration_provider_not_public` | `quic/s2n-quic/src/provider.rs` | `23` | `pub(crate) mod path_migration;` | The path migration provider is present but not exposed as a public application provider. |
| `path_migration_provider_future_public_comment` | `quic/s2n-quic/src/provider/path_migration.rs` | `4` | `// this functionality isn't public but should be assumed that it` | The provider file itself marks this functionality as currently non-public. |
| `core_migration_validator_trait` | `quic/s2n-quic-core/src/path/migration.rs` | `110` | `pub trait Validator: 'static + Send {` | The core stack has a validator trait for migration attempts. |
| `active_migration_transport_parameter_toggle` | `quic/s2n-quic-core/src/connection/limits.rs` | `329` | `pub fn with_active_connection_migration(` | Endpoint limits can advertise or disable active connection migration support. |
| `test_socket_rebind_trigger` | `quic/s2n-quic-tests/src/tests/connection_migration.rs` | `36` | `socket.rebind(local_addr);` | The test suite triggers address changes through a test IO socket rebind hook. |
| `active_path_event_recorder` | `quic/s2n-quic-tests/src/tests/connection_migration.rs` | `41` | `let active_paths = recorder::ActivePathUpdated::new();` | The test suite records active path update events. |
| `ip_rebind_test` | `quic/s2n-quic-tests/src/tests/connection_migration.rs` | `213` | `fn ip_rebind_test() {` | The test suite covers IP rebinding. |
| `port_rebind_test` | `quic/s2n-quic-tests/src/tests/connection_migration.rs` | `218` | `fn port_rebind_test() {` | The test suite covers port rebinding. |
| `blocked_port_negative_test` | `quic/s2n-quic-tests/src/tests/connection_migration.rs` | `511` | `fn rebind_blocked_port() {` | The test suite covers a migration-denial/control case. |
| `zero_length_cid_quiche_interop_enables_active_migration` | `quic/s2n-quic-tests/src/tests/zero_length_cid_client_connection_migration.rs` | `79` | `client_config.set_disable_active_migration(false);` | A zero-length CID interop test enables active migration on the quiche client side. |
| `qns_connection_migration_unsupported` | `quic/s2n-quic-qns/src/client/interop.rs` | `254` | `ConnectionMigration => false,` | The qns client marks the active migration testcase unsupported. |
| `qns_active_migration_todo` | `quic/s2n-quic-qns/src/client/interop.rs` | `253` | `// TODO support the ability to actively migrate on the client` | The interop client still carries an explicit active-migration TODO. |

## Observed Test Names

- `fn rebind_after_handshake_confirmed() {`
- `fn ip_rebind_test() {`
- `fn port_rebind_test() {`
- `fn ip_and_port_rebind_test() {`
- `fn rebind_before_handshake_confirmed() {`
- `fn rebind_blocked_port() {`
- `fn rebind_server_addr_before_handshake_confirmed() {`

## Interpretation

- Supports: s2n-quic has tested connection migration/rebinding machinery and active-path observability, but the current public application API does not expose a quic-go-like AddPath/Probe/Switch trigger.
- Do not claim: Do not claim that the AWS NLB+s2n live runner already performs active migration; its current phase is forwarding echo readiness.
- Paper use: classify s2n-quic as implementation-level migration mature, while keeping AWS NLB+s2n active migration as a phase-2 follow-up after forwarding echo.

## Reproduction

```bash
python3 tools/audit_s2n_active_migration_feasibility.py \
  --output docs/results/s2n-active-migration-api-audit-20260630.md \
  --json-output data/s2n-active-migration-api-audit-20260630.json
```

Focused test command used for the latest local check:

```bash
cargo test --manifest-path "$S2N_QUIC_DIR/quic/s2n-quic-tests/Cargo.toml" \
  connection_migration -- --nocapture
```

Latest local check summary: `10 passed; 0 failed; 90 filtered out`.
