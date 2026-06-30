# mvfst Migration Test Readiness

Generated: `2026-06-30`

This document is public-safe. It records source-relative test targets and current readiness, not raw build logs.

## Summary

| field | value |
| --- | --- |
| source commit | `d9d65a3ab3e6ffba785d6605afe6f05b8db015ec` |
| remote head | `d9d65a3ab3e6ffba785d6605afe6f05b8db015ec` |
| host os | `Darwin` |
| disk free GiB | `17.84` |
| disk threshold GiB | `30.0` |
| validation | `blocked` |
| blocked reasons | `['disk_below_threshold', 'buck2_missing', 'focused_files_not_directly_exposed_by_current_cmake']` |
| total test cases observed | `106` |
| high-value migration/path cases observed | `78` |

## Readiness

| check | value |
| --- | --- |
| `source_ready` | `True` |
| `getdeps_ready` | `True` |
| `python3_ready` | `True` |
| `cmake_ready` | `True` |
| `ninja_ready` | `True` |
| `buck2_ready` | `False` |
| `disk_ready` | `False` |
| `buck_targets_ready` | `True` |
| `cmake_direct_targets_ready` | `False` |
| `can_run_focused_buck_now` | `False` |
| `can_run_getdeps_now` | `False` |
| `validation` | `blocked` |
| `blocked_reasons` | `['disk_below_threshold', 'buck2_missing', 'focused_files_not_directly_exposed_by_current_cmake']` |

## Focused Targets

| kind | source file | BUCK target | CMake direct file ref | tests | high-value tests |
| --- | --- | --- | --- | ---: | ---: |
| path-manager | `quic/state/test/QuicPathManagerTest.cpp` | `quic/state/test:quic_path_manager_test` | `False` | `55` | `27` |
| client-active-migration | `quic/client/test/QuicClientTransportLiteMigrationTest.cpp` | `quic/client/test:QuicClientTransportLiteMigrationTest` | `False` | `14` | `14` |
| server-passive-migration | `quic/server/test/QuicServerTransportMigrationTest.cpp` | `quic/server/test:QuicServerTransportMigrationTest` | `False` | `37` | `37` |

## Sample High-Value Tests

### path-manager
- `QuicPathManagerTest.GetPathByChallengeData`
- `QuicPathManagerTest.GetPathByChallengeDataNotFound`
- `QuicPathManagerTest.PrepareChallengeForSending`
- `QuicPathManagerTest.PrepareChallengeForSendingNonExistentPath`
- `QuicPathManagerTest.PrepareChallengeForSendingValidatedPath`
- `QuicPathManagerTest.OnPathResponseReceived`
- `QuicPathManagerTest.OnPathResponseReceivedStaleResponse`
- `QuicPathManagerTest.OnPathResponseClearsPendingFlag`
- `QuicPathManagerTest.OnPathResponseReceivedAfterRetransmit`
- `QuicPathManagerTest.OnPathResponseReceivedMatchesOriginalAfterRetransmit`
- `QuicPathManagerTest.GetEarliestChallengeTimeout`
- `QuicPathManagerTest.OnPathValidationTimeoutExpired`

### client-active-migration
- `QuicClientTransportLiteMigrationTest.StartPathProbeSuccessWithoutMigrating`
- `QuicClientTransportLiteMigrationTest.StartPathProbeSuccessWithMigrating`
- `QuicClientTransportLiteMigrationTest.MigrateConnectionSwitchesCurrentPath`
- `QuicClientTransportLiteMigrationTest.PathProbeTimeout`
- `QuicClientTransportLiteMigrationTest.MigrateToUnvalidatedPathThenTimeout`
- `QuicClientTransportLiteMigrationTest.CannotStartProbeWithUnboundSocket`
- `QuicClientTransportLiteMigrationTest.CannotStartProbeWithSocketAddressFamilyMismatch`
- `QuicClientTransportLiteMigrationTest.CannotStartProbeWhenPeerDisablesActiveMigration`
- `QuicClientTransportLiteMigrationTest.CannotStartProbeWithoutOneRttCipher`
- `QuicClientTransportLiteMigrationTest.CannotStartProbeWithoutSocket`
- `QuicClientTransportLiteMigrationTest.StartPathProbeAssignsConnectionId`
- `QuicClientTransportLiteMigrationTest.StartPathProbeFailsWhenNoAvailableConnectionIds`

### server-passive-migration
- `QuicServerTransportAllowMigrationTest.SendsCorrectNumberOfNewConnectionIdsBasedOnParam`
- `QuicServerTransportAllowMigrationTest.ReceiveProbeFromNewPeerAddressWithoutMigratingLongGracePeriod`
- `QuicServerTransportAllowMigrationTest.ReceiveProbeFromNewPeerAddressWithoutMigratingShortGracePeriod`
- `QuicServerTransportAllowMigrationTest.ReceiveProbeFromNewPeerAddressWithMigrating`
- `QuicServerTransportAllowMigrationTest.ReceiveReorderedDataFromChangedPeerAddress`
- `QuicServerTransportAllowMigrationTest.MigrateToNewPeerAndBackWithoutProbing`
- `QuicServerTransportAllowMigrationTest.MigrateToNewPeerRespondOnFallbackPath`
- `QuicServerTransportAllowMigrationTest.ResetPathRttPathResponse`
- `QuicServerTransportAllowMigrationTest.IgnoreInvalidPathResponse`
- `QuicServerTransportAllowMigrationTest.ReceivePathResponseFromDifferentPeerAddress`
- `QuicServerTransportAllowMigrationTest.RetiringConnIdIssuesNewIds`
- `QuicServerTransportAllowMigrationTest.RetiringInvalidConnId`

## Generated Commands

Focused BUCK targets if a suitable Buck/buck2 environment is available:

```bash
buck2 test quic/state/test:quic_path_manager_test
buck2 test quic/client/test:QuicClientTransportLiteMigrationTest
buck2 test quic/server/test:QuicServerTransportMigrationTest
```

Broad getdeps build/test fallback. This is not focused and may be expensive:

```bash
python3 build/fbcode_builder/getdeps.py --allow-system-packages --num-jobs 4 build mvfst
python3 build/fbcode_builder/getdeps.py --allow-system-packages --num-jobs 4 test mvfst
```

## Interpretation

- Supports: mvfst has focused migration/path-manager test files and BUCK targets for path-manager, client active migration, and server passive migration coverage.
- Do not claim: Do not claim local mvfst build/test success from this readiness report; it only fixes the focused target map and current blockers.
- Paper use: keep mvfst as production-relevant source/test maturity evidence until a Linux/Buck/getdeps run produces executed test results.
