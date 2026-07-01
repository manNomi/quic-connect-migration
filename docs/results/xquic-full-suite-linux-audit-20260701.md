# XQUIC Full-suite Linux Audit

Generated: `2026-07-01`

This public-safe audit closes the XQUIC gap left by the non-quic-go execution-depth audit. It separates the already-observed NAT rebinding demo from the still-pending Linux full-suite replay.

## Summary

| field | value |
| --- | --- |
| implementation | `XQUIC` |
| source commit | `96155cffbde7f062fe45ac3f6899f47e25709d30` |
| local clone observed | `True` |
| local clone commit | `96155cffbde7f062fe45ac3f6899f47e25709d30` |
| local clone matches audit commit | `yes` |
| source evidence items | `16` |
| NAT rebinding demo status | `PASS` |
| macOS full-suite status | `blocked_by_appleclang_werror` |
| Linux replay runner ready | `yes` |
| paper use | Use XQUIC as focused NAT rebinding evidence with a packaged Linux full-suite replay gate; do not claim full-suite PASS until the Linux runner produces an ok artifact. |
| interpretation | XQUIC is not empty or purely theoretical: rebinding source callbacks and a local NAT rebinding demo exist. The remaining gap is full-suite replay on a Linux-compatible host. |

## Existing NAT Rebinding Demo

| field | value |
| --- | --- |
| input_path | `harness/results/impl-rerun-20260630T070249Z/xquic-nat-rebinding/results.env` |
| input_exists | `True` |
| status | `PASS` |
| client0_exit | `0` |
| path0_rebinding_evidence_count | `2` |
| path0_pass_count | `2` |
| client1_exit | `0` |
| path1_rebinding_evidence_count | `1` |
| path1_pass_count | `2` |

## macOS Full-suite Attempt

| field | value |
| --- | --- |
| input_path | `harness/results/impl-rerun-20260630T070249Z/logs/xquic-build-tests.log` |
| input_exists | `True` |
| status | `blocked_by_appleclang_werror` |
| compiler | `not_observed` |
| failure_file | `tests/unittest/xqc_qpack_test.c:462` |
| failure_flag | `-Werror,-Wgnu-folding-constant` |

## Linux Replay Runner

| field | value |
| --- | --- |
| path | `harness/scripts/run-xquic-full-suite-linux.sh` |
| exists | `True` |
| required tokens present | `True` |

## Source Evidence

| id | source | topic | observation | implication |
| --- | --- | --- | --- | --- |
| `official-requirements` | [README.md:71-79](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/README.md#L71) | Build and test dependencies | The README lists CMake plus BoringSSL or BabaSSL for builds, and libevent plus CUnit for test cases. | The full-suite replay must be treated as a Linux/toolchain gate, not merely a source scan. |
| `official-boringssl-quickstart` | [README.md:85-118](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/README.md#L85) | BoringSSL build path | The README gives a BoringSSL build and XQUIC Debug/testing CMake path. | The runner follows the documented BoringSSL route while keeping output public-safe. |
| `official-testcase-entrypoint` | [README.md:153-157](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/README.md#L153) | Testcase entrypoint | The README documents running testcases through scripts/xquic_test.sh. | A Linux replay packet should cover both unit tests and case tests when host prerequisites allow it. |
| `werror-cmake-flags` | [CMakeLists.txt:108-114](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/CMakeLists.txt#L108) | Compiler policy | Non-MSVC builds add -Werror to common C flags. | The observed macOS AppleClang failure is a host/toolchain strictness issue, not evidence that migration code failed at runtime. |
| `run-tests-target` | [tests/CMakeLists.txt:77-134](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/tests/CMakeLists.txt#L77) | Unit test target | The run_tests target includes transport, crypto, HTTP/3, QPACK, retry, datagram, and frame-type unit tests. | A Linux full-suite PASS would materially deepen XQUIC beyond the current focused NAT rebinding demo. |
| `official-test-script` | [scripts/xquic_test.sh:70-76](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/scripts/xquic_test.sh#L70) | Unit and case test execution | The official test script runs tests/run_tests and scripts/case_test.sh. | The replay runner mirrors this split and records separate unit/case exits and markers. |
| `peer-address-callback-api` | [include/xquic/xquic.h:324-344](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/include/xquic/xquic.h#L324) | Peer address change callbacks | Public callbacks exist for connection-level and path-level peer address changes. | XQUIC exposes passive migration/NAT rebinding observability to applications and tests. |
| `ready-to-create-path-api` | [include/xquic/xquic.h:404-413](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/include/xquic/xquic.h#L404) | Ready-to-create-path callback | A ready-to-create-path callback is triggered after receiving a new connection ID. | The demo can create an additional path when multipath prerequisites appear. |
| `callback-registration` | [include/xquic/xquic.h:684-712](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/include/xquic/xquic.h#L684) | Transport callback registration | Transport callbacks register ready-to-create-path and peer-address-change hooks. | The implementation has explicit callback surface for path and address transition evidence. |
| `nat-rebinding-validation` | [src/transport/xqc_frame.c:1730-1773](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/src/transport/xqc_frame.c#L1730) | PATH_RESPONSE and rebinding validation | PATH_RESPONSE data is checked against the prior PATH_CHALLENGE, then NAT rebinding address validation updates path or connection peer address and emits callbacks. | The source implements the critical validation/notification logic behind the observed rebinding demo. |
| `test-client-rebind-socket` | [tests/test_client.c:1518-1563](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/tests/test_client.c#L1518) | Rebinding test socket | Test cases 103/104 allocate and register a rebinding path socket. | The example client can exercise a tuple-change-like path in local runtime tests. |
| `test-client-create-path` | [tests/test_client.c:3795-3824](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/tests/test_client.c#L3795) | Client path creation callback | The client prints ready-to-create-path and creates a new path when multipath is enabled. | The existing demo output can be tied to concrete source triggers. |
| `test-client-callback-registration` | [tests/test_client.c:4600-4609](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/tests/test_client.c#L4600) | Client callback registration | The test client registers the ready-to-create-path callback in xqc_transport_callbacks_t. | The observed demo path-creation marker is not a detached log string. |
| `test-server-peer-change-callback` | [tests/test_server.c:1583-1594](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/tests/test_server.c#L1583) | Server peer-address-change logs | The test server prints connection-level and path-level peer address change notifications. | The runtime demo can observe server-side rebinding acceptance. |
| `test-server-callback-registration` | [tests/test_server.c:2438-2444](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/tests/test_server.c#L2438) | Server callback registration | The server registers connection and path peer-address-change callbacks. | Server-side log evidence is rooted in registered transport callbacks. |
| `transport-parameter-boundary` | [src/transport/xqc_transport_params.h:110-131](https://github.com/alibaba/xquic/blob/96155cffbde7f062fe45ac3f6899f47e25709d30/src/transport/xqc_transport_params.h#L110) | Preferred address and disable active migration | Transport parameters include preferred address and disable_active_migration fields. | XQUIC tracks the RFC-level migration boundary conditions in transport parameters. |

## Claim Boundary

- Safe claim: XQUIC has source-level path/address-change hooks, NAT rebinding validation logic, registered client/server demo callbacks, and a local NAT rebinding demo PASS artifact.
- Unsafe claim: XQUIC full test-suite PASS, browser/mobile handover success, or production Alibaba deployment continuity.
- Next non-iPhone gate: Run harness/scripts/run-xquic-full-suite-linux.sh on Linux with CMake, BoringSSL build prerequisites, libevent, and CUnit; accept only validation=ok with zero failed markers.

## Interpretation

1. XQUIC should remain `focused_or_partial_positive` until the Linux replay runner produces an `ok` artifact.
2. The existing NAT rebinding demo still matters because it ties callback source evidence to runtime client/server logs.
3. The macOS full-suite interruption should be reported as toolchain friction caused by strict warning policy, not as a migration failure.
4. A future paper row can promote XQUIC only after the Linux full-suite artifact passes the runner's fail-closed gates.
