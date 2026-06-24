# HAProxy HTTP/3 Negative Control Results

작성일: 2026-06-23  
상태: PASS as negative control  
범위: local HAProxy HTTP/3 frontend가 일반 HTTP/3 요청은 처리하지만 active Connection Migration 시도는 유지하지 못하는지 확인한다.

## 1. 결론

HAProxy 3.4.0 Homebrew build는 HTTP/3 endpoint로 정상 동작했다. 그러나 같은 endpoint에 대해 Cloudflare `quiche-client --perform-migration`을 실행하면 새 source port path validation이 실패했다.

핵심 결과:

| 항목 | 결과 |
| --- | --- |
| HAProxy version | `3.4.0-64a335366`, `USE_QUIC=1`, feature `+QUIC` |
| TLS library | OpenSSL `3.6.2` |
| curl HTTP/3 baseline | PASS, `HTTP/3 200` |
| quiche no-migration baseline | PASS, `1/1 response(s) received` |
| quiche migration attempt | FAIL as expected |
| initial active path | `0.0.0.0:65415 -> 127.0.0.1:8443` |
| attempted migrated path | `0.0.0.0:51818 -> 127.0.0.1:8443` |
| client migration outcome | new path `validation_state=Failed active=false` |
| qlog | `PATH_CHALLENGE` 3회, `PATH_RESPONSE` 0회 |

논문용 한 문장:

> In the HAProxy local negative-control setup, HTTP/3 availability did not imply active Connection Migration support: both curl and quiche completed ordinary HTTP/3 requests, but quiche's migrated path failed validation because the client observed PATH_CHALLENGE probes without a corresponding PATH_RESPONSE.

## 2. Testbed

```text
quiche-client / curl
        |
        | HTTP/3 over QUIC
        v
HAProxy 3.4.0, 127.0.0.1:8443
        |
        | HTTP/1.1
        v
WEBrick origin, 127.0.0.1:18080
```

Config and artifacts:

- `experiments/haproxy-http3-negative-control/haproxy.cfg`
- `experiments/haproxy-http3-negative-control/www/index.html`
- `experiments/haproxy-http3-negative-control/certs/haproxy.pem`
- `experiments/haproxy-http3-negative-control/logs/curl-http3-baseline.log`
- `experiments/haproxy-http3-negative-control/logs/quiche-client-baseline-no-migration.log`
- `experiments/haproxy-http3-negative-control/logs/quiche-client-perform-migration-qlog.log`
- `experiments/haproxy-http3-negative-control/qlog/client-c3c63fc6340d1e40827d1424ed612750c961c634.sqlog`

## 3. Baseline Checks

### 3.1 HAProxy QUIC capability

`haproxy -vv` confirmed:

- build option: `USE_QUIC=1`
- feature list: `+QUIC`
- available mux: `quic`, mode `HTTP`, side `FE|BE`
- OpenSSL runtime: `3.6.2`

### 3.2 curl HTTP/3 baseline

Command:

```bash
/opt/homebrew/opt/curl/bin/curl --http3-only -k -v https://localhost:8443/
```

Result:

- `using HTTP/3`
- `HTTP/3 200`
- response body: `haproxy h3 negative control`

### 3.3 quiche no-migration baseline

Command:

```bash
RUST_LOG=info /opt/homebrew/bin/quiche-client --no-verify --dump-json https://127.0.0.1:8443/
```

Result:

- `1/1 response(s) received in 2.535291ms`
- response status `200`
- final path state: `validation_state=Validated active=true`

This separates the negative-control result from a generic quiche/HAProxy interoperability failure. The same client can complete HTTP/3 through HAProxy when migration is not requested.

## 4. Migration Attempt

Command:

```bash
QLOGDIR=experiments/haproxy-http3-negative-control/qlog \
RUST_LOG=info \
/opt/homebrew/bin/quiche-client \
  --no-verify \
  --enable-active-migration \
  --perform-migration \
  --dump-json \
  https://127.0.0.1:8443/
```

Client log:

- connected from `0.0.0.0:65415`
- attempted new path `0.0.0.0:51818`
- new path failed validation
- final stats:
  - old path: `validation_state=Validated active=true`
  - new path: `validation_state=Failed active=false`

qlog evidence:

| qlog line | event | interpretation |
| ---: | --- | --- |
| 24 | `PATH_CHALLENGE` sent | first probe on attempted migrated path |
| 30 | `PATH_CHALLENGE` sent | retry probe |
| 33 | `PATH_CHALLENGE` sent | retry probe |

No `PATH_RESPONSE` frame appears in the client qlog.

## 5. Interpretation

This is a useful negative control because it shows three layers separately.

| Layer | Observation | Meaning |
| --- | --- | --- |
| HTTP/3 endpoint | curl HTTP/3 request succeeds | HAProxy can terminate HTTP/3 |
| client/proxy interoperability | quiche no-migration request succeeds | quiche and HAProxy interoperate for ordinary H3 |
| Connection Migration | migrated path validation fails | HTTP/3 support is not enough to infer CM support |

The failure is best classified as proxy endpoint path-validation failure. The client sends `PATH_CHALLENGE` on the new path and receives no `PATH_RESPONSE`, so it keeps the original path active and marks the new path failed.

## 6. Limitation

- This is a local loopback experiment, not an AWS or mobile network experiment.
- HAProxy server-side qlog was not collected; the strongest packet-level evidence is from the quiche client qlog.
- This result is version/build-specific: HAProxy `3.4.0` Homebrew build with `USE_QUIC=1` and OpenSSL `3.6.2`.
- The result should be phrased as a negative control for this tested endpoint, not as a universal claim about every future HAProxy release.

## 7. Paper Use

보수적으로 쓸 수 있는 claim:

> Our HAProxy negative control demonstrates that HTTP/3 availability at a proxy endpoint is insufficient evidence of active Connection Migration support. In the tested HAProxy 3.4.0 setup, ordinary HTTP/3 requests completed, but active path migration failed during path validation.

다음 실험은 AWS NLB QUIC feasibility와 `s2n-quic` custom CID provider 검수다.
