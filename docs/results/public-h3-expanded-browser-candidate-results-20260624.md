# Public H3 Expanded Browser Candidate Results

작성일: 2026-06-24

## 목적

controlled public WebPKI origin이 아직 준비되지 않은 상태에서, 제3자 public endpoint가 Chrome HTTP/3 application evidence의 대체물이 될 수 있는지 확인했다.

이 실험의 위치는 다음과 같다.

- final browser handover trial의 대체 증거가 아니다.
- public WebPKI 환경에서 Chrome이 실제 HTTP/3를 사용할 수 있는 후보가 있는지 확인하는 보조 evidence다.
- 제3자 endpoint는 server-side qlog, workload duration, network-change trigger, backend routing을 통제할 수 없으므로 CM 성공 claim에는 사용할 수 없다.

## Alt-Svc 확장 스캔

20개 public endpoint를 `curl -sSIL` 기반으로 스캔했다.

| metric | value |
| --- | ---: |
| scanned endpoints | 20 |
| endpoints advertising H3 Alt-Svc | 12 |
| HTTPS 2xx + H3 Alt-Svc workload candidates | 7 |

H3 Alt-Svc와 2xx workload 후보:

| url | status | H3 Alt-Svc | workload candidate |
| --- | --- | ---: | ---: |
| `https://www.google.com/generate_204` | `HTTP/2 204` | yes | yes |
| `https://www.youtube.com/generate_204` | `HTTP/2 204` | yes | yes |
| `https://www.cloudflare.com/` | `HTTP/2 200` | yes | yes |
| `https://blog.cloudflare.com/` | `HTTP/2 200` | yes | yes |
| `https://www.facebook.com/` | `HTTP/2 200` | yes | yes |
| `https://www.instagram.com/` | `HTTP/2 200` | yes | yes |
| `https://www.bing.com/` | `HTTP/2 200` | yes | yes |

Non-candidates included H3-advertising but non-2xx endpoints such as `openai.com`, `chatgpt.com`, and `www.amazon.com`, and non-H3 endpoints such as GitHub, Naver, Kakao, Apple, Wikipedia, Microsoft, Netflix, and TikTok in this scan.

Raw CSV:

- `data/public-alt-svc-expanded-survey-20260624.csv`
- `data/public-origin-readiness-expanded-survey-20260624.csv`

## Chrome public H3 observation runs

Five public candidates were tested with the existing Chrome NetLog wrapper.

```bash
cd repro/quic-go-min-repro
RUN_ID=<run-id> TARGET_URL=<url> SECOND_URL=<url> \
  CHROME_TIMEOUT_SECONDS=25 CHROME_VIRTUAL_TIME_BUDGET_MS=8000 \
  ./scripts/run-chrome-public-h3.sh
```

| run | url | status | classification | observed application H3 | note |
| --- | --- | --- | --- | ---: | --- |
| `chrome-public-h3-cloudflare-home-20260624` | `https://www.cloudflare.com/` | `PASS_NEGATIVE_CONTROL` | `public_h3_discovery_without_application_h3` | no | H3 discovery and QUIC session hints existed, but application H3 job count was 0 |
| `chrome-public-h3-cloudflare-blog-20260624` | `https://blog.cloudflare.com/` | `PASS` | `public_natural_h3_observed` | yes | bootstrap NetLog showed 75 target application `using_quic` jobs |
| `chrome-public-h3-bing-home-20260624` | `https://www.bing.com/` | `PASS` | `public_natural_h3_observed` | yes | second NetLog showed 27 target application `using_quic` jobs |
| `chrome-public-h3-facebook-home-20260624` | `https://www.facebook.com/` | `PASS` | `public_natural_h3_observed` | yes | second NetLog showed 9 target application `using_quic` jobs |
| `chrome-public-h3-instagram-home-20260624` | `https://www.instagram.com/` | `PASS` | `public_natural_h3_observed` | yes | second NetLog showed 12 target application `using_quic` jobs |

All five Chrome runs ended with Chrome timeout exit `124` because the pages did not naturally quiesce within the headless window. The classifier still used the captured NetLog evidence. Therefore these rows should be interpreted as browser protocol observation, not page-complete workload success.

## Interpretation

This expanded scan changes the public-browser story in a useful way.

Earlier Google/YouTube/Cloudflare trace controls mostly showed H3 discovery without confirming application H3. The expanded run found public pages where Chrome did create target application `using_quic` jobs. That means browser-level HTTP/3 use is observable in the current environment.

However, these third-party pages still do not satisfy the final CM evidence chain:

1. The server-side qlog and request log are not available.
2. The page workload is uncontrolled and often does not quiesce in headless mode.
3. Application H3 jobs can coexist with non-QUIC main jobs, so a single page load may be mixed-protocol.
4. There is no controlled active path-change trigger.
5. There is no way to prove same logical backend/routing continuity after tuple change.

Therefore the conclusion is:

> Public WebPKI endpoints can help confirm that Chrome is capable of natural HTTP/3 application use, but they do not replace a controlled public origin for browser Connection Migration experiments.
