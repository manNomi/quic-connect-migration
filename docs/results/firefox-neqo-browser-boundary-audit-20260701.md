# Firefox/Neqo Browser Boundary Audit

Generated: `2026-06-30`

This public-safe audit tightens the Mozilla/Firefox part of the implementation survey. Neqo is important because it is Firefox-adjacent, but Neqo transport tests are not the same as a Firefox browser network-change experiment.

## Summary

| field | value |
| --- | --- |
| implementation | `Neqo` |
| browser runtime | `Firefox` |
| source repository | [https://github.com/mozilla/neqo](https://github.com/mozilla/neqo) |
| source commit | `3ba227d37f46a5684e984ead831b73344d9fec63` |
| Firefox glue reference | [https://github.com/mozilla-firefox/firefox/blob/main/netwerk/socket/neqo_glue/Cargo.toml](https://github.com/mozilla-firefox/firefox/blob/main/netwerk/socket/neqo_glue/Cargo.toml) |
| evidence items | `18` |
| Firefox adjacency supported | `yes` |
| transport migration API present | `yes` |
| passive rebinding handling present | `yes` |
| preferred-address tests present | `yes` |
| migration policy boundary tests present | `yes` |
| qlog migration parameter observability present | `yes` |
| local Neqo transport migration rerun | `53_passed_0_failed_recorded_20260630` |
| Firefox browser runtime handover proven here | `no` |
| Firefox browser runtime rows in current study | `absent` |
| interpretation | Neqo is strong Mozilla/Firefox-adjacent implementation maturity evidence, but standalone Neqo transport tests must not be promoted to a Firefox browser HTTP/3 network-change continuity claim. |

## Conclusion

| claim axis | result |
| --- | --- |
| implementation status | `transport_migration_mature_in_source_and_tests` |
| Firefox status | `browser_runtime_claim_not_executed` |
| paper use | Use Neqo to rebut a pure implementation-absence explanation for CM underuse; keep Firefox browser handover as a separate runtime gate. |

## Evidence Table

| id | source | topic | observation | implication |
| --- | --- | --- | --- | --- |
| `neqo-firefox-implementation-claim` | [README.md:5-12](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/README.md#L5) | `Firefox adjacency` | Neqo describes itself as the QUIC implementation used by Mozilla in Firefox and other products, and as a QUIC transport, HTTP/3, and QPACK library. | Neqo is a legitimate Firefox-adjacent implementation maturity target, not an unrelated toy stack. |
| `neqo-server-experimental-boundary` | [README.md:15-24](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/README.md#L15) | `Server maturity boundary` | The README warns that Neqo server functionality is experimental and not for production use. | A Neqo server result should be treated as test/debug implementation evidence, not production Firefox-server deployment evidence. |
| `neqo-firefox-version-linkage` | [SECURITY.md:7-17](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/SECURITY.md#L7) | `Firefox release linkage` | Neqo support is tied to Firefox versions where it has landed, and active Firefox versions point to vendored Neqo versions. | Firefox relevance is real, but the exact browser behavior depends on the Firefox vendored version and runtime integration. |
| `neqo-firefox-local-server-recipe` | [README.md:154-162](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/README.md#L154) | `Firefox test integration recipe` | The README includes a recipe for connecting Firefox to a local neqo-server with HTTP/3 testing preferences and optional logging/profiling. | Firefox-adjacent runtime experiments are possible, but they require explicit browser setup and separate execution artifacts. |
| `neqo-firefox-vendor-glue` | [README.md:179-186](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/README.md#L179) | `Firefox vendoring path` | The Neqo release process tells maintainers to update Firefox-side neqo dependency versions in neqo_glue and HTTP/3 test-server Cargo manifests. | The Firefox browser claim must bind the observed Firefox build/version, not only the standalone Neqo repository commit. |
| `neqo-migrate-api` | [neqo-transport/src/connection/mod.rs:2068-2140](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/neqo-transport/src/connection/mod.rs#L2068) | `Active migration API` | Connection::migrate accepts local/remote address choices, supports immediate or post-probe migration, rejects disabled/invalid migration, probes the candidate path, and emits a path-migrated event. | Neqo has explicit transport-level active migration machinery. |
| `neqo-peer-migration-handler` | [neqo-transport/src/connection/mod.rs:2198-2218](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/neqo-transport/src/connection/mod.rs#L2198) | `Passive peer migration handling` | Server-side peer migration handling can ensure a permanent path, update path state, and emit migration events. | Neqo covers passive migration/rebinding handling as well as client-initiated migration. |
| `neqo-path-probe-and-primary-selection` | [neqo-transport/src/path.rs:200-220](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/neqo-transport/src/path.rs#L200) | `Probe before path promotion` | The path manager starts ECN validation, promotes a path immediately only when forced or already valid, otherwise records it as a migration target and probes it. | Neqo implements the path-validation gate expected by QUIC migration. |
| `neqo-path-response-validation` | [neqo-transport/src/path.rs:792-801](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/neqo-transport/src/path.rs#L792) | `PATH_RESPONSE validation` | A matching PATH_RESPONSE marks the path valid and can trigger the next probe stage for full-MTU probing. | The implementation has explicit validation state for a candidate migrated path. |
| `neqo-qlog-transport-parameters` | [neqo-transport/src/qlog.rs:59-99](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/neqo-transport/src/qlog.rs#L59) | `qlog for migration-related transport parameters` | Neqo qlog output includes disable_active_migration and preferred_address transport parameter fields. | Neqo has observability hooks for migration-relevant policy/configuration evidence. |
| `neqo-rebinding-tests` | [neqo-transport/src/connection/tests/migration.rs:320-339](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/neqo-transport/src/connection/tests/migration.rs#L320) | `NAT rebinding tests` | The migration tests include port rebinding and address+port rebinding, with and without zero-length connection IDs. | Neqo has focused tests for rebinding cases that matter in mobility-like scenarios. |
| `neqo-immediate-migration-test` | [neqo-transport/src/connection/tests/migration.rs:428-446](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/neqo-transport/src/connection/tests/migration.rs#L428) | `Immediate active migration test` | The immediate migration test calls migrate(..., true, ...) and expects a PathMigrated event and PATH_CHALLENGE. | Neqo tests active migration at the transport layer. |
| `neqo-graceful-migration-test` | [neqo-transport/src/connection/tests/migration.rs:638-720](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/neqo-transport/src/connection/tests/migration.rs#L638) | `Graceful migration test` | The graceful migration test probes the new path, keeps data on the old path until validation, switches after PATH_RESPONSE, and confirms server traffic on the new path. | Neqo's test suite covers more than API presence; it checks path validation and data continuity across the migration sequence. |
| `neqo-preferred-address-test` | [neqo-transport/src/connection/tests/migration.rs:741-830](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/neqo-transport/src/connection/tests/migration.rs#L741) | `Preferred address test` | The preferred-address test probes the server's preferred address after handshake, keeps data on the original path during probing, then sends data on the preferred path. | Neqo exercises the preferred-address migration path separately from generic rebinding. |
| `neqo-disable-migration-test` | [neqo-transport/src/connection/tests/migration.rs:1011-1020](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/neqo-transport/src/connection/tests/migration.rs#L1011) | `disable_active_migration test` | The migration_disabled test expects InvalidMigration when the peer disables migration. | Neqo tests the policy boundary where a peer forbids active migration. |
| `neqo-pmtud-migration-test` | [neqo-transport/src/connection/tests/pmtud.rs:120-150](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/neqo-transport/src/connection/tests/pmtud.rs#L120) | `PMTUD after migration` | The PMTUD test documents VPN-like migration to a lower MTU path and checks PMTUD behavior. | Neqo covers post-migration path property changes, not just tuple switching. |
| `neqo-ecn-migration-test` | [neqo-transport/src/connection/tests/ecn.rs:436-456](https://github.com/mozilla/neqo/blob/3ba227d37f46a5684e984ead831b73344d9fec63/neqo-transport/src/connection/tests/ecn.rs#L436) | `ECN after migration` | The ECN migration tests vary path marking behavior and assert migrated/non-migrated outcomes. | Neqo tests migration interaction with path-quality transport state. |
| `neqo-local-rerun-summary` | [docs/results/implementation-rerun-results-20260630.md:37-40](https://github.com/manNomi/quic-connect-migration/blob/docs/quinn-neqo-rerun-20260630/docs/results/implementation-rerun-results-20260630.md) | `Fresh local rerun result` | The research rerun records cargo test -p neqo-transport migration at commit 3ba227d37f46a5684e984ead831b73344d9fec63 with 53 passed and 0 failed. | The study has local test-suite evidence for Neqo, but this is not a Firefox browser handover row. |

## Reporting Boundary

- Safe claim: Neqo has explicit migration API/source support, rebinding handling, preferred-address coverage, qlog transport-parameter observability, and a fresh local migration test rerun.
- Unsafe claim: Firefox desktop or mobile has been shown by this study to preserve a single HTTP/3 browser session across Wi-Fi/cellular or interface handover.
- Next non-iPhone gate: Install/run Firefox desktop against a controlled H3 origin or local neqo-server, capture Firefox/Necko logging plus server qlog/tuple evidence, and require target session attribution, client path change, server path validation, and workload completion before claiming Firefox CM.

## Paper Interpretation

1. Neqo should remain in the high-value implementation survey because it is the Mozilla/Firefox-adjacent QUIC stack.
2. The fresh Neqo rerun and source audit are enough to say CM is implemented and tested in this stack.
3. They are not enough to say Firefox browser requests survive a live network handover; that requires Firefox runtime logs and server-side path evidence.
4. This distinction helps the paper answer why CM is underused: implementation support exists, but browser integration, policy, observability, and workload evidence still form separate gates.
