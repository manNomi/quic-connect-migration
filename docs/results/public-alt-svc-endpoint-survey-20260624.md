# Public HTTP/3 Alt-Svc endpoint survey

작성일: 2026-06-24

## 1. 목적

Chrome public natural H3 baseline을 확보한 뒤, 후속 browser/network-change 실험의 target origin을 고르기 위해 public HTTPS endpoint의 HTTP/3 advertisement를 작은 표본으로 확인했다.

이 조사는 connection migration 실험이 아니다. `Alt-Svc: h3` 광고 여부를 보는 endpoint discovery 사전 조사다.

## 2. 재현 방법

```bash
python3 tools/scan_public_alt_svc.py \
  --url-file data/public-alt-svc-targets.txt \
  --format csv \
  --output data/public-alt-svc-survey-20260624.csv

python3 tools/scan_public_alt_svc.py \
  --url-file data/public-alt-svc-targets.txt \
  --format markdown
```

## 3. 결과

| url | final status | h3 Alt-Svc | 해석 |
| --- | --- | ---: | --- |
| `https://www.google.com/generate_204` | `HTTP/2 204` | true | Chrome natural H3 양성 대조군으로 사용 가능 |
| `https://cloudflare-quic.com/cdn-cgi/trace` | `HTTP/2 404` | true | Chrome natural H3 양성 대조군으로 사용 가능 |
| `https://www.cloudflare.com/cdn-cgi/trace` | `HTTP/2 404` | true | Cloudflare 계열 public H3 후보 |
| `https://github.com/` | `HTTP/2 200` | false | 이번 관찰에서는 H3 후보로 부적합 |
| `https://www.amazon.com/` | `HTTP/2 503` | true | H3 광고는 있으나 status 503이라 workload target으로는 부적합 |
| `https://www.naver.com/` | `HTTP/2 200` | false | 이번 관찰에서는 H3 후보로 부적합 |
| `https://www.kakao.com/` | `HTTP/2 200` | false | redirect 후 최종 응답 기준 H3 후보로 부적합 |
| `https://www.youtube.com/generate_204` | `HTTP/2 204` | true | Google 계열 public H3 후보 |

전체 CSV는 `data/public-alt-svc-survey-20260624.csv`에 저장했다.

## 4. 해석

public HTTPS endpoint라고 해서 모두 HTTP/3 discovery target이 되는 것은 아니다. 또한 `Alt-Svc: h3`가 있더라도 Amazon처럼 workload target으로 쓰기 어려운 응답 상태가 나올 수 있다.

따라서 다음 browser CM 실험의 target은 다음 조건을 만족해야 한다.

1. 실행 시점에 `Alt-Svc: h3`를 광고한다.
2. Chrome NetLog에서 natural HTTP/3 사용이 확인된다.
3. test workload를 안정적으로 제공한다.
4. 가능하면 연구자가 제어하는 public WebPKI origin이어야 한다.

현재 public third-party endpoint 중에서는 Google `generate_204`, YouTube `generate_204`, Cloudflare 계열 endpoint가 browser discovery positive control에 적합하다. 그러나 upload/download/dashboard 작업 연속성 실험에는 third-party endpoint가 아니라 controlled public origin이 필요하다.
