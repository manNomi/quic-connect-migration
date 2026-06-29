# i18nexus.pro Public H3 Feasibility Check

작성일: 2026-06-29

## 목적

사용자가 제공한 `https://i18nexus.pro/`를 controlled public origin 후보 또는 public H3 observation control로 쓸 수 있는지 확인했다.

이 검수는 final browser Connection Migration 증거가 아니다. 제3자 또는 managed hosting endpoint는 server qlog, request tuple, workload timing, routing path를 통제할 수 없으므로 CM success claim을 대체하지 못한다.

## 실행 명령

```bash
python3 tools/scan_public_alt_svc.py https://i18nexus.pro/ --format markdown

python3 tools/check_public_origin_readiness.py \
  --url https://i18nexus.pro/ \
  --require-h3-alt-svc \
  --redact-sensitive \
  --format markdown

cd repro/quic-go-min-repro
RUN_ID=chrome-public-h3-i18nexus-20260629 \
TARGET_URL=https://i18nexus.pro/ \
SECOND_URL=https://i18nexus.pro/ \
CHROME_TIMEOUT_SECONDS=25 \
CHROME_VIRTUAL_TIME_BUDGET_MS=5000 \
./scripts/run-chrome-public-h3.sh
```

## 결과

| check | result |
| --- | --- |
| HTTPS status | `HTTP/2 200` |
| server header | `Vercel` |
| `Alt-Svc: h3` | `false` |
| controlled origin readiness | `not ready for H3 requirement` |
| Chrome classifier status | `PASS_NEGATIVE_CONTROL` |
| Chrome classification | `public_h3_discovery_without_application_h3` |
| any H3 observed | `false` |
| DNS ALPN/H3 discovery jobs | bootstrap `38`, second `11` |
| target QUIC sessions | bootstrap `0`, second `0` |
| target application `using_quic` jobs | bootstrap `0`, second `0` |

`check_public_origin_readiness.py` reported curl-verified HTTPS success, but Python TLS verification failed on the local trust store. This does not change the H3 conclusion because curl reached the site and the response did not advertise `Alt-Svc: h3`.

Raw Chrome artifacts are under the ignored local artifact directory:

```text
repro/quic-go-min-repro/artifacts/chrome-public-h3-i18nexus-20260629
```

## 해석

`i18nexus.pro`는 public HTTPS endpoint로는 살아 있지만, 현재 상태에서는 application HTTP/3 positive control이 아니다. Chrome NetLog에서 DNS ALPN/H3 discovery job은 있었지만 target QUIC session과 application `using_quic` job이 모두 0이었다.

따라서 이 도메인은 다음처럼만 사용할 수 있다.

- public endpoint가 살아 있어도 H3 application traffic이 자동으로 관찰되는 것은 아니라는 negative/control evidence
- controlled public origin 후보에서 제외해야 하는 근거
- third-party/managed endpoint가 final CM evidence chain을 대체할 수 없다는 reviewer-defense 사례

논문에는 `i18nexus.pro`를 Chrome CM 성공 또는 controlled-origin 대체 증거로 쓰지 않는다.
