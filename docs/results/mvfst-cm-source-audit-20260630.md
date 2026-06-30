# mvfst Connection Migration Source Audit

작성일: `2026-06-30`

## 1. 목적

mvfst는 Meta/Facebook 계열의 C++ QUIC client/server implementation으로 production relevance가 높다. 다만 이번 연구 환경에서는 full build/test까지 실행하지 않았으므로, 이 문서는 `fresh rerun PASS`가 아니라 `source/test audit`로 분류한다.

목표는 다음이다.

> mvfst를 "source inspected"로만 남기더라도, Connection Migration 관련 핵심 파일, 상태 기계, 테스트 coverage 후보를 논문 appendix에서 검증 가능한 형태로 고정한다.

## 2. 기준 소스

| 항목 | 값 |
| --- | --- |
| repository | [facebook/mvfst](https://github.com/facebook/mvfst) |
| inspected commit | `25da134df2201e78903aa5f7eb6be189e2c11dc3` |
| commit date | `2026-06-29T09:31:49-07:00` |
| local clone | `/private/tmp/quic-cm-scan-repos/mvfst` |
| claim strength | source/test audit, not local runtime PASS |

2026-06-30 추가 readiness:

> `tools/check_mvfst_migration_test_readiness.py`로 mvfst remote HEAD `d9d65a3ab3e6ffba785d6605afe6f05b8db015ec`를 다시 확인했다. focused migration/path test file 3개는 최신 HEAD에서도 존재하고, BUCK target 3개가 확인됐다. 총 106개 test case 중 78개가 path/migration high-value case로 분류됐다. 다만 현재 로컬은 `disk_below_threshold`, `buck2_missing`, `focused_files_not_directly_exposed_by_current_cmake` 때문에 build/test 실행이 아니라 readiness-blocked evidence로만 분류한다.

검수 명령:

```bash
git -C /private/tmp/quic-cm-scan-repos/mvfst rev-parse HEAD
git -C /private/tmp/quic-cm-scan-repos/mvfst ls-remote origin HEAD

rg -n "migration|migrat|PATH_CHALLENGE|PATH_RESPONSE|PathChallenge|PathResponse|path validation|PathValidation|rebinding|PathManager" \
  /private/tmp/quic-cm-scan-repos/mvfst/quic

python3 - <<'PY'
from pathlib import Path
for f in [
    "/private/tmp/quic-cm-scan-repos/mvfst/quic/state/test/QuicPathManagerTest.cpp",
    "/private/tmp/quic-cm-scan-repos/mvfst/quic/client/test/QuicClientTransportLiteMigrationTest.cpp",
    "/private/tmp/quic-cm-scan-repos/mvfst/quic/server/test/QuicServerTransportMigrationTest.cpp",
]:
    print(Path(f).name)
    for i, line in enumerate(Path(f).read_text(errors="ignore").splitlines(), 1):
        if line.strip().startswith(("TEST_F(", "TEST_P(", "TEST(")):
            print(i, line.strip())
PY
```

## 3. 핵심 source evidence

| 파일 | 링크 | 확인 내용 | 해석 |
| --- | --- | --- | --- |
| `quic/state/QuicPathManager.h` | [source](https://github.com/facebook/mvfst/blob/25da134df2201e78903aa5f7eb6be189e2c11dc3/quic/state/QuicPathManager.h#L117-L123) | path probing과 connection migration 기능을 관리한다고 명시 | migration 전용 path manager 존재 |
| `quic/state/QuicPathManager.cpp` | [source](https://github.com/facebook/mvfst/blob/25da134df2201e78903aa5f7eb6be189e2c11dc3/quic/state/QuicPathManager.cpp#L165-L228) | `PATH_CHALLENGE` 생성, validation timeout scheduling | path validation 송신 측 상태 관리 |
| `quic/state/QuicPathManager.cpp` | [source](https://github.com/facebook/mvfst/blob/25da134df2201e78903aa5f7eb6be189e2c11dc3/quic/state/QuicPathManager.cpp#L254-L315) | `PATH_RESPONSE` 수신 시 path validated 처리, RTT sample 계산, qlog event | path validation 성공 처리 |
| `quic/state/QuicPathManager.cpp` | [source](https://github.com/facebook/mvfst/blob/25da134df2201e78903aa5f7eb6be189e2c11dc3/quic/state/QuicPathManager.cpp#L330-L358) | timeout 시 path `NotValid`, qlog failure, callback 호출 | validation failure 처리 |
| `quic/state/QuicPathManager.cpp` | [source](https://github.com/facebook/mvfst/blob/25da134df2201e78903aa5f7eb6be189e2c11dc3/quic/state/QuicPathManager.cpp#L467-L500) | current path switch와 destination CID cache | migration 시 active path 교체 |
| `quic/client/QuicClientTransportLite.cpp` | [source](https://github.com/facebook/mvfst/blob/25da134df2201e78903aa5f7eb6be189e2c11dc3/quic/client/QuicClientTransportLite.cpp#L1972-L2064) | active migration 가능 여부 확인, probe socket/path 추가, path challenge scheduling, CID 할당 | client-side active path probe API 흐름 |
| `quic/client/QuicClientTransportLite.cpp` | [source](https://github.com/facebook/mvfst/blob/25da134df2201e78903aa5f7eb6be189e2c11dc3/quic/client/QuicClientTransportLite.cpp#L2071-L2137) | `migrateConnection`에서 current path switch, congestion/RTT reset, qlog migration update | client-side active migration execution |
| `quic/server/state/ServerStateMachine.cpp` | [source](https://github.com/facebook/mvfst/blob/25da134df2201e78903aa5f7eb6be189e2c11dc3/quic/server/state/ServerStateMachine.cpp#L812-L875) | server-side `onConnectionMigration`, fallback path, NAT rebinding 판단, path switch | server passive migration state machine |
| `quic/server/QuicServerTransport.cpp` | [source](https://github.com/facebook/mvfst/blob/25da134df2201e78903aa5f7eb6be189e2c11dc3/quic/server/QuicServerTransport.cpp#L1569-L1700) | path validation result를 valid/current, valid/probe, invalid/current, invalid/probe로 분기 | validation 성공/실패 복구 정책 |
| `quic/logging/QLoggerTypes.cpp` | [source](https://github.com/facebook/mvfst/blob/25da134df2201e78903aa5f7eb6be189e2c11dc3/quic/logging/QLoggerTypes.cpp#L1232-L1290) | `connection_migration`, `PathValidation` qlog event type mapping | observability 근거 |

## 4. 테스트 evidence 후보

실행하지는 않았지만, source tree에는 migration/path manager 테스트가 별도 파일로 정리되어 있다.

| 테스트 파일 | 링크 | 확인한 coverage |
| --- | --- | --- |
| `quic/state/test/QuicPathManagerTest.cpp` | [source](https://github.com/facebook/mvfst/blob/25da134df2201e78903aa5f7eb6be189e2c11dc3/quic/state/test/QuicPathManagerTest.cpp) | path add/remove, challenge generation, response matching, timeout, callback, congestion/RTT restore, destination CID assignment, path switch |
| `quic/client/test/QuicClientTransportLiteMigrationTest.cpp` | [source](https://github.com/facebook/mvfst/blob/25da134df2201e78903aa5f7eb6be189e2c11dc3/quic/client/test/QuicClientTransportLiteMigrationTest.cpp) | start path probe success/failure, migrate after probe, peer disables active migration, no CID, timeout |
| `quic/server/test/QuicServerTransportMigrationTest.cpp` | [source](https://github.com/facebook/mvfst/blob/25da134df2201e78903aa5f7eb6be189e2c11dc3/quic/server/test/QuicServerTransportMigrationTest.cpp) | server migration with/without probe, reordered packet guard, fallback path, NAT rebinding, path validation timeout, CID update, failure counter |

대표 테스트 이름:

| 범주 | 테스트명 예시 |
| --- | --- |
| Path manager primitive | `PrepareChallengeForSending`, `OnPathResponseReceived`, `OnPathValidationTimeoutExpired`, `SwitchCurrentPath_CachesOldCid_Client`, `MultiplePathsWithDifferentDestinationCids` |
| Client active migration | `StartPathProbeSuccessWithoutMigrating`, `StartPathProbeSuccessWithMigrating`, `MigrateConnectionSwitchesCurrentPath`, `CannotStartProbeWhenPeerDisablesActiveMigration`, `StartPathProbeAssignsConnectionId` |
| Server passive migration | `ReceiveProbeFromNewPeerAddressWithMigrating`, `MigrateToNewPeerAndBackWithoutProbing`, `MigrateToNewPeerRespondOnFallbackPath`, `ClientPortChangeNATRebinding`, `ClientAddressChangeNATRebinding`, `PathValidationTimeoutForCurrentPathWithFallback` |
| Failure/control | `ReceiveReorderedDataFromChangedPeerAddress`, `IgnoreInvalidPathResponse`, `ConnectionClosesAfterMaxConsecutiveMigrationFailures`, `SuccessfulMigrationDoesNotIncrementFailureCounter` |

## 5. 판정

mvfst는 source/test 구조 기준으로 Connection Migration 성숙도가 높다.

확인된 특징:

1. dedicated `QuicPathManager`가 path probing, validation, timeout, current path switch, destination CID assignment를 관리한다.
2. client transport에는 active path probe와 `migrateConnection` 흐름이 있다.
3. server state machine에는 non-active path packet 기반 passive migration, fallback path, NAT rebinding 판단, failure counter가 있다.
4. qlog/stat callback이 migration과 path validation observability를 제공한다.
5. 테스트 파일이 path manager, client migration, server migration으로 분리되어 있어 coverage 구조가 명확하다.

제한:

1. 이번 턴에는 mvfst를 local build/test로 실행하지 않았다.
2. 따라서 `fresh_rerun_20260630`으로 승격하지 않고 `source_inspected`로 유지한다.
3. 논문에서는 "large-scale implementation has mature source/test support"까지만 말하고, "our host reproduced mvfst migration tests"라고 쓰면 안 된다.

## 6. 논문용 문장

안전한 문장:

> mvfst provides a production-relevant source-level maturity signal: its dedicated path manager, client active probe/migration flow, server passive migration state machine, qlog/stat hooks, and migration-specific tests indicate that Connection Migration is a first-class implementation concern. However, in this study mvfst remains source-audited evidence rather than a locally executed positive control.

한국어 표현:

> mvfst는 dedicated path manager, client active probe/migration 흐름, server passive migration state machine, qlog/stat hook, migration 전용 테스트 파일을 갖고 있어 source-level 성숙도는 높다. 다만 이번 연구에서는 local build/test를 실행하지 않았으므로 fresh positive control이 아니라 source-audited evidence로 분류한다.

## 7. 후속 작업

가능하면 Linux 환경에서 다음 순서로 보강한다.

1. `getdeps.py` 또는 repo guide 기반으로 mvfst test build.
2. `QuicPathManagerTest`, `QuicClientTransportLiteMigrationTest`, `QuicServerTransportMigrationTest`만 선택 실행.
3. qlog/stat output 또는 gtest result를 sanitized evidence bundle로 저장.

이 보강은 iPhone 없이 가능하지만 dependency/build cost가 커서 AWS/Linux builder나 별도 긴 실행 시간이 필요하다.

추가로 생성된 focused target map은 `docs/results/mvfst-migration-test-readiness-20260630.md`와 `data/mvfst-migration-test-readiness-20260630.json`에 있다. 이 문서는 build success가 아니라, 실행해야 할 test target과 현재 blocker를 고정하는 재현성 근거다.
