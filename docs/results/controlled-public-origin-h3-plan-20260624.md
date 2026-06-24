# Controlled public WebPKI H3 origin plan

작성일: 2026-06-24

## 1. 목적

지금까지 Chrome public natural H3 positive control은 Google/Cloudflare 같은 third-party endpoint로 수행했다. 그러나 connection migration 연구의 핵심 workload인 upload, streaming download, dashboard polling은 third-party endpoint에서 제어할 수 없다.

따라서 다음 연구에는 연구자가 제어하는 public WebPKI origin이 필요하다.

## 2. 추가한 하네스

### 2.1 Public origin readiness checker

파일:

- `tools/check_public_origin_readiness.py`

확인 항목:

| 항목 | 의미 |
| --- | --- |
| DNS address | public host가 해석되는지 |
| TCP/TLS | Python SSL 또는 curl 기준으로 HTTPS 검증이 되는지 |
| final HTTP status | browser workload endpoint가 응답하는지 |
| `Alt-Svc: h3` | Chrome natural HTTP/3 discovery 후보인지 |

예시:

```bash
python3 tools/check_public_origin_readiness.py \
  --url https://h3.example.com/browser-slow?duration_ms=6000 \
  --require-h3-alt-svc \
  --format markdown
```

### 2.2 Controlled public H3 server wrapper

파일:

- `repro/quic-go-min-repro/scripts/run-controlled-public-h3-server.sh`

역할:

- WebPKI certificate/key를 `h3server`에 주입한다.
- UDP HTTP/3 listener와 TCP HTTPS Alt-Svc bootstrap listener를 같은 public port에서 연다.
- server qlog, request JSON, JSONL log를 artifact로 남긴다.

예시:

```bash
cd repro/quic-go-min-repro
PUBLIC_ORIGIN_HOST=h3.example.com \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
PUBLIC_ORIGIN_PORT=443 \
EXPECTED_REQUESTS=2 \
./scripts/run-controlled-public-h3-server.sh
```

### 2.3 Controlled public browser baseline wrapper

파일:

- `repro/quic-go-min-repro/scripts/run-controlled-public-h3-browser-baseline.sh`

역할:

- public origin readiness를 먼저 검사한다.
- 같은 artifact directory에 Chrome NetLog를 수집한다.
- `classify_chrome_public_h3_artifacts.py`로 natural HTTP/3 사용 여부를 분류한다.

예시:

```bash
cd repro/quic-go-min-repro
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow' \
CHROME_TIMEOUT_SECONDS=20 \
CHROME_VIRTUAL_TIME_BUDGET_MS=0 \
./scripts/run-controlled-public-h3-browser-baseline.sh
```

## 3. 성공 기준

첫 단계인 no-change baseline은 다음을 만족해야 한다.

1. readiness checker가 DNS/TLS/HTTP response를 통과한다.
2. readiness checker 또는 response header에서 `Alt-Svc: h3`가 관찰된다.
3. Chrome classifier가 `public_natural_h3_observed`를 반환한다.
4. server request log에서 target workload request가 관찰된다.
5. server qlog에 HTTP/3 frame evidence가 남는다.

이 baseline이 성공한 뒤에만 active network-change trigger를 넣는다.

## 4. 아직 실행하지 못한 이유

현재 로컬 readiness 점검에서는 다음이 부족했다.

| 부족한 항목 | 이유 |
| --- | --- |
| public DNS/domain | controlled origin hostname 필요 |
| WebPKI certificate | Chrome natural H3에는 local self-signed/mkcert가 충분하지 않았음 |
| active secondary network | handover trigger를 실제 source path change로 만들기 위해 필요 |
| Android device | Android Chrome/Cronet handover 실험에 필요 |

## 5. Wrapper smoke test

controlled public origin은 아직 없지만, browser baseline wrapper 자체는 기존 public positive control인 Google `generate_204`로 검증했다.

실행:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-h3-browser-wrapper-google-smoke-20260624 \
PUBLIC_ORIGIN_URL=https://www.google.com/generate_204 \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_VIRTUAL_TIME_BUDGET_MS=1000 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
./scripts/run-controlled-public-h3-browser-baseline.sh
```

결과:

| 항목 | 값 |
| --- | --- |
| status | `PASS` |
| classification | `public_natural_h3_observed` |
| bootstrap target QUIC_SESSION | `1` |
| bootstrap target using_quic jobs | `3` |
| second target QUIC_SESSION | `1` |
| second target using_quic jobs | `3` |
| target broken alternative service | `false` |

Chrome headless는 timeout exit `124`를 남겼지만 bootstrap/second NetLog 모두 JSON으로 파싱됐고 target HTTP/3 evidence가 확인됐다. 따라서 wrapper의 readiness -> Chrome NetLog classification 흐름은 동작한다.

## 6. 논문상 의미

이 단계는 결론을 만들기 위한 실험이 아니라, browser CM 실험의 해석 가능성을 확보하는 통제 조건이다.

> Chrome/Cronet handover 실험은 public WebPKI natural H3 baseline이 먼저 성공한 origin에서만 수행해야 한다.

그렇지 않으면 실패 원인이 connection migration이 아니라 HTTP/3 discovery, certificate, origin policy, server reachability 중 어디인지 분리할 수 없다.
