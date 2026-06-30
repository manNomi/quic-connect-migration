# quicly Full e2e Linux Runner Audit

Generated: `2026-06-30`

This public-safe audit narrows the remaining quicly gap from focused e2e path-migration evidence to a reproducible Linux full-e2e gate. It does not claim full quicly e2e success.

## Summary

| field | value |
| --- | --- |
| implementation | `quicly` |
| source commit | `ed83c7c7d545a01650651c9523466f561ec5d4bb` |
| local clone observed | `True` |
| local clone commit | `ed83c7c7d545a01650651c9523466f561ec5d4bb` |
| local clone matches audit commit | `yes` |
| source evidence items | `11` |
| focused e2e status | `PASS_FOCUSED_E2E` |
| focused path subtest ok | `yes` |
| focused CID sequence check ok | `yes` |
| focused full prove exit | `1` |
| focused slow-start failed | `yes` |
| Linux runner ready | `yes` |
| paper use | Use quicly as focused e2e path-migration evidence plus a fail-closed Linux full-e2e replay gate; do not claim full e2e PASS until validation=ok_full_e2e exists. |
| interpretation | quicly has concrete path validation/promotion internals and a focused e2e PASS, but the current study still lacks a clean full t/e2e.t PASS artifact. |

## Focused e2e Input

| field | value |
| --- | --- |
| input_path | `harness/results/quicly-e2e-path-migration-local-20260630/results/result.env` |
| input_exists | `True` |
| status | `PASS_FOCUSED_E2E` |
| ready | `yes` |
| prove_exit | `1` |
| path_subtest_seen | `yes` |
| path_subtest_ok | `yes` |
| cid_seq_check_ok | `yes` |
| slow_start_failed | `yes` |
| validation | `ok_path_migration` |

## Linux Full-e2e Runner

| field | value |
| --- | --- |
| path | `harness/scripts/run-quicly-full-e2e-linux.sh` |
| exists | `True` |
| required tokens present | `True` |

## Source Evidence

| id | source | topic | observation | implication |
| --- | --- | --- | --- | --- |
| `official-build-instructions` | [README.md:8-18](https://github.com/h2o/quicly/blob/ed83c7c7d545a01650651c9523466f561ec5d4bb/README.md#L8) | Build prerequisites | The README documents submodule initialization, CMake/make builds, and OpenSSL as a build dependency. | A full e2e replay needs a real build gate, not only a source scan or prebuilt local binary. |
| `official-test-instructions` | [README.md:24-42](https://github.com/h2o/quicly/blob/ed83c7c7d545a01650651c9523466f561ec5d4bb/README.md#L24) | Perl dependency and make check path | The README documents Perl dependency installation before running make check. | The runner must fail closed when Net::EmptyPort or other Perl-side prerequisites are missing. |
| `frame-primitive` | [lib/frame.c:28-30](https://github.com/h2o/quicly/blob/ed83c7c7d545a01650651c9523466f561ec5d4bb/lib/frame.c#L28) | PATH_CHALLENGE/PATH_RESPONSE frame encoding | The frame encoder selects PATH_RESPONSE or PATH_CHALLENGE and copies the 8-byte challenge payload. | quicly contains the RFC path-validation frame primitive used by the e2e migration test. |
| `path-validation-state` | [lib/quicly.c:226-240](https://github.com/h2o/quicly/blob/ed83c7c7d545a01650651c9523466f561ec5d4bb/lib/quicly.c#L226) | Path challenge/response state | Each path tracks PATH_CHALLENGE scheduling/data and PATH_RESPONSE data. | Path validation is represented in connection path state, not only in stateless frame parsing. |
| `promote-path` | [lib/quicly.c:2091-2096](https://github.com/h2o/quicly/blob/ed83c7c7d545a01650651c9523466f561ec5d4bb/lib/quicly.c#L2091) | Path promotion | promote_path logs a promote_path event and promotes a validated path index. | The e2e test's promote_path log checks are tied to a concrete path switch implementation point. |
| `path-challenge-send-logging` | [lib/quicly.c:5317-5330](https://github.com/h2o/quicly/blob/ed83c7c7d545a01650651c9523466f561ec5d4bb/lib/quicly.c#L5317) | PATH_CHALLENGE/PATH_RESPONSE send logging | Sending path challenge/response frames updates stats and emits path_challenge_send/path_response_send logs. | The implementation can expose migration evidence through stats/log events. |
| `path-response-validation` | [lib/quicly.c:6615-6630](https://github.com/h2o/quicly/blob/ed83c7c7d545a01650651c9523466f561ec5d4bb/lib/quicly.c#L6615) | PATH_RESPONSE receive validation | PATH_RESPONSE data is compared against the outstanding PATH_CHALLENGE and path validation is completed when it matches. | The e2e path-migration PASS covers the same validation mechanism that decides whether a path can be promoted. |
| `disable-active-migration-boundary` | [lib/quicly.c:7687-7689](https://github.com/h2o/quicly/blob/ed83c7c7d545a01650651c9523466f561ec5d4bb/lib/quicly.c#L7687) | disable_active_migration policy | The receive path respects the peer's disable_active_migration transport parameter after TLS handshake completion. | quicly has policy boundaries; implementation support does not mean every peer/path migration is allowed. |
| `path-migration-e2e` | [t/e2e.t:371-430](https://github.com/h2o/quicly/blob/ed83c7c7d545a01650651c9523466f561ec5d4bb/t/e2e.t#L371) | Focused path-migration e2e test | The e2e test respawns a UDP forwarder twice, checks two promote_path events, and verifies CID sequence 1 is used for the first path probe in the CID-enabled case. | The focused local PASS is migration-specific and stronger than primitive-only evidence. |
| `slow-start-boundary` | [t/e2e.t:432-546](https://github.com/h2o/quicly/blob/ed83c7c7d545a01650651c9523466f561ec5d4bb/t/e2e.t#L432) | Unrelated full e2e timing caveat | The slow-start subtest is a separate congestion-control timing test after path-migration. | The observed macOS full-e2e failure should not be reported as a path-migration failure, but it also prevents a full e2e PASS claim. |
| `stats-surface` | [include/quicly.h:785-790](https://github.com/h2o/quicly/blob/ed83c7c7d545a01650651c9523466f561ec5d4bb/include/quicly.h#L785) | Path stats | Public stats include validated paths, validation failures, migration-elicited paths, promoted paths, and closed-no-DCID paths. | quicly exposes migration/path state as measurable counters useful for implementation maturity reporting. |

## Claim Boundary

- Safe claim: quicly's focused path-migration e2e subtest passed locally, including CID sequence 1 first path probe evidence, and the repository now has a Linux full-e2e replay gate.
- Unsafe claim: quicly full t/e2e.t PASS, production H2O deployment continuity, browser handover success, or quic-go-equivalent public AddPath/Probe/Switch control.
- Next non-iPhone gate: Run harness/scripts/run-quicly-full-e2e-linux.sh on Linux; accept full-e2e promotion only when validation=ok_full_e2e with unit_test_exit=0, prove_exit=0, path_subtest_ok=yes, and cid_seq_check_ok=yes.

## Interpretation

1. quicly remains `focused_e2e_positive_with_full_e2e_gate` until the Linux runner produces `validation=ok_full_e2e`.
2. The existing focused PASS is useful because it checks path promotion and CID use for the first path probe.
3. The previous `slow-start` caveat is outside the path-migration subtest, but it still prevents a full e2e PASS claim.
4. A future Linux PASS would strengthen implementation maturity evidence without requiring iPhone handover.
