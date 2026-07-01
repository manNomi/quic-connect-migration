# User-Provided Public Origin Readiness

작성일: `2026-06-30`

## 1. 목적

이 문서는 사용자가 제안한 public HTTPS origin 후보가 iPhone 없이 진행할 Chrome controlled-public workload trial의 바로 실행 가능한 대상인지 확인한 결과다. 공개 저장소에 남길 수 있도록 URL, DNS address, certificate subject/issuer는 redaction했다.

## 2. 실행 명령

```bash
python3 tools/check_public_origin_readiness.py \
  --url <user-provided-public-origin> \
  --timeout 10 \
  --redact-sensitive \
  --format json \
  --output data/user-provided-public-origin-readiness-20260630.json
```

Raw local redacted markdown smoke도 ignored artifact path에 보관했다.

```bash
harness/results/user-provided-public-origin-readiness-20260630/results/public-origin-readiness-redacted.md
```

## 3. 결과

| check | value |
| --- | --- |
| DNS addresses | `<redacted:1 address>` |
| TCP/TLS OK | `true` |
| Python TLS OK | `false` |
| curl HTTPS OK | `true` |
| TLS version | `curl-verified` |
| final status | `HTTP/2 200` |
| h3 Alt-Svc | `false` |
| Alt-Svc | `-` |
| public-safe JSON | `data/user-provided-public-origin-readiness-20260630.json` |

Observed TLS note:

```text
tls: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

curl still verified the HTTPS endpoint and returned `HTTP/2 200`, so the main blocker for this research purpose is not basic reachability. The blocker is the absence of `Alt-Svc: h3`.

## 4. 해석

확인된 것:

1. 후보 origin은 HTTPS endpoint로 접근 가능하다.
2. 현재 관찰에서는 `Alt-Svc: h3`가 없어서 browser H3 controlled-public trial의 ready target이 아니다.
3. 따라서 이 origin을 그대로 Chrome H3/CM 실험에 쓰면 HTTP/3 application baseline부터 실패하거나 H2-only baseline으로 분류될 가능성이 높다.

논문 claim boundary:

> A public HTTPS endpoint returning HTTP/2 without `Alt-Svc: h3` is not a controlled HTTP/3 origin for browser Connection Migration trials. It can become useful only if we control the origin configuration and enable WebPKI TLS, HTTP/3, and Alt-Svc for the workload endpoints.

한국어 표현:

> 사용자가 제안한 public origin 후보는 HTTPS 접속 자체는 되지만, 현재 관찰에서는 H3 Alt-Svc를 광고하지 않는다. 따라서 그대로는 Chrome controlled-public H3/CM 실험 타깃이 아니며, 해당 도메인을 쓰려면 우리가 HTTP/3 origin과 Alt-Svc, workload endpoint를 통제하도록 서버 설정을 바꿔야 한다.

## 5. 다음 액션

| 우선순위 | 작업 | 근거 |
| ---: | --- | --- |
| 1 | 해당 도메인 뒤에 controlled H3 origin 배치 또는 AWS public origin 새로 구축 | browser H3 application baseline 필요 |
| 2 | `Alt-Svc: h3=":443"; ma=...` 또는 equivalent H3 advertisement 확인 | Chrome H3 discovery gate |
| 3 | `check_public_origin_readiness.py --require-h3-alt-svc` 재실행 | H3 readiness gate |
| 4 | Chrome controlled-public media/range/upload no-change baseline 실행 | active path-change 전 application H3 baseline |

## 6. 피해야 할 주장

| 금지 claim | 이유 |
| --- | --- |
| 이 public origin으로 바로 Chrome H3 CM 실험이 가능하다 | 현재 `h3 Alt-Svc=false`다 |
| HTTPS 200이면 H3 baseline도 준비된 것이다 | HTTP/2 200과 HTTP/3 application baseline은 다르다 |
| public endpoint readiness가 CM evidence다 | readiness는 target selection gate이며 migration evidence가 아니다 |
