# Safari WebDriver Session Readiness

작성일: `2026-06-30`

## 1. 목적

이 문서는 iPhone 없이 보강할 수 있는 browser observability gap 중 Safari desktop 자동화 readiness를 재검수한 결과다.

기존 readiness는 `safaridriver --version` 성공을 `Safari WebDriver ready`로 보았다. 그러나 실제 Safari 실험에서는 WebDriver binary 존재보다 session creation 가능 여부가 더 중요하다. 따라서 `tools/check_browser_cm_observability.py`에 `--safari-session-smoke` 옵션을 추가해 실제 WebDriver session 생성까지 확인하도록 했다.

## 2. 실행 명령

```bash
python3 tools/check_browser_cm_observability.py \
  --format markdown \
  --safari-session-smoke \
  --safari-session-smoke-port 4456 \
  --output docs/results/browser-cm-observability-readiness-refresh-20260630.md

python3 tools/check_browser_cm_observability.py \
  --format json \
  --safari-session-smoke \
  --safari-session-smoke-port 4457 \
  --output data/browser-cm-observability-refresh-20260630.json
```

별도 raw smoke artifact:

```bash
python3 tools/run_safari_webdriver_navigation.py \
  --url 'data:text/html,<smoke page>' \
  --port 4455 \
  --wait-seconds 1 \
  --output harness/results/safari-webdriver-local-smoke-20260630/results/safari-navigation.json
```

## 3. 결과

| check | value |
| --- | --- |
| Safari found | `true` |
| Safari version | `26.2` |
| safaridriver binary | `exit=0` |
| Safari WebDriver binary ready | `true` |
| Safari WebDriver session checked | `true` |
| Safari WebDriver session ready | `false` |
| packet capture tooling ready | `true` |
| iOS remote capture candidate | `true` |

session creation failure:

```text
Could not create a session: You must enable 'Allow remote automation' in the Developer section of Safari Settings to control Safari via WebDriver.
```

## 4. 해석

확인된 것:

1. Safari와 `safaridriver` binary는 존재한다.
2. `tcpdump`, `route`, `ifconfig`, `rvictl` 등 관찰성 도구는 준비되어 있다.
3. 현재 Safari 설정에서는 WebDriver session creation이 실패한다.
4. 따라서 Safari controlled-public baseline 또는 network-change wrapper는 현재 사용자 설정 변경 없이 실행할 수 없다.

논문 claim boundary:

> Safari desktop remains a feasible cross-browser target, but the current host is not ready to run Safari WebDriver trials until Safari's Allow remote automation setting is enabled. Even after automation is enabled, Safari lacks a Chrome NetLog-equivalent artifact in this harness, so Safari results remain server/qlog/client-path feasibility evidence unless stronger browser-internal telemetry is added.

한국어 표현:

> Safari desktop은 교차 브라우저 feasibility 후보로 남아 있지만, 현재 장비에서는 Safari 설정의 `Allow remote automation`이 꺼져 있어 WebDriver session 생성이 되지 않는다. 이 설정을 켠 뒤에도 Safari는 Chrome NetLog에 해당하는 내부 QUIC session artifact가 없으므로, Safari 결과는 server/qlog/client-path 중심의 `PASS_FEASIBILITY`로 해석해야 한다.

## 5. 다음 액션

| 우선순위 | 작업 | 근거 |
| ---: | --- | --- |
| 1 | Safari Settings > Developer > Allow remote automation 활성화 | WebDriver session creation gate |
| 2 | `--safari-session-smoke` 재실행 | `Safari WebDriver session ready=true` |
| 3 | controlled public Safari baseline 실행 | server/qlog application H3 evidence |
| 4 | Safari network-change feasibility 실행 | client path snapshot + server/qlog path evidence |

## 6. 피해야 할 주장

| 금지 claim | 이유 |
| --- | --- |
| `safaridriver --version`이 성공했으므로 Safari 실험 가능 | 현재 session creation이 실패한다 |
| Safari automation success가 Safari QUIC CM success | WebDriver는 navigation automation이며 QUIC session continuity artifact가 아니다 |
| Safari 결과를 Chrome NetLog 결과와 같은 등급으로 비교 | Safari에는 현재 harness 기준 Chrome NetLog-equivalent가 없다 |
