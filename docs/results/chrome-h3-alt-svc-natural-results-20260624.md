# Chrome natural Alt-Svc HTTP/3 control results

작성일: 2026-06-24

## 1. 목적

기존 Chrome browser baseline은 `--origin-to-force-quic-on`으로 target origin을 강제로 HTTP/3로 태웠다. 이 실험은 더 실제 배포에 가까운 조건을 확인하기 위해, 같은 origin에서 TCP HTTPS 응답이 `Alt-Svc: h3=":4443"; ma=60`를 광고한 뒤 두 번째 Chrome request가 자연스럽게 HTTP/3로 전환되는지 검수했다.

이 실험은 connection migration 실험이 아니라 browser HTTP/3 discovery/control 실험이다.

## 2. 하네스 변경

추가/수정한 재현 코드:

- `repro/quic-go-min-repro/cmd/h3server/main.go`
  - 기존 UDP HTTP/3 listener에 더해 선택적으로 TCP HTTPS listener를 함께 실행한다.
  - `--tcp-addr`, `--alt-svc` flag를 추가했다.
  - 각 request에 `proto`, `tls_alpn`을 기록한다.
- `repro/quic-go-min-repro/scripts/run-h3-server.sh`
  - `TCP_ADDR`, `ALT_SVC` environment variable을 h3server flag로 전달한다.
- `repro/quic-go-min-repro/scripts/run-chrome-h3-alt-svc.sh`
  - test cert/SPKI 생성
  - TCP+UDP origin 실행
  - 같은 Chrome profile로 bootstrap request와 second request를 순차 실행
  - NetLog, server JSON, qlog 수집
- `tools/classify_chrome_alt_svc_artifacts.py`
  - server protocol record, target NetLog, qlog를 함께 보고 natural h3 upgrade 여부를 판정한다.

## 3. 실행 1: IP literal origin

명령:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-alt-svc-local-20260624 ./scripts/run-chrome-h3-alt-svc.sh
```

조건:

- URL origin: `https://127.0.0.1:4443`
- UDP HTTP/3 listen: `127.0.0.1:4443`
- TCP HTTPS listen: `127.0.0.1:4443`
- Alt-Svc: `h3=":4443"; ma=60`
- Chrome flag: `--enable-quic`, SPKI cert exception
- Chrome flag intentionally omitted: `--origin-to-force-quic-on`

결과:

| 항목 | 값 |
| --- | --- |
| status | `PASS_NEGATIVE_CONTROL` |
| classification | `alt_svc_advertised_but_h3_not_observed` |
| server request count | `2` |
| server request protos | `HTTP/1.1`, `HTTP/1.1` |
| server request TLS ALPN | `http/1.1`, `http/1.1` |
| qlog `http3_frame` | `0` |
| target NetLog confirmed QUIC session | `false` |

관찰:

- 첫 번째 TCP response에 `Alt-Svc: h3=":4443"; ma=60`가 포함됐다.
- NetLog에는 target origin에 대한 h3 candidate job이 보였다.
- 그러나 target `QUIC_SESSION`은 확인되지 않았고, server qlog도 비어 있었다.
- 따라서 IP literal origin에서는 natural HTTP/3 upgrade를 관찰하지 못했다.

## 4. 실행 2: localhost origin

명령:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-alt-svc-localhost-20260624 \
ADDR=localhost:4443 \
LISTEN_ADDR=127.0.0.1:4443 \
TCP_ADDR=127.0.0.1:4443 \
./scripts/run-chrome-h3-alt-svc.sh
```

조건:

- URL origin: `https://localhost:4443`
- UDP HTTP/3 listen: `127.0.0.1:4443`
- TCP HTTPS listen: `127.0.0.1:4443`
- Alt-Svc: `h3=":4443"; ma=60`
- Chrome flag: `--enable-quic`, SPKI cert exception
- Chrome flag intentionally omitted: `--origin-to-force-quic-on`

결과:

| 항목 | 값 |
| --- | --- |
| status | `PASS_NEGATIVE_CONTROL` |
| classification | `alt_svc_advertised_but_h3_not_observed` |
| server request count | `2` |
| server request protos | `HTTP/1.1`, `HTTP/1.1` |
| server request TLS ALPN | `http/1.1`, `http/1.1` |
| qlog `http3_frame` | `0` |
| target NetLog confirmed QUIC session | `false` |

관찰:

- NetLog는 Chrome timeout 때문에 JSON으로 완전히 닫히지 않아 `text_fallback`으로만 해석했다.
- target origin에 대한 QUIC session hint는 있었지만 server qlog와 server protocol record가 모두 HTTP/3를 부정했다.
- 따라서 localhost origin에서도 natural HTTP/3 upgrade는 확정 관찰하지 못했다.

## 5. 실행 3: HTML page/subresource diagnostic

이전 두 실행은 `/download` binary response를 `--dump-dom`으로 요청했기 때문에 Chrome headless가 timeout으로 끝났다. 따라서 세 번째 실행에서는 HTML page와 subresource를 사용해 더 browser-like workload로 재검증했다.

명령:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-alt-svc-html-local-20260624 \
EXPECTED_REQUESTS=4 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_VIRTUAL_TIME_BUDGET_MS=3000 \
BOOTSTRAP_PATH='/browser-sequence?resources=1&bytes=64&label=alt-svc-bootstrap-html' \
H3_PATH='/browser-sequence?resources=1&bytes=64&label=alt-svc-h3-html' \
./scripts/run-chrome-h3-alt-svc.sh
```

결과:

| 항목 | 값 |
| --- | --- |
| status | `PASS_NEGATIVE_CONTROL` |
| classification | `alt_svc_quic_candidate_cert_rejected` |
| server request count | `4` |
| server request protos | `HTTP/1.1`, `HTTP/1.1`, `HTTP/1.1`, `HTTP/1.1` |
| qlog `connection_started` | `1` |
| qlog `http3_frame` | `1` |
| qlog close reason | `certificate unknown`, `CERTIFICATE_VERIFY_FAILED` |

관찰:

- Chrome은 target origin에 대해 QUIC 후보 연결을 열었다.
- server qlog에는 QUIC handshake와 HTTP/3 SETTINGS frame 생성이 기록됐다.
- 그러나 application request 4개는 모두 TCP `HTTP/1.1`로 처리됐다.
- QUIC 후보 연결은 remote 측에서 `certificate unknown / CERTIFICATE_VERIFY_FAILED`로 닫혔다.

## 6. 실행 4: `--ignore-certificate-errors` diagnostic

인증서 실패가 원인인지 확인하기 위해 Chrome에 `--ignore-certificate-errors`를 추가한 진단 실험을 수행했다.

명령:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-alt-svc-html-ignore-cert-local-20260624 \
EXPECTED_REQUESTS=4 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_VIRTUAL_TIME_BUDGET_MS=3000 \
CHROME_EXTRA_ARGS='--ignore-certificate-errors' \
BOOTSTRAP_PATH='/browser-sequence?resources=1&bytes=64&label=alt-svc-bootstrap-html-ignore-cert' \
H3_PATH='/browser-sequence?resources=1&bytes=64&label=alt-svc-h3-html-ignore-cert' \
./scripts/run-chrome-h3-alt-svc.sh
```

결과:

| 항목 | 값 |
| --- | --- |
| status | `PASS_NEGATIVE_CONTROL` |
| classification | `alt_svc_quic_candidate_cert_rejected` |
| server request count | `4` |
| server request protos | `HTTP/1.1`, `HTTP/1.1`, `HTTP/1.1`, `HTTP/1.1` |
| qlog `connection_started` | `1` |
| qlog `http3_frame` | `1` |
| qlog close reason | `certificate unknown`, `CERTIFICATE_VERIFY_FAILED` |

관찰:

- `--ignore-certificate-errors`를 추가해도 natural Alt-Svc 후보 연결은 application request를 운반하지 못했다.
- qlog close reason은 여전히 `certificate unknown / CERTIFICATE_VERIFY_FAILED`였다.
- 따라서 이 local self-signed setup에서는 SPKI 예외 또는 broad certificate-ignore flag만으로 natural Alt-Svc HTTP/3 전환을 보장하지 못했다.

## 7. 해석

이 결과는 "Chrome이 HTTP/3를 못 한다"는 뜻이 아니다. 같은 Chrome 149 headless에서 `--origin-to-force-quic-on` 조건을 주면 local quic-go H3 origin으로 HTTP/3 request가 도달하는 것을 이미 확인했다.

이번 결과의 의미는 더 좁다.

> Local self-signed origin에서 Alt-Svc만으로 Chrome natural HTTP/3 upgrade를 재현하지 못했다. HTML workload에서는 QUIC/H3 후보 연결이 열렸지만 인증서 검증 실패로 application request가 HTTP/3로 전환되지 않았다. 따라서 forced-QUIC browser baseline과 real deployment style browser discovery baseline은 분리해서 검증해야 한다.

논문에서는 이 결과를 다음 주장에 사용할 수 있다.

1. Browser CM 실험 전에 "브라우저가 target origin을 실제 HTTP/3로 선택했는가"를 먼저 증명해야 한다.
2. NetLog의 h3 candidate job이나 `QUIC_CONNECTION_MIGRATION_MODE` event만으로는 HTTP/3 사용이나 migration 발생을 주장할 수 없다.
3. local self-signed certificate control은 forced QUIC baseline에는 충분할 수 있지만 natural Alt-Svc browser experiment에는 충분하지 않을 수 있다.
4. 실제 browser/mobile 연구는 public trusted certificate, Alt-Svc/DNS HTTPS/SVCB, active network change를 포함한 환경에서 다시 수행해야 한다.

## 8. 후속 작업

- public trusted origin 또는 AWS direct-origin HTTPS bootstrap에서 natural HTTP/3 upgrade를 재검증한다.
- Chrome background traffic을 줄이기 위해 추가 flag 또는 isolated test profile 정책을 검토한다. HTML diagnostic에서는 artifact 크기를 약 3.6 MiB로 줄였다.
- `localhost` 실험에서 UDP IPv6/IPv4 경로 차이를 분리하려면 `[::]:4443` listen 또는 explicit host mapping을 추가 대조한다.
- natural HTTP/3가 안정적으로 확인된 뒤에만 active interface change 실험으로 넘어간다.

## 9. 참고한 표준/구현 문서

- [RFC 9114 HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114): HTTP/3 endpoint discovery와 QUIC 기반 HTTP mapping의 표준 근거.
- [quic-go Serving HTTP/3](https://quic-go.net/docs/http3/server/): HTTP/1.1 또는 HTTP/2 response에서 Alt-Svc로 HTTP/3 지원을 광고하는 구현 패턴.
