# Final Trial Acceptance Scorecard

Generated: `2026-06-26`

This scorecard is public-safe. It states which final browser handover rows can be accepted into the paper protocol, what each row must prove, and what evidence excludes a CM success claim.

## Summary

| field | value |
| --- | --- |
| final protocol complete | `no` |
| complete requirements | `3/6` |
| config source | `public template` |
| public safe | `yes` |

## Acceptance Rows

| requirement | phase | browser | matched | planned trials | paper use |
| --- | --- | --- | ---: | --- | --- |
| `chrome-controlled-public-application-h3-baseline` | baseline | Chrome | 1/1 | `controlled-public-chrome-h3-baseline-001` | baseline/control evidence available |
| `chrome-downlink-noheartbeat-active-cm` | active-network-change | Chrome | 0/3 | `controlled-public-chrome-downlink-noheartbeat-network-change-001;controlled-public-chrome-downlink-noheartbeat-network-change-002;controlled-public-chrome-downlink-noheartbeat-network-change-003` | pending; do not claim browser CM success |
| `chrome-downlink-heartbeat-active-cm` | active-network-change | Chrome | 0/3 | `controlled-public-chrome-downlink-heartbeat-network-change-001;controlled-public-chrome-downlink-heartbeat-network-change-002;controlled-public-chrome-downlink-heartbeat-network-change-003` | pending; do not claim browser CM success |
| `chrome-downlink-noheartbeat-nochange-baseline` | no-change-baseline | Chrome | 1/1 | `controlled-public-chrome-downlink-noheartbeat-nochange-001` | baseline/control evidence available |
| `chrome-downlink-heartbeat-nochange-baseline` | no-change-baseline | Chrome | 1/1 | `controlled-public-chrome-downlink-heartbeat-nochange-001` | baseline/control evidence available |
| `p1-safari-or-android-feasibility` | active-network-change | Safari or Android Chrome | 0/1 | `controlled-public-safari-downlink-network-change-001` | pending; do not claim browser CM success |

## Acceptance Rules

### `chrome-controlled-public-application-h3-baseline`

- accept when: status in PASS; trial_id contains: controlled-public, baseline; deployment contains: controlled public; task contains: browser; notes contain any: controlled_public_application_h3_confirmed, controlled_public_server_qlog_h3_confirmed
- reject CM success when: -
- required artifact roles: server result; server qlog directory; public origin readiness; classifier summary; Chrome bootstrap NetLog; Chrome second NetLog; Chrome public H3 summary

### `chrome-downlink-noheartbeat-active-cm`

- accept when: status in PASS; trial_id contains: controlled-public, network-change, chrome, downlink, noheartbeat; deployment contains: controlled public; trigger contains: active, path, change; task contains: downlink; notes contain any: possible_connection_migration
- reject CM success when: reject if notes/failure evidence contains: reconnect_or_multiple_sessions, tuple_changed_without_path_validation, no_path_change_after_trigger, multiple_quic_sessions_without_client_path_change
- required artifact roles: server result; server qlog directory; public origin readiness; classifier summary; network-change command record; client path-change summary; Chrome network-change NetLog

### `chrome-downlink-heartbeat-active-cm`

- accept when: status in PASS; trial_id contains: controlled-public, network-change, chrome, downlink, heartbeat; deployment contains: controlled public; trigger contains: active, path, change; task contains: downlink, heartbeat; notes contain any: possible_connection_migration
- reject CM success when: reject if notes/failure evidence contains: reconnect_or_multiple_sessions, tuple_changed_without_path_validation, no_path_change_after_trigger, multiple_quic_sessions_without_client_path_change
- required artifact roles: server result; server qlog directory; public origin readiness; classifier summary; network-change command record; client path-change summary; Chrome network-change NetLog

### `chrome-downlink-noheartbeat-nochange-baseline`

- accept when: status in PASS; trial_id contains: controlled-public, nochange, chrome, downlink, noheartbeat; deployment contains: controlled public; trigger contains: no network change; task contains: downlink; notes contain all: no_path_change_baseline
- reject CM success when: -
- required artifact roles: server result; server qlog directory; public origin readiness; classifier summary; Chrome bootstrap NetLog; Chrome second NetLog; Chrome public H3 summary

### `chrome-downlink-heartbeat-nochange-baseline`

- accept when: status in PASS; trial_id contains: controlled-public, nochange, chrome, downlink, heartbeat; deployment contains: controlled public; trigger contains: no network change; task contains: downlink, heartbeat; notes contain all: no_path_change_baseline
- reject CM success when: -
- required artifact roles: server result; server qlog directory; public origin readiness; classifier summary; Chrome bootstrap NetLog; Chrome second NetLog; Chrome public H3 summary

### `p1-safari-or-android-feasibility`

- accept when: status in PASS_FEASIBILITY; trial_id contains: controlled-public, network-change; trigger contains: active, path, change; notes contain all: possible_connection_migration_server_qlog_only; notes contain any: safari, android
- reject CM success when: -
- required artifact roles: server result; server qlog directory; public origin readiness; classifier summary; network-change command record; client path-change summary; Safari navigation summary
