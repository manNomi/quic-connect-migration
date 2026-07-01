# Controlled Public Chrome Artifact Classifier Contract

Generated: `2026-07-01`

This public-safe contract defines how future controlled-public Chrome HTTP/3 workload artifacts must be interpreted before they are used as paper evidence.

## Summary

| field | value |
| --- | --- |
| source classifier | `tools/classify_controlled_public_h3_network_change.py` |
| source trial packet | `docs/results/noniphone-public-workload-trial-packet-20260701.md` |
| source bridge synthesis | `docs/results/controlled-public-chrome-bridge-synthesis-20260701.md` |
| paper use | Run the source classifier on each future controlled-public Chrome row, then use this contract to decide whether the row is baseline evidence, strong single-session CM evidence, task recovery, or a negative control. |

## Baseline H3 Gates

| gate | artifact source | accept when | why |
| --- | --- | --- | --- |
| `public_origin_https_ok` | `public-origin-readiness.json` | HTTPS reachability is true and the target origin is controlled by the experiment. | A browser CM row is meaningless if the public origin itself is not reachable. |
| `public_origin_alt_svc_h3` | `public-origin-readiness.json` | Alt-Svc advertises h3 for the same WebPKI origin. | Chrome must be offered an ordinary HTTP/3 route without forced local-only overrides. |
| `server_application_h3_confirmed` | `server.json + server qlog` | Server request log and qlog show application HTTP/3 for the target workload. | H3 discovery alone is not enough; the application request must actually use HTTP/3. |
| `chrome_target_quic_session_observed` | `Chrome NetLog` | Chrome NetLog contains target-origin QUIC session or application QUIC job evidence. | Server-side H3 should be paired with browser-side attribution when Chrome is the client. |
| `expected_workload_requests_reached` | `server.json` | Expected workload request count is reached for the selected route. | A partial request sequence should not be promoted to workload continuity evidence. |

## Active Strong CM Gates

| gate | artifact source | accept when | why |
| --- | --- | --- | --- |
| `application_completion_metric_true` | `DOM dump / application-summary` | The workload-specific completion metric is true. | Connection continuity claims must not ignore whether the user-visible task completed. |
| `network_change_command_executed` | `network-change.json` | The non-iPhone network-change command is present and exits 0 or an explicitly accepted no-exit condition. | No-change rows are controls, not active migration trials. |
| `client_active_path_changed` | `client-path-change-summary.json` | Before/after route snapshots classify an active client path change. | Server tuple movement alone can be misleading without client-side path evidence. |
| `server_target_h3_tuple_changed` | `server.json` | Target H3 remote tuple count is greater than one for the workload. | A single observed tuple cannot prove path migration at the server endpoint. |
| `server_qlog_path_validation` | `server qlog` | PATH_CHALLENGE and/or PATH_RESPONSE evidence is present for the active row. | Tuple changes without QUIC path validation are not enough for CM. |
| `chrome_single_target_quic_session` | `Chrome NetLog` | Target-origin Chrome QUIC session count is exactly one. | Multiple target sessions indicate reconnect/session churn rather than single-session CM. |

## Result Classes

| class | claim strength | accept when | safe claim | do not claim |
| --- | --- | --- | --- | --- |
| `public_h3_baseline_positive` | `baseline_only` | baseline_h3 gates pass and no active network-change command is part of the row. | The controlled public origin can serve the selected Chrome workload over HTTP/3. | Do not claim Connection Migration from a no-change or baseline row. |
| `strong_single_session_cm_positive` | `browser_deployment_positive` | All active_strong_cm gates pass in the same row. | For this controlled public Chrome workload, task completion coincided with client path change, server tuple change, qlog path validation, and a single Chrome target QUIC session. | Do not generalize to mobile Wi-Fi/LTE, other browsers, CDNs, or all workloads. |
| `application_recovery_or_reconnect` | `task_recovery_not_cm` | Application completion is true but Chrome target sessions are greater than one, retry is used, or qlog path validation is absent. | The application task recovered or completed under disruption. | Do not describe this as single-session QUIC Connection Migration. |
| `negative_control_record` | `gap_or_negative_control` | The row maps to a PASS_NEGATIVE_CONTROL classification from the source classifier. | The row documents a missing gate or conservative failure mode. | Do not count it as public browser CM success. |
| `not_claimable` | `not_claimable` | The row lacks the H3 precondition, server artifact, or workload completion evidence needed for interpretation. | No paper result claim should be made from this row. | Do not use incomplete infrastructure rows as CM evidence. |

## Negative-Control Classes To Preserve

`controlled_public_network_change_not_executed`, `path_snapshot_missing`, `no_client_active_path_change_observed`, `application_task_incomplete_without_quic_path_validation`, `application_task_incomplete_despite_quic_path_validation`, `application_task_failed_without_quic_path_validation`, `application_task_failed_despite_quic_path_validation`, `tuple_changed_without_path_validation`, `reconnect_or_multiple_sessions`, `path_validation_without_observed_tuple_change`, `application_task_succeeded_without_observed_quic_migration`, `no_path_change_after_trigger`, `controlled_public_network_change_inconclusive`

## Workload Rules

| workload | primary use | strong CM extra requirement | fallback interpretation |
| --- | --- | --- | --- |
| large byte-range download | First active public workload because byte accounting and completion are crisp. | Range complete, expected byte count reached, no application retry, and one Chrome target QUIC session. | If range completes with multiple sessions or no qlog path validation, report recovery/reconnect rather than CM. |
| large upload | Second active public workload because it tests client-sending continuity. | Upload complete, received bytes match intended payload, and packet/path evidence is not inferred from request tuple alone. | If upload completes but request-level tuple stays one, use qlog/NetLog/proxy evidence before making any path claim. |
| buffered video playback | QoE workload that can hide disruption behind startup buffer or rebuffering. | Playback complete plus startup delay, rebuffer count, target session count, tuple change, and qlog path validation. | Playback completion alone is QoE/recovery evidence, not CM. |
| music-like segment | Streaming-like boundary workload that separates retry recovery from transport continuity. | Segment completion without retry/reconnect and with all active strong CM gates in one row. | Retry-based segment completion should be framed as application recovery. |

## Interpretation

1. No-change and baseline rows are infrastructure controls, not CM success rows.
2. Application completion alone is insufficient because retry, reconnect, and multiple Chrome QUIC sessions can also complete a task.
3. A strong public Chrome CM row must carry the full single-row evidence chain: task completion, client active path change, target H3 tuple change, qlog path validation, and one Chrome target QUIC session.
4. Streaming rows must include startup delay, rebuffer count, retry count, completion, tuple/path evidence, and Chrome session count.
