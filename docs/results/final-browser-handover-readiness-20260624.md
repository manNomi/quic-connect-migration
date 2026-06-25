# Final Browser Handover Readiness

Generated: `2026-06-25`

## Summary

| check | value |
| --- | --- |
| Chrome protocol ready | `no` |
| Safari protocol ready | `no` |
| Android Chrome protocol ready | `no` |
| final trial completion | `0/6` |
| can finish goal now | `no` |

## Gates

| gate | value |
| --- | --- |
| config present | `no` |
| public origin URL | `-` |
| baseline summary ready | `no` |
| baseline status | `not provided` |
| network-change command present | `no` |
| Android network-change command present | `no` |
| active IPv4 interfaces | `en0(192.168.0.212)` |
| secondary path ready | `no` |
| Android ready | `no` |
| Safari WebDriver ready | `yes` |
| disk ready | `yes` |
| disk free GiB | `9.81` |

## Blockers

- controlled public config file is missing
- PUBLIC_ORIGIN_URL is not configured
- PUBLIC_ORIGIN_NETWORK_CHANGE_URL is not configured
- controlled public baseline summary is missing or not PASS/PASS_FEASIBILITY
- NETWORK_CHANGE_CMD is not configured
- desktop active secondary path is not ready
- Android device is not connected over ADB
- final browser handover trial protocol is not complete

## Final Trial Blockers

- chrome-controlled-public-application-h3-baseline: 0/1
- chrome-downlink-noheartbeat-active-cm: 0/3
- chrome-downlink-heartbeat-active-cm: 0/3
- chrome-downlink-noheartbeat-nochange-baseline: 0/1
- chrome-downlink-heartbeat-nochange-baseline: 0/1
- p1-safari-or-android-feasibility: 0/1
