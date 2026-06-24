# Public origin readiness survey

작성일: 2026-06-24

## 1. 목적

`Alt-Svc: h3` 광고 여부만으로는 browser workload target을 고르기에 부족하다. 후속 Chrome/Cronet handover 실험에서는 DNS, HTTPS 검증, H3 discovery 가능성, workload endpoint 상태를 함께 봐야 한다.

이 조사는 connection migration 실험이 아니다. public third-party endpoint 중 browser discovery positive control과 workload 후보를 분리하기 위한 target readiness 조사다.

## 2. 재현 방법

```bash
python3 tools/scan_public_origin_readiness.py \
  --url-file data/public-alt-svc-targets.txt \
  --format csv \
  --output data/public-origin-readiness-survey-20260624.csv

python3 tools/scan_public_origin_readiness.py \
  --url-file data/public-alt-svc-targets.txt \
  --format markdown
```

## 3. 결과

| url | final status | HTTPS OK | h3 Alt-Svc | browser H3 candidate | workload candidate |
| --- | --- | ---: | ---: | ---: | ---: |
| `https://www.google.com/generate_204` | `HTTP/2 204` | true | true | true | true |
| `https://cloudflare-quic.com/cdn-cgi/trace` | `HTTP/2 404` | true | true | true | false |
| `https://www.cloudflare.com/cdn-cgi/trace` | `HTTP/2 404` | true | true | true | false |
| `https://github.com/` | `HTTP/2 200` | true | false | false | false |
| `https://www.amazon.com/` | `HTTP/2 503` | true | true | true | false |
| `https://www.naver.com/` | `HTTP/2 200` | true | false | false | false |
| `https://www.kakao.com/` | `HTTP/2 200` | true | false | false | false |
| `https://www.youtube.com/generate_204` | `HTTP/2 204` | true | true | true | true |

전체 CSV는 `data/public-origin-readiness-survey-20260624.csv`에 저장했다.

## 4. 해석

분류 기준:

| classification | 조건 |
| --- | --- |
| HTTPS OK | DNS, TLS/HTTPS, response가 기본적으로 동작 |
| browser H3 candidate | HTTPS OK이고 `Alt-Svc: h3`가 있음 |
| workload candidate | browser H3 candidate이고 final status가 2xx |

이번 관찰의 의미:

1. Google `generate_204`와 YouTube `generate_204`는 public browser H3 positive control과 lightweight workload candidate로 적합하다.
2. Cloudflare trace endpoint는 H3 discovery candidate지만 final status가 404라 workload candidate는 아니다.
3. Amazon은 H3 Alt-Svc는 있으나 503이라 안정적인 workload target으로 부적합하다.
4. GitHub/Naver/Kakao는 HTTPS는 정상이나 이번 관찰에서 H3 discovery candidate가 아니다.

## 5. 후속 실험 결정

third-party endpoint로는 browser discovery와 small no-change baseline까지만 검증한다. upload, streaming download, dashboard polling, handover continuity는 controlled public WebPKI origin에서 수행해야 한다.

다음 public third-party 추가 실험 후보는 YouTube `generate_204`다. Google과 같은 계열이지만 별도 hostname이므로 Chrome natural H3 baseline 반복 검증에 쓸 수 있다.
