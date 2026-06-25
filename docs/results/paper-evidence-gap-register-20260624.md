# Paper Evidence Gap Register

Generated: `2026-06-25`

This register is public-safe. It converts the evidence-chain rubric into paper-claim guidance and links unresolved claims to final browser handover trial requirements.

## Summary

| field | value |
| --- | --- |
| final protocol complete | `no` |
| complete requirements | `0/6` |
| incomplete requirements | `chrome-controlled-public-application-h3-baseline; chrome-downlink-noheartbeat-active-cm; chrome-downlink-heartbeat-active-cm; chrome-downlink-noheartbeat-nochange-baseline; chrome-downlink-heartbeat-nochange-baseline; p1-safari-or-android-feasibility` |

## Claim Register

| claim id | evidence item | current status | paper use now | gap | blocking requirements |
| --- | --- | --- | --- | --- | --- |
| `browser-used-http-3-for-the-application-request` | server request protocol | `observed` | scoped claim supported | needs linked final trial requirement completion | `chrome-controlled-public-application-h3-baseline` |
| `browser-used-http-3-for-the-application-request-2` | server qlog H3 evidence | `observed` | scoped claim supported | needs linked final trial requirement completion | `chrome-controlled-public-application-h3-baseline` |
| `network-change-trigger-actually-changed-the-client-path` | client route/interface snapshot | `partially_observed` | limitation or caution only | needs active secondary path proof: before/after route, interface, or public IP change | `chrome-downlink-noheartbeat-active-cm;chrome-downlink-heartbeat-active-cm;p1-safari-or-android-feasibility` |
| `connection-migration-occurred` | server tuple change | `observed_in_controls` | control evidence only | needs browser/runtime repetition before being generalized beyond controlled implementation evidence | `chrome-downlink-noheartbeat-active-cm;chrome-downlink-heartbeat-active-cm;p1-safari-or-android-feasibility` |
| `connection-migration-occurred-2` | qlog path validation | `observed_in_quic_go_controls` | control evidence only | needs browser/runtime repetition before being generalized beyond controlled implementation evidence | `chrome-downlink-noheartbeat-active-cm;chrome-downlink-heartbeat-active-cm;p1-safari-or-android-feasibility` |
| `connection-migration-occurred-3` | browser session continuity | `partially_observed` | limitation or caution only | needs browser active-path trial showing no replacement session plus path-validation evidence | `chrome-downlink-noheartbeat-active-cm;chrome-downlink-heartbeat-active-cm;p1-safari-or-android-feasibility` |
| `application-continuity-held` | task completion | `observed_in_controls` | control evidence only | needs browser/runtime repetition before being generalized beyond controlled implementation evidence | `chrome-downlink-noheartbeat-active-cm;chrome-downlink-heartbeat-active-cm;chrome-downlink-noheartbeat-nochange-baseline;chrome-downlink-heartbeat-nochange-baseline` |
| `deployment-path-supports-cm` | routing continuity | `observed` | scoped claim supported | none for scoped AWS NLB/direct-origin claim; CDN/proxy scope still separate | `-` |
| `claim-is-publishable-as-browser-cm-evidence` | combined evidence chain | `pending` | do not claim yet | needs complete final browser handover protocol rows | `chrome-controlled-public-application-h3-baseline;chrome-downlink-noheartbeat-active-cm;chrome-downlink-heartbeat-active-cm;chrome-downlink-noheartbeat-nochange-baseline;chrome-downlink-heartbeat-nochange-baseline;p1-safari-or-android-feasibility` |

## Next Actions

- `browser-used-http-3-for-the-application-request`: run and register: chrome-controlled-public-application-h3-baseline
- `browser-used-http-3-for-the-application-request-2`: run and register: chrome-controlled-public-application-h3-baseline
- `network-change-trigger-actually-changed-the-client-path`: run and register: chrome-downlink-noheartbeat-active-cm; chrome-downlink-heartbeat-active-cm; p1-safari-or-android-feasibility
- `connection-migration-occurred`: run and register: chrome-downlink-noheartbeat-active-cm; chrome-downlink-heartbeat-active-cm; p1-safari-or-android-feasibility
- `connection-migration-occurred-2`: run and register: chrome-downlink-noheartbeat-active-cm; chrome-downlink-heartbeat-active-cm; p1-safari-or-android-feasibility
- `connection-migration-occurred-3`: run and register: chrome-downlink-noheartbeat-active-cm; chrome-downlink-heartbeat-active-cm; p1-safari-or-android-feasibility
- `application-continuity-held`: run and register: chrome-downlink-noheartbeat-active-cm; chrome-downlink-heartbeat-active-cm; chrome-downlink-noheartbeat-nochange-baseline; chrome-downlink-heartbeat-nochange-baseline
- `deployment-path-supports-cm`: cite as scoped result and keep limitation wording
- `claim-is-publishable-as-browser-cm-evidence`: run and register: chrome-controlled-public-application-h3-baseline; chrome-downlink-noheartbeat-active-cm; chrome-downlink-heartbeat-active-cm; chrome-downlink-noheartbeat-nochange-baseline; chrome-downlink-heartbeat-nochange-baseline; p1-safari-or-android-feasibility
