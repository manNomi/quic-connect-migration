# Final Browser Handover Readiness

Generated: `2026-06-30`

## Summary

| check | value |
| --- | --- |
| Chrome protocol ready | `no` |
| Safari protocol ready | `no` |
| Android Chrome protocol ready | `no` |
| final trial completion | `3/6` |
| can finish goal now | `no` |

## Gates

| gate | value |
| --- | --- |
| config present | `yes` |
| public origin URL | `<configured>` |
| baseline summary ready | `no` |
| baseline status | `missing` |
| network-change command present | `no` |
| Android network-change command present | `no` |
| active IPv4 interfaces | `en0(192.168.0.212)` |
| secondary path ready | `no` |
| latent iPhone USB candidate ready | `no` |
| allow latent secondary path | `no` |
| desktop path-change ready | `no` |
| desktop path-change mode | `not-ready` |
| Android ready | `no` |
| Safari WebDriver ready | `yes` |
| disk ready | `yes` |
| disk free GiB | `14.51` |

## Blockers

- controlled public baseline summary is missing or not PASS/PASS_FEASIBILITY
- NETWORK_CHANGE_CMD is not configured
- desktop path-change trigger is not ready
- Android device is not connected over ADB
- final browser handover trial protocol is not complete

## Final Trial Blockers

- chrome-downlink-noheartbeat-active-cm: 0/3
- chrome-downlink-heartbeat-active-cm: 0/3
- p1-safari-or-android-feasibility: 0/1
