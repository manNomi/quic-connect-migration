# Chrome iPhone USB Handover Evidence

Generated: `2026-06-29`

This report is public-safe. It summarizes controlled public-origin Chrome
handover trials without exposing the origin hostname, IP address, AWS resource
IDs, SSH target, certificate path, qlog contents, NetLog contents, or local
private routes.

## Purpose

Evaluate whether browser-observed HTTP/3 over QUIC preserves a downlink web
application task when the client path changes from Wi-Fi to iPhone USB tethering
on macOS.

This is not a generic QUIC transport-only test. The measured outcome is web
task continuity: whether the browser page completes the downlink workload after
the path-change trigger.

## Testbed

| field | value |
| --- | --- |
| client | `macOS Chrome headless via CDP` |
| path-change mechanism | `Wi-Fi disabled with networksetup; iPhone USB tethering as latent fallback` |
| origin | `fresh AWS EC2 direct origin` |
| server | `quic-go controlled public H3 harness` |
| TLS | `WebPKI certificate on temporary sslip.io origin` |
| protocol evidence | `Chrome NetLog + server qlog + server request log` |
| application workload | `GET /browser-downlink then streaming GET /downlink-stream` |

## Path-Change Preflight

| check | result |
| --- | --- |
| iPhone USB service configured | `yes` |
| iPhone USB hardware/interface present | `yes` |
| measured failover | `yes` |
| observed failover time | `1347 ms` |
| before default interface | `Wi-Fi` |
| after default interface | `iPhone USB` |

Interpretation: the client machine can produce a real OS-level path change from
Wi-Fi to iPhone USB, but the fallback is latent rather than simultaneous
multipath. Therefore, trial claims should say "delayed OS failover" instead of
"two active paths".

## Trial Matrix

| trial | phase | heartbeat | client path changed | Chrome H3 observed | server H3/qlog observed | qlog path validation | app success | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `controlled-public-chrome-downlink-noheartbeat-nochange-20260629-003` | no-change baseline | no | n/a | yes | yes | no | yes | `controlled_public_application_h3_confirmed` |
| `controlled-public-chrome-downlink-heartbeat-nochange-20260629-001` | no-change baseline | yes | n/a | yes | yes | no | yes | `controlled_public_application_h3_confirmed` |
| `controlled-public-chrome-downlink-noheartbeat-network-change-20260629-001` | active network-change | no | yes | yes | yes | no | no | `application_task_failed_without_quic_path_validation` |
| `controlled-public-chrome-downlink-noheartbeat-network-change-20260629-002` | active network-change | no | yes | yes | yes | no | no | `application_task_failed_without_quic_path_validation` |
| `controlled-public-chrome-downlink-noheartbeat-network-change-20260629-003` | active network-change | no | yes | yes | yes | no | no | `application_task_failed_without_quic_path_validation` |
| `controlled-public-chrome-downlink-noheartbeat-network-change-page-ready-20260629-001` | active network-change | no | yes | yes | yes | no | no | `application_task_failed_without_quic_path_validation` |
| `controlled-public-chrome-downlink-heartbeat-network-change-20260629-001` | active network-change | yes | no | yes | yes | no | no | `no_client_active_path_change_observed` |

## Key Findings

1. The fresh AWS direct origin is capable of serving browser-observed H3.
2. Both no-change baselines completed the downlink application task over H3.
3. In all three no-heartbeat active trials, the client path changed from Wi-Fi
   to iPhone USB, Chrome used H3, and the application task still failed.
4. The no-heartbeat active trials did not show server qlog path validation
   events (`PATH_CHALLENGE`/`PATH_RESPONSE`), and the target H3 server remote
   address count stayed at one in each run.
5. A page-ready no-heartbeat trial triggered the path change only after the
   browser had received downlink bytes. It still failed without server-side path
   validation evidence.
6. The heartbeat active trial failed earlier at the OS failover layer: the
   command changed interface availability, but the captured default route did
   not move to iPhone USB during the measured window.
7. These active trials are negative-control evidence, not positive CM success
   evidence.

## Repeated No-Heartbeat Active Runs

| trial | client path change | downlink bytes before failure | error elapsed | target H3 remote address count | qlog path validation | application success |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `001` | `client_active_path_changed` | 13143 | 17023 ms | 1 | no | no |
| `002` | `client_active_path_changed` | 13143 | 16044 ms | 1 | no | no |
| `003` | `client_active_path_changed` | 13143 | 17019 ms | 1 | no | no |

The repeated pattern strengthens the negative finding: the active path-change
trigger is not merely failing to fire, and the failure is not a one-off Chrome
run artifact. The browser reaches the H3 downlink workload, the OS path changes,
and the task fails without server-side path validation evidence.

## Page-Ready Trigger Check

The first three active trials used a fixed time offset after Chrome navigation
started. To reduce the chance that the path cut happened before the application
stream was active, an additional trial used this CDP ready expression:

```text
Number(document.body.dataset.downlinkBytes || "0") > 0
```

| field | value |
| --- | --- |
| trial | `controlled-public-chrome-downlink-noheartbeat-network-change-page-ready-20260629-001` |
| ready expression matched | `yes` |
| ready attempts | `1` |
| trigger mode | `page-ready` |
| client path change | `client_active_path_changed` |
| downlink bytes before failure | `17524` |
| application success | `no` |
| qlog path validation | `no` |
| classification | `application_task_failed_without_quic_path_validation` |

This strengthens the timing boundary: the negative result is not explained only
by cutting the path before the browser began receiving `/downlink-stream`.

## Interpretation

The current evidence supports a conservative claim:

> In this macOS Chrome + quic-go direct-origin testbed, HTTP/3 availability and
> successful no-change H3 operation did not imply web-task continuity under a
> Wi-Fi to iPhone USB path-change trigger.

The strongest active evidence is the no-heartbeat repetition set, because each
run proves a client path change occurred. All three runs still ended with a
downlink application failure and no server-side QUIC path validation evidence.
This suggests the experiment is currently observing browser/session breakage or
path-loss behavior rather than successful QUIC connection migration.

## Claim Boundary

Do not claim that Chrome Connection Migration succeeded in these trials. The
active rows are useful because they show the gap between:

- H3 being available,
- Chrome using H3 for the target origin,
- the OS-level client path changing, and
- the web task actually surviving the path change.

The result is still valuable for the paper because it directly supports the
research motivation: connection migration maturity must be evaluated at the
implementation and application-task level, not only by checking that HTTP/3 is
enabled.

## Artifact Index

Raw artifacts are intentionally ignored by git.

| trial | local artifact directory |
| --- | --- |
| no-heartbeat no-change | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-nochange-20260629-003` |
| heartbeat no-change | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-heartbeat-nochange-20260629-001` |
| no-heartbeat active network-change 001 | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-20260629-001` |
| no-heartbeat active network-change 002 | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-20260629-002` |
| no-heartbeat active network-change 003 | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-20260629-003` |
| no-heartbeat active page-ready network-change | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-page-ready-20260629-001` |
| heartbeat active network-change | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-heartbeat-network-change-20260629-001` |

Tracked validation summaries:

- `docs/results/controlled-public-chrome-downlink-noheartbeat-nochange-20260629-003-validation.md`
- `docs/results/controlled-public-chrome-downlink-heartbeat-nochange-20260629-001-validation.md`
- `docs/results/controlled-public-chrome-downlink-noheartbeat-network-change-20260629-001-validation.md`
- `docs/results/controlled-public-chrome-downlink-noheartbeat-network-change-20260629-002-validation.md`
- `docs/results/controlled-public-chrome-downlink-noheartbeat-network-change-20260629-003-validation.md`
- `docs/results/controlled-public-chrome-downlink-noheartbeat-network-change-page-ready-20260629-001-validation.md`
- `docs/results/controlled-public-chrome-downlink-heartbeat-network-change-20260629-001-validation.md`
- `docs/results/iphone-usb-failover-measurement-20260629.md`
- `docs/results/active-path-change-command-candidates-20260629.md`

## Next Research Actions

1. Run the same workload in Safari and Android Chrome, because browser network
   stack policy may dominate the outcome.
2. Add retry/resume workloads for media segments, range download, and upload to
   test whether application-level recovery can compensate when transport-level
   migration is not observed.
3. Package the repeated negative-control evidence into the paper's evaluation
   section as "H3 availability is insufficient for task continuity".
