# Chrome public H3 discovery baseline results

작성일: 2026-06-24

## 1. 목적

local Alt-Svc control에서는 Chrome이 forced QUIC 없이 local self-signed/mkcert origin의 HTTP/3 application request를 만들지 못했다. 이 결과가 Chrome 자체의 H3 capability 부족 때문인지, local certificate/origin 특성 때문인지 분리하기 위해 public WebPKI origin을 확인했다.

재검수 결과 이 실험은 "public natural application HTTP/3 성공"이 아니라 "public H3 discovery control"로 해석해야 한다. Chrome NetLog의 `HTTP_STREAM_JOB using_quic=true` 중 일부는 `dns_alpn_h3` discovery job이며, 이것만으로 application request가 HTTP/3로 처리됐다고 볼 수 없다.

이 실험은 connection migration 실험이 아니다.

## 2. 하네스

추가한 파일:

- `repro/quic-go-min-repro/scripts/run-chrome-public-h3.sh`
- `tools/classify_chrome_public_h3_artifacts.py`

하네스 흐름:

```text
Chrome headless bootstrap navigation
  -> 같은 Chrome profile로 second navigation
  -> bootstrap/second NetLog 수집
  -> target host의 QUIC_SESSION, dns_alpn_h3 job, application using_quic job, Alt-Svc/broken state 분류
```

Chrome 조건:

- `--enable-quic`
- no `--origin-to-force-quic-on`
- public trusted certificate
- target-specific NetLog classification

## 3. 재분류 기준

새 classifier는 다음을 분리한다.

| evidence | 해석 |
| --- | --- |
| `target_dns_alpn_h3_job_count > 0` | H3 discovery job이 생성됨 |
| `target_quic_session_count > 0` | target host/port에 QUIC session 단서가 있음 |
| `target_application_using_quic_job_count > 0` | discovery가 아닌 application job이 QUIC을 사용함 |
| `target_main_non_quic_job_count > 0` | main request job은 non-QUIC으로 처리됨 |

`public_natural_h3_observed`는 `target_quic_session_count > 0`과 `target_application_using_quic_job_count > 0`이 함께 있을 때만 반환한다.

## 4. 실행 결과

| target | status | classification | QUIC_SESSION | dns_alpn_h3 jobs | application using_quic jobs | main non-QUIC jobs |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Cloudflare `https://cloudflare-quic.com/cdn-cgi/trace` bootstrap | `PASS_NEGATIVE_CONTROL` | `public_h3_discovery_without_application_h3` | 1 | 1 | 0 | 1 |
| Google `https://www.google.com/generate_204` bootstrap | `PASS_NEGATIVE_CONTROL` | `public_h3_discovery_without_application_h3` | 2 | 3 | 0 | 2 |
| Google `https://www.google.com/generate_204` second | `PASS_NEGATIVE_CONTROL` | `public_h3_discovery_without_application_h3` | 1 | 3 | 0 | 1 |
| YouTube `https://www.youtube.com/generate_204` bootstrap | `PASS_NEGATIVE_CONTROL` | `public_h3_discovery_without_application_h3` | 0 | 2 | 0 | 2 |
| YouTube `https://www.youtube.com/generate_204` second | `PASS_NEGATIVE_CONTROL` | `public_h3_discovery_without_application_h3` | 0 | 2 | 0 | 2 |

Cloudflare second NetLog는 text fallback만 가능했으므로 application H3 확정 evidence로 사용하지 않는다.

## 5. 해석

local forced-QUIC Chrome baseline은 이미 HTTP/3 application request를 확인했다. 따라서 Chrome H3 capability 자체가 없다는 뜻은 아니다.

이번 public WebPKI endpoint 결과는 다음을 보여준다.

1. public endpoint들은 H3 discovery 후보로는 유용하다.
2. `dns_alpn_h3` discovery job 또는 `QUIC_SESSION` 단서만으로 application request의 HTTP/3 처리를 확정하면 안 된다.
3. third-party public endpoint는 server log와 qlog를 통제할 수 없어서 upload/download/dashboard continuity 실험에는 부적합하다.
4. browser Connection Migration 실험에는 연구자가 제어하는 public WebPKI origin이 필요하다.

## 6. 후속 작업

- controlled public WebPKI origin을 만든다.
- server request log와 qlog로 application HTTP/3 baseline을 먼저 확인한다.
- 그 뒤 active network/interface change를 넣어 migration, reconnect, failure를 분류한다.
