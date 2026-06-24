# Browser CM Observability Matrix

작성일: 2026-06-24

이 문서는 browser-level Connection Migration 결과를 어떤 수준까지 주장할 수 있는지 정리한다. 결론은 단순하다. Chrome desktop은 NetLog 덕분에 session attribution을 할 수 있지만, Safari와 Android는 현재 harness에서 같은 수준의 browser-internal QUIC session evidence가 없다.

## Matrix

| target | usable automation | browser-internal QUIC evidence | session continuity 판정 | 현재 readiness | 논문 claim ceiling |
| --- | --- | --- | --- | --- | --- |
| Chrome desktop | CDP + Chrome NetLog | NetLog file, QUIC session/path/migration event type | 가능 | Chrome/NetLog ready | controlled-public baseline과 active path-change가 충족되면 countable browser CM 후보 |
| Android Chrome | ADB + Chrome/Cronet logging path 필요 | 현재 local harness에서는 미확정 | 미확정 | ADB device 없음 | Android session log path 확보 전에는 not countable |
| Safari macOS | safaridriver WebDriver | WebDriver automation/logging은 가능하나 Chrome NetLog-equivalent는 없음 | 불가 | WebDriver ready, packet capture 필요 | server/qlog/pcap 중심 `PASS_FEASIBILITY`까지만 주장 |
| Safari iOS | Appium 또는 iOS automation + remote capture 필요 | 현재 harness에서는 없음 | 불가 | `rvictl`/device capture not ready | current harness에서는 not countable |
| quic-go controlled client | custom Go client | client transport state + qlog | 가능 | 6/6 mid-flight repetition PASS | browser claim이 아니라 implementation positive control |

## Source-Backed Notes

- Chromium은 NetLog를 browser network-level event/state dump로 설명하고, startup capture에 `--log-net-log`와 capture mode flags를 제공한다.
- Chromium NetLog event list에는 QUIC session network change, path challenge/response, probing, migration success/failure event types가 존재한다.
- WebKit은 Safari 10 이후 `/usr/bin/safaridriver` 기반 native WebDriver automation을 제공한다고 설명한다.
- Selenium Safari 문서는 Safari automation enablement와 logging 위치를 설명하지만, 그 logging은 WebDriver diagnostic log이지 QUIC session-continuity artifact로 취급하면 안 된다.

## Interpretation

Chrome desktop 결과는 `server tuple change + qlog path validation + single target QUIC session`이 동시에 있어야 browser CM 후보가 된다.

Safari/macOS 또는 Android Chrome 결과는 controlled public origin에서 request success와 server qlog가 있더라도, browser-internal session continuity가 없으면 `PASS_FEASIBILITY`로 낮춰 해석한다.

quic-go controlled client 반복 결과는 CM primitive와 HTTP/3 task continuity가 구현체 수준에서 작동함을 보여주는 positive control이다. 하지만 browser policy와 application lifecycle이 개입하는 Chrome/Safari/Android claim으로 일반화하지 않는다.

## References

- [Chromium NetLog capture guide](https://www.chromium.org/for-testers/providing-network-details/)
- [Chromium NetLog QUIC event type list](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h)
- [WebKit: WebDriver Support in Safari 10](https://webkit.org/blog/6900/webdriver-support-in-safari-10/)
- [Selenium Safari documentation](https://www.selenium.dev/documentation/webdriver/browsers/safari/)
