# MsQuic Rebind Path Validation Packet

Generated: `2026-07-01`

This public-safe packet turns MsQuic selected user-mode rebind/path-validation tests into a reproducible gate. It does not claim browser, HTTP/3 application, CDN/LB, or production deployment continuity.

## Summary

| field | value |
| --- | --- |
| implementation | `MsQuic` |
| source commit | `51d449b7d2deb553d6503591f72a8e62d1071054` |
| local clone observed | `True` |
| local clone commit | `51d449b7d2deb553d6503591f72a8e62d1071054` |
| local clone matches audit commit | `yes` |
| runner exists | `True` |
| runner result env exists | `True` |
| runtime trial status | `ready_or_passed` |
| runtime trial reason | `runner_validation_ok` |
| can claim selected runtime-test PASS | `yes` |
| public safety scan | `ok` |

## Runner

| field | value |
| --- | --- |
| path | `harness/scripts/run-msquic-rebind-pathvalidation-demo.sh` |
| result env | `harness/results/msquic-rebind-pathvalidation-local-20260701/results/result.env` |
| validation | `ok` |
| blocked or failed reason | `none` |
| msquictest list exit | `0` |
| msquictest v4 exit | `0` |
| msquictest v6 exit | `0` |
| listed rebind/path-validation count | `8` |
| v4 ok count | `4` |
| v6 ok count | `4` |
| total ok count | `8` |
| passed summary count | `2` |
| failed marker count | `0` |

## Evidence Table

| id | source | topic | observation | implication |
| --- | --- | --- | --- | --- |
| `migration-setting` | [docs/Settings.md:55](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/docs/Settings.md#L55) | `Client migration setting` | MsQuic documents MigrationEnabled as client migration support for IP address and tuple changes with a cooperative load balancer or no load balancer. | MsQuic treats migration as a configurable deployment-sensitive feature rather than unconditional application continuity. |
| `local-address-param-doc` | [docs/Settings.md:183](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/docs/Settings.md#L183) | `Local address control parameter` | QUIC_PARAM_CONN_LOCAL_ADDRESS is settable on clients before start or after handshake confirmation. | MsQuic exposes policy-constrained local-address control, unlike quic-go's AddPath/Probe/Switch shape. |
| `client-migration-deployment-doc` | [docs/Deployment.md:107](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/docs/Deployment.md#L107) | `Deployment boundary` | The deployment guide separates client migration from load-balancer routing requirements. | A selected local MsQuic rebind PASS must not be promoted to generic LB/CDN deployment success. |
| `rebind-port-gtest` | [src/test/bin/quic_gtest.cpp:1868](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/test/bin/quic_gtest.cpp#L1868) | `NAT port rebind test registration` | The RebindPort gtest invokes QuicTestNatPortRebind_NoPadding for user-mode tests. | The local runner exercises MsQuic's selected NAT port rebinding test path. |
| `rebind-addr-gtest` | [src/test/bin/quic_gtest.cpp:1924](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/test/bin/quic_gtest.cpp#L1924) | `NAT address rebind test registration` | The RebindAddr gtest invokes QuicTestNatAddrRebind_NoPadding for user-mode tests. | The local runner exercises MsQuic's selected NAT address rebinding test path. |
| `path-validation-gtests` | [src/test/bin/quic_gtest.cpp:1973](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/test/bin/quic_gtest.cpp#L1973) | `Path validation selected tests` | PathValidationTimeout and PathValidationLastPathClose are registered as WithFamilyArgs tests. | The selected runner ties NAT rebinding evidence to path-validation failure handling. |
| `test-local-address-helper` | [src/test/lib/TestConnection.cpp:363](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/test/lib/TestConnection.cpp#L363) | `Test local-address helper` | TestConnection::SetLocalAddr sets QUIC_PARAM_CONN_LOCAL_ADDRESS with retry handling after handshake confirmation. | The tests use the documented local-address control surface rather than only parser-level checks. |
| `core-local-address-param` | [src/core/connection.c:6380](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/core/connection.c#L6380) | `Core local-address parameter handling` | The core connection parameter handler validates QUIC_PARAM_CONN_LOCAL_ADDRESS and rejects invalid states such as server-side use or pre-confirmation changes. | MsQuic local-address control is real but policy-constrained. |
| `disable-active-migration-transport-param` | [src/core/connection.c:2412](https://github.com/microsoft/msquic/blob/51d449b7d2deb553d6503591f72a8e62d1071054/src/core/connection.c#L2412) | `Disable active migration transport parameter` | Server transport parameters include disable_active_migration when MigrationEnabled is false. | MsQuic migration behavior is explicitly controlled by policy and settings. |

## Claim Boundary

- Safe claim: MsQuic has source/API evidence plus a local user-mode selected rebind/path-validation PASS: v4 and v6 RebindPort, RebindAddr, PathValidationTimeout, and PathValidationLastPathClose all passed under msquictest.
- Unsafe claim: MsQuic browser handover, HTTP/3 application continuity, AWS NLB/CloudFront deployment success, or quic-go-equivalent AddPath/Probe/Switch control.
- Next gap: Use this as selected MsQuic runtime-test evidence; build a separate application payload or live LB experiment only if reviewers require deployment/application continuity evidence.

## Interpretation

1. MsQuic should move above generic test-suite-only wording for the selected rebind/path-validation subset because the dedicated runner records v4 and v6 user-mode test PASS.
2. This strengthens the API-shape explanation: MsQuic exposes a policy-constrained local-address parameter and deployment migration setting, not a quic-go-style AddPath/Probe/Switch controller.
3. Browser, HTTP/3 application, CDN/LB, and production continuity remain separate gates.
