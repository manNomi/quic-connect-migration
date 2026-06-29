# Terminology And Scope Boundaries

Generated: `2026-06-29`

## Why This Exists

The phrase "unstable mobile network" is too broad for this study. In networking contexts, "mobile network" often refers to cellular operator networks such as LTE/5G, while this project studies a web client moving between Wi-Fi and cellular-tethered access. The paper should therefore avoid vague wording and name the exact path-change model.

## Recommended Study Scope

Use this scope statement:

> This study evaluates workload continuity for HTTP/3 applications under controlled QUIC path-change conditions, with a final browser target of Wi-Fi-to-cellular failover through iPhone USB tethering. It separates transport-level single-session connection migration from application-level recovery such as retry, byte-range resume, buffering, and replacement-session continuity.

Korean version:

> 본 연구는 HTTP/3 애플리케이션의 작업 연속성을 QUIC path-change 조건에서 평가하며, 최종 브라우저 실험은 iPhone USB tethering을 통한 Wi-Fi-to-cellular failover를 대상으로 한다. Transport 수준의 single-session connection migration과 retry, byte-range resume, buffering, replacement-session continuity 같은 application-level recovery를 분리해 해석한다.

## Terms To Use

| term | use in this paper | reason |
| --- | --- | --- |
| `path change` | Generic client address/interface/route change | Neutral term before proving QUIC migration |
| `Wi-Fi-to-cellular failover` | The intended real browser transition | Names the access change without implying cellular-core handover |
| `latent iPhone USB failover` | Current Mac+iPhone trigger mode | iPhone USB is inactive while Wi-Fi is active, then becomes default after Wi-Fi loss |
| `wireless access transition` | Broader Wi-Fi/cellular framing | Safer than "mobile network" when Wi-Fi is included |
| `client path-change trigger` | Scripted action such as `networksetup -setairportpower en0 off` | Separates command execution from proof of actual path change |
| `single-session browser CM` | Browser keeps the original target QUIC session across path change | Requires full evidence chain, not just task completion |
| `application-level recovery` | Retry, Range resume, buffering, reconnect, Service Worker or UI recovery | Explains user-visible continuity without transport CM |
| `workload continuity` | Whether a page/upload/download/poll/media task completes without manual refresh | User-facing outcome, separate from transport mechanism |
| `QoE continuity` | Startup delay, rebuffer events, completion, recovery latency | Needed for streaming workloads |
| `transient return-path loss` | Local proxy drops server-to-client packets for a bounded window | Exact term for local outage controls |
| `local UDP rebinding control` | Local proxy changes upstream socket/tuple | Useful control, not public Wi-Fi/cellular handover evidence |

## Terms To Avoid Or Qualify

| phrase | problem | replacement |
| --- | --- | --- |
| `unstable mobile network` | Too vague; may imply cellular operator network only | `Wi-Fi-to-cellular failover`, `wireless access transition`, or measured impairment |
| `mobile network environment` | In Korean, can exclude Wi-Fi and imply LTE/5G network only | `무선 접속 전환 환경`, `Wi-Fi-to-cellular failover 환경` |
| `handover` / `handoff` | Can imply cellular network-managed base-station handover | Use only when discussing related work or explicitly define as access transition |
| `degraded network` | Needs measured degradation such as RTT/loss/bandwidth | Specify `loss`, `RTT`, `throughput`, or `return-path outage` |
| `fluctuating network` | Needs time-varying metric evidence | Specify the metric and time window |
| `unreliable network` | Informal unless tied to drop/failure model | Use `intermittent connectivity` or measured failure mode |
| `Connection Migration succeeded` | Too strong unless session continuity and path validation are proven | `task recovered`, `replacement-session continuity`, or `single-session CM evidence` |
| `HTTP/3 supports CM` | H3 availability does not imply browser/runtime migration | `HTTP/3 application baseline passed`; then separately test CM |

## Evidence Boundary For This Study

Use this hierarchy when writing results:

1. `Application HTTP/3 baseline`: target request actually used HTTP/3.
2. `Client path changed`: route/interface/public path changed after the trigger.
3. `Server tuple evidence`: server saw peer address/port change for the relevant connection or workload.
4. `qlog/path validation`: PATH_CHALLENGE/PATH_RESPONSE or equivalent migration evidence exists.
5. `Browser session continuity`: Chrome/Safari evidence does not show replacement target QUIC sessions.
6. `Task continuity`: workload completed without manual refresh or user reattempt.

Only when all six align should the paper call a row browser single-session QUIC Connection Migration success.

## Recommended Title Direction

Korean:

> Wi-Fi-to-Cellular Failover 환경에서 HTTP/3/QUIC Connection Migration 성숙도와 웹 작업 연속성 평가

English:

> Evaluating HTTP/3/QUIC Connection Migration Maturity and Web Task Continuity under Wi-Fi-to-Cellular Failover

If the final public browser rows remain incomplete, use a more conservative title:

Korean:

> HTTP/3/QUIC Connection Migration의 구현 성숙도와 웹 작업 연속성: Evidence Chain 및 Workload-Sensitive Recovery 분석

English:

> QUIC Connection Migration Maturity and Web Task Continuity: An Evidence-Chain and Workload-Sensitive Recovery Study

## Current Experiment Label

Current real-path trigger label:

`latent Wi-Fi-loss-to-iPhone-USB cellular failover`

Use this label in results until a simultaneous active secondary path or Android cellular cutover is measured.

## Source Anchors

- RFC 9000: normative QUIC connection migration and path validation semantics.
- RFC 9114: HTTP/3 endpoint discovery and HTTP/3-over-QUIC mapping.
- IETF QUIC multipath draft: simultaneous multipath is distinct from RFC 9000 single-path migration.
- `data/literature-review-tracker.csv`: related work entries for mQUIC, QUIC CM in the Wild, EnCoR, Chromium/Cronet migration policy, and operational/deployment friction.
- `docs/results/paper-claim-readiness-audit-20260629.md`: current claim-level readiness and boundaries.
