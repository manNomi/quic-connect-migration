# mvfst Focused Linux Runner Audit

Generated: `2026-07-01`

This public-safe audit narrows the mvfst gap from source/test-map evidence to a runnable Linux focused-test gate. It does not claim local mvfst execution success.

## Summary

| field | value |
| --- | --- |
| implementation | `mvfst` |
| source commit | `d9d65a3ab3e6ffba785d6605afe6f05b8db015ec` |
| local clone observed | `True` |
| local clone commit | `d9d65a3ab3e6ffba785d6605afe6f05b8db015ec` |
| local clone matches audit commit | `yes` |
| source evidence items | `10` |
| focused target count | `3` |
| test cases observed | `106` |
| high-value migration/path cases observed | `78` |
| readiness validation | `blocked` |
| Linux runner ready | `yes` |
| paper use | Use mvfst as production-relevant source/test maturity evidence with a packaged Linux focused-test gate; do not claim local mvfst execution until the runner produces an ok artifact. |
| interpretation | mvfst has strong migration-specific source/test structure, but the current study still lacks executed Linux Buck/getdeps results. |

## Readiness Input

| field | value |
| --- | --- |
| path | `data/mvfst-migration-test-readiness-20260630.json` |
| exists | `True` |
| source commit | `d9d65a3ab3e6ffba785d6605afe6f05b8db015ec` |
| remote head at readiness | `d9d65a3ab3e6ffba785d6605afe6f05b8db015ec` |
| validation | `blocked` |
| blocked reasons | `['disk_below_threshold', 'buck2_missing', 'focused_files_not_directly_exposed_by_current_cmake']` |

## Focused Targets

| kind | BUCK target | source file | tests | high-value tests |
| --- | --- | --- | ---: | ---: |
| path-manager | `quic/state/test:quic_path_manager_test` | `quic/state/test/QuicPathManagerTest.cpp` | `55` | `27` |
| client-active-migration | `quic/client/test:QuicClientTransportLiteMigrationTest` | `quic/client/test/QuicClientTransportLiteMigrationTest.cpp` | `14` | `14` |
| server-passive-migration | `quic/server/test:QuicServerTransportMigrationTest` | `quic/server/test/QuicServerTransportMigrationTest.cpp` | `37` | `37` |

## Linux Runner

| field | value |
| --- | --- |
| path | `harness/scripts/run-mvfst-focused-migration-tests-linux.sh` |
| exists | `True` |
| required tokens present | `True` |

## Source Evidence

| id | source | topic | observation | implication |
| --- | --- | --- | --- | --- |
| `path-manager-purpose` | [quic/state/QuicPathManager.h:117-121](https://github.com/facebook/mvfst/blob/d9d65a3ab3e6ffba785d6605afe6f05b8db015ec/quic/state/QuicPathManager.h#L117) | Dedicated path manager | QuicPathManager is documented as managing QUIC path probing and connection migration functionality. | mvfst treats migration/path probing as a first-class state-management concern. |
| `client-start-path-probe` | [quic/client/QuicClientTransportLite.cpp:1972-2064](https://github.com/facebook/mvfst/blob/d9d65a3ab3e6ffba785d6605afe6f05b8db015ec/quic/client/QuicClientTransportLite.cpp#L1972) | Client active path probe | startPathProbe checks active-migration support, handshake state, socket binding, address family, adds a path, schedules PATH_CHALLENGE, and assigns a destination CID. | mvfst has an explicit client active-probe flow that is richer than passive rebinding only. |
| `client-migrate-connection` | [quic/client/QuicClientTransportLite.cpp:2071-2137](https://github.com/facebook/mvfst/blob/d9d65a3ab3e6ffba785d6605afe6f05b8db015ec/quic/client/QuicClientTransportLite.cpp#L2071) | Client active migration | migrateConnection switches the current path, optionally resets congestion/RTT, emits qlog/stat migration hooks, and sends a ping to trigger migration. | The client transport has an active path switch execution path. |
| `server-passive-migration` | [quic/server/state/ServerStateMachine.cpp:812-878](https://github.com/facebook/mvfst/blob/d9d65a3ab3e6ffba785d6605afe6f05b8db015ec/quic/server/state/ServerStateMachine.cpp#L812) | Server passive migration state machine | Server-side migration handles validated/fallback paths, NAT rebinding detection, qlog update, congestion state, and current path switch. | mvfst has server-side passive migration logic that must be tested separately from client active migration. |
| `buck-path-manager-target` | [quic/state/test/BUCK:220-224](https://github.com/facebook/mvfst/blob/d9d65a3ab3e6ffba785d6605afe6f05b8db015ec/quic/state/test/BUCK#L220) | Focused BUCK target | BUCK defines quic_path_manager_test using QuicPathManagerTest.cpp. | The path-manager primitive tests can be addressed as a focused target on a Buck-capable host. |
| `buck-client-migration-target` | [quic/client/test/BUCK:101-105](https://github.com/facebook/mvfst/blob/d9d65a3ab3e6ffba785d6605afe6f05b8db015ec/quic/client/test/BUCK#L101) | Focused BUCK target | BUCK defines QuicClientTransportLiteMigrationTest using QuicClientTransportLiteMigrationTest.cpp. | Client active migration can be tested without running the entire mvfst suite if Buck is available. |
| `buck-server-migration-target` | [quic/server/test/BUCK:103-108](https://github.com/facebook/mvfst/blob/d9d65a3ab3e6ffba785d6605afe6f05b8db015ec/quic/server/test/BUCK#L103) | Focused BUCK target | BUCK defines QuicServerTransportMigrationTest using QuicServerTransportMigrationTest.cpp. | Server passive migration can be tested as a focused target. |
| `path-manager-test-cases` | [quic/state/test/QuicPathManagerTest.cpp:250-299](https://github.com/facebook/mvfst/blob/d9d65a3ab3e6ffba785d6605afe6f05b8db015ec/quic/state/test/QuicPathManagerTest.cpp#L250) | PATH_CHALLENGE primitive tests | Tests cover challenge lookup and challenge preparation, including nonexistent and already-validated path cases. | Focused path-manager coverage includes path-validation primitives that underpin migration. |
| `client-migration-test-cases` | [quic/client/test/QuicClientTransportLiteMigrationTest.cpp:181-287](https://github.com/facebook/mvfst/blob/d9d65a3ab3e6ffba785d6605afe6f05b8db015ec/quic/client/test/QuicClientTransportLiteMigrationTest.cpp#L181) | Client path probe and migration tests | Tests cover path probe success with and without migration, current-path switch, and probe timeout. | Focused client tests exercise the active probe/migrate boundary directly. |
| `server-nat-rebinding-test-cases` | [quic/server/test/QuicServerTransportMigrationTest.cpp:1148-1263](https://github.com/facebook/mvfst/blob/d9d65a3ab3e6ffba785d6605afe6f05b8db015ec/quic/server/test/QuicServerTransportMigrationTest.cpp#L1148) | Server NAT rebinding tests | Tests include client port-change NAT rebinding and client address-change NAT rebinding cases. | Focused server tests cover passive migration and NAT rebinding behavior. |

## Claim Boundary

- Safe claim: mvfst has dedicated path manager, client active probe/migration, server passive migration/NAT rebinding logic, focused BUCK targets, and 106 observed migration/path-related test cases in the readiness map.
- Unsafe claim: Local mvfst build/test PASS, browser handover success, production Meta deployment behavior, or equal controllability to the quic-go AddPath/Probe/Switch positive control.
- Next non-iPhone gate: Run harness/scripts/run-mvfst-focused-migration-tests-linux.sh on a Linux host with buck2 and enough disk; accept only validation=ok with all three focused BUCK targets exiting 0.

## Interpretation

1. mvfst remains `source_test_map_only` until the Linux runner produces an `ok` artifact.
2. The runner improves reproducibility by fixing the exact focused BUCK targets and getdeps fallback boundary.
3. A future PASS can strengthen the paper's cross-implementation maturity argument without involving iPhone handover.
4. This still would not prove Chrome/Safari/mobile browser continuity or managed deployment behavior.
