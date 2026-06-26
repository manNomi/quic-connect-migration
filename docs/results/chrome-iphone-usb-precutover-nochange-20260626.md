# Chrome iPhone USB Pre-Cutover No-Change Control

작성일: 2026-06-26

## 목적

active network-change trial에서 관찰한 실패가 mid-flight connection migration 실패인지, 아니면 iPhone USB tethering 경로 자체의 HTTP/3 workload 안정성 문제인지 분리하기 위해 pre-cutover no-change control을 수행했다. 이 실험은 Wi-Fi를 workload 시작 전에 끄고, default/target route가 iPhone USB `en8`로 바뀐 것을 확인한 뒤 Chrome HTTP/3 downlink workload를 실행했다.

## Long Downlink 실행 조건

| 항목 | 값 |
| --- | --- |
| trial id | `controlled-public-chrome-downlink-noheartbeat-iphone-usb-precutover-nochange-001` |
| browser | Chrome headless CDP runner |
| origin | controlled public WebPKI origin, EC2 quic-go `h3server` |
| workload | `GET /browser-downlink` + streaming `GET /downlink-stream` |
| bootstrap | `GET /browser-slow` + streaming `GET /slow-js` |
| network condition | workload 시작 전 `networksetup -setairportpower en0 off` |
| restore | shell trap으로 `networksetup -setairportpower en0 on` |
| expected server requests | 4 |
| local artifact | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-iphone-usb-precutover-nochange-001` |

## Long Downlink 경로 검증

| 관찰 | 결과 |
| --- | --- |
| pre-cutover default route | `en8` |
| pre-cutover target route | `en8` |
| active IPv4 interface | `en8`, `172.20.10.8` |
| public IP probe | `106.101.2.80` |
| before-restore default/target route | `en8` / `en8` |

## Long Downlink 프로토콜 결과

| 관찰 | 결과 |
| --- | --- |
| combined classifier | `PASS / controlled_public_application_h3_confirmed` |
| Chrome second navigation | `second_exit=0` |
| Chrome second H3 evidence | target application QUIC job 1, target QUIC session 1 |
| server request count | 5 requests, expected 4 이상 |
| server H3 requests | `/slow-js`, `/downlink-stream` |
| qlog application H3 | `chosen_alpn=2`, `http3_frame=17` |
| qlog PATH_CHALLENGE/PATH_RESPONSE | 0/0 |

## Long Downlink 애플리케이션 결과

프로토콜 계층에서는 HTTP/3가 확인됐지만, CDP page dataset 기준 downlink task는 완료되지 않았다.

| 관찰 | 결과 |
| --- | --- |
| `downlinkBytes` | `8762` |
| `downlinkError` | `Error: TypeError: network error` |
| `downlinkErrorElapsedMs` | `2002` |
| server log | `response_write_error=H3_NO_ERROR (local)` |

## Short Downlink 대조군

long downlink 실패가 iPhone USB 경로 전체의 불능인지 확인하기 위해 같은 pre-cutover 조건에서 workload를 줄인 short downlink control을 추가했다.

| 항목 | 값 |
| --- | --- |
| trial id | `controlled-public-chrome-downlink-short-iphone-usb-precutover-nochange-001` |
| bootstrap | `GET /browser-slow?duration_ms=1000&chunks=1` |
| workload | `GET /browser-downlink?duration_ms=3000&chunks=3&bytes=8192` + streaming `GET /downlink-stream` |
| pre-cutover route | default `en8`, target `en8` |
| active IPv4 interface | `en8`, `172.20.10.8` |
| public IP probe | `106.101.2.80` |
| combined classifier | `PASS / controlled_public_application_h3_confirmed` |
| Chrome second navigation | `second_exit=0` |
| application dataset | `downlinkComplete=true`, `downlinkBytes=8390`, `downlinkElapsedMs=3056` |
| server H3 requests | `/slow-js`, `/browser-downlink`, `/downlink-stream` |
| qlog application H3 | `chosen_alpn=2`, `http3_frame=16` |
| qlog PATH_CHALLENGE/PATH_RESPONSE | 0/0 |
| local artifact | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-short-iphone-usb-precutover-nochange-001` |

## 재현 명령

client-side pre-cutover 제어는 다음 wrapper로 반복할 수 있다. 서버는 기존 controlled public EC2 origin에서 `repro/quic-go-min-repro/scripts/run-controlled-public-h3-server.sh`를 먼저 실행해 둔다.

```bash
TRIAL_ID=controlled-public-chrome-downlink-short-iphone-usb-precutover-nochange-001 \
PUBLIC_ORIGIN_BOOTSTRAP_URL='https://43-203-244-29.sslip.io/browser-slow?duration_ms=1000&chunks=1&label=public-short-bootstrap' \
PUBLIC_ORIGIN_PRECUTOVER_URL='https://43-203-244-29.sslip.io/browser-downlink?duration_ms=3000&chunks=3&bytes=8192&heartbeat=false&heartbeat_delay_ms=1000&label=public-downlink-short-noheartbeat' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=5 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=8 \
CHROME_TIMEOUT_SECONDS=35 \
harness/scripts/chrome-iphone-usb-precutover-control-run.sh
```

## 해석

이 결과는 iPhone USB pre-cutover 경로에서 Chrome이 controlled public origin과 HTTP/3 application traffic을 만들 수 있음을 보여준다. 특히 short downlink control은 같은 `en8` route와 같은 셀룰러 public IP에서 application completion까지 확인했다. 따라서 이전 active network-change trial의 실패를 단순히 "테더링 경로가 H3를 전혀 못 한다"로 해석하면 안 된다.

동시에 long downlink control은 no-change 상태에서도 application task가 완료되지 않았음을 보여준다. 즉 현재 macOS + iPhone USB tethering 조건은 short H3 application task에는 충분하지만, 15초 long streaming downlink에는 불안정하다. 논문상으로는 transport-level H3 confirmation, route confirmation, application task completion을 분리해서 평가해야 한다는 근거로 쓰는 것이 더 안전하다.

## 다음 판단

- iPhone USB 경로는 H3 가능 경로로는 확인됐다.
- short no-change downlink는 완료됐지만 long no-change downlink는 실패했다.
- 따라서 이 경로만으로 active CM 성공/실패를 단정하기 어렵고, workload duration/size를 통제한 반복 실험이 필요하다.
- 다음 active CM positive evidence는 Android Chrome cellular handover 또는 Safari/iOS 계열처럼 OS가 경로 전환을 더 자연스럽게 처리하는 환경에서 우선 찾는 편이 낫다.
