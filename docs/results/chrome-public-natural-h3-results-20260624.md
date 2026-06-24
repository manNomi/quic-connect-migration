# Chrome public natural HTTP/3 baseline results

작성일: 2026-06-24

## 1. 목적

local Alt-Svc control에서는 Chrome이 forced QUIC 없이 local self-signed/mkcert origin의 HTTP/3 application request를 만들지 못했다. 이 결과가 Chrome 자체의 HTTP/3 capability 부족 때문인지, local certificate/origin 특성 때문인지 분리하기 위해 public WebPKI origin에서 natural HTTP/3 baseline을 확인했다.

이 실험은 connection migration 실험이 아니다. browser가 실제 public origin을 자연스럽게 HTTP/3로 선택할 수 있는지 확인하는 prerequisite baseline이다.

## 2. 하네스

추가한 파일:

- `repro/quic-go-min-repro/scripts/run-chrome-public-h3.sh`
- `tools/classify_chrome_public_h3_artifacts.py`

하네스 흐름:

```text
Chrome headless bootstrap navigation
  -> 같은 Chrome profile로 second navigation
  -> bootstrap/second NetLog 수집
  -> target host의 QUIC_SESSION, HTTP_STREAM_JOB using_quic, Alt-Svc/broken state 분류
```

Chrome 조건:

- `--enable-quic`
- no `--origin-to-force-quic-on`
- public trusted certificate
- target-specific NetLog classification

## 3. 실행 1: Cloudflare QUIC trace endpoint

사전 확인:

```bash
curl -I https://cloudflare-quic.com/cdn-cgi/trace
```

응답은 `Alt-Svc: h3=":443"; ma=86400`를 광고했다.

실행:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-public-h3-cloudflare-quic-trace-20260624 \
TARGET_URL=https://cloudflare-quic.com/cdn-cgi/trace \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_VIRTUAL_TIME_BUDGET_MS=1000 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
./scripts/run-chrome-public-h3.sh
```

결과:

| 항목 | 값 |
| --- | --- |
| status | `PASS` |
| classification | `public_natural_h3_observed` |
| target host | `cloudflare-quic.com:443` |
| bootstrap NetLog parser | `json` |
| bootstrap target QUIC_SESSION | `1` |
| bootstrap target using_quic jobs | `1` |
| second NetLog parser | `text_fallback` |
| target broken alternative service | `false` |

해석:

- public WebPKI Cloudflare endpoint에서 Chrome natural HTTP/3가 관찰됐다.
- second NetLog는 timeout으로 JSON이 완전히 닫히지 않았지만, bootstrap NetLog JSON만으로도 target QUIC session과 `using_quic` job이 확인된다.

## 4. 실행 2: Google generate_204 endpoint

사전 확인:

```bash
curl -I https://www.google.com
```

응답은 `Alt-Svc: h3=":443"; ma=2592000` 계열을 광고했다.

실행:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-public-h3-google-generate204-20260624 \
TARGET_URL=https://www.google.com/generate_204 \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_VIRTUAL_TIME_BUDGET_MS=1000 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
./scripts/run-chrome-public-h3.sh
```

결과:

| 항목 | 값 |
| --- | --- |
| status | `PASS` |
| classification | `public_natural_h3_observed` |
| target host | `www.google.com:443` |
| bootstrap NetLog parser | `json` |
| bootstrap target QUIC_SESSION | `2` |
| bootstrap target using_quic jobs | `3` |
| second NetLog parser | `json` |
| second target QUIC_SESSION | `1` |
| second target using_quic jobs | `3` |
| target advertised alternative service | `true` |
| target broken alternative service | `false` |

해석:

- public WebPKI Google endpoint에서도 Chrome natural HTTP/3가 관찰됐다.
- bootstrap과 second NetLog가 모두 JSON으로 파싱됐고, target QUIC session과 `using_quic` jobs가 확인됐다.

## 5. 논문상 의미

local Alt-Svc control과 public WebPKI baseline을 함께 보면 다음처럼 분리할 수 있다.

| 조건 | 결과 | 의미 |
| --- | --- | --- |
| Chrome forced QUIC + local quic-go H3 | HTTP/3 request observed | Chrome H3 capability exists |
| Chrome natural Alt-Svc + local self-signed/mkcert | no H3 application request | local trust/origin/policy can block natural H3 |
| Chrome natural Alt-Svc + public WebPKI endpoints | H3 observed | public browser runtime can use natural HTTP/3 |

따라서 후속 browser CM 실험은 다음 조건을 만족해야 한다.

1. target origin이 실제로 Chrome natural HTTP/3로 선택되는지 먼저 확인한다.
2. local self-signed/mkcert result를 public deployment result로 일반화하지 않는다.
3. public WebPKI 또는 이에 준하는 controlled public origin을 준비한 뒤 active interface/path change를 적용한다.

## 6. 후속 작업

- controlled public WebPKI origin을 만든다.
- 같은 application workload(`/browser-slow`, upload/download/dashboard)를 public origin에서 natural H3로 먼저 확인한다.
- 그 뒤 active network/interface change를 넣어 migration/reconnect/failure를 분류한다.
