# Browser CM observability readiness

작성일: 2026-06-24

## 1. 목적

Chrome 이후 Safari까지 browser-level HTTP/3 Connection Migration 실험 대상으로 확장할 수 있는지 확인하기 위해, 현재 장비의 browser/driver/packet-capture 관찰성을 점검했다.

이 단계는 migration 결과가 아니다. 어떤 browser를 어떤 evidence chain으로 실험할 수 있는지 정하는 readiness 조사다.

## 2. 추가한 도구

파일:

- `tools/check_browser_cm_observability.py`

실행:

```bash
python3 tools/check_browser_cm_observability.py --format markdown
python3 tools/check_browser_cm_observability.py --format json --output data/browser-cm-observability-20260624.json
```

기본 출력은 공개 artifact용으로 raw command stdout/stderr를 저장하지 않는다. 로컬 디버깅에만 `--include-command-output`을 사용한다.

## 3. 현재 결과

| check | value |
| --- | --- |
| Chrome found | `true` |
| Chrome version | `149.0.7827.158` |
| Chrome NetLog ready | `true` |
| Safari found | `true` |
| Safari version | `26.2` |
| Safari TP found | `false` |
| Safari WebDriver ready | `true` |
| tcpdump | `exit=0` |
| rvictl | `exit=0` |
| packet capture tooling ready | `true` |
| iOS remote capture candidate | `true` |

blocker:

```text
Safari does not provide a Chrome NetLog-equivalent artifact in this harness; use packet capture and server-side qlog
```

## 4. 해석

Chrome:

- Chrome binary가 있고 NetLog 기반 browser H3 artifact 수집이 가능하다.
- 따라서 controlled public origin이 준비되면 Chrome network-change 실험을 먼저 수행하는 것이 가장 해석 가능성이 높다.

Safari:

- Safari와 `safaridriver`는 준비되어 있다.
- `tcpdump`와 `rvictl`도 있어 macOS Safari 또는 iOS Safari packet-capture 기반 실험을 설계할 수 있다.
- 다만 현재 harness에는 Chrome NetLog처럼 browser 내부 QUIC session/reconnect를 직접 분류하는 Safari artifact가 없다.

## 5. 다음 실험 설계

Safari 실험은 Chrome과 같은 classifier를 그대로 쓰지 않는다.

필요 evidence chain:

1. controlled public application H3 baseline PASS
2. Safari WebDriver 또는 수동 Safari navigation
3. server request log와 server qlog의 application H3 evidence
4. client route/interface snapshot
5. packet capture 또는 `rvictl` capture에서 UDP 443 flow continuity 관찰
6. server tuple change와 qlog path validation 여부

따라서 논문에서는 Safari를 “Chrome NetLog와 동등한 browser-internal observability 실험”이 아니라 “server/qlog/packet-capture 중심의 browser compatibility experiment”로 분리하는 편이 안전하다.

## 6. 논문상 의미

이 결과는 browser별 CM 성숙도를 같은 잣대로 단정하면 안 된다는 근거다.

Chrome은 NetLog가 있어 browser-internal QUIC session evidence를 수집할 수 있다. Safari는 실행 readiness는 있지만, 현재 harness 기준으로는 packet capture와 server-side evidence에 더 의존한다. 따라서 Chrome 결과와 Safari 결과는 같은 표에 넣더라도 observability level을 별도 열로 분리해야 한다.
